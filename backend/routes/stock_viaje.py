from flask import Blueprint, jsonify, request
from datetime import datetime
from decimal import Decimal, InvalidOperation
import sqlite3

from werkzeug.security import check_password_hash, generate_password_hash

from database import conectar_db
from utils import *

bp = Blueprint("stock_viaje", __name__)

@bp.route("/api/vendedores/<int:vendedor_id>/stock-viaje", methods=["GET"])
def obtener_stock_viaje(vendedor_id):
    conexion = conectar_db()
    cursor = conexion.cursor()

    cursor.execute("""
        SELECT id FROM vendedores
        WHERE id = ? AND activo = 1
    """, (vendedor_id,))
    if not cursor.fetchone():
        conexion.close()
        return jsonify({"mensaje": "Vendedor no encontrado o inactivo"}), 404

    cursor.execute("""
        SELECT
            sv.id,
            sv.vendedor_id,
            sv.producto_id,
            sv.cantidad,
            sv.actualizado_en,
            p.codigo,
            p.nombre,
            p.descripcion,
            p.precio_venta,
            p.stock AS stock_central,
            pr.nombre AS proveedor
        FROM stock_viaje sv
        INNER JOIN productos p ON p.id = sv.producto_id
        LEFT JOIN proveedores pr ON pr.id = p.proveedor_id
        WHERE sv.vendedor_id = ?
          AND sv.cantidad > 0
        ORDER BY p.nombre ASC
    """, (vendedor_id,))

    stock = [dict(fila) for fila in cursor.fetchall()]
    conexion.close()
    return jsonify(stock)

@bp.route("/api/vendedores/<int:vendedor_id>/stock-viaje/asignar", methods=["POST"])
def asignar_stock_viaje(vendedor_id):
    datos = request.json or {}

    try:
        producto_id = int(datos.get("producto_id"))
        cantidad = int(datos.get("cantidad"))
    except (TypeError, ValueError):
        return jsonify({
            "mensaje": "Producto y cantidad son obligatorios"
        }), 400

    if cantidad <= 0:
        return jsonify({"mensaje": "La cantidad debe ser mayor a cero"}), 400

    conexion = conectar_db()
    cursor = conexion.cursor()

    try:
        cursor.execute("""
            SELECT id FROM vendedores
            WHERE id = ? AND activo = 1
        """, (vendedor_id,))
        if not cursor.fetchone():
            conexion.close()
            return jsonify({"mensaje": "Vendedor no encontrado o inactivo"}), 404

        cursor.execute("""
            SELECT id, nombre, stock
            FROM productos
            WHERE id = ?
        """, (producto_id,))
        producto = cursor.fetchone()

        if not producto:
            conexion.close()
            return jsonify({"mensaje": "Producto no encontrado"}), 404

        stock_central = int(producto["stock"] or 0)

        if stock_central < cantidad:
            conexion.close()
            return jsonify({
                "mensaje": (
                    f"Stock central insuficiente. Disponible: {stock_central}"
                )
            }), 400

        fecha = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        nuevo_stock_central = stock_central - cantidad

        cursor.execute("""
            SELECT id, cantidad
            FROM stock_viaje
            WHERE vendedor_id = ? AND producto_id = ?
        """, (vendedor_id, producto_id))
        registro = cursor.fetchone()

        if registro:
            nuevo_stock_viaje = int(registro["cantidad"] or 0) + cantidad
            cursor.execute("""
                UPDATE stock_viaje
                SET cantidad = ?, actualizado_en = ?
                WHERE id = ?
            """, (
                nuevo_stock_viaje,
                fecha,
                registro["id"]
            ))
        else:
            nuevo_stock_viaje = cantidad
            cursor.execute("""
                INSERT INTO stock_viaje (
                    vendedor_id, producto_id, cantidad, actualizado_en
                )
                VALUES (?, ?, ?, ?)
            """, (
                vendedor_id,
                producto_id,
                cantidad,
                fecha
            ))

        cursor.execute("""
            UPDATE productos
            SET stock = ?
            WHERE id = ?
        """, (nuevo_stock_central, producto_id))

        cursor.execute("""
            INSERT INTO movimientos_stock_viaje (
                vendedor_id, producto_id, fecha, tipo, cantidad,
                descripcion, stock_viaje_resultante, stock_central_resultante
            )
            VALUES (?, ?, ?, 'Carga', ?, ?, ?, ?)
        """, (
            vendedor_id,
            producto_id,
            fecha,
            cantidad,
            limpiar_texto(datos.get("descripcion")) or "Carga de mercadería",
            nuevo_stock_viaje,
            nuevo_stock_central
        ))

        cursor.execute("""
            INSERT INTO movimientos_stock (
                producto_id, fecha, tipo, cantidad, descripcion, stock_resultante
            )
            VALUES (?, ?, 'Salida a viaje', ?, ?, ?)
        """, (
            producto_id,
            fecha,
            -cantidad,
            f"Mercadería asignada al vendedor #{vendedor_id}",
            nuevo_stock_central
        ))

        conexion.commit()
    except Exception:
        conexion.rollback()
        conexion.close()
        raise

    conexion.close()
    return jsonify({
        "mensaje": "Mercadería asignada al stock en viaje",
        "stock_viaje": nuevo_stock_viaje,
        "stock_central": nuevo_stock_central
    }), 201

@bp.route("/api/vendedores/<int:vendedor_id>/stock-viaje/devolver", methods=["POST"])
def devolver_stock_viaje(vendedor_id):
    datos = request.json or {}

    try:
        producto_id = int(datos.get("producto_id"))
        cantidad = int(datos.get("cantidad"))
    except (TypeError, ValueError):
        return jsonify({
            "mensaje": "Producto y cantidad son obligatorios"
        }), 400

    if cantidad <= 0:
        return jsonify({"mensaje": "La cantidad debe ser mayor a cero"}), 400

    conexion = conectar_db()
    cursor = conexion.cursor()

    cursor.execute("""
        SELECT cantidad
        FROM stock_viaje
        WHERE vendedor_id = ? AND producto_id = ?
    """, (vendedor_id, producto_id))
    registro = cursor.fetchone()

    if not registro or int(registro["cantidad"] or 0) < cantidad:
        conexion.close()
        return jsonify({
            "mensaje": "El vendedor no tiene esa cantidad para devolver"
        }), 400

    cursor.execute("""
        SELECT stock
        FROM productos
        WHERE id = ?
    """, (producto_id,))
    producto = cursor.fetchone()

    if not producto:
        conexion.close()
        return jsonify({"mensaje": "Producto no encontrado"}), 404

    stock_viaje_actual = int(registro["cantidad"] or 0)
    stock_central_actual = int(producto["stock"] or 0)
    nuevo_stock_viaje = stock_viaje_actual - cantidad
    nuevo_stock_central = stock_central_actual + cantidad
    fecha = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    cursor.execute("""
        UPDATE stock_viaje
        SET cantidad = ?, actualizado_en = ?
        WHERE vendedor_id = ? AND producto_id = ?
    """, (
        nuevo_stock_viaje,
        fecha,
        vendedor_id,
        producto_id
    ))

    cursor.execute("""
        UPDATE productos
        SET stock = ?
        WHERE id = ?
    """, (nuevo_stock_central, producto_id))

    cursor.execute("""
        INSERT INTO movimientos_stock_viaje (
            vendedor_id, producto_id, fecha, tipo, cantidad,
            descripcion, stock_viaje_resultante, stock_central_resultante
        )
        VALUES (?, ?, ?, 'Devolución', ?, ?, ?, ?)
    """, (
        vendedor_id,
        producto_id,
        fecha,
        -cantidad,
        limpiar_texto(datos.get("descripcion")) or "Devolución a depósito",
        nuevo_stock_viaje,
        nuevo_stock_central
    ))

    cursor.execute("""
        INSERT INTO movimientos_stock (
            producto_id, fecha, tipo, cantidad, descripcion, stock_resultante
        )
        VALUES (?, ?, 'Retorno de viaje', ?, ?, ?)
    """, (
        producto_id,
        fecha,
        cantidad,
        f"Devolución del vendedor #{vendedor_id}",
        nuevo_stock_central
    ))

    conexion.commit()
    conexion.close()

    return jsonify({
        "mensaje": "Mercadería devuelta correctamente",
        "stock_viaje": nuevo_stock_viaje,
        "stock_central": nuevo_stock_central
    })

@bp.route("/api/vendedores/<int:vendedor_id>/stock-viaje/movimientos", methods=["GET"])
def listar_movimientos_stock_viaje(vendedor_id):
    conexion = conectar_db()
    cursor = conexion.cursor()

    cursor.execute("""
        SELECT
            m.*,
            p.codigo,
            p.nombre AS producto
        FROM movimientos_stock_viaje m
        INNER JOIN productos p ON p.id = m.producto_id
        WHERE m.vendedor_id = ?
        ORDER BY m.id DESC
        LIMIT 200
    """, (vendedor_id,))

    movimientos = [dict(fila) for fila in cursor.fetchall()]
    conexion.close()
    return jsonify(movimientos)

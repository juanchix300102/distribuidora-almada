from flask import Blueprint, jsonify, request
from datetime import datetime
from decimal import Decimal, InvalidOperation
import sqlite3

from werkzeug.security import check_password_hash, generate_password_hash

from database import conectar_db
from utils import *

bp = Blueprint("proveedores", __name__)

@bp.route("/api/proveedores", methods=["GET"])
def listar_proveedores():
    conexion = conectar_db()
    cursor = conexion.cursor()

    cursor.execute("SELECT * FROM proveedores ORDER BY nombre ASC")
    proveedores = cursor.fetchall()

    conexion.close()

    return jsonify([dict(proveedor) for proveedor in proveedores])

@bp.route("/api/proveedores", methods=["POST"])
def agregar_proveedor():
    datos = request.json or {}

    nombre = datos.get("nombre", "").strip()

    if not nombre:
        return jsonify({"mensaje": "El nombre del proveedor es obligatorio"}), 400

    conexion = conectar_db()
    cursor = conexion.cursor()

    cursor.execute("""
        INSERT INTO proveedores (nombre, telefono, direccion, localidad, contacto, observaciones)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (
        nombre,
        datos.get("telefono", ""),
        datos.get("direccion", ""),
        datos.get("localidad", ""),
        datos.get("contacto", ""),
        datos.get("observaciones", "")
    ))

    conexion.commit()
    proveedor_id = cursor.lastrowid
    conexion.close()

    return jsonify({
        "mensaje": "Proveedor agregado correctamente",
        "id": proveedor_id
    }), 201

@bp.route("/api/proveedores/<int:proveedor_id>/productos", methods=["GET"])
def productos_por_proveedor(proveedor_id):
    conexion = conectar_db()
    cursor = conexion.cursor()

    cursor.execute("""
        SELECT
            pp.id AS precio_id,
            p.id AS producto_id,
            p.codigo,
            p.nombre AS producto,
            p.categoria,
            p.stock,
            pp.precio_base,
            pp.bonificacion_1,
            pp.bonificacion_2,
            pp.bonificacion_3,
            pp.iva,
            pp.flete,
            pp.precio_final_compra,
            pp.ganancia,
            pp.precio_venta,
            pp.fecha_actualizacion
        FROM precios_proveedor pp
        INNER JOIN productos p ON pp.producto_id = p.id
        WHERE pp.proveedor_id = ?
        ORDER BY p.nombre ASC
    """, (proveedor_id,))

    productos = cursor.fetchall()
    conexion.close()

    return jsonify([dict(producto) for producto in productos])

@bp.route("/api/proveedores/<int:proveedor_id>/productos", methods=["POST"])
def agregar_producto_a_proveedor(proveedor_id):
    datos = request.json or {}

    nombre = str(datos.get("nombre", "") or "").strip()

    if not nombre:
        return jsonify({"mensaje": "El nombre del producto es obligatorio"}), 400

    variantes = datos.get("variantes")
    if variantes is None:
        variantes = []

    if not isinstance(variantes, list):
        return jsonify({"mensaje": "Las variantes deben enviarse como una lista"}), 400

    precio_base = float(datos.get("precio_base", 0) or 0)
    bonif1 = float(datos.get("bonificacion_1", 0) or 0)
    bonif2 = float(datos.get("bonificacion_2", 0) or 0)
    bonif3 = float(datos.get("bonificacion_3", 0) or 0)
    iva = float(datos.get("iva", 21) or 21)
    flete = float(datos.get("flete", 0) or 0)
    ganancia = float(datos.get("ganancia", 0) or 0)

    precio_final_compra, precio_venta_calculado = calcular_precios(
        precio_base, bonif1, bonif2, bonif3, iva, flete, ganancia
    )

    # Mientras adaptamos todo el frontend, los campos del producto padre
    # reflejan la primera variante. Así las pantallas antiguas siguen funcionando.
    if variantes:
        primera = variantes[0] or {}
        codigo_padre = str(primera.get("codigo", "") or "").strip()
        cantidad_caja_padre = int(primera.get("cantidad_caja", 1) or 1)
        precio_unidad_padre = float(primera.get("precio_unidad", 0) or 0)
        precio_caja_padre = float(primera.get("precio_caja", 0) or 0)
        precio_venta_padre = float(
            primera.get("precio_venta", precio_venta_calculado) or precio_venta_calculado or 0
        )
        stock_padre = sum(int((variante or {}).get("stock", 0) or 0) for variante in variantes)
    else:
        codigo_padre = str(datos.get("codigo", "") or "").strip()
        cantidad_caja_padre = int(datos.get("cantidad_caja", 1) or 1)
        precio_unidad_padre = float(datos.get("precio_unidad", 0) or 0)
        precio_caja_padre = float(datos.get("precio_caja", 0) or 0)
        precio_venta_padre = float(
            datos.get("precio_venta", precio_venta_calculado) or precio_venta_calculado or 0
        )
        stock_padre = int(datos.get("stock", 0) or 0)

    conexion = conectar_db()
    cursor = conexion.cursor()

    try:
        cursor.execute("SELECT id FROM proveedores WHERE id = ?", (proveedor_id,))
        if not cursor.fetchone():
            conexion.close()
            return jsonify({"mensaje": "Proveedor no encontrado"}), 404

        cursor.execute("""
            INSERT INTO productos (
                proveedor_id, codigo, nombre, descripcion, categoria, foto,
                cantidad_caja, precio_unidad, precio_caja, precio_venta, stock,
                foto_origen, foto_palabra_clave
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            proveedor_id,
            codigo_padre,
            nombre,
            datos.get("descripcion", ""),
            datos.get("categoria", ""),
            datos.get("foto", ""),
            cantidad_caja_padre,
            precio_unidad_padre,
            precio_caja_padre,
            precio_venta_padre,
            stock_padre,
            datos.get("foto_origen", ""),
            datos.get("foto_palabra_clave", "")
        ))

        producto_id = cursor.lastrowid

        for variante in variantes:
            variante = variante or {}
            nombre_variante = str(variante.get("nombre_variante", "") or "").strip()

            if not nombre_variante:
                raise ValueError("Todas las variantes deben tener una medida, modelo o nombre")

            cursor.execute("""
                INSERT INTO producto_variantes (
                    producto_id, nombre_variante, codigo,
                    cantidad_caja, precio_unidad, precio_caja,
                    precio_venta, stock, activo
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                producto_id,
                nombre_variante,
                str(variante.get("codigo", "") or "").strip(),
                int(variante.get("cantidad_caja", 1) or 1),
                float(variante.get("precio_unidad", 0) or 0),
                float(variante.get("precio_caja", 0) or 0),
                float(variante.get("precio_venta", precio_venta_calculado) or precio_venta_calculado or 0),
                int(variante.get("stock", 0) or 0),
                1
            ))

        cursor.execute("""
            INSERT INTO precios_proveedor (
                proveedor_id, producto_id, precio_base,
                bonificacion_1, bonificacion_2, bonificacion_3,
                iva, flete, precio_final_compra, ganancia,
                precio_venta, fecha_actualizacion
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            proveedor_id,
            producto_id,
            precio_base,
            bonif1,
            bonif2,
            bonif3,
            iva,
            flete,
            precio_final_compra,
            ganancia,
            precio_venta_padre,
            datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        ))

        conexion.commit()

        return jsonify({
            "mensaje": "Producto agregado al proveedor correctamente",
            "producto_id": producto_id,
            "cantidad_variantes": len(variantes)
        }), 201

    except (ValueError, TypeError) as error:
        conexion.rollback()
        return jsonify({"mensaje": str(error)}), 400
    except Exception as error:
        conexion.rollback()
        print("ERROR CREAR PRODUCTO:", error)
        return jsonify({"mensaje": "No se pudo guardar el producto", "error": str(error)}), 500
    finally:
        conexion.close()

@bp.route("/api/precios/<int:precio_id>", methods=["PUT"])
def actualizar_precio_proveedor(precio_id):
    datos = request.json or {}

    precio_base = float(datos.get("precio_base", 0) or 0)
    bonif1 = float(datos.get("bonificacion_1", 0) or 0)
    bonif2 = float(datos.get("bonificacion_2", 0) or 0)
    bonif3 = float(datos.get("bonificacion_3", 0) or 0)
    iva = float(datos.get("iva", 21) or 21)
    flete = float(datos.get("flete", 0) or 0)
    ganancia = float(datos.get("ganancia", 0) or 0)

    precio_final_compra, precio_venta = calcular_precios(
        precio_base, bonif1, bonif2, bonif3, iva, flete, ganancia
    )

    conexion = conectar_db()
    cursor = conexion.cursor()

    cursor.execute("""
        UPDATE precios_proveedor
        SET precio_base = ?,
            bonificacion_1 = ?,
            bonificacion_2 = ?,
            bonificacion_3 = ?,
            iva = ?,
            flete = ?,
            precio_final_compra = ?,
            ganancia = ?,
            precio_venta = ?,
            fecha_actualizacion = ?
        WHERE id = ?
    """, (
        precio_base,
        bonif1,
        bonif2,
        bonif3,
        iva,
        flete,
        precio_final_compra,
        ganancia,
        precio_venta,
        datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        precio_id
    ))

    cursor.execute("""
        UPDATE productos
        SET precio_venta = ?
        WHERE id = (
            SELECT producto_id FROM precios_proveedor WHERE id = ?
        )
    """, (precio_venta, precio_id))

    conexion.commit()
    conexion.close()

    return jsonify({
        "mensaje": "Precio actualizado correctamente",
        "precio_final_compra": precio_final_compra,
        "precio_venta": precio_venta
    })

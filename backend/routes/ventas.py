from flask import Blueprint, jsonify, request
from datetime import datetime
from decimal import Decimal, InvalidOperation
import sqlite3

from werkzeug.security import check_password_hash, generate_password_hash

from database import conectar_db
from utils import *

bp = Blueprint("ventas", __name__)

def _consultar_ventas(cursor, vendedor_id=None):
    parametros = []
    condicion = ""

    if vendedor_id is not None:
        condicion = "WHERE ve.vendedor_id = ?"
        parametros.append(vendedor_id)

    cursor.execute(f"""
        SELECT
            ve.id,
            ve.vendedor_id,
            ve.cliente_id,
            ve.fecha,
            ve.forma_pago,
            ve.total,
            ve.observaciones,
            v.nombre AS vendedor,
            c.nombre AS cliente,
            c.numero_cliente
        FROM ventas ve
        INNER JOIN vendedores v ON v.id = ve.vendedor_id
        LEFT JOIN clientes c ON c.id = ve.cliente_id
        {condicion}
        ORDER BY ve.id DESC
        LIMIT 300
    """, parametros)

    ventas = [dict(fila) for fila in cursor.fetchall()]

    for venta in ventas:
        cursor.execute("""
            SELECT
                vd.id,
                vd.producto_id,
                vd.cantidad,
                vd.precio_unitario,
                vd.subtotal,
                p.codigo,
                p.nombre AS producto
            FROM venta_detalles vd
            INNER JOIN productos p ON p.id = vd.producto_id
            WHERE vd.venta_id = ?
            ORDER BY vd.id ASC
        """, (venta["id"],))
        venta["detalles"] = [dict(fila) for fila in cursor.fetchall()]

    return ventas

@bp.route("/api/ventas", methods=["GET"])
def listar_ventas():
    conexion = conectar_db()
    cursor = conexion.cursor()
    ventas = _consultar_ventas(cursor)
    conexion.close()
    return jsonify(ventas)

@bp.route("/api/vendedores/<int:vendedor_id>/ventas", methods=["GET"])
def listar_ventas_vendedor(vendedor_id):
    conexion = conectar_db()
    cursor = conexion.cursor()
    ventas = _consultar_ventas(cursor, vendedor_id)
    conexion.close()
    return jsonify(ventas)

@bp.route("/api/vendedores/<int:vendedor_id>/ventas", methods=["POST"])
def registrar_venta_vendedor(vendedor_id):
    datos = request.json or {}
    items = datos.get("items") or []
    forma_pago = limpiar_texto(datos.get("forma_pago"))
    observaciones = limpiar_texto(datos.get("observaciones"))

    cliente_id = datos.get("cliente_id")
    if cliente_id in ("", None):
        cliente_id = None
    else:
        try:
            cliente_id = int(cliente_id)
        except (TypeError, ValueError):
            return jsonify({"mensaje": "Cliente inválido"}), 400

    if not forma_pago:
        return jsonify({"mensaje": "La forma de pago es obligatoria"}), 400

    if not isinstance(items, list) or len(items) == 0:
        return jsonify({"mensaje": "La venta debe tener al menos un producto"}), 400

    es_cuenta_corriente = forma_pago.strip().lower() == "cuenta corriente"

    if cliente_id is None:
        return jsonify({
            "mensaje": "Seleccioná un cliente para registrar la venta"
        }), 400

    conexion = conectar_db()
    cursor = conexion.cursor()

    try:
        cursor.execute("""
            SELECT id, nombre
            FROM vendedores
            WHERE id = ? AND activo = 1
        """, (vendedor_id,))
        vendedor = cursor.fetchone()

        if not vendedor:
            conexion.close()
            return jsonify({"mensaje": "Vendedor no encontrado o inactivo"}), 404

        cliente = None
        if cliente_id is not None:
            cursor.execute("""
                SELECT id, nombre, saldo_actual
                FROM clientes
                WHERE id = ?
            """, (cliente_id,))
            cliente = cursor.fetchone()

            if not cliente:
                conexion.close()
                return jsonify({"mensaje": "Cliente no encontrado"}), 404

        detalles_preparados = []
        total = 0.0

        for item in items:
            try:
                producto_id = int(item.get("producto_id"))
                cantidad = int(item.get("cantidad"))
            except (TypeError, ValueError, AttributeError):
                conexion.close()
                return jsonify({"mensaje": "Hay un producto inválido en la venta"}), 400

            if cantidad <= 0:
                conexion.close()
                return jsonify({"mensaje": "Las cantidades deben ser mayores a cero"}), 400

            cursor.execute("""
                SELECT
                    sv.cantidad AS stock_viaje,
                    p.id,
                    p.codigo,
                    p.nombre,
                    p.precio_venta
                FROM stock_viaje sv
                INNER JOIN productos p ON p.id = sv.producto_id
                WHERE sv.vendedor_id = ?
                  AND sv.producto_id = ?
            """, (vendedor_id, producto_id))
            producto = cursor.fetchone()

            if not producto:
                conexion.close()
                return jsonify({
                    "mensaje": "Uno de los productos no pertenece al stock en viaje"
                }), 400

            stock_disponible = int(producto["stock_viaje"] or 0)

            if stock_disponible < cantidad:
                conexion.close()
                return jsonify({
                    "mensaje": (
                        f"Stock insuficiente de {producto['nombre']}. "
                        f"Disponible: {stock_disponible}"
                    )
                }), 400

            precio_unitario = round(float(producto["precio_venta"] or 0), 2)
            subtotal = round(precio_unitario * cantidad, 2)
            total = round(total + subtotal, 2)

            detalles_preparados.append({
                "producto_id": producto_id,
                "cantidad": cantidad,
                "precio_unitario": precio_unitario,
                "subtotal": subtotal,
                "stock_anterior": stock_disponible,
                "nombre": producto["nombre"]
            })

        fecha = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        cursor.execute("""
            INSERT INTO ventas (
                vendedor_id, cliente_id, fecha,
                forma_pago, total, observaciones
            )
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            vendedor_id,
            cliente_id,
            fecha,
            forma_pago,
            total,
            observaciones
        ))
        venta_id = cursor.lastrowid

        for detalle in detalles_preparados:
            nuevo_stock_viaje = detalle["stock_anterior"] - detalle["cantidad"]

            cursor.execute("""
                INSERT INTO venta_detalles (
                    venta_id, producto_id, cantidad,
                    precio_unitario, subtotal
                )
                VALUES (?, ?, ?, ?, ?)
            """, (
                venta_id,
                detalle["producto_id"],
                detalle["cantidad"],
                detalle["precio_unitario"],
                detalle["subtotal"]
            ))

            cursor.execute("""
                UPDATE stock_viaje
                SET cantidad = ?, actualizado_en = ?
                WHERE vendedor_id = ? AND producto_id = ?
            """, (
                nuevo_stock_viaje,
                fecha,
                vendedor_id,
                detalle["producto_id"]
            ))

            cursor.execute("""
                SELECT stock FROM productos WHERE id = ?
            """, (detalle["producto_id"],))
            stock_central = int(cursor.fetchone()["stock"] or 0)

            cursor.execute("""
                INSERT INTO movimientos_stock_viaje (
                    vendedor_id, producto_id, fecha, tipo, cantidad,
                    descripcion, stock_viaje_resultante, stock_central_resultante
                )
                VALUES (?, ?, ?, 'Venta', ?, ?, ?, ?)
            """, (
                vendedor_id,
                detalle["producto_id"],
                fecha,
                -detalle["cantidad"],
                f"Venta #{venta_id}",
                nuevo_stock_viaje,
                stock_central
            ))

        if es_cuenta_corriente and cliente is not None:
            saldo_anterior = float(cliente["saldo_actual"] or 0)
            nuevo_saldo = round(saldo_anterior + total, 2)

            cursor.execute("""
                INSERT INTO cuentas_corrientes (
                    cliente_id, fecha, tipo, descripcion, comprobante,
                    debe, haber, saldo, medio_pago
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                cliente_id,
                fecha,
                "Venta vendedor",
                f"Venta #{venta_id} - {vendedor['nombre']}",
                str(venta_id),
                total,
                0,
                nuevo_saldo,
                "Cuenta corriente"
            ))

            cursor.execute("""
                UPDATE clientes
                SET saldo_actual = ?
                WHERE id = ?
            """, (nuevo_saldo, cliente_id))

        conexion.commit()
    except Exception:
        conexion.rollback()
        conexion.close()
        raise

    conexion.close()

    return jsonify({
        "mensaje": "Venta registrada correctamente",
        "venta_id": venta_id,
        "total": total
    }), 201

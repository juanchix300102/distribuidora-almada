from flask import Blueprint, jsonify, request
from datetime import datetime
from decimal import Decimal, InvalidOperation
import sqlite3

from werkzeug.security import check_password_hash, generate_password_hash

from database import conectar_db
from utils import *

bp = Blueprint("cuentas_corrientes", __name__)

@bp.route("/api/clientes/<int:cliente_id>/cuenta-corriente", methods=["GET"])
def obtener_cuenta_corriente(cliente_id):
    conexion = conectar_db()
    cursor = conexion.cursor()

    cursor.execute("SELECT * FROM clientes WHERE id = ?", (cliente_id,))
    cliente = cursor.fetchone()

    if not cliente:
        conexion.close()
        return jsonify({
            "mensaje": "Cliente no encontrado"
        }), 404

    cursor.execute("""
        SELECT *
        FROM cuentas_corrientes
        WHERE cliente_id = ?
        ORDER BY id DESC
    """, (cliente_id,))

    movimientos = cursor.fetchall()

    conexion.close()

    return jsonify({
        "cliente": dict(cliente),
        "saldo_actual": cliente["saldo_actual"],
        "movimientos": [dict(movimiento) for movimiento in movimientos]
    })

@bp.route("/api/clientes/<int:cliente_id>/cuenta-corriente/movimiento", methods=["POST"])
def agregar_movimiento_cuenta_corriente(cliente_id):
    datos = request.json or {}

    descripcion = datos.get("descripcion", "").strip()
    monto = float(datos.get("monto", 0) or 0)
    tipo = datos.get("tipo", "Venta").strip()

    if not descripcion:
        return jsonify({
            "mensaje": "La descripción es obligatoria"
        }), 400

    if monto <= 0:
        return jsonify({
            "mensaje": "El monto debe ser mayor a cero"
        }), 400

    conexion = conectar_db()
    cursor = conexion.cursor()

    cursor.execute("SELECT * FROM clientes WHERE id = ?", (cliente_id,))
    cliente = cursor.fetchone()

    if not cliente:
        conexion.close()
        return jsonify({
            "mensaje": "Cliente no encontrado"
        }), 404

    saldo_anterior = float(cliente["saldo_actual"] or 0)
    nuevo_saldo = saldo_anterior + monto

    cursor.execute("""
        INSERT INTO cuentas_corrientes (
            cliente_id, fecha, tipo, descripcion, comprobante,
            debe, haber, saldo, medio_pago
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        cliente_id,
        datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        tipo,
        descripcion,
        datos.get("comprobante", ""),
        monto,
        0,
        nuevo_saldo,
        ""
    ))

    cursor.execute("""
        UPDATE clientes
        SET saldo_actual = ?
        WHERE id = ?
    """, (nuevo_saldo, cliente_id))

    conexion.commit()
    conexion.close()

    return jsonify({
        "mensaje": "Movimiento agregado correctamente",
        "saldo_actual": nuevo_saldo
    }), 201

@bp.route("/api/clientes/<int:cliente_id>/pagos", methods=["POST"])
def registrar_pago_cliente(cliente_id):
    datos = request.json or {}

    monto = float(datos.get("monto", 0) or 0)
    medio_pago = datos.get("medio_pago", "").strip()
    comprobante = datos.get("comprobante", "").strip()
    observaciones = datos.get("observaciones", "").strip()

    if monto <= 0:
        return jsonify({
            "mensaje": "El monto del pago debe ser mayor a cero"
        }), 400

    if not medio_pago:
        return jsonify({
            "mensaje": "El medio de pago es obligatorio"
        }), 400

    conexion = conectar_db()
    cursor = conexion.cursor()

    cursor.execute("SELECT * FROM clientes WHERE id = ?", (cliente_id,))
    cliente = cursor.fetchone()

    if not cliente:
        conexion.close()
        return jsonify({
            "mensaje": "Cliente no encontrado"
        }), 404

    saldo_anterior = float(cliente["saldo_actual"] or 0)
    nuevo_saldo = saldo_anterior - monto

    if nuevo_saldo < 0:
        nuevo_saldo = 0

    fecha = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    cursor.execute("""
        INSERT INTO pagos (
            cliente_id, fecha, monto, medio_pago, comprobante, observaciones
        )
        VALUES (?, ?, ?, ?, ?, ?)
    """, (
        cliente_id,
        fecha,
        monto,
        medio_pago,
        comprobante,
        observaciones
    ))

    cursor.execute("""
        INSERT INTO cuentas_corrientes (
            cliente_id, fecha, tipo, descripcion, comprobante,
            debe, haber, saldo, medio_pago
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        cliente_id,
        fecha,
        "Pago",
        observaciones if observaciones else "Pago registrado",
        comprobante,
        0,
        monto,
        nuevo_saldo,
        medio_pago
    ))

    cursor.execute("""
        UPDATE clientes
        SET saldo_actual = ?
        WHERE id = ?
    """, (nuevo_saldo, cliente_id))

    conexion.commit()
    conexion.close()

    return jsonify({
        "mensaje": "Pago registrado correctamente",
        "saldo_actual": nuevo_saldo
    }), 201

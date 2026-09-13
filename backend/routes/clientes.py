from flask import Blueprint, jsonify, request
from datetime import datetime
from decimal import Decimal, InvalidOperation
import sqlite3

from werkzeug.security import check_password_hash, generate_password_hash

from database import conectar_db
from utils import *

bp = Blueprint("clientes", __name__)

@bp.route("/api/clientes", methods=["GET"])
def listar_clientes():
    conexion = conectar_db()
    cursor = conexion.cursor()

    cursor.execute("SELECT * FROM clientes ORDER BY nombre ASC")

    clientes = cursor.fetchall()
    conexion.close()

    return jsonify([dict(cliente) for cliente in clientes])

@bp.route("/api/clientes", methods=["POST"])
def agregar_cliente():
    datos = request.json or {}

    nombre = datos.get("nombre", "").strip()

    if not nombre:
        return jsonify({"mensaje": "El nombre del cliente es obligatorio"}), 400

    conexion = conectar_db()
    cursor = conexion.cursor()

    numero_cliente = datos.get("numero_cliente") or generar_numero_cliente(cursor)

    cursor.execute("""
        INSERT INTO clientes (
            numero_cliente, nombre, direccion, localidad, telefono, email, observaciones, saldo_actual
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        numero_cliente,
        nombre,
        datos.get("direccion", ""),
        datos.get("localidad", ""),
        datos.get("telefono", ""),
        datos.get("email", ""),
        datos.get("observaciones", ""),
        float(datos.get("saldo_actual", 0) or 0)
    ))

    cliente_id = cursor.lastrowid

    conexion.commit()
    conexion.close()

    return jsonify({
        "mensaje": "Cliente creado correctamente",
        "cliente_id": cliente_id,
        "numero_cliente": numero_cliente
    }), 201

@bp.route("/api/clientes/<int:id>", methods=["PUT"])
def editar_cliente(id):
    datos = request.json or {}

    conexion = conectar_db()
    cursor = conexion.cursor()

    cursor.execute("""
        UPDATE clientes
        SET numero_cliente = ?,
            nombre = ?,
            direccion = ?,
            localidad = ?,
            telefono = ?,
            email = ?,
            observaciones = ?,
            saldo_actual = ?
        WHERE id = ?
    """, (
        datos.get("numero_cliente"),
        datos.get("nombre"),
        datos.get("direccion", ""),
        datos.get("localidad", ""),
        datos.get("telefono", ""),
        datos.get("email", ""),
        datos.get("observaciones", ""),
        float(datos.get("saldo_actual", 0) or 0),
        id
    ))

    conexion.commit()
    conexion.close()

    return jsonify({
        "mensaje": "Cliente actualizado correctamente"
    })

@bp.route("/api/clientes/<int:id>", methods=["DELETE"])
def eliminar_cliente(id):
    conexion = conectar_db()
    cursor = conexion.cursor()

    cursor.execute("DELETE FROM cuentas_corrientes WHERE cliente_id = ?", (id,))
    cursor.execute("DELETE FROM pagos WHERE cliente_id = ?", (id,))
    cursor.execute("DELETE FROM saldos WHERE cliente_id = ?", (id,))
    cursor.execute("DELETE FROM clientes WHERE id = ?", (id,))

    conexion.commit()
    conexion.close()

    return jsonify({
        "mensaje": "Cliente eliminado correctamente"
    })

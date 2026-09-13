from flask import Blueprint, jsonify, request
from datetime import datetime
from decimal import Decimal, InvalidOperation
import sqlite3

from werkzeug.security import check_password_hash, generate_password_hash

from database import conectar_db
from utils import *

bp = Blueprint("auth", __name__)

@bp.route("/api/login", methods=["POST"])
def login():
    datos = request.json or {}

    usuario = datos.get("usuario", "").strip()
    contrasena = datos.get("contrasena", "").strip()

    if not usuario or not contrasena:
        return jsonify({
            "mensaje": "Usuario y contraseña son obligatorios"
        }), 400

    conexion = conectar_db()
    cursor = conexion.cursor()

    cursor.execute("""
        SELECT id, usuario, contrasena, rol, activo
        FROM usuarios
        WHERE usuario = ?
    """, (usuario,))

    usuario_encontrado = cursor.fetchone()

    if (
        not usuario_encontrado
        or not usuario_encontrado["activo"]
        or not check_password_hash(
            usuario_encontrado["contrasena"],
            contrasena
        )
    ):
        conexion.close()
        return jsonify({
            "mensaje": "Usuario o contraseña incorrectos"
        }), 401

    respuesta = {
        "mensaje": "Login correcto",
        "usuario_id": usuario_encontrado["id"],
        "usuario": usuario_encontrado["usuario"],
        "rol": usuario_encontrado["rol"]
    }

    if usuario_encontrado["rol"] == "vendedor":
        cursor.execute("""
            SELECT id, nombre, activo
            FROM vendedores
            WHERE usuario_id = ?
        """, (usuario_encontrado["id"],))
        vendedor = cursor.fetchone()

        if not vendedor or not vendedor["activo"]:
            conexion.close()
            return jsonify({
                "mensaje": "El vendedor no está habilitado"
            }), 403

        respuesta["vendedor_id"] = vendedor["id"]
        respuesta["nombre"] = vendedor["nombre"]

    conexion.close()
    return jsonify(respuesta)

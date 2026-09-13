from flask import Blueprint, jsonify, request
from datetime import datetime
from decimal import Decimal, InvalidOperation
import sqlite3

from werkzeug.security import check_password_hash, generate_password_hash

from database import conectar_db
from utils import *

bp = Blueprint("vendedores", __name__)

@bp.route("/api/vendedores", methods=["GET"])
def listar_vendedores():
    conexion = conectar_db()
    cursor = conexion.cursor()

    cursor.execute("""
        SELECT
            v.id,
            v.usuario_id,
            v.nombre,
            v.telefono,
            v.zona,
            v.observaciones,
            v.activo,
            v.fecha_alta,
            u.usuario
        FROM vendedores v
        INNER JOIN usuarios u ON u.id = v.usuario_id
        ORDER BY v.activo DESC, v.nombre ASC
    """)

    vendedores = [dict(fila) for fila in cursor.fetchall()]
    conexion.close()
    return jsonify(vendedores)

@bp.route("/api/vendedores", methods=["POST"])
def crear_vendedor():
    datos = request.json or {}

    nombre = limpiar_texto(datos.get("nombre"))
    usuario = limpiar_texto(datos.get("usuario"))
    contrasena = limpiar_texto(datos.get("contrasena"))

    if not nombre:
        return jsonify({"mensaje": "El nombre del vendedor es obligatorio"}), 400

    if not usuario:
        return jsonify({"mensaje": "El usuario del vendedor es obligatorio"}), 400

    if len(contrasena) < 4:
        return jsonify({"mensaje": "La contraseña debe tener al menos 4 caracteres"}), 400

    conexion = conectar_db()
    cursor = conexion.cursor()

    try:
        cursor.execute("""
            INSERT INTO usuarios (usuario, contrasena, rol, activo)
            VALUES (?, ?, 'vendedor', 1)
        """, (
            usuario,
            generate_password_hash(contrasena)
        ))
        usuario_id = cursor.lastrowid

        fecha_alta = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute("""
            INSERT INTO vendedores (
                usuario_id, nombre, telefono, zona,
                observaciones, activo, fecha_alta
            )
            VALUES (?, ?, ?, ?, ?, 1, ?)
        """, (
            usuario_id,
            nombre,
            limpiar_texto(datos.get("telefono")),
            limpiar_texto(datos.get("zona")),
            limpiar_texto(datos.get("observaciones")),
            fecha_alta
        ))

        vendedor_id = cursor.lastrowid
        conexion.commit()
    except sqlite3.IntegrityError:
        conexion.rollback()
        conexion.close()
        return jsonify({
            "mensaje": "Ese nombre de usuario ya está en uso"
        }), 409

    conexion.close()
    return jsonify({
        "mensaje": "Vendedor creado correctamente",
        "id": vendedor_id,
        "usuario_id": usuario_id
    }), 201

@bp.route("/api/vendedores/<int:vendedor_id>", methods=["PUT"])
def actualizar_vendedor(vendedor_id):
    datos = request.json or {}
    nombre = limpiar_texto(datos.get("nombre"))
    usuario = limpiar_texto(datos.get("usuario"))
    contrasena = limpiar_texto(datos.get("contrasena"))
    activo = 1 if datos.get("activo", True) else 0

    if not nombre or not usuario:
        return jsonify({
            "mensaje": "Nombre y usuario son obligatorios"
        }), 400

    conexion = conectar_db()
    cursor = conexion.cursor()

    cursor.execute("""
        SELECT usuario_id
        FROM vendedores
        WHERE id = ?
    """, (vendedor_id,))
    vendedor = cursor.fetchone()

    if not vendedor:
        conexion.close()
        return jsonify({"mensaje": "Vendedor no encontrado"}), 404

    try:
        cursor.execute("""
            UPDATE vendedores
            SET nombre = ?, telefono = ?, zona = ?,
                observaciones = ?, activo = ?
            WHERE id = ?
        """, (
            nombre,
            limpiar_texto(datos.get("telefono")),
            limpiar_texto(datos.get("zona")),
            limpiar_texto(datos.get("observaciones")),
            activo,
            vendedor_id
        ))

        if contrasena:
            cursor.execute("""
                UPDATE usuarios
                SET usuario = ?, contrasena = ?, activo = ?
                WHERE id = ?
            """, (
                usuario,
                generate_password_hash(contrasena),
                activo,
                vendedor["usuario_id"]
            ))
        else:
            cursor.execute("""
                UPDATE usuarios
                SET usuario = ?, activo = ?
                WHERE id = ?
            """, (
                usuario,
                activo,
                vendedor["usuario_id"]
            ))

        conexion.commit()
    except sqlite3.IntegrityError:
        conexion.rollback()
        conexion.close()
        return jsonify({
            "mensaje": "Ese nombre de usuario ya está en uso"
        }), 409

    conexion.close()
    return jsonify({"mensaje": "Vendedor actualizado correctamente"})

@bp.route("/api/vendedores/<int:vendedor_id>", methods=["DELETE"])
def desactivar_vendedor(vendedor_id):
    conexion = conectar_db()
    cursor = conexion.cursor()

    cursor.execute("""
        SELECT usuario_id
        FROM vendedores
        WHERE id = ?
    """, (vendedor_id,))
    vendedor = cursor.fetchone()

    if not vendedor:
        conexion.close()
        return jsonify({"mensaje": "Vendedor no encontrado"}), 404

    cursor.execute("""
        UPDATE vendedores SET activo = 0 WHERE id = ?
    """, (vendedor_id,))
    cursor.execute("""
        UPDATE usuarios SET activo = 0 WHERE id = ?
    """, (vendedor["usuario_id"],))

    conexion.commit()
    conexion.close()

    return jsonify({"mensaje": "Vendedor desactivado correctamente"})

@bp.route("/api/vendedores/por-usuario/<int:usuario_id>", methods=["GET"])
def vendedor_por_usuario(usuario_id):
    conexion = conectar_db()
    cursor = conexion.cursor()

    cursor.execute("""
        SELECT
            v.id, v.nombre, v.telefono, v.zona,
            v.observaciones, v.activo, u.usuario
        FROM vendedores v
        INNER JOIN usuarios u ON u.id = v.usuario_id
        WHERE v.usuario_id = ?
    """, (usuario_id,))

    vendedor = cursor.fetchone()
    conexion.close()

    if not vendedor:
        return jsonify({"mensaje": "Vendedor no encontrado"}), 404

    return jsonify(dict(vendedor))

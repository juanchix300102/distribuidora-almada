from flask import Blueprint, jsonify, request
from datetime import datetime
from decimal import Decimal, InvalidOperation
import sqlite3

from werkzeug.security import check_password_hash, generate_password_hash

from database import conectar_db
from utils import *

bp = Blueprint("catalogo_visual", __name__)

@bp.route("/api/vendedores/<int:vendedor_id>/catalogo-visual", methods=["GET"])
def obtener_catalogo_visual(vendedor_id):
    """Catálogo para mostrar al cliente durante la venta ambulante.

    La respuesta excluye precios, costos, proveedores y cantidades internas.
    Solo informa si cada producto está disponible en el stock móvil del
    vendedor indicado.
    """
    conexion = conectar_db()
    cursor = conexion.cursor()

    cursor.execute("""
        SELECT id, nombre, activo
        FROM vendedores
        WHERE id = ?
    """, (vendedor_id,))
    vendedor = cursor.fetchone()

    if not vendedor or not vendedor["activo"]:
        conexion.close()
        return jsonify({
            "mensaje": "Vendedor no encontrado o inactivo"
        }), 404

    cursor.execute("""
        SELECT
            p.id,
            p.codigo,
            p.nombre,
            p.descripcion,
            p.categoria,
            p.foto,
            COALESCE(sv.cantidad, 0) AS cantidad_viaje
        FROM productos p
        LEFT JOIN stock_viaje sv
          ON sv.producto_id = p.id
         AND sv.vendedor_id = ?
        ORDER BY p.nombre COLLATE NOCASE ASC, p.id ASC
    """, (vendedor_id,))
    productos = cursor.fetchall()

    cursor.execute("""
        SELECT
            id,
            producto_id,
            nombre_variante,
            codigo
        FROM producto_variantes
        WHERE activo = 1
        ORDER BY producto_id ASC, nombre_variante COLLATE NOCASE ASC, id ASC
    """)

    variantes_por_producto = {}
    for variante in cursor.fetchall():
        producto_id = variante["producto_id"]
        variantes_por_producto.setdefault(producto_id, []).append({
            "id": variante["id"],
            "nombre_variante": variante["nombre_variante"],
            "codigo": variante["codigo"]
        })

    catalogo = []
    for producto in productos:
        catalogo.append({
            "id": producto["id"],
            "codigo": producto["codigo"] or "",
            "nombre": producto["nombre"],
            "descripcion": producto["descripcion"] or "",
            "categoria": producto["categoria"] or "Sin categoría",
            "foto": producto["foto"] or "",
            "disponible": int(producto["cantidad_viaje"] or 0) > 0,
            "variantes": variantes_por_producto.get(producto["id"], [])
        })

    conexion.close()

    respuesta = jsonify({
        "vendedor_id": vendedor["id"],
        "vendedor": vendedor["nombre"],
        "actualizado_en": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "productos": catalogo
    })
    respuesta.headers["Cache-Control"] = "no-store"
    return respuesta

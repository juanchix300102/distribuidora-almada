from flask import Blueprint, jsonify, request
from datetime import datetime
from decimal import Decimal, InvalidOperation
import sqlite3

from werkzeug.security import check_password_hash, generate_password_hash

from database import conectar_db
from utils import *

bp = Blueprint("productos", __name__)

@bp.route("/api/productos", methods=["GET"])
def listar_productos():
    conexion = conectar_db()
    cursor = conexion.cursor()

    cursor.execute("""
        SELECT
            p.*,
            pr.nombre AS proveedor
        FROM productos p
        LEFT JOIN proveedores pr ON p.proveedor_id = pr.id
        ORDER BY p.id DESC
    """)

    productos = cursor.fetchall()
    lista = []

    for producto in productos:
        cursor.execute("""
            SELECT
                id,
                producto_id,
                nombre_variante,
                codigo,
                cantidad_caja,
                precio_unidad,
                precio_caja,
                precio_venta,
                stock,
                activo
            FROM producto_variantes
            WHERE producto_id = ?
              AND activo = 1
            ORDER BY id ASC
        """, (producto["id"],))

        variantes = [dict(variante) for variante in cursor.fetchall()]

        lista.append({
            "id": producto["id"],
            "proveedor_id": producto["proveedor_id"],
            "proveedor": producto["proveedor"],
            "codigo": producto["codigo"],
            "nombre": producto["nombre"],
            "descripcion": producto["descripcion"],
            "categoria": producto["categoria"],
            "foto": producto["foto"],
            "foto_origen": producto["foto_origen"] if "foto_origen" in producto.keys() else "",
            "foto_palabra_clave": producto["foto_palabra_clave"] if "foto_palabra_clave" in producto.keys() else "",
            "cantidad_caja": producto["cantidad_caja"],
            "precio_unidad": producto["precio_unidad"],
            "precio_caja": producto["precio_caja"],
            "precio": producto["precio_venta"],
            "precio_venta": producto["precio_venta"],
            "stock": producto["stock"],
            "variantes": variantes,
            "cantidad_variantes": len(variantes)
        })

    conexion.close()
    return jsonify(lista)

@bp.route("/api/productos/<int:id>", methods=["PUT"])
def editar_producto(id):
    datos = request.json or {}

    nombre = str(datos.get("nombre", "") or "").strip()
    if not nombre:
        return jsonify({"mensaje": "El nombre del producto es obligatorio"}), 400

    conexion = conectar_db()
    cursor = conexion.cursor()

    try:
        cursor.execute("SELECT * FROM productos WHERE id = ?", (id,))
        producto_actual = cursor.fetchone()

        if not producto_actual:
            conexion.close()
            return jsonify({"mensaje": "Producto no encontrado"}), 404

        tiene_variantes_en_payload = "variantes" in datos
        variantes = datos.get("variantes", []) if tiene_variantes_en_payload else None

        if tiene_variantes_en_payload and not isinstance(variantes, list):
            conexion.close()
            return jsonify({"mensaje": "Las variantes deben enviarse como una lista"}), 400

        if tiene_variantes_en_payload and variantes:
            primera = variantes[0] or {}
            codigo_padre = str(primera.get("codigo", "") or "").strip()
            cantidad_caja_padre = int(primera.get("cantidad_caja", 1) or 1)
            precio_unidad_padre = float(primera.get("precio_unidad", 0) or 0)
            precio_caja_padre = float(primera.get("precio_caja", 0) or 0)
            precio_venta_padre = float(primera.get("precio_venta", 0) or 0)
            stock_padre = sum(int((variante or {}).get("stock", 0) or 0) for variante in variantes)
        else:
            codigo_padre = datos.get("codigo", producto_actual["codigo"] or "")
            cantidad_caja_padre = int(datos.get("cantidad_caja", producto_actual["cantidad_caja"] or 1) or 1)
            precio_unidad_padre = float(datos.get("precio_unidad", producto_actual["precio_unidad"] or 0) or 0)
            precio_caja_padre = float(datos.get("precio_caja", producto_actual["precio_caja"] or 0) or 0)
            precio_venta_padre = float(
                datos.get("precio_venta", datos.get("precio", producto_actual["precio_venta"] or 0)) or 0
            )
            stock_padre = int(datos.get("stock", producto_actual["stock"] or 0) or 0)

        cursor.execute("""
            UPDATE productos
            SET codigo = ?,
                nombre = ?,
                descripcion = ?,
                categoria = ?,
                foto = ?,
                cantidad_caja = ?,
                precio_unidad = ?,
                precio_caja = ?,
                precio_venta = ?,
                stock = ?,
                foto_origen = ?,
                foto_palabra_clave = ?
            WHERE id = ?
        """, (
            codigo_padre,
            nombre,
            datos.get("descripcion", producto_actual["descripcion"] or ""),
            datos.get("categoria", producto_actual["categoria"] or ""),
            datos.get("foto", producto_actual["foto"] or ""),
            cantidad_caja_padre,
            precio_unidad_padre,
            precio_caja_padre,
            precio_venta_padre,
            stock_padre,
            datos.get("foto_origen", producto_actual["foto_origen"] if "foto_origen" in producto_actual.keys() else ""),
            datos.get("foto_palabra_clave", producto_actual["foto_palabra_clave"] if "foto_palabra_clave" in producto_actual.keys() else ""),
            id
        ))

        if tiene_variantes_en_payload:
            ids_recibidos = []

            for variante in variantes:
                variante = variante or {}
                nombre_variante = str(variante.get("nombre_variante", "") or "").strip()

                if not nombre_variante:
                    raise ValueError("Todas las variantes deben tener una medida, modelo o nombre")

                variante_id = variante.get("id")

                if variante_id:
                    cursor.execute("""
                        SELECT id
                        FROM producto_variantes
                        WHERE id = ? AND producto_id = ?
                    """, (variante_id, id))

                    existe = cursor.fetchone()

                    if existe:
                        cursor.execute("""
                            UPDATE producto_variantes
                            SET nombre_variante = ?,
                                codigo = ?,
                                cantidad_caja = ?,
                                precio_unidad = ?,
                                precio_caja = ?,
                                precio_venta = ?,
                                stock = ?,
                                activo = 1
                            WHERE id = ? AND producto_id = ?
                        """, (
                            nombre_variante,
                            str(variante.get("codigo", "") or "").strip(),
                            int(variante.get("cantidad_caja", 1) or 1),
                            float(variante.get("precio_unidad", 0) or 0),
                            float(variante.get("precio_caja", 0) or 0),
                            float(variante.get("precio_venta", 0) or 0),
                            int(variante.get("stock", 0) or 0),
                            variante_id,
                            id
                        ))
                        ids_recibidos.append(int(variante_id))
                        continue

                cursor.execute("""
                    INSERT INTO producto_variantes (
                        producto_id, nombre_variante, codigo,
                        cantidad_caja, precio_unidad, precio_caja,
                        precio_venta, stock, activo
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    id,
                    nombre_variante,
                    str(variante.get("codigo", "") or "").strip(),
                    int(variante.get("cantidad_caja", 1) or 1),
                    float(variante.get("precio_unidad", 0) or 0),
                    float(variante.get("precio_caja", 0) or 0),
                    float(variante.get("precio_venta", 0) or 0),
                    int(variante.get("stock", 0) or 0),
                    1
                ))
                ids_recibidos.append(cursor.lastrowid)

            if ids_recibidos:
                placeholders = ",".join("?" for _ in ids_recibidos)
                cursor.execute(
                    f"DELETE FROM producto_variantes WHERE producto_id = ? AND id NOT IN ({placeholders})",
                    [id] + ids_recibidos
                )
            else:
                cursor.execute("DELETE FROM producto_variantes WHERE producto_id = ?", (id,))

        conexion.commit()

        return jsonify({
            "mensaje": "Producto actualizado correctamente",
            "producto_id": id,
            "cantidad_variantes": len(variantes) if tiene_variantes_en_payload else None
        })

    except (ValueError, TypeError) as error:
        conexion.rollback()
        return jsonify({"mensaje": str(error)}), 400
    except Exception as error:
        conexion.rollback()
        print("ERROR EDITAR PRODUCTO:", error)
        return jsonify({"mensaje": "No se pudo actualizar el producto", "error": str(error)}), 500
    finally:
        conexion.close()

@bp.route("/api/productos/<int:id>", methods=["DELETE"])
def eliminar_producto(id):
    conexion = conectar_db()
    cursor = conexion.cursor()

    try:
        cursor.execute("SELECT id FROM productos WHERE id = ?", (id,))
        if not cursor.fetchone():
            conexion.close()
            return jsonify({"mensaje": "Producto no encontrado"}), 404

        cursor.execute("DELETE FROM producto_variantes WHERE producto_id = ?", (id,))
        cursor.execute("DELETE FROM precios_proveedor WHERE producto_id = ?", (id,))
        cursor.execute("DELETE FROM productos WHERE id = ?", (id,))

        conexion.commit()

        return jsonify({
            "mensaje": "Producto y sus variantes eliminados correctamente"
        })

    except Exception as error:
        conexion.rollback()
        print("ERROR ELIMINAR PRODUCTO:", error)
        return jsonify({"mensaje": "No se pudo eliminar el producto", "error": str(error)}), 500
    finally:
        conexion.close()

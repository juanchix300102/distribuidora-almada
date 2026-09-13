from flask import Blueprint, jsonify, request
from datetime import datetime
from decimal import Decimal, InvalidOperation
import sqlite3

from werkzeug.security import check_password_hash, generate_password_hash

from database import conectar_db
from utils import *

bp = Blueprint("importador_catalogo", __name__)

@bp.route("/api/importar-catalogo", methods=["POST"])
def importar_catalogo():
    if "archivo" not in request.files:
        return jsonify({
            "mensaje": "No se recibió ningún archivo."
        }), 400

    archivo = request.files["archivo"]
    tipo_importacion = request.form.get("tipo_importacion", "catalogo_completo")

    tipos_permitidos = [
        "catalogo_venta",
        "lista_proveedores",
        "catalogo_completo"
    ]

    if tipo_importacion not in tipos_permitidos:
        return jsonify({
            "mensaje": "Tipo de importación no válido."
        }), 400

    if archivo.filename == "":
        return jsonify({
            "mensaje": "Seleccioná un archivo."
        }), 400

    try:
        filas = leer_archivo_importacion(archivo)

        conexion = conectar_db()
        cursor = conexion.cursor()

        proveedores_creados = 0
        productos_creados = 0
        productos_actualizados = 0
        costos_actualizados = 0
        errores = []

        for indice, fila in enumerate(filas, start=2):
            proveedor_nombre = limpiar_texto(
                obtener_valor(fila, "Proveedor")
            )

            codigo = limpiar_texto(
                obtener_valor(fila, "Código", "Codigo", "Cod", "Cod.")
            )

            nombre_producto = limpiar_texto(
                obtener_valor(fila, "Producto", "Nombre", "Artículo", "Articulo", "Descripcion", "Descripción")
            )

            if not nombre_producto:
                errores.append(f"Fila {indice}: falta el nombre del producto.")
                continue

            if not proveedor_nombre:
                if tipo_importacion == "catalogo_venta":
                    proveedor_nombre = "ALMADA / CATÁLOGO DE VENTA"
                else:
                    proveedor_nombre = "SIN PROVEEDOR"

            cursor.execute("""
                SELECT id FROM proveedores
                WHERE LOWER(nombre) = LOWER(?)
            """, (proveedor_nombre,))

            proveedor = cursor.fetchone()

            if proveedor:
                proveedor_id = proveedor["id"]
            else:
                cursor.execute("""
                    INSERT INTO proveedores (
                        nombre, telefono, direccion, localidad, contacto, observaciones
                    )
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    proveedor_nombre,
                    "",
                    "",
                    "",
                    "",
                    "Creado por importación"
                ))

                proveedor_id = cursor.lastrowid
                proveedores_creados += 1

            descripcion = limpiar_texto(
                obtener_valor(fila, "Descripción", "Descripcion", "Detalle")
            )

            if not descripcion:
                descripcion = nombre_producto

            categoria = limpiar_texto(
                obtener_valor(fila, "Categoría", "Categoria", "Rubro", "Linea", "Línea")
            )

            cantidad_caja = int(limpiar_numero(
                obtener_valor(fila, "Cantidad por caja", "Cantidad_caja", "Caja", "Unidades por caja"),
                1
            ))

            if cantidad_caja <= 0:
                cantidad_caja = 1

            precio_venta_excel = limpiar_numero(
                obtener_valor(
                    fila,
                    "Precio venta",
                    "Precio_venta",
                    "Precio unitario",
                    "Precio unidad",
                    "Precio",
                    "Venta"
                ),
                0
            )

            precio_caja_excel = limpiar_numero(
                obtener_valor(fila, "Precio caja", "Precio_caja"),
                0
            )

            precio_base = limpiar_numero(
                obtener_valor(
                    fila,
                    "Precio costo",
                    "Precio_costo",
                    "Precio base",
                    "Precio_base",
                    "Costo",
                    "Compra"
                ),
                0
            )

            bonif1 = limpiar_numero(
                obtener_valor(fila, "Bonificación 1", "Bonificacion 1", "Bonif 1", "Bonif1"),
                0
            )

            bonif2 = limpiar_numero(
                obtener_valor(fila, "Bonificación 2", "Bonificacion 2", "Bonif 2", "Bonif2"),
                0
            )

            bonif3 = limpiar_numero(
                obtener_valor(fila, "Bonificación 3", "Bonificacion 3", "Bonif 3", "Bonif3"),
                0
            )

            iva = limpiar_numero(
                obtener_valor(fila, "IVA", "Iva"),
                21
            )

            flete = limpiar_numero(
                obtener_valor(fila, "Flete"),
                0
            )

            ganancia = limpiar_numero(
                obtener_valor(fila, "Ganancia", "Margen"),
                40
            )

            stock = int(limpiar_numero(
                obtener_valor(fila, "Stock", "Existencia", "Cantidad"),
                0
            ))

            if precio_base > 0:
                precio_final_compra, precio_venta_calculado = calcular_precios(
                    precio_base,
                    bonif1,
                    bonif2,
                    bonif3,
                    iva,
                    flete,
                    ganancia
                )
            else:
                precio_final_compra = 0
                precio_venta_calculado = 0

            precio_venta_final = precio_venta_excel

            if precio_venta_final <= 0 and precio_venta_calculado > 0:
                precio_venta_final = precio_venta_calculado

            precio_unidad = precio_venta_final

            if precio_caja_excel > 0:
                precio_caja = precio_caja_excel
            else:
                precio_caja = precio_unidad * cantidad_caja

            cursor.execute("""
                SELECT id FROM productos
                WHERE codigo = ?
                AND codigo != ''
            """, (codigo,))

            producto_existente = cursor.fetchone()

            if not producto_existente:
                cursor.execute("""
                    SELECT id FROM productos
                    WHERE LOWER(nombre) = LOWER(?)
                    AND proveedor_id = ?
                """, (
                    nombre_producto,
                    proveedor_id
                ))

                producto_existente = cursor.fetchone()

            if producto_existente:
                producto_id = producto_existente["id"]

                cursor.execute("""
                    UPDATE productos
                    SET proveedor_id = ?,
                        nombre = ?,
                        descripcion = ?,
                        categoria = ?,
                        cantidad_caja = ?,
                        precio_unidad = ?,
                        precio_caja = ?,
                        precio_venta = ?,
                        stock = ?
                    WHERE id = ?
                """, (
                    proveedor_id,
                    nombre_producto,
                    descripcion,
                    categoria,
                    cantidad_caja,
                    precio_unidad,
                    precio_caja,
                    precio_venta_final,
                    stock,
                    producto_id
                ))

                productos_actualizados += 1
            else:
                cursor.execute("""
                    INSERT INTO productos (
                        proveedor_id, codigo, nombre, descripcion, categoria, foto,
                        cantidad_caja, precio_unidad, precio_caja,
                        precio_venta, stock
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    proveedor_id,
                    codigo,
                    nombre_producto,
                    descripcion,
                    categoria,
                    "",
                    cantidad_caja,
                    precio_unidad,
                    precio_caja,
                    precio_venta_final,
                    stock
                ))

                producto_id = cursor.lastrowid
                productos_creados += 1

            if tipo_importacion in ["lista_proveedores", "catalogo_completo"]:
                cursor.execute("""
                    SELECT id FROM precios_proveedor
                    WHERE proveedor_id = ?
                    AND producto_id = ?
                """, (
                    proveedor_id,
                    producto_id
                ))

                precio_existente = cursor.fetchone()

                if precio_existente:
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
                        precio_venta_final,
                        datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        precio_existente["id"]
                    ))
                else:
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
                        precio_venta_final,
                        datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    ))

                costos_actualizados += 1

        conexion.commit()
        conexion.close()

        nombre_tipo = {
            "catalogo_venta": "Catálogo de venta",
            "lista_proveedores": "Lista proveedores / costos",
            "catalogo_completo": "Catálogo completo"
        }

        return jsonify({
            "mensaje": "Importación finalizada.",
            "tipo_importacion": nombre_tipo.get(tipo_importacion, tipo_importacion),
            "proveedores_creados": proveedores_creados,
            "productos_creados": productos_creados,
            "productos_actualizados": productos_actualizados,
            "costos_actualizados": costos_actualizados,
            "errores": errores
        })

    except Exception as error:
        print("ERROR IMPORTAR CATALOGO:", error)

        return jsonify({
            "mensaje": "No se pudo importar el catálogo.",
            "error": str(error)
        }), 500

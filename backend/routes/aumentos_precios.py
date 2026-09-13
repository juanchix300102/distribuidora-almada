from flask import Blueprint, jsonify, request
from datetime import datetime
from decimal import Decimal, InvalidOperation
import sqlite3

from werkzeug.security import check_password_hash, generate_password_hash

from database import conectar_db
from utils import *

bp = Blueprint("aumentos_precios", __name__)

def _leer_porcentaje_aumento(datos):
    valor = str(datos.get("porcentaje", "") or "").strip().replace(",", ".")

    try:
        porcentaje = Decimal(valor)
    except (InvalidOperation, ValueError):
        raise ValueError("Ingresá un porcentaje válido")

    if not porcentaje.is_finite() or porcentaje <= 0:
        raise ValueError("El porcentaje debe ser mayor a cero")

    if porcentaje > Decimal("1000"):
        raise ValueError("El porcentaje no puede superar el 1000%")

    return float(porcentaje)

def _leer_ids_productos(datos):
    valores = datos.get("producto_ids") or []

    if not isinstance(valores, list):
        raise ValueError("La selección de productos no es válida")

    ids = []
    for valor in valores:
        try:
            producto_id = int(valor)
        except (TypeError, ValueError):
            raise ValueError("La selección contiene un producto inválido")

        if producto_id > 0 and producto_id not in ids:
            ids.append(producto_id)

    return ids

def _seleccionar_productos_para_aumento(cursor, datos):
    modo = str(datos.get("modo", "") or "").strip().lower()

    if modo not in ("general", "parcial", "individual"):
        raise ValueError("Seleccioná un tipo de aumento válido")

    producto_ids = _leer_ids_productos(datos)
    proveedor_id = datos.get("proveedor_id")
    categoria = str(datos.get("categoria", "") or "").strip()

    if proveedor_id in (None, ""):
        proveedor_id = None
    else:
        try:
            proveedor_id = int(proveedor_id)
        except (TypeError, ValueError):
            raise ValueError("El proveedor seleccionado no es válido")

    if modo == "individual" and len(producto_ids) != 1:
        raise ValueError("Seleccioná un producto para el aumento individual")

    if modo == "parcial" and not (producto_ids or proveedor_id or categoria):
        raise ValueError(
            "Elegí un proveedor, una categoría o productos para el aumento parcial"
        )

    condiciones = []
    parametros = []

    if modo == "individual":
        condiciones.append("p.id = ?")
        parametros.append(producto_ids[0])
    elif modo == "parcial":
        if proveedor_id:
            condiciones.append("p.proveedor_id = ?")
            parametros.append(proveedor_id)

        if categoria:
            condiciones.append("LOWER(TRIM(COALESCE(p.categoria, ''))) = LOWER(?)")
            parametros.append(categoria)

    clausula_where = ""
    if condiciones:
        clausula_where = "WHERE " + " AND ".join(condiciones)

    cursor.execute(f"""
        SELECT
            p.id,
            p.proveedor_id,
            p.codigo,
            p.nombre,
            p.categoria,
            p.precio_venta,
            pr.nombre AS proveedor
        FROM productos p
        LEFT JOIN proveedores pr ON pr.id = p.proveedor_id
        {clausula_where}
        ORDER BY p.nombre COLLATE NOCASE ASC, p.id ASC
    """, parametros)

    productos = [dict(fila) for fila in cursor.fetchall()]

    if modo == "parcial" and producto_ids:
        ids_permitidos = set(producto_ids)
        productos = [
            producto for producto in productos
            if producto["id"] in ids_permitidos
        ]

    if not productos:
        raise ValueError("No hay productos que coincidan con la selección")

    if modo == "general":
        criterio = "Todos los productos con precio de venta"
    elif modo == "individual":
        criterio = f"Producto: {productos[0]['nombre']}"
    else:
        partes = []

        if proveedor_id:
            cursor.execute(
                "SELECT nombre FROM proveedores WHERE id = ?",
                (proveedor_id,)
            )
            proveedor = cursor.fetchone()
            partes.append(
                f"Proveedor: {proveedor['nombre'] if proveedor else proveedor_id}"
            )

        if categoria:
            partes.append(f"Categoría: {categoria}")

        if producto_ids:
            partes.append(f"Selección manual: {len(productos)} producto(s)")

        criterio = " · ".join(partes)

    return modo, criterio, productos

def _construir_vista_previa_aumento(cursor, productos, porcentaje):
    productos_por_id = {producto["id"]: producto for producto in productos}
    variantes_por_producto = {}
    ids = list(productos_por_id.keys())

    for inicio in range(0, len(ids), 800):
        bloque = ids[inicio:inicio + 800]
        placeholders = ",".join("?" for _ in bloque)
        cursor.execute(f"""
            SELECT
                id,
                producto_id,
                nombre_variante,
                codigo,
                precio_venta
            FROM producto_variantes
            WHERE activo = 1
              AND producto_id IN ({placeholders})
            ORDER BY producto_id ASC, id ASC
        """, bloque)

        for fila in cursor.fetchall():
            variante = dict(fila)
            variantes_por_producto.setdefault(
                variante["producto_id"], []
            ).append(variante)

    vista = []
    omitidos_sin_precio = 0
    cantidad_precios = 0

    for producto in productos:
        lineas = []

        for variante in variantes_por_producto.get(producto["id"], []):
            precio_anterior = float(variante["precio_venta"] or 0)
            if precio_anterior <= 0:
                continue

            lineas.append({
                "variante_id": variante["id"],
                "variante": variante["nombre_variante"] or "Presentación",
                "codigo": variante["codigo"] or producto["codigo"] or "",
                "precio_anterior": precio_anterior,
                "precio_nuevo": redondear_aumento_hacia_arriba_10(
                    precio_anterior,
                    porcentaje
                )
            })

        if not lineas:
            precio_anterior = float(producto["precio_venta"] or 0)

            if precio_anterior > 0:
                lineas.append({
                    "variante_id": None,
                    "variante": "Precio principal",
                    "codigo": producto["codigo"] or "",
                    "precio_anterior": precio_anterior,
                    "precio_nuevo": redondear_aumento_hacia_arriba_10(
                        precio_anterior,
                        porcentaje
                    )
                })

        if not lineas:
            omitidos_sin_precio += 1
            continue

        cantidad_precios += len(lineas)
        vista.append({
            "id": producto["id"],
            "nombre": producto["nombre"],
            "codigo": producto["codigo"] or lineas[0]["codigo"],
            "proveedor": producto["proveedor"] or "Sin proveedor",
            "categoria": producto["categoria"] or "Sin categoría",
            "precio_anterior": lineas[0]["precio_anterior"],
            "precio_nuevo": lineas[0]["precio_nuevo"],
            "precios": lineas
        })

    if not vista:
        raise ValueError("Los productos seleccionados no tienen precio de venta")

    return {
        "productos": vista,
        "cantidad_productos": len(vista),
        "cantidad_precios": cantidad_precios,
        "omitidos_sin_precio": omitidos_sin_precio
    }

@bp.route("/api/aumentos-precios/opciones", methods=["GET"])
def opciones_aumentos_precios():
    conexion = conectar_db()
    cursor = conexion.cursor()

    cursor.execute("""
        SELECT
            p.id,
            p.proveedor_id,
            p.codigo,
            p.nombre,
            p.categoria,
            COALESCE(
                (
                    SELECT pv.precio_venta
                    FROM producto_variantes pv
                    WHERE pv.producto_id = p.id
                      AND pv.activo = 1
                      AND pv.precio_venta > 0
                    ORDER BY pv.id ASC
                    LIMIT 1
                ),
                p.precio_venta,
                0
            ) AS precio_actual,
            (
                SELECT COUNT(*)
                FROM producto_variantes pv
                WHERE pv.producto_id = p.id AND pv.activo = 1
            ) AS cantidad_variantes,
            pr.nombre AS proveedor
        FROM productos p
        LEFT JOIN proveedores pr ON pr.id = p.proveedor_id
        ORDER BY p.nombre COLLATE NOCASE ASC, p.id ASC
    """)
    productos = [dict(fila) for fila in cursor.fetchall()]

    cursor.execute("""
        SELECT id, nombre
        FROM proveedores
        ORDER BY nombre COLLATE NOCASE ASC
    """)
    proveedores = [dict(fila) for fila in cursor.fetchall()]

    cursor.execute("""
        SELECT DISTINCT TRIM(categoria) AS categoria
        FROM productos
        WHERE TRIM(COALESCE(categoria, '')) <> ''
        ORDER BY categoria COLLATE NOCASE ASC
    """)
    categorias = [fila["categoria"] for fila in cursor.fetchall()]

    conexion.close()
    respuesta = jsonify({
        "productos": productos,
        "proveedores": proveedores,
        "categorias": categorias,
        "redondeo": "Siempre hacia arriba al próximo múltiplo de $10"
    })
    respuesta.headers["Cache-Control"] = "no-store"
    return respuesta

@bp.route("/api/aumentos-precios/vista-previa", methods=["POST"])
def vista_previa_aumento_precios():
    datos = request.json or {}
    conexion = conectar_db()
    cursor = conexion.cursor()

    try:
        porcentaje = _leer_porcentaje_aumento(datos)
        modo, criterio, productos = _seleccionar_productos_para_aumento(
            cursor,
            datos
        )
        vista = _construir_vista_previa_aumento(
            cursor,
            productos,
            porcentaje
        )
    except ValueError as error:
        conexion.close()
        return jsonify({"mensaje": str(error)}), 400

    conexion.close()
    return jsonify({
        "modo": modo,
        "porcentaje": porcentaje,
        "criterio": criterio,
        "redondeo": "Hacia arriba a $10",
        **vista
    })

@bp.route("/api/aumentos-precios", methods=["POST"])
def aplicar_aumento_precios():
    datos = request.json or {}
    conexion = conectar_db()
    cursor = conexion.cursor()

    try:
        cursor.execute("BEGIN IMMEDIATE")
        porcentaje = _leer_porcentaje_aumento(datos)
        modo, criterio, productos = _seleccionar_productos_para_aumento(
            cursor,
            datos
        )
        vista = _construir_vista_previa_aumento(
            cursor,
            productos,
            porcentaje
        )
        fecha = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        cursor.execute("""
            INSERT INTO aumentos_precios (
                fecha, modo, porcentaje, criterio,
                cantidad_productos, cantidad_precios, redondeo
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            fecha,
            modo,
            porcentaje,
            criterio,
            vista["cantidad_productos"],
            vista["cantidad_precios"],
            "Hacia arriba a $10"
        ))
        aumento_id = cursor.lastrowid

        for producto in vista["productos"]:
            for precio in producto["precios"]:
                if precio["variante_id"] is not None:
                    cursor.execute("""
                        UPDATE producto_variantes
                        SET precio_venta = ?
                        WHERE id = ? AND producto_id = ?
                    """, (
                        precio["precio_nuevo"],
                        precio["variante_id"],
                        producto["id"]
                    ))

                cursor.execute("""
                    INSERT INTO aumento_precio_detalles (
                        aumento_id, producto_id, producto,
                        variante_id, variante, codigo,
                        proveedor, categoria, precio_anterior, precio_nuevo
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    aumento_id,
                    producto["id"],
                    producto["nombre"],
                    precio["variante_id"],
                    precio["variante"],
                    precio["codigo"],
                    producto["proveedor"],
                    producto["categoria"],
                    precio["precio_anterior"],
                    precio["precio_nuevo"]
                ))

            nuevo_precio_principal = producto["precios"][0]["precio_nuevo"]
            cursor.execute("""
                UPDATE productos
                SET precio_venta = ?
                WHERE id = ?
            """, (nuevo_precio_principal, producto["id"]))

            cursor.execute("""
                UPDATE precios_proveedor
                SET precio_venta = ?,
                    ganancia = CASE
                        WHEN COALESCE(precio_final_compra, 0) > 0
                        THEN ROUND(
                            ((? / precio_final_compra) - 1) * 100,
                            2
                        )
                        ELSE ganancia
                    END,
                    fecha_actualizacion = ?
                WHERE producto_id = ?
            """, (
                nuevo_precio_principal,
                nuevo_precio_principal,
                fecha,
                producto["id"]
            ))

        conexion.commit()
    except ValueError as error:
        conexion.rollback()
        conexion.close()
        return jsonify({"mensaje": str(error)}), 400
    except Exception as error:
        conexion.rollback()
        conexion.close()
        print("ERROR AUMENTO PRECIOS:", error)
        return jsonify({
            "mensaje": "No se pudo aplicar el aumento",
            "error": str(error)
        }), 500

    conexion.close()
    return jsonify({
        "mensaje": "Aumento aplicado correctamente",
        "aumento_id": aumento_id,
        "modo": modo,
        "porcentaje": porcentaje,
        "cantidad_productos": vista["cantidad_productos"],
        "cantidad_precios": vista["cantidad_precios"],
        "omitidos_sin_precio": vista["omitidos_sin_precio"],
        "redondeo": "Hacia arriba a $10"
    }), 201

@bp.route("/api/aumentos-precios/historial", methods=["GET"])
def historial_aumentos_precios():
    conexion = conectar_db()
    cursor = conexion.cursor()
    cursor.execute("""
        SELECT
            id, fecha, modo, porcentaje, criterio,
            cantidad_productos, cantidad_precios, redondeo
        FROM aumentos_precios
        ORDER BY id DESC
        LIMIT 100
    """)
    historial = [dict(fila) for fila in cursor.fetchall()]
    conexion.close()
    return jsonify(historial)

@bp.route("/api/aumentos-precios/historial/<int:aumento_id>", methods=["GET"])
def detalle_aumento_precios(aumento_id):
    conexion = conectar_db()
    cursor = conexion.cursor()
    cursor.execute("""
        SELECT
            id, fecha, modo, porcentaje, criterio,
            cantidad_productos, cantidad_precios, redondeo
        FROM aumentos_precios
        WHERE id = ?
    """, (aumento_id,))
    aumento = cursor.fetchone()

    if not aumento:
        conexion.close()
        return jsonify({"mensaje": "Aumento no encontrado"}), 404

    cursor.execute("""
        SELECT
            id, producto_id, producto, variante_id, variante,
            codigo, proveedor, categoria, precio_anterior, precio_nuevo
        FROM aumento_precio_detalles
        WHERE aumento_id = ?
        ORDER BY producto COLLATE NOCASE ASC, id ASC
    """, (aumento_id,))
    detalles = [dict(fila) for fila in cursor.fetchall()]
    conexion.close()

    respuesta = dict(aumento)
    respuesta["detalles"] = detalles
    return jsonify(respuesta)

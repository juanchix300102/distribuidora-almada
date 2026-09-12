from flask import Flask, jsonify, request
from flask_cors import CORS
import sqlite3
from datetime import datetime
import csv
import io
import os
from pathlib import Path

from werkzeug.security import check_password_hash, generate_password_hash

app = Flask(__name__)
CORS(app)

BASE_DIR = Path(__file__).resolve().parent
DB_NAME = Path(
    os.environ.get(
        "ALMADA2_DB_PATH",
        BASE_DIR / "data" / "almada2.db"
    )
)

DB_NAME.parent.mkdir(parents=True, exist_ok=True)

ADMIN_INICIAL = os.environ.get("ALMADA2_ADMIN_USER", "admin")
CLAVE_ADMIN_INICIAL = os.environ.get(
    "ALMADA2_ADMIN_PASSWORD",
    "almada2-dev"
)


def conectar_db():
    conexion = sqlite3.connect(
        str(DB_NAME),
        timeout=30,
        check_same_thread=False
    )
    conexion.row_factory = sqlite3.Row
    conexion.execute("PRAGMA foreign_keys = ON")
    return conexion


def fila_a_diccionario(fila):
    if fila is None:
        return None
    return dict(fila)


def limpiar_documento(valor):
    return "".join(caracter for caracter in str(valor or "") if caracter.isdigit())


def obtener_dni_desde_documento(valor):
    documento = limpiar_documento(valor)

    # CUIL/CUIT argentino: 11 dígitos. Ejemplo: 20 30123456 7
    if len(documento) == 11:
        return documento[2:10]

    # DNI común: últimos 8 dígitos
    if len(documento) >= 8:
        return documento[-8:]

    return documento


def calcular_precios(precio_base, bonif1, bonif2, bonif3, iva, flete, ganancia):
    precio = float(precio_base or 0)

    precio = precio * (1 - float(bonif1 or 0) / 100)
    precio = precio * (1 - float(bonif2 or 0) / 100)
    precio = precio * (1 - float(bonif3 or 0) / 100)

    precio = precio * (1 + float(iva or 0) / 100)
    precio = precio * (1 + float(flete or 0) / 100)

    precio_final_compra = round(precio, 2)
    precio_venta = round(precio_final_compra * (1 + float(ganancia or 0) / 100), 2)

    return precio_final_compra, precio_venta

def limpiar_texto(valor):
    return str(valor or "").strip()


def limpiar_numero(valor, defecto=0):
    if valor is None:
        return defecto

    texto = str(valor).strip()

    if texto == "":
        return defecto

    texto = texto.replace("$", "").replace(" ", "")

    if "," in texto and "." in texto:
        texto = texto.replace(".", "").replace(",", ".")
    else:
        texto = texto.replace(",", ".")

    try:
        return float(texto)
    except ValueError:
        return defecto


def normalizar_columna(nombre):
    texto = str(nombre or "").strip().lower()
    reemplazos = {
        "á": "a",
        "é": "e",
        "í": "i",
        "ó": "o",
        "ú": "u",
        "ñ": "n"
    }

    for original, reemplazo in reemplazos.items():
        texto = texto.replace(original, reemplazo)

    texto = texto.replace(" ", "_").replace("-", "_")
    return texto


def obtener_valor(fila, *nombres):
    for nombre in nombres:
        clave = normalizar_columna(nombre)

        if clave in fila:
            return fila.get(clave)

    return ""


def leer_archivo_importacion(archivo):
    nombre = archivo.filename.lower()

    if nombre.endswith(".csv"):
        contenido = archivo.read().decode("utf-8-sig")
        muestra = contenido[:2048]

        try:
            dialecto = csv.Sniffer().sniff(muestra, delimiters=";,")
            separador = dialecto.delimiter
        except Exception:
            separador = ";"

        lector = csv.DictReader(io.StringIO(contenido), delimiter=separador)

        filas = []
        for fila in lector:
            fila_normalizada = {}

            for clave, valor in fila.items():
                fila_normalizada[normalizar_columna(clave)] = valor

            filas.append(fila_normalizada)

        return filas

    if nombre.endswith(".xlsx"):
        from openpyxl import load_workbook

        workbook = load_workbook(archivo, data_only=True)
        hoja = workbook.active

        encabezados = []
        filas = []

        for celda in hoja[1]:
            encabezados.append(normalizar_columna(celda.value))

        for row in hoja.iter_rows(min_row=2, values_only=True):
            fila = {}

            for index, valor in enumerate(row):
                if index < len(encabezados):
                    fila[encabezados[index]] = valor

            filas.append(fila)

        return filas

    raise ValueError("Formato no permitido. Usá CSV o XLSX.")

def generar_numero_cliente(cursor):
    cursor.execute("SELECT numero_cliente FROM clientes")
    clientes = cursor.fetchall()

    numero_mayor = 0

    for cliente in clientes:
        numero = cliente["numero_cliente"]

        if numero and str(numero).startswith("C"):
            try:
                numero_limpio = int(str(numero).replace("C", ""))
                if numero_limpio > numero_mayor:
                    numero_mayor = numero_limpio
            except ValueError:
                pass

    nuevo_numero = numero_mayor + 1
    return f"C{nuevo_numero:04d}"


def crear_tablas():
    conexion = conectar_db()
    cursor = conexion.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario TEXT NOT NULL UNIQUE,
            contrasena TEXT NOT NULL,
            rol TEXT NOT NULL,
            activo INTEGER NOT NULL DEFAULT 1
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS clientes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            numero_cliente TEXT NOT NULL UNIQUE,
            nombre TEXT NOT NULL,
            direccion TEXT,
            localidad TEXT,
            telefono TEXT,
            email TEXT,
            observaciones TEXT,
            saldo_actual REAL DEFAULT 0
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS proveedores (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL,
            telefono TEXT,
            direccion TEXT,
            localidad TEXT,
            contacto TEXT,
            observaciones TEXT
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS productos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            proveedor_id INTEGER,
            codigo TEXT,
            nombre TEXT NOT NULL,
            descripcion TEXT,
            categoria TEXT,
            foto TEXT,
            cantidad_caja INTEGER DEFAULT 1,
            precio_unidad REAL DEFAULT 0,
            precio_caja REAL DEFAULT 0,
            precio_venta REAL DEFAULT 0,
            stock INTEGER DEFAULT 0,
            FOREIGN KEY (proveedor_id) REFERENCES proveedores(id)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS producto_variantes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            producto_id INTEGER NOT NULL,
            nombre_variante TEXT NOT NULL DEFAULT '',
            codigo TEXT DEFAULT '',
            cantidad_caja INTEGER DEFAULT 1,
            precio_unidad REAL DEFAULT 0,
            precio_caja REAL DEFAULT 0,
            precio_venta REAL DEFAULT 0,
            stock INTEGER DEFAULT 0,
            activo INTEGER DEFAULT 1,
            FOREIGN KEY (producto_id) REFERENCES productos(id)
        )
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_variantes_producto
        ON producto_variantes(producto_id)
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_variantes_codigo
        ON producto_variantes(codigo)
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS precios_proveedor (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            proveedor_id INTEGER NOT NULL,
            producto_id INTEGER NOT NULL,
            precio_base REAL DEFAULT 0,
            bonificacion_1 REAL DEFAULT 0,
            bonificacion_2 REAL DEFAULT 0,
            bonificacion_3 REAL DEFAULT 0,
            iva REAL DEFAULT 21,
            flete REAL DEFAULT 0,
            precio_final_compra REAL DEFAULT 0,
            ganancia REAL DEFAULT 0,
            precio_venta REAL DEFAULT 0,
            fecha_actualizacion TEXT,
            FOREIGN KEY (proveedor_id) REFERENCES proveedores(id),
            FOREIGN KEY (producto_id) REFERENCES productos(id)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS cuentas_corrientes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cliente_id INTEGER NOT NULL,
            fecha TEXT NOT NULL,
            tipo TEXT NOT NULL,
            descripcion TEXT,
            comprobante TEXT,
            debe REAL DEFAULT 0,
            haber REAL DEFAULT 0,
            saldo REAL DEFAULT 0,
            medio_pago TEXT,
            FOREIGN KEY (cliente_id) REFERENCES clientes(id)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS pagos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cliente_id INTEGER NOT NULL,
            fecha TEXT NOT NULL,
            monto REAL NOT NULL,
            medio_pago TEXT NOT NULL,
            comprobante TEXT,
            observaciones TEXT,
            FOREIGN KEY (cliente_id) REFERENCES clientes(id)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS saldos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cliente_id INTEGER NOT NULL,
            fecha TEXT NOT NULL,
            descripcion TEXT,
            monto_inicial REAL NOT NULL,
            monto_pagado REAL DEFAULT 0,
            saldo_restante REAL NOT NULL,
            estado TEXT DEFAULT 'Pendiente',
            FOREIGN KEY (cliente_id) REFERENCES clientes(id)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS movimientos_stock (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            producto_id INTEGER NOT NULL,
            fecha TEXT NOT NULL,
            tipo TEXT NOT NULL,
            cantidad INTEGER NOT NULL,
            descripcion TEXT,
            stock_resultante INTEGER,
            FOREIGN KEY (producto_id) REFERENCES productos(id)
        )
    """)

    conexion.commit()
    conexion.close()


def agregar_columna_si_no_existe(tabla, columna, definicion):
    conexion = conectar_db()
    cursor = conexion.cursor()

    cursor.execute(f"PRAGMA table_info({tabla})")
    columnas = [fila["name"] for fila in cursor.fetchall()]

    if columna not in columnas:
        cursor.execute(f"ALTER TABLE {tabla} ADD COLUMN {columna} {definicion}")

    conexion.commit()
    conexion.close()


def asegurar_columnas():
    agregar_columna_si_no_existe("clientes", "saldo_actual", "REAL DEFAULT 0")

    agregar_columna_si_no_existe("productos", "foto_origen", "TEXT DEFAULT ''")
    agregar_columna_si_no_existe("productos", "foto_palabra_clave", "TEXT DEFAULT ''")


def cargar_datos_iniciales():
    conexion = conectar_db()
    cursor = conexion.cursor()

    cursor.execute("SELECT id FROM usuarios WHERE usuario = ?", (ADMIN_INICIAL,))
    admin_existente = cursor.fetchone()

    if not admin_existente:
        cursor.execute("""
            INSERT INTO usuarios (usuario, contrasena, rol, activo)
            VALUES (?, ?, ?, 1)
        """, (
            ADMIN_INICIAL,
            generate_password_hash(CLAVE_ADMIN_INICIAL),
            "admin"
        ))

    conexion.commit()
    conexion.close()


@app.route("/")
def inicio():
    return jsonify({
        "mensaje": "API de Almada 2 funcionando correctamente"
    })


@app.route("/api/login", methods=["POST"])
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
    conexion.close()

    if (
        not usuario_encontrado
        or not usuario_encontrado["activo"]
        or not check_password_hash(
            usuario_encontrado["contrasena"],
            contrasena
        )
    ):
        return jsonify({
            "mensaje": "Usuario o contraseña incorrectos"
        }), 401

    return jsonify({
        "mensaje": "Login correcto",
        "usuario_id": usuario_encontrado["id"],
        "usuario": usuario_encontrado["usuario"],
        "rol": usuario_encontrado["rol"]
    })


@app.route("/api/resumen", methods=["GET"])
def resumen():
    conexion = conectar_db()
    cursor = conexion.cursor()

    cursor.execute("SELECT COUNT(*) FROM productos")
    total_productos = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM productos WHERE stock <= 5")
    stock_bajo = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM proveedores")
    total_proveedores = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM clientes")
    total_clientes = cursor.fetchone()[0]

    cursor.execute("SELECT SUM(saldo_actual) FROM clientes")
    saldo_clientes = cursor.fetchone()[0] or 0

    conexion.close()

    return jsonify({
        "productos_cargados": total_productos,
        "stock_bajo": stock_bajo,
        "proveedores": total_proveedores,
        "clientes": total_clientes,
        "saldo_clientes": saldo_clientes,
        "ventas_mes": 0
    })


@app.route("/api/proveedores", methods=["GET"])
def listar_proveedores():
    conexion = conectar_db()
    cursor = conexion.cursor()

    cursor.execute("SELECT * FROM proveedores ORDER BY nombre ASC")
    proveedores = cursor.fetchall()

    conexion.close()

    return jsonify([dict(proveedor) for proveedor in proveedores])


@app.route("/api/proveedores", methods=["POST"])
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


@app.route("/api/proveedores/<int:proveedor_id>/productos", methods=["GET"])
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


@app.route("/api/proveedores/<int:proveedor_id>/productos", methods=["POST"])
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


@app.route("/api/precios/<int:precio_id>", methods=["PUT"])
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


@app.route("/api/productos", methods=["GET"])
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


@app.route("/api/productos/<int:id>", methods=["PUT"])
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


@app.route("/api/productos/<int:id>", methods=["DELETE"])
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


@app.route("/api/clientes", methods=["GET"])
def listar_clientes():
    conexion = conectar_db()
    cursor = conexion.cursor()

    cursor.execute("SELECT * FROM clientes ORDER BY nombre ASC")

    clientes = cursor.fetchall()
    conexion.close()

    return jsonify([dict(cliente) for cliente in clientes])


@app.route("/api/clientes", methods=["POST"])
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


@app.route("/api/clientes/<int:id>", methods=["PUT"])
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


@app.route("/api/clientes/<int:id>", methods=["DELETE"])
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


@app.route("/api/clientes/<int:cliente_id>/cuenta-corriente", methods=["GET"])
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


@app.route("/api/clientes/<int:cliente_id>/cuenta-corriente/movimiento", methods=["POST"])
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


@app.route("/api/clientes/<int:cliente_id>/pagos", methods=["POST"])
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


@app.route("/api/importar-catalogo", methods=["POST"])
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
if __name__ == "__main__":
    crear_tablas()
    asegurar_columnas()
    cargar_datos_iniciales()
    app.run(
        debug=os.environ.get("FLASK_DEBUG", "0") == "1",
        port=int(os.environ.get("PORT", "5000"))
    )

import os
import sqlite3
from pathlib import Path

from werkzeug.security import generate_password_hash

BASE_DIR = Path(__file__).resolve().parent
DB_NAME = Path(os.environ.get("ALMADA2_DB_PATH", BASE_DIR / "data" / "almada2.db"))
DB_NAME.parent.mkdir(parents=True, exist_ok=True)

ADMIN_INICIAL = os.environ.get("ALMADA2_ADMIN_USER", "admin")
CLAVE_ADMIN_INICIAL = os.environ.get("ALMADA2_ADMIN_PASSWORD", "almada2-dev")

def conectar_db():
    conexion = sqlite3.connect(
        str(DB_NAME),
        timeout=30,
        check_same_thread=False
    )
    conexion.row_factory = sqlite3.Row
    conexion.execute("PRAGMA foreign_keys = ON")
    return conexion

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


    cursor.execute("""
        CREATE TABLE IF NOT EXISTS vendedores (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario_id INTEGER NOT NULL UNIQUE,
            nombre TEXT NOT NULL,
            telefono TEXT,
            zona TEXT,
            observaciones TEXT,
            activo INTEGER NOT NULL DEFAULT 1,
            fecha_alta TEXT NOT NULL,
            FOREIGN KEY (usuario_id) REFERENCES usuarios(id)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS stock_viaje (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            vendedor_id INTEGER NOT NULL,
            producto_id INTEGER NOT NULL,
            cantidad INTEGER NOT NULL DEFAULT 0,
            actualizado_en TEXT,
            UNIQUE (vendedor_id, producto_id),
            FOREIGN KEY (vendedor_id) REFERENCES vendedores(id),
            FOREIGN KEY (producto_id) REFERENCES productos(id)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS ventas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            vendedor_id INTEGER NOT NULL,
            cliente_id INTEGER,
            fecha TEXT NOT NULL,
            forma_pago TEXT NOT NULL,
            total REAL NOT NULL DEFAULT 0,
            observaciones TEXT,
            FOREIGN KEY (vendedor_id) REFERENCES vendedores(id),
            FOREIGN KEY (cliente_id) REFERENCES clientes(id)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS venta_detalles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            venta_id INTEGER NOT NULL,
            producto_id INTEGER NOT NULL,
            cantidad INTEGER NOT NULL,
            precio_unitario REAL NOT NULL,
            subtotal REAL NOT NULL,
            FOREIGN KEY (venta_id) REFERENCES ventas(id),
            FOREIGN KEY (producto_id) REFERENCES productos(id)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS movimientos_stock_viaje (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            vendedor_id INTEGER NOT NULL,
            producto_id INTEGER NOT NULL,
            fecha TEXT NOT NULL,
            tipo TEXT NOT NULL,
            cantidad INTEGER NOT NULL,
            descripcion TEXT,
            stock_viaje_resultante INTEGER NOT NULL DEFAULT 0,
            stock_central_resultante INTEGER NOT NULL DEFAULT 0,
            FOREIGN KEY (vendedor_id) REFERENCES vendedores(id),
            FOREIGN KEY (producto_id) REFERENCES productos(id)
        )
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_stock_viaje_vendedor
        ON stock_viaje(vendedor_id)
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_ventas_vendedor
        ON ventas(vendedor_id)
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS aumentos_precios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fecha TEXT NOT NULL,
            modo TEXT NOT NULL,
            porcentaje REAL NOT NULL,
            criterio TEXT NOT NULL,
            cantidad_productos INTEGER NOT NULL DEFAULT 0,
            cantidad_precios INTEGER NOT NULL DEFAULT 0,
            redondeo TEXT NOT NULL DEFAULT 'Hacia arriba a $10'
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS aumento_precio_detalles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            aumento_id INTEGER NOT NULL,
            producto_id INTEGER,
            producto TEXT NOT NULL,
            variante_id INTEGER,
            variante TEXT,
            codigo TEXT,
            proveedor TEXT,
            categoria TEXT,
            precio_anterior REAL NOT NULL,
            precio_nuevo REAL NOT NULL,
            FOREIGN KEY (aumento_id) REFERENCES aumentos_precios(id)
                ON DELETE CASCADE
        )
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_aumentos_precios_fecha
        ON aumentos_precios(fecha)
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_aumento_detalles_aumento
        ON aumento_precio_detalles(aumento_id)
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

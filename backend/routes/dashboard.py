from flask import Blueprint, jsonify, request
from datetime import datetime
from decimal import Decimal, InvalidOperation
import sqlite3

from werkzeug.security import check_password_hash, generate_password_hash

from database import conectar_db
from utils import *

bp = Blueprint("dashboard", __name__)

@bp.route("/api/resumen", methods=["GET"])
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

    cursor.execute("SELECT COUNT(*) FROM vendedores WHERE activo = 1")
    total_vendedores = cursor.fetchone()[0]

    cursor.execute("SELECT COALESCE(SUM(cantidad), 0) FROM stock_viaje")
    unidades_en_viaje = cursor.fetchone()[0] or 0

    mes_actual = datetime.now().strftime("%Y-%m")
    cursor.execute("""
        SELECT COALESCE(SUM(total), 0)
        FROM ventas
        WHERE substr(fecha, 1, 7) = ?
    """, (mes_actual,))
    ventas_mes = cursor.fetchone()[0] or 0

    conexion.close()

    return jsonify({
        "productos_cargados": total_productos,
        "stock_bajo": stock_bajo,
        "proveedores": total_proveedores,
        "clientes": total_clientes,
        "saldo_clientes": saldo_clientes,
        "vendedores": total_vendedores,
        "unidades_en_viaje": unidades_en_viaje,
        "ventas_mes": ventas_mes
    })

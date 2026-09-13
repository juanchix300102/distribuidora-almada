from decimal import Decimal, ROUND_CEILING

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

def redondear_aumento_hacia_arriba_10(precio_actual, porcentaje):
    """Aplica el porcentaje y redondea hacia arriba al múltiplo de $10."""
    precio = Decimal(str(precio_actual or 0))
    aumento = Decimal(str(porcentaje))
    precio_calculado = precio * (Decimal("1") + aumento / Decimal("100"))
    precio_redondeado = (
        precio_calculado / Decimal("10")
    ).to_integral_value(rounding=ROUND_CEILING) * Decimal("10")
    return float(precio_redondeado)

def limpiar_texto(valor):
    return str(valor or "").strip()


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

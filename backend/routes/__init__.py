from .auth import bp as auth_bp
from .dashboard import bp as dashboard_bp
from .proveedores import bp as proveedores_bp
from .productos import bp as productos_bp
from .aumentos_precios import bp as aumentos_precios_bp
from .clientes import bp as clientes_bp
from .cuentas_corrientes import bp as cuentas_corrientes_bp
from .vendedores import bp as vendedores_bp
from .stock_viaje import bp as stock_viaje_bp
from .catalogo_visual import bp as catalogo_visual_bp
from .ventas import bp as ventas_bp

BLUEPRINTS = [
    auth_bp,
    dashboard_bp,
    proveedores_bp,
    productos_bp,
    aumentos_precios_bp,
    clientes_bp,
    cuentas_corrientes_bp,
    vendedores_bp,
    stock_viaje_bp,
    catalogo_visual_bp,
    ventas_bp,
]

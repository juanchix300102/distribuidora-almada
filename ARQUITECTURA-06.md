# Almada 2 — Organización modular 06

Esta versión reorganiza el sistema sin cambiar la lógica comercial ni la base de datos.

## Frontend

`app.ts` y `app.html` quedan como carcasa de autenticación, navegación y selección de vista.
La lógica de cada sección vive en su propio componente.

### Secciones administrativas

- `components/panel/` — resumen general.
- `components/productos-admin/` — productos, variantes y stock de depósito.
- `components/proveedores/` — proveedores y costos.
- `components/aumentos-precios/` — aumentos porcentuales e historial.
- `components/clientes/` — registro interno de clientes.
- `components/cuentas-corrientes/` — cuentas corrientes.
- `components/vendedores/` — alta, edición, credenciales y estado de vendedores.
- `components/stock-viaje/` — carga, devolución y control del stock en viaje.
- `components/catalogo-visual/` — catálogo para tablet conectado al stock del vendedor.

### Secciones del vendedor

- `components/venta-vendedor/` — carga de ventas.
- `components/catalogo-visual/` — catálogo visual en otro dispositivo.

### Servicios

Los endpoints están separados por dominio dentro de `services/api/`:

- auth
- dashboard
- productos
- proveedores
- clientes
- cuentas corrientes
- vendedores / stock en viaje
- ventas
- aumentos de precios

`api.service.ts` se mantiene únicamente como fachada de compatibilidad para los componentes existentes.

## Backend

El backend ya no concentra las rutas en `app.py`.

- `routes/auth.py`
- `routes/dashboard.py`
- `routes/productos.py`
- `routes/importador_catalogo.py`
- `routes/proveedores.py`
- `routes/clientes.py`
- `routes/cuentas_corrientes.py`
- `routes/vendedores.py`
- `routes/stock_viaje.py`
- `routes/ventas.py`
- `routes/catalogo_visual.py`
- `routes/aumentos_precios.py`

`app.py` solo crea Flask y registra los módulos.

## Separaciones realizadas en la versión 06

Antes, Productos contenía también el Panel general. Ahora son dos componentes distintos.

Antes, Vendedores contenía también la gestión del Stock en viaje. Ahora son dos componentes distintos y dos opciones independientes del menú.


Aumentos de precios tiene acceso propio y no está mezclado con Productos.

## Pendientes futuros

Gastos, Saldos y Reportes deberán crearse como nuevos módulos independientes siguiendo esta misma estructura.

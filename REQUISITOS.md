# Requisitos confirmados — Almada 2

## Separación obligatoria

- Almada 2 es un negocio independiente.
- Tiene una base de datos propia.
- No se deben copiar clientes, movimientos, pedidos, solicitudes ni
  credenciales de Almada 1.
- Su identidad visual, logo y colores se definirán de manera independiente.

## Funciones que se mantienen

- Acceso interno al sistema.
- Panel administrativo.
- Registro y gestión interna de clientes.
- Productos, proveedores y stock de depósito.
- Cuentas corrientes y saldos de clientes.
- Catálogo visual para la venta ambulante.
- Usuario vendedor.

## Funciones que no tendrá

- Inicio público para clientes.
- Autorregistro de clientes.
- Solicitudes de registro o aprobación.
- Usuario o contraseña para clientes.
- Pedidos online realizados por clientes.
- Carrito de compra del cliente.
- Catálogo de compra para clientes.

## Venta ambulante

### Catálogo visual

- Muestra imagen y nombre del producto.
- Al abrir un producto, muestra descripción y medidas o variantes.
- Sirve para mostrar mercadería durante la visita al cliente.
- No permite que un cliente haga un pedido online.

### Usuario vendedor

- El vendedor selecciona al cliente por nombre.
- Puede buscar productos por código o nombre.
- Ve la lista en orden alfabético con código, nombre y precio.
- Marca productos e ingresa cantidades.
- El sistema calcula el total.
- Elige forma de pago o deja la venta a deuda.
- Confirma la venta.
- Puede consultar las ventas que fue realizando.

### Stock en viaje

En este sistema, “stock en viaje” significa la mercadería que un vendedor carga
y lleva consigo para vender. No es mercadería enviada por un proveedor.

- El administrador asigna productos y cantidades a cada vendedor.
- La carga descuenta existencias del depósito y suma existencias al stock móvil.
- Cada vendedor ve únicamente lo que lleva disponible.
- Cada venta descuenta automáticamente su stock en viaje.
- El administrador ve cuánto lleva y cuánto le queda a cada vendedor.
- Lo no vendido puede devolverse al depósito.

## Ventas y cuenta corriente

- Toda venta confirmada queda registrada en la sección Ventas.
- La venta se asocia a un vendedor y a un cliente.
- El vendedor puede revisar productos, cantidades y total de sus ventas.
- El administrador puede ver las ventas de todos los vendedores.
- Si la operación queda a deuda, el total se carga en la cuenta corriente.
- Si hay un pago inmediato, se registra el pago y su forma.
- Cuando la forma de pago sea cheque, se debe guardar el número de cheque.

## Actualización de precios

El sistema de precios sugeridos de reventa de Almada 1 se reemplazará por:

- Aumento general sobre todos los productos.
- Aumento parcial sobre un grupo de productos.
- Aumento individual por producto.
- Buscador por código o nombre.

Falta definir si el aumento parcial se seleccionará por proveedor, categoría o
productos marcados, y si se permitirán porcentajes, montos fijos o ambos.

## Otras secciones

- Gastos.
- Reportes con gráficos.
- Saldos más desarrollados.
- Número de cheque en los movimientos correspondientes.

## Decisiones todavía pendientes

- Nombre comercial exacto que se mostrará en pantalla.
- Logo y paleta de colores.
- Criterio del aumento parcial.
- Tipo de aumento: porcentaje, monto fijo o ambos.
- Si cada venta puede marcarse como facturada o no facturada.
- Formas de pago habilitadas.
- Cantidad inicial de vendedores y datos que se registrarán de cada uno.


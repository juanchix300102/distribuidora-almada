# Requisitos confirmados — Almada 2

## Separación obligatoria

- Almada 2 es un negocio independiente.
- Tiene una base de datos propia.
- No se deben copiar clientes, movimientos, pedidos, solicitudes ni
  credenciales de Almada 1.
- Su identidad visual, logo y colores son independientes de Almada 1.

## Identidad visual

- Nombre visible: Distribuidora Almada.
- Logo oficial: monograma negro DA con la leyenda “Venta y Distribución de Herrajes”.
- Color principal: azul Francia, cercano al azul de los potes Nivea.
- Colores complementarios: beige/arena y negro.
- La interfaz debe ser clara, moderna y apta para computadora, tablet y teléfono.

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
- Funciona como una vista separada y a pantalla completa, pensada para una
  tablet distinta del dispositivo donde el vendedor registra la venta.
- Ambos dispositivos ingresan con el mismo usuario vendedor y, por eso,
  consultan el mismo stock en viaje.
- Muestra código, categoría y estado “Disponible” o “Sin stock”.
- No muestra precios, costos, proveedores, cantidades internas ni controles
  para vender.
- Presenta los productos directamente en una grilla ordenada, sin buscador ni
  filtros, para mantener una vista simple destinada al cliente.
- El título principal ocupa un lugar destacado y de mayor tamaño.
- El logo no aparece en la esquina superior: reemplaza las letras “DA” dentro
  de las fichas de productos que todavía no tienen una fotografía cargada.
- El estado de stock se actualiza automáticamente mientras el catálogo está
  abierto. Cuando una venta agota un producto, la tablet pasa a mostrarlo
  como “Sin stock”.
- El administrador puede abrir una vista previa eligiendo al vendedor.

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
- La herramienta estará dentro del panel inicial, en la ubicación que en Almada 1
  ocupaba la configuración de porcentajes sugeridos.
- No tendrá una sección independiente en el menú lateral.

Falta definir si el aumento parcial se seleccionará por proveedor, categoría o
productos marcados, y si se permitirán porcentajes, montos fijos o ambos.

## Otras secciones

- Gastos.
- Reportes con gráficos.
- Saldos más desarrollados.
- Número de cheque en los movimientos correspondientes.

## Estado implementado de venta ambulante

- Gestión interna de vendedores con usuario y contraseña propios.
- Login habilitado para rol vendedor.
- Asignación de mercadería desde depósito a stock en viaje.
- Devolución de mercadería desde stock en viaje a depósito.
- Registro e historial de movimientos de stock en viaje.
- Pantalla del vendedor para registrar ventas desde su stock disponible.
- Historial de ventas por vendedor y vista general para administración.
- Descuento automático del stock en viaje al confirmar una venta.
- Carga automática en cuenta corriente cuando la forma de pago es Cuenta corriente.
- Catálogo visual independiente para tablet, vinculado al stock en viaje del
  vendedor y con actualización automática de disponibilidad.

## Decisiones todavía pendientes

- Criterio del aumento parcial.
- Tipo de aumento: porcentaje, monto fijo o ambos.
- Si cada venta puede marcarse como facturada o no facturada.
- Formas de pago habilitadas.
- Cantidad inicial de vendedores y datos que se registrarán de cada uno.

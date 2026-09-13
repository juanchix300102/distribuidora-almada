import { Injectable } from '@angular/core';
import { Observable } from 'rxjs';

import { AuthApiService } from './api/auth-api.service';
import { DashboardApiService } from './api/dashboard-api.service';
import { ProductosApiService } from './api/productos-api.service';
import { ProveedoresApiService } from './api/proveedores-api.service';
import { ClientesApiService } from './api/clientes-api.service';
import { CuentasCorrientesApiService } from './api/cuentas-corrientes-api.service';
import { AumentosPreciosApiService } from './api/aumentos-precios-api.service';
import { VendedoresApiService } from './api/vendedores-api.service';
import { VentasApiService } from './api/ventas-api.service';

/**
 * Fachada de compatibilidad.
 *
 * Los componentes existentes siguen usando ApiService, pero cada grupo de
 * endpoints vive ahora en su servicio de módulo. Esto permite migrar un
 * componente por vez sin romper la aplicación.
 */
@Injectable({ providedIn: 'root' })
export class ApiService {
  constructor(
    private auth: AuthApiService,
    private dashboard: DashboardApiService,
    private productos: ProductosApiService,
    private proveedores: ProveedoresApiService,
    private clientes: ClientesApiService,
    private cuentas: CuentasCorrientesApiService,
    private aumentos: AumentosPreciosApiService,
    private vendedores: VendedoresApiService,
    private ventas: VentasApiService
  ) {}

  login(datos: any): Observable<any> { return this.auth.login(datos); }
  obtenerResumen(): Observable<any> { return this.dashboard.obtenerResumen(); }
  obtenerProductos(): Observable<any[]> { return this.productos.obtenerProductos(); }
  actualizarProducto(id: number, datos: any): Observable<any> { return this.productos.actualizarProducto(id, datos); }
  eliminarProducto(id: number): Observable<any> { return this.productos.eliminarProducto(id); }

  obtenerClientes(): Observable<any[]> { return this.clientes.obtenerClientes(); }
  crearCliente(datos: any): Observable<any> { return this.clientes.crearCliente(datos); }
  actualizarCliente(id: number, datos: any): Observable<any> { return this.clientes.actualizarCliente(id, datos); }
  eliminarCliente(id: number): Observable<any> { return this.clientes.eliminarCliente(id); }

  obtenerCuentaCorriente(clienteId: number): Observable<any> { return this.cuentas.obtenerCuentaCorriente(clienteId); }
  agregarMovimientoCuenta(clienteId: number, datos: any): Observable<any> { return this.cuentas.agregarMovimientoCuenta(clienteId, datos); }
  registrarPagoCliente(clienteId: number, datos: any): Observable<any> { return this.cuentas.registrarPagoCliente(clienteId, datos); }

  obtenerProveedores(): Observable<any[]> { return this.proveedores.obtenerProveedores(); }
  crearProveedor(datos: any): Observable<any> { return this.proveedores.crearProveedor(datos); }
  obtenerProductosProveedor(proveedorId: number): Observable<any[]> { return this.proveedores.obtenerProductosProveedor(proveedorId); }
  crearProductoProveedor(proveedorId: number, datos: any): Observable<any> { return this.proveedores.crearProductoProveedor(proveedorId, datos); }
  actualizarPrecioProveedor(precioId: number, datos: any): Observable<any> { return this.proveedores.actualizarPrecioProveedor(precioId, datos); }

  obtenerOpcionesAumentos(): Observable<any> { return this.aumentos.obtenerOpcionesAumentos(); }
  obtenerVistaPreviaAumento(datos: any): Observable<any> { return this.aumentos.obtenerVistaPreviaAumento(datos); }
  aplicarAumentoPrecios(datos: any): Observable<any> { return this.aumentos.aplicarAumentoPrecios(datos); }
  obtenerHistorialAumentos(): Observable<any[]> { return this.aumentos.obtenerHistorialAumentos(); }
  obtenerDetalleAumento(id: number): Observable<any> { return this.aumentos.obtenerDetalleAumento(id); }

  obtenerVendedores(): Observable<any[]> { return this.vendedores.obtenerVendedores(); }
  crearVendedor(datos: any): Observable<any> { return this.vendedores.crearVendedor(datos); }
  actualizarVendedor(id: number, datos: any): Observable<any> { return this.vendedores.actualizarVendedor(id, datos); }
  desactivarVendedor(id: number): Observable<any> { return this.vendedores.desactivarVendedor(id); }
  obtenerVendedorPorUsuario(usuarioId: number): Observable<any> { return this.vendedores.obtenerVendedorPorUsuario(usuarioId); }
  obtenerStockViaje(vendedorId: number): Observable<any[]> { return this.vendedores.obtenerStockViaje(vendedorId); }
  obtenerCatalogoVisual(vendedorId: number): Observable<any> { return this.vendedores.obtenerCatalogoVisual(vendedorId); }
  asignarStockViaje(vendedorId: number, datos: any): Observable<any> { return this.vendedores.asignarStockViaje(vendedorId, datos); }
  devolverStockViaje(vendedorId: number, datos: any): Observable<any> { return this.vendedores.devolverStockViaje(vendedorId, datos); }
  obtenerMovimientosStockViaje(vendedorId: number): Observable<any[]> { return this.vendedores.obtenerMovimientosStockViaje(vendedorId); }

  obtenerVentas(): Observable<any[]> { return this.ventas.obtenerVentas(); }
  obtenerVentasVendedor(vendedorId: number): Observable<any[]> { return this.ventas.obtenerVentasVendedor(vendedorId); }
  registrarVentaVendedor(vendedorId: number, datos: any): Observable<any> { return this.ventas.registrarVentaVendedor(vendedorId, datos); }
}

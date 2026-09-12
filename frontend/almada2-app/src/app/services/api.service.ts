import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

@Injectable({
  providedIn: 'root'
})
export class ApiService {
  private apiUrl = this.construirApiUrl();

  constructor(private http: HttpClient) {}

  private construirApiUrl(): string {
    const host =
      typeof window !== 'undefined' && window.location.hostname
        ? window.location.hostname
        : '127.0.0.1';

    return `http://${host}:5000/api`;
  }

  login(datos: any): Observable<any> {
    return this.http.post<any>(`${this.apiUrl}/login`, datos);
  }

  obtenerResumen(): Observable<any> {
    return this.http.get<any>(`${this.apiUrl}/resumen`);
  }

  obtenerProductos(): Observable<any[]> {
    return this.http.get<any[]>(`${this.apiUrl}/productos`);
  }

  obtenerClientes(): Observable<any[]> {
    return this.http.get<any[]>(`${this.apiUrl}/clientes`);
  }

  crearCliente(datos: any): Observable<any> {
    return this.http.post<any>(`${this.apiUrl}/clientes`, datos);
  }

  actualizarCliente(id: number, datos: any): Observable<any> {
    return this.http.put<any>(
      `${this.apiUrl}/clientes/${id}`,
      datos
    );
  }

  eliminarCliente(id: number): Observable<any> {
    return this.http.delete<any>(
      `${this.apiUrl}/clientes/${id}`
    );
  }

  obtenerCuentaCorriente(clienteId: number): Observable<any> {
    return this.http.get<any>(
      `${this.apiUrl}/clientes/${clienteId}/cuenta-corriente`
    );
  }

  agregarMovimientoCuenta(
    clienteId: number,
    datos: any
  ): Observable<any> {
    return this.http.post<any>(
      `${this.apiUrl}/clientes/${clienteId}/cuenta-corriente/movimiento`,
      datos
    );
  }

  registrarPagoCliente(
    clienteId: number,
    datos: any
  ): Observable<any> {
    return this.http.post<any>(
      `${this.apiUrl}/clientes/${clienteId}/pagos`,
      datos
    );
  }

  obtenerProveedores(): Observable<any[]> {
    return this.http.get<any[]>(
      `${this.apiUrl}/proveedores`
    );
  }

  crearProveedor(datos: any): Observable<any> {
    return this.http.post<any>(
      `${this.apiUrl}/proveedores`,
      datos
    );
  }

  obtenerProductosProveedor(
    proveedorId: number
  ): Observable<any[]> {
    return this.http.get<any[]>(
      `${this.apiUrl}/proveedores/${proveedorId}/productos`
    );
  }

  crearProductoProveedor(
    proveedorId: number,
    datos: any
  ): Observable<any> {
    return this.http.post<any>(
      `${this.apiUrl}/proveedores/${proveedorId}/productos`,
      datos
    );
  }

  actualizarPrecioProveedor(
    precioId: number,
    datos: any
  ): Observable<any> {
    return this.http.put<any>(
      `${this.apiUrl}/precios/${precioId}`,
      datos
    );
  }

  actualizarProducto(
    id: number,
    datos: any
  ): Observable<any> {
    return this.http.put<any>(
      `${this.apiUrl}/productos/${id}`,
      datos
    );
  }

  eliminarProducto(id: number): Observable<any> {
    return this.http.delete<any>(
      `${this.apiUrl}/productos/${id}`
    );
  }

  obtenerOpcionesAumentos(): Observable<any> {
    return this.http.get<any>(
      `${this.apiUrl}/aumentos-precios/opciones`
    );
  }

  obtenerVistaPreviaAumento(datos: any): Observable<any> {
    return this.http.post<any>(
      `${this.apiUrl}/aumentos-precios/vista-previa`,
      datos
    );
  }

  aplicarAumentoPrecios(datos: any): Observable<any> {
    return this.http.post<any>(
      `${this.apiUrl}/aumentos-precios`,
      datos
    );
  }

  obtenerHistorialAumentos(): Observable<any[]> {
    return this.http.get<any[]>(
      `${this.apiUrl}/aumentos-precios/historial`
    );
  }

  obtenerDetalleAumento(id: number): Observable<any> {
    return this.http.get<any>(
      `${this.apiUrl}/aumentos-precios/historial/${id}`
    );
  }

  importarCatalogo(
    archivo: File,
    tipoImportacion: string
  ): Observable<any> {
    const formData = new FormData();

    formData.append('archivo', archivo);
    formData.append('tipo_importacion', tipoImportacion);

    return this.http.post<any>(
      `${this.apiUrl}/importar-catalogo`,
      formData
    );
  }

  obtenerVendedores(): Observable<any[]> {
    return this.http.get<any[]>(`${this.apiUrl}/vendedores`);
  }

  crearVendedor(datos: any): Observable<any> {
    return this.http.post<any>(`${this.apiUrl}/vendedores`, datos);
  }

  actualizarVendedor(id: number, datos: any): Observable<any> {
    return this.http.put<any>(`${this.apiUrl}/vendedores/${id}`, datos);
  }

  desactivarVendedor(id: number): Observable<any> {
    return this.http.delete<any>(`${this.apiUrl}/vendedores/${id}`);
  }

  obtenerVendedorPorUsuario(usuarioId: number): Observable<any> {
    return this.http.get<any>(
      `${this.apiUrl}/vendedores/por-usuario/${usuarioId}`
    );
  }

  obtenerStockViaje(vendedorId: number): Observable<any[]> {
    return this.http.get<any[]>(
      `${this.apiUrl}/vendedores/${vendedorId}/stock-viaje`
    );
  }

  obtenerCatalogoVisual(vendedorId: number): Observable<any> {
    return this.http.get<any>(
      `${this.apiUrl}/vendedores/${vendedorId}/catalogo-visual`
    );
  }

  asignarStockViaje(vendedorId: number, datos: any): Observable<any> {
    return this.http.post<any>(
      `${this.apiUrl}/vendedores/${vendedorId}/stock-viaje/asignar`,
      datos
    );
  }

  devolverStockViaje(vendedorId: number, datos: any): Observable<any> {
    return this.http.post<any>(
      `${this.apiUrl}/vendedores/${vendedorId}/stock-viaje/devolver`,
      datos
    );
  }

  obtenerMovimientosStockViaje(vendedorId: number): Observable<any[]> {
    return this.http.get<any[]>(
      `${this.apiUrl}/vendedores/${vendedorId}/stock-viaje/movimientos`
    );
  }

  obtenerVentas(): Observable<any[]> {
    return this.http.get<any[]>(`${this.apiUrl}/ventas`);
  }

  obtenerVentasVendedor(vendedorId: number): Observable<any[]> {
    return this.http.get<any[]>(
      `${this.apiUrl}/vendedores/${vendedorId}/ventas`
    );
  }

  registrarVentaVendedor(vendedorId: number, datos: any): Observable<any> {
    return this.http.post<any>(
      `${this.apiUrl}/vendedores/${vendedorId}/ventas`,
      datos
    );
  }
}

import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { construirApiUrl } from './api-url';

@Injectable({ providedIn: 'root' })
export class VendedoresApiService {
  private readonly apiUrl = construirApiUrl();

  constructor(private http: HttpClient) {}

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
    return this.http.get<any>(`${this.apiUrl}/vendedores/por-usuario/${usuarioId}`);
  }

  obtenerStockViaje(vendedorId: number): Observable<any[]> {
    return this.http.get<any[]>(`${this.apiUrl}/vendedores/${vendedorId}/stock-viaje`);
  }

  obtenerCatalogoVisual(vendedorId: number): Observable<any> {
    return this.http.get<any>(`${this.apiUrl}/vendedores/${vendedorId}/catalogo-visual`);
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
}

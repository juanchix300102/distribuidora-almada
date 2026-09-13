import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { construirApiUrl } from './api-url';

@Injectable({ providedIn: 'root' })
export class ProveedoresApiService {
  private readonly apiUrl = construirApiUrl();

  constructor(private http: HttpClient) {}

  obtenerProveedores(): Observable<any[]> {
    return this.http.get<any[]>(`${this.apiUrl}/proveedores`);
  }

  crearProveedor(datos: any): Observable<any> {
    return this.http.post<any>(`${this.apiUrl}/proveedores`, datos);
  }

  obtenerProductosProveedor(proveedorId: number): Observable<any[]> {
    return this.http.get<any[]>(`${this.apiUrl}/proveedores/${proveedorId}/productos`);
  }

  crearProductoProveedor(proveedorId: number, datos: any): Observable<any> {
    return this.http.post<any>(`${this.apiUrl}/proveedores/${proveedorId}/productos`, datos);
  }

  actualizarPrecioProveedor(precioId: number, datos: any): Observable<any> {
    return this.http.put<any>(`${this.apiUrl}/precios/${precioId}`, datos);
  }
}

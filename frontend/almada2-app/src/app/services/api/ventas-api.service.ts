import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { construirApiUrl } from './api-url';

@Injectable({ providedIn: 'root' })
export class VentasApiService {
  private readonly apiUrl = construirApiUrl();

  constructor(private http: HttpClient) {}

  obtenerVentas(): Observable<any[]> {
    return this.http.get<any[]>(`${this.apiUrl}/ventas`);
  }

  obtenerVentasVendedor(vendedorId: number): Observable<any[]> {
    return this.http.get<any[]>(`${this.apiUrl}/vendedores/${vendedorId}/ventas`);
  }

  registrarVentaVendedor(vendedorId: number, datos: any): Observable<any> {
    return this.http.post<any>(`${this.apiUrl}/vendedores/${vendedorId}/ventas`, datos);
  }
}

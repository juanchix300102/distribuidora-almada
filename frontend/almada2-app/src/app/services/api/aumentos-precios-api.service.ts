import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { construirApiUrl } from './api-url';

@Injectable({ providedIn: 'root' })
export class AumentosPreciosApiService {
  private readonly apiUrl = construirApiUrl();

  constructor(private http: HttpClient) {}

  obtenerOpcionesAumentos(): Observable<any> {
    return this.http.get<any>(`${this.apiUrl}/aumentos-precios/opciones`);
  }

  obtenerVistaPreviaAumento(datos: any): Observable<any> {
    return this.http.post<any>(`${this.apiUrl}/aumentos-precios/vista-previa`, datos);
  }

  aplicarAumentoPrecios(datos: any): Observable<any> {
    return this.http.post<any>(`${this.apiUrl}/aumentos-precios`, datos);
  }

  obtenerHistorialAumentos(): Observable<any[]> {
    return this.http.get<any[]>(`${this.apiUrl}/aumentos-precios/historial`);
  }

  obtenerDetalleAumento(id: number): Observable<any> {
    return this.http.get<any>(`${this.apiUrl}/aumentos-precios/historial/${id}`);
  }
}

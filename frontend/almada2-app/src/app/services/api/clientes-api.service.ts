import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { construirApiUrl } from './api-url';

@Injectable({ providedIn: 'root' })
export class ClientesApiService {
  private readonly apiUrl = construirApiUrl();

  constructor(private http: HttpClient) {}

  obtenerClientes(): Observable<any[]> {
    return this.http.get<any[]>(`${this.apiUrl}/clientes`);
  }

  crearCliente(datos: any): Observable<any> {
    return this.http.post<any>(`${this.apiUrl}/clientes`, datos);
  }

  actualizarCliente(id: number, datos: any): Observable<any> {
    return this.http.put<any>(`${this.apiUrl}/clientes/${id}`, datos);
  }

  eliminarCliente(id: number): Observable<any> {
    return this.http.delete<any>(`${this.apiUrl}/clientes/${id}`);
  }
}

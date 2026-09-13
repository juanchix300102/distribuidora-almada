import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { construirApiUrl } from './api-url';

@Injectable({ providedIn: 'root' })
export class CuentasCorrientesApiService {
  private readonly apiUrl = construirApiUrl();

  constructor(private http: HttpClient) {}

  obtenerCuentaCorriente(clienteId: number): Observable<any> {
    return this.http.get<any>(`${this.apiUrl}/clientes/${clienteId}/cuenta-corriente`);
  }

  agregarMovimientoCuenta(clienteId: number, datos: any): Observable<any> {
    return this.http.post<any>(
      `${this.apiUrl}/clientes/${clienteId}/cuenta-corriente/movimiento`,
      datos
    );
  }

  registrarPagoCliente(clienteId: number, datos: any): Observable<any> {
    return this.http.post<any>(`${this.apiUrl}/clientes/${clienteId}/pagos`, datos);
  }
}

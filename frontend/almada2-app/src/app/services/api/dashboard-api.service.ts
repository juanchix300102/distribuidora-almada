import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { construirApiUrl } from './api-url';

@Injectable({ providedIn: 'root' })
export class DashboardApiService {
  private readonly apiUrl = construirApiUrl();

  constructor(private http: HttpClient) {}

  obtenerResumen(): Observable<any> {
    return this.http.get<any>(`${this.apiUrl}/resumen`);
  }
}

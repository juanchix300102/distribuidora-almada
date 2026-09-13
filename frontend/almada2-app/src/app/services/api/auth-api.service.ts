import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { construirApiUrl } from './api-url';

@Injectable({ providedIn: 'root' })
export class AuthApiService {
  private readonly apiUrl = construirApiUrl();

  constructor(private http: HttpClient) {}

  login(datos: any): Observable<any> {
    return this.http.post<any>(`${this.apiUrl}/login`, datos);
  }
}

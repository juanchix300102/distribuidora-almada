import { CommonModule } from '@angular/common';
import {
  ChangeDetectorRef,
  Component,
  EventEmitter,
  Output,
  inject
} from '@angular/core';
import { FormsModule } from '@angular/forms';

import { ApiService } from '../../services/api.service';

@Component({
  selector: 'app-auth',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './auth.html',
  styleUrl: './auth.css'
})
export class AuthComponent {
  private api = inject(ApiService);
  private cdr = inject(ChangeDetectorRef);

  @Output() loginExitoso = new EventEmitter<any>();

  loginForm = {
    usuario: '',
    contrasena: ''
  };

  loginError = '';
  ingresando = false;

  iniciarSesion(): void {
    const usuario = String(this.loginForm.usuario || '').trim();
    const contrasena = String(this.loginForm.contrasena || '').trim();

    if (!usuario || !contrasena) {
      this.loginError = 'Ingresá el usuario y la contraseña.';
      this.cdr.detectChanges();
      return;
    }

    this.ingresando = true;
    this.loginError = '';

    this.api.login({ usuario, contrasena }).subscribe({
      next: (respuesta) => {
        this.ingresando = false;
        this.loginExitoso.emit(respuesta);
        this.cdr.detectChanges();
      },
      error: (error) => {
        this.ingresando = false;
        this.loginError =
          error.error?.mensaje || 'No se pudo iniciar sesión.';
        this.cdr.detectChanges();
      }
    });
  }
}

import { CommonModule } from '@angular/common';
import {
  ChangeDetectorRef,
  Component,
  OnInit,
  inject
} from '@angular/core';

import { ApiService } from './services/api.service';
import { AuthComponent } from './components/auth/auth';
import { ClientesComponent } from './components/clientes/clientes';
import { CuentasCorrientesComponent } from './components/cuentas corrientes/cuentas-corrientes';
import { ProductosAdminComponent } from './components/productos-admin/productos-admin';
import { ProveedoresComponent } from './components/proveedores/proveedores';

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [
    CommonModule,
    AuthComponent,
    ClientesComponent,
    CuentasCorrientesComponent,
    ProductosAdminComponent,
    ProveedoresComponent
  ],
  templateUrl: './app.html',
  styleUrl: './app.css'
})
export class App implements OnInit {
  private api = inject(ApiService);
  private cdr = inject(ChangeDetectorRef);

  autenticado = false;
  rolActual = '';
  vista = 'login';
  error = '';
  resumen: any = null;
  clienteCuentaInicial: any = null;

  ngOnInit(): void {
    this.vista = 'login';
  }

  procesarLogin(respuesta: any): void {
    if (respuesta?.rol !== 'admin') {
      this.error = 'Este perfil todavía no está habilitado.';
      this.autenticado = false;
      this.vista = 'login';
      this.cdr.detectChanges();
      return;
    }

    this.autenticado = true;
    this.rolActual = respuesta.rol;
    this.vista = 'panel';
    this.error = '';
    this.cargarResumen();
    this.cdr.detectChanges();
  }

  cerrarSesion(): void {
    this.autenticado = false;
    this.rolActual = '';
    this.vista = 'login';
    this.error = '';
    this.resumen = null;
    this.clienteCuentaInicial = null;
    this.cdr.detectChanges();
  }

  cambiarVista(vista: string): void {
    if (!this.autenticado) {
      this.vista = 'login';
      this.cdr.detectChanges();
      return;
    }

    this.vista = vista;
    this.error = '';

    if (vista === 'panel') {
      this.cargarResumen();
    }

    if (vista === 'cuenta-corriente-lista') {
      this.clienteCuentaInicial = null;
      this.cargarResumen();
    }

    this.cdr.detectChanges();
  }

  abrirCuentaCorrienteDesdeClientes(cliente: any): void {
    this.clienteCuentaInicial = { ...cliente };
    this.vista = 'cuenta-corriente';
    this.cdr.detectChanges();
  }

  cargarResumen(): void {
    this.api.obtenerResumen().subscribe({
      next: (respuesta) => {
        this.resumen = respuesta;
        this.cdr.detectChanges();
      },
      error: () => {
        this.error = 'No se pudo cargar el resumen.';
        this.cdr.detectChanges();
      }
    });
  }
}

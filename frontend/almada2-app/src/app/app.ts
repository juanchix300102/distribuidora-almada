import { CommonModule } from '@angular/common';
import {
  ChangeDetectorRef,
  Component,
  OnInit,
  inject
} from '@angular/core';

import { ApiService } from './services/api.service';
import { AuthComponent } from './components/auth/auth';
import { CatalogoVisualComponent } from './components/catalogo-visual/catalogo-visual';
import { ClientesComponent } from './components/clientes/clientes';
import { CuentasCorrientesComponent } from './components/cuentas corrientes/cuentas-corrientes';
import { ProductosAdminComponent } from './components/productos-admin/productos-admin';
import { ProveedoresComponent } from './components/proveedores/proveedores';
import { VendedoresComponent } from './components/vendedores/vendedores';
import { VentaVendedorComponent } from './components/venta-vendedor/venta-vendedor';

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [
    CommonModule,
    AuthComponent,
    CatalogoVisualComponent,
    ClientesComponent,
    CuentasCorrientesComponent,
    ProductosAdminComponent,
    ProveedoresComponent,
    VendedoresComponent,
    VentaVendedorComponent
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
  usuarioId: number | null = null;
  vendedorId: number | null = null;
  nombreActual = '';

  ngOnInit(): void {
    this.vista = 'login';
  }

  procesarLogin(respuesta: any): void {
    if (!['admin', 'vendedor'].includes(respuesta?.rol)) {
      this.error = 'Este perfil no está habilitado.';
      this.autenticado = false;
      this.vista = 'login';
      this.cdr.detectChanges();
      return;
    }

    this.autenticado = true;
    this.rolActual = respuesta.rol;
    this.usuarioId = Number(respuesta.usuario_id || 0) || null;
    this.vendedorId = Number(respuesta.vendedor_id || 0) || null;
    this.nombreActual =
      respuesta.nombre ||
      respuesta.usuario ||
      (respuesta.rol === 'admin' ? 'Administrador' : 'Vendedor');

    this.vista = respuesta.rol === 'admin' ? 'panel' : 'venta-vendedor';
    this.error = '';

    if (respuesta.rol === 'admin') {
      this.cargarResumen();
    }

    this.cdr.detectChanges();
  }

  cerrarSesion(): void {
    this.autenticado = false;
    this.rolActual = '';
    this.vista = 'login';
    this.error = '';
    this.resumen = null;
    this.clienteCuentaInicial = null;
    this.usuarioId = null;
    this.vendedorId = null;
    this.nombreActual = '';
    this.cdr.detectChanges();
  }

  cambiarVista(vista: string): void {
    if (!this.autenticado) {
      this.vista = 'login';
      this.cdr.detectChanges();
      return;
    }

    if (
      this.rolActual === 'vendedor' &&
      !['venta-vendedor', 'catalogo-visual'].includes(vista)
    ) {
      this.vista = 'venta-vendedor';
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

  cerrarCatalogoVisual(): void {
    this.vista =
      this.rolActual === 'admin' ? 'panel' : 'venta-vendedor';

    if (this.rolActual === 'admin') {
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

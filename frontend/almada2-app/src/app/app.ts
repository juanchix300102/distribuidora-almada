import { CommonModule } from '@angular/common';
import { ChangeDetectorRef, Component, OnInit, inject } from '@angular/core';

import { AumentosPreciosComponent } from './components/aumentos-precios/aumentos-precios';
import { AuthComponent } from './components/auth/auth';
import { CatalogoVisualComponent } from './components/catalogo-visual/catalogo-visual';
import { ClientesComponent } from './components/clientes/clientes';
import { CuentasCorrientesComponent } from './components/cuentas-corrientes/cuentas-corrientes';
import { PanelComponent } from './components/panel/panel';
import { ProductosAdminComponent } from './components/productos-admin/productos-admin';
import { ProveedoresComponent } from './components/proveedores/proveedores';
import { StockViajeComponent } from './components/stock-viaje/stock-viaje';
import { VendedoresComponent } from './components/vendedores/vendedores';
import { VentaVendedorComponent } from './components/venta-vendedor/venta-vendedor';

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [
    CommonModule,
    AumentosPreciosComponent,
    AuthComponent,
    CatalogoVisualComponent,
    ClientesComponent,
    CuentasCorrientesComponent,
    PanelComponent,
    ProductosAdminComponent,
    ProveedoresComponent,
    StockViajeComponent,
    VendedoresComponent,
    VentaVendedorComponent
  ],
  templateUrl: './app.html',
  styleUrl: './app.css'
})
export class App implements OnInit {
  private cdr = inject(ChangeDetectorRef);

  autenticado = false;
  rolActual = '';
  vista = 'login';
  error = '';
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
    this.cdr.detectChanges();
  }

  cerrarSesion(): void {
    this.autenticado = false;
    this.rolActual = '';
    this.vista = 'login';
    this.error = '';
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

    if (vista === 'cuenta-corriente-lista') {
      this.clienteCuentaInicial = null;
    }

    this.cdr.detectChanges();
  }

  cerrarCatalogoVisual(): void {
    this.vista = this.rolActual === 'admin' ? 'panel' : 'venta-vendedor';
    this.cdr.detectChanges();
  }

  abrirCuentaCorrienteDesdeClientes(cliente: any): void {
    this.clienteCuentaInicial = { ...cliente };
    this.vista = 'cuenta-corriente';
    this.cdr.detectChanges();
  }

  tituloVista(): string {
    const titulos: Record<string, string> = {
      panel: 'Panel general',
      productos: 'Productos',
      proveedores: 'Proveedores y precios',
      'aumentos-precios': 'Aumentos de precios',
      clientes: 'Clientes',
      'cuenta-corriente-lista': 'Cuenta corriente',
      'cuenta-corriente': 'Detalle de cuenta',
      vendedores: 'Vendedores',
      'stock-viaje': 'Stock en viaje',
      'venta-vendedor': 'Mi jornada de venta'
    };

    return titulos[this.vista] || 'Almada 2';
  }

  descripcionVista(): string {
    const descripciones: Record<string, string> = {
      panel: 'Una vista clara del movimiento comercial.',
      productos: 'Alta, edición, variantes, stock y precios de los productos.',
      proveedores: 'Proveedores y costos de los productos.',
      'aumentos-precios': 'Actualización porcentual con vista previa y registro de cambios.',
      clientes: 'Registro interno y datos comerciales de clientes.',
      'cuenta-corriente-lista': 'Buscá clientes, revisá saldos y accedé a sus cuentas.',
      'cuenta-corriente': 'Pagos, deudas y movimientos del cliente.',
      vendedores: 'Usuarios, credenciales, zonas y estado de cada vendedor.',
      'stock-viaje': 'Carga, devolución y control de la mercadería que lleva cada vendedor.',
      'venta-vendedor': 'Registrá ventas directamente desde la mercadería disponible.'
    };

    return descripciones[this.vista] || '';
  }
}

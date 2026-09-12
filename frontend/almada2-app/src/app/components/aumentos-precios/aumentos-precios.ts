import { CommonModule } from '@angular/common';
import {
  ChangeDetectorRef,
  Component,
  EventEmitter,
  OnInit,
  Output,
  inject
} from '@angular/core';
import { FormsModule } from '@angular/forms';

import { ApiService } from '../../services/api.service';

type ModoAumento = 'general' | 'parcial' | 'individual';

@Component({
  selector: 'app-aumentos-precios',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './aumentos-precios.html',
  styleUrl: './aumentos-precios.css'
})
export class AumentosPreciosComponent implements OnInit {
  private api = inject(ApiService);
  private cdr = inject(ChangeDetectorRef);

  @Output() preciosActualizados = new EventEmitter<void>();
  @Output() volverPanel = new EventEmitter<void>();

  modo: ModoAumento = 'general';
  porcentaje: number | null = null;
  proveedorId: number | null = null;
  categoria = '';
  busqueda = '';

  productos: any[] = [];
  proveedores: any[] = [];
  categorias: string[] = [];
  seleccionados = new Set<number>();
  productoIndividualId: number | null = null;

  vistaPrevia: any = null;
  historial: any[] = [];
  detalleHistorial: any = null;

  cargandoOpciones = false;
  generandoVista = false;
  aplicando = false;
  cargandoHistorial = false;
  cargandoDetalle = false;
  mensajeExito = '';
  error = '';

  ngOnInit(): void {
    this.cargarOpciones();
    this.cargarHistorial();
  }

  cargarOpciones(): void {
    this.cargandoOpciones = true;
    this.error = '';

    this.api.obtenerOpcionesAumentos().subscribe({
      next: (respuesta) => {
        this.productos = respuesta?.productos || [];
        this.proveedores = respuesta?.proveedores || [];
        this.categorias = respuesta?.categorias || [];
        this.cargandoOpciones = false;
        this.cdr.detectChanges();
      },
      error: () => {
        this.cargandoOpciones = false;
        this.error = 'No se pudieron cargar los productos para actualizar.';
        this.cdr.detectChanges();
      }
    });
  }

  cargarHistorial(): void {
    this.cargandoHistorial = true;

    this.api.obtenerHistorialAumentos().subscribe({
      next: (respuesta) => {
        this.historial = respuesta || [];
        this.cargandoHistorial = false;
        this.cdr.detectChanges();
      },
      error: () => {
        this.cargandoHistorial = false;
        this.error = 'No se pudo cargar el historial de aumentos.';
        this.cdr.detectChanges();
      }
    });
  }

  cambiarModo(modo: ModoAumento): void {
    this.modo = modo;
    this.proveedorId = null;
    this.categoria = '';
    this.busqueda = '';
    this.seleccionados.clear();
    this.productoIndividualId = null;
    this.invalidarVistaPrevia();
  }

  cambiarFiltroParcial(): void {
    this.seleccionados.clear();
    this.invalidarVistaPrevia();
  }

  invalidarVistaPrevia(): void {
    this.vistaPrevia = null;
    this.mensajeExito = '';
    this.error = '';
  }

  get productosFiltrados(): any[] {
    const texto = this.normalizar(this.busqueda);

    return this.productos.filter((producto: any) => {
      if (
        this.modo === 'parcial' &&
        this.proveedorId &&
        Number(producto.proveedor_id) !== Number(this.proveedorId)
      ) {
        return false;
      }

      if (
        this.modo === 'parcial' &&
        this.categoria &&
        producto.categoria !== this.categoria
      ) {
        return false;
      }

      if (!texto) {
        return true;
      }

      return this.normalizar(
        `${producto.nombre || ''} ${producto.codigo || ''} ` +
          `${producto.proveedor || ''} ${producto.categoria || ''}`
      ).includes(texto);
    });
  }

  get productosMostrados(): any[] {
    return this.productosFiltrados.slice(0, 200);
  }

  get productosConPrecio(): any[] {
    return this.productos.filter(
      (producto: any) => Number(producto.precio_actual || 0) > 0
    );
  }

  get cantidadObjetivo(): number {
    if (this.modo === 'general') {
      return this.productosConPrecio.length;
    }

    if (this.modo === 'individual') {
      return this.productoIndividualId ? 1 : 0;
    }

    if (this.seleccionados.size > 0) {
      return this.seleccionados.size;
    }

    if (this.proveedorId || this.categoria) {
      return this.productosFiltrados.filter(
        (producto: any) => Number(producto.precio_actual || 0) > 0
      ).length;
    }

    return 0;
  }

  get productosVistaPrevia(): any[] {
    return (this.vistaPrevia?.productos || []).slice(0, 250);
  }

  preciosMostrados(producto: any): any[] {
    return (producto?.precios || []).slice(0, 5);
  }

  estaSeleccionado(productoId: number): boolean {
    if (this.modo === 'individual') {
      return Number(this.productoIndividualId) === Number(productoId);
    }

    return this.seleccionados.has(Number(productoId));
  }

  alternarProducto(producto: any): void {
    if (Number(producto.precio_actual || 0) <= 0) {
      return;
    }

    const id = Number(producto.id);

    if (this.modo === 'individual') {
      this.productoIndividualId = id;
    } else if (this.seleccionados.has(id)) {
      this.seleccionados.delete(id);
    } else {
      this.seleccionados.add(id);
    }

    this.invalidarVistaPrevia();
    this.cdr.detectChanges();
  }

  seleccionarResultados(): void {
    for (const producto of this.productosFiltrados) {
      if (Number(producto.precio_actual || 0) > 0) {
        this.seleccionados.add(Number(producto.id));
      }
    }

    this.invalidarVistaPrevia();
    this.cdr.detectChanges();
  }

  limpiarSeleccion(): void {
    this.seleccionados.clear();
    this.invalidarVistaPrevia();
    this.cdr.detectChanges();
  }

  generarVistaPrevia(): void {
    const porcentaje = Number(this.porcentaje || 0);

    if (porcentaje <= 0) {
      this.error = 'Ingresá un porcentaje mayor a cero.';
      this.cdr.detectChanges();
      return;
    }

    if (porcentaje > 1000) {
      this.error = 'El porcentaje no puede superar el 1000%.';
      this.cdr.detectChanges();
      return;
    }

    if (this.modo === 'individual' && !this.productoIndividualId) {
      this.error = 'Seleccioná un producto para continuar.';
      this.cdr.detectChanges();
      return;
    }

    if (
      this.modo === 'parcial' &&
      !this.proveedorId &&
      !this.categoria &&
      this.seleccionados.size === 0
    ) {
      this.error = 'Elegí un filtro o seleccioná productos.';
      this.cdr.detectChanges();
      return;
    }

    this.generandoVista = true;
    this.error = '';
    this.mensajeExito = '';

    this.api.obtenerVistaPreviaAumento(this.construirPayload()).subscribe({
      next: (respuesta) => {
        this.vistaPrevia = respuesta;
        this.generandoVista = false;
        this.cdr.detectChanges();
      },
      error: (respuestaError) => {
        this.generandoVista = false;
        this.error =
          respuestaError.error?.mensaje ||
          'No se pudo generar la vista previa.';
        this.cdr.detectChanges();
      }
    });
  }

  aplicarAumento(): void {
    if (!this.vistaPrevia || this.aplicando) {
      return;
    }

    const confirmar = confirm(
      `¿Confirmar el aumento del ${this.vistaPrevia.porcentaje}% ` +
        `sobre ${this.vistaPrevia.cantidad_productos} producto(s)?\n\n` +
        'Esta operación quedará registrada en el historial.'
    );

    if (!confirmar) {
      return;
    }

    this.aplicando = true;
    this.error = '';

    this.api.aplicarAumentoPrecios(this.construirPayload()).subscribe({
      next: (respuesta) => {
        this.aplicando = false;
        this.vistaPrevia = null;
        this.mensajeExito =
          `Aumento aplicado a ${respuesta.cantidad_productos} producto(s).`;
        this.seleccionados.clear();
        this.productoIndividualId = null;
        this.cargarOpciones();
        this.cargarHistorial();
        this.preciosActualizados.emit();
        this.cdr.detectChanges();
      },
      error: (respuestaError) => {
        this.aplicando = false;
        this.error =
          respuestaError.error?.mensaje ||
          'No se pudo aplicar el aumento.';
        this.cdr.detectChanges();
      }
    });
  }

  abrirDetalleHistorial(aumento: any): void {
    this.cargandoDetalle = true;
    this.detalleHistorial = null;
    this.error = '';

    this.api.obtenerDetalleAumento(aumento.id).subscribe({
      next: (respuesta) => {
        this.detalleHistorial = respuesta;
        this.cargandoDetalle = false;
        this.cdr.detectChanges();
      },
      error: () => {
        this.cargandoDetalle = false;
        this.error = 'No se pudo abrir el detalle del aumento.';
        this.cdr.detectChanges();
      }
    });
  }

  cerrarDetalleHistorial(): void {
    this.detalleHistorial = null;
    this.cargandoDetalle = false;
    this.cdr.detectChanges();
  }

  nombreModo(modo: string): string {
    const nombres: Record<string, string> = {
      general: 'General',
      parcial: 'Parcial',
      individual: 'Por producto'
    };

    return nombres[modo] || modo;
  }

  formatearMoneda(valor: any): string {
    return Number(valor || 0).toLocaleString('es-AR', {
      minimumFractionDigits: 0,
      maximumFractionDigits: 0
    });
  }

  formatearFecha(valor: string): string {
    if (!valor) {
      return '-';
    }

    const fecha = new Date(valor.replace(' ', 'T'));

    if (Number.isNaN(fecha.getTime())) {
      return valor;
    }

    return fecha.toLocaleString('es-AR', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  }

  trackProducto(_indice: number, producto: any): number {
    return producto.id;
  }

  trackHistorial(_indice: number, aumento: any): number {
    return aumento.id;
  }

  private construirPayload(): any {
    const payload: any = {
      modo: this.modo,
      porcentaje: Number(this.porcentaje || 0)
    };

    if (this.modo === 'individual') {
      payload.producto_ids = [this.productoIndividualId];
    }

    if (this.modo === 'parcial') {
      if (this.proveedorId) {
        payload.proveedor_id = this.proveedorId;
      }

      if (this.categoria) {
        payload.categoria = this.categoria;
      }

      if (this.seleccionados.size > 0) {
        payload.producto_ids = Array.from(this.seleccionados);
      }
    }

    return payload;
  }

  private normalizar(valor: any): string {
    return String(valor || '')
      .normalize('NFD')
      .replace(/[\u0300-\u036f]/g, '')
      .toLowerCase()
      .trim();
  }
}

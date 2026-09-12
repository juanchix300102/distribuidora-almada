import { CommonModule, isPlatformBrowser } from '@angular/common';
import {
  ChangeDetectorRef,
  Component,
  EventEmitter,
  Input,
  OnChanges,
  OnDestroy,
  OnInit,
  Output,
  PLATFORM_ID,
  SimpleChanges,
  inject
} from '@angular/core';
import { FormsModule } from '@angular/forms';

import { ApiService } from '../../services/api.service';

@Component({
  selector: 'app-catalogo-visual',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './catalogo-visual.html',
  styleUrl: './catalogo-visual.css'
})
export class CatalogoVisualComponent implements OnInit, OnChanges, OnDestroy {
  private api = inject(ApiService);
  private cdr = inject(ChangeDetectorRef);
  private platformId = inject(PLATFORM_ID);

  @Input() vendedorId: number | null = null;
  @Input() vendedorNombre = '';
  @Input() modoAdmin = false;
  @Output() cerrarCatalogo = new EventEmitter<void>();

  vendedores: any[] = [];
  vendedorSeleccionadoId: number | null = null;
  vendedorSeleccionadoNombre = '';
  productos: any[] = [];
  productoAbierto: any = null;
  imagenesFallidas: Record<number, boolean> = {};

  cargando = false;
  actualizando = false;
  error = '';
  actualizadoEn = '';

  private iniciado = false;
  private intervaloActualizacion: ReturnType<typeof setInterval> | null = null;

  ngOnInit(): void {
    this.iniciado = true;
    this.configurarCatalogo();
  }

  ngOnChanges(changes: SimpleChanges): void {
    if (!this.iniciado) {
      return;
    }

    if (changes['modoAdmin'] || changes['vendedorId']) {
      this.configurarCatalogo();
    }
  }

  ngOnDestroy(): void {
    this.detenerActualizacionAutomatica();
  }

  configurarCatalogo(): void {
    this.detenerActualizacionAutomatica();
    this.productos = [];
    this.productoAbierto = null;
    this.error = '';

    if (this.modoAdmin) {
      this.cargarVendedores();
      return;
    }

    this.vendedorSeleccionadoId = Number(this.vendedorId || 0) || null;
    this.vendedorSeleccionadoNombre = this.vendedorNombre || '';

    if (this.vendedorSeleccionadoId) {
      this.cargarCatalogo(true);
      this.iniciarActualizacionAutomatica();
    } else {
      this.error = 'No se pudo identificar al vendedor.';
    }
  }

  cargarVendedores(): void {
    this.cargando = true;

    this.api.obtenerVendedores().subscribe({
      next: (respuesta) => {
        this.vendedores = (respuesta || []).filter(
          (vendedor: any) => Boolean(vendedor.activo)
        );

        const vendedorPreferido = this.vendedores.find(
          (vendedor: any) => vendedor.id === this.vendedorId
        );
        const primero = vendedorPreferido || this.vendedores[0];

        if (primero) {
          this.seleccionarVendedor(primero.id);
        } else {
          this.cargando = false;
          this.error = 'Creá y activá un vendedor para visualizar su catálogo.';
          this.cdr.detectChanges();
        }
      },
      error: () => {
        this.cargando = false;
        this.error = 'No se pudo cargar la lista de vendedores.';
        this.cdr.detectChanges();
      }
    });
  }

  seleccionarVendedor(valor: any): void {
    const id = Number(valor || 0);
    const vendedor = this.vendedores.find((item: any) => item.id === id);

    this.detenerActualizacionAutomatica();
    this.vendedorSeleccionadoId = id || null;
    this.vendedorSeleccionadoNombre = vendedor?.nombre || '';
    this.productos = [];
    this.productoAbierto = null;

    if (this.vendedorSeleccionadoId) {
      this.cargarCatalogo(true);
      this.iniciarActualizacionAutomatica();
    }
  }

  cargarCatalogo(mostrarCarga = false): void {
    if (!this.vendedorSeleccionadoId) {
      return;
    }

    const vendedorConsultado = this.vendedorSeleccionadoId;

    if (mostrarCarga) {
      this.cargando = true;
    } else {
      this.actualizando = true;
    }

    this.api.obtenerCatalogoVisual(vendedorConsultado).subscribe({
      next: (respuesta) => {
        if (vendedorConsultado !== this.vendedorSeleccionadoId) {
          return;
        }

        this.productos = respuesta?.productos || [];
        this.vendedorSeleccionadoNombre =
          respuesta?.vendedor || this.vendedorSeleccionadoNombre;
        this.actualizadoEn = respuesta?.actualizado_en || '';

        if (this.productoAbierto) {
          this.productoAbierto =
            this.productos.find(
              (producto: any) => producto.id === this.productoAbierto.id
            ) || null;
        }

        this.cargando = false;
        this.actualizando = false;
        this.error = '';
        this.cdr.detectChanges();
      },
      error: (respuestaError) => {
        if (vendedorConsultado !== this.vendedorSeleccionadoId) {
          return;
        }

        this.cargando = false;
        this.actualizando = false;
        this.error =
          respuestaError.error?.mensaje ||
          'No se pudo actualizar el catálogo visual.';
        this.cdr.detectChanges();
      }
    });
  }

  iniciarActualizacionAutomatica(): void {
    if (!isPlatformBrowser(this.platformId)) {
      return;
    }

    this.detenerActualizacionAutomatica();
    this.intervaloActualizacion = setInterval(() => {
      this.cargarCatalogo(false);
    }, 5000);
  }

  detenerActualizacionAutomatica(): void {
    if (this.intervaloActualizacion) {
      clearInterval(this.intervaloActualizacion);
      this.intervaloActualizacion = null;
    }
  }

  get productosVisibles(): any[] {
    return this.productos;
  }

  get disponibles(): number {
    return this.productos.filter((producto: any) => producto.disponible).length;
  }

  abrirProducto(producto: any): void {
    this.productoAbierto = producto;
    this.cdr.detectChanges();
  }

  cerrarProducto(): void {
    this.productoAbierto = null;
    this.cdr.detectChanges();
  }

  manejarTecla(evento: KeyboardEvent, producto: any): void {
    if (evento.key === 'Enter' || evento.key === ' ') {
      evento.preventDefault();
      this.abrirProducto(producto);
    }
  }

  obtenerImagenProducto(producto: any): string {
    if (!producto?.foto || this.imagenesFallidas[producto.id]) {
      return '';
    }

    const foto = String(producto.foto).trim().replace(/\\/g, '/');

    if (/^(https?:|data:|blob:)/i.test(foto)) {
      return foto;
    }

    if (foto.startsWith('/uploads/')) {
      return `${this.obtenerBackendBase()}${foto}`;
    }

    if (foto.startsWith('uploads/')) {
      return `${this.obtenerBackendBase()}/${foto}`;
    }

    if (foto.startsWith('assets/')) {
      return foto;
    }

    if (foto.startsWith('catalogo-productos/')) {
      return `assets/${foto}`;
    }

    return `assets/catalogo-productos/${foto}`;
  }

  marcarImagenFallida(productoId: number): void {
    this.imagenesFallidas[productoId] = true;
  }

  codigoVisible(producto: any): string {
    return (
      producto?.codigo ||
      producto?.variantes?.find((variante: any) => variante.codigo)?.codigo ||
      'Sin código'
    );
  }

  horaActualizacion(): string {
    const partes = String(this.actualizadoEn || '').split(' ');
    return partes[1]?.slice(0, 5) || 'ahora';
  }

  trackProducto(_indice: number, producto: any): number {
    return producto.id;
  }

  private obtenerBackendBase(): string {
    const host =
      typeof window !== 'undefined' && window.location.hostname
        ? window.location.hostname
        : '127.0.0.1';

    return `http://${host}:5000`;
  }
}

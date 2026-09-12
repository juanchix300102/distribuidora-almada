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

@Component({
  selector: 'app-vendedores',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './vendedores.html',
  styleUrl: './vendedores.css'
})
export class VendedoresComponent implements OnInit {
  private api = inject(ApiService);
  private cdr = inject(ChangeDetectorRef);

  @Output() resumenActualizado = new EventEmitter<void>();

  vendedores: any[] = [];
  productos: any[] = [];
  stockViaje: any[] = [];
  movimientos: any[] = [];
  ventas: any[] = [];

  vendedorSeleccionado: any = null;
  error = '';
  cargando = false;
  mostrarFormulario = false;
  editandoId: number | null = null;
  filtroProducto = '';

  vendedorForm: any = {
    nombre: '',
    usuario: '',
    contrasena: '',
    telefono: '',
    zona: '',
    observaciones: '',
    activo: true
  };

  asignacionForm: any = {
    producto_id: '',
    cantidad: 1,
    descripcion: ''
  };

  devoluciones: Record<number, number> = {};

  ngOnInit(): void {
    this.cargarTodo();
  }

  cargarTodo(): void {
    this.cargando = true;
    this.error = '';

    this.api.obtenerVendedores().subscribe({
      next: (vendedores) => {
        this.vendedores = vendedores || [];
        this.api.obtenerProductos().subscribe({
          next: (productos) => {
            this.productos = productos || [];
            this.api.obtenerVentas().subscribe({
              next: (ventas) => {
                this.ventas = ventas || [];
                this.cargando = false;
                this.cdr.detectChanges();
              },
              error: () => {
                this.ventas = [];
                this.cargando = false;
                this.cdr.detectChanges();
              }
            });
          },
          error: () => {
            this.error = 'No se pudieron cargar los productos.';
            this.cargando = false;
            this.cdr.detectChanges();
          }
        });
      },
      error: () => {
        this.error = 'No se pudieron cargar los vendedores.';
        this.cargando = false;
        this.cdr.detectChanges();
      }
    });
  }

  abrirNuevo(): void {
    this.mostrarFormulario = true;
    this.editandoId = null;
    this.vendedorForm = {
      nombre: '',
      usuario: '',
      contrasena: '',
      telefono: '',
      zona: '',
      observaciones: '',
      activo: true
    };
    this.cdr.detectChanges();
  }

  editar(vendedor: any): void {
    this.mostrarFormulario = true;
    this.editandoId = vendedor.id;
    this.vendedorForm = {
      nombre: vendedor.nombre || '',
      usuario: vendedor.usuario || '',
      contrasena: '',
      telefono: vendedor.telefono || '',
      zona: vendedor.zona || '',
      observaciones: vendedor.observaciones || '',
      activo: Boolean(vendedor.activo)
    };
    this.cdr.detectChanges();
  }

  cerrarFormulario(): void {
    this.mostrarFormulario = false;
    this.editandoId = null;
  }

  guardar(): void {
    if (!String(this.vendedorForm.nombre || '').trim()) {
      this.error = 'El nombre del vendedor es obligatorio.';
      return;
    }

    if (!String(this.vendedorForm.usuario || '').trim()) {
      this.error = 'El usuario es obligatorio.';
      return;
    }

    if (!this.editandoId && String(this.vendedorForm.contrasena || '').length < 4) {
      this.error = 'La contraseña debe tener al menos 4 caracteres.';
      return;
    }

    const accion = this.editandoId
      ? this.api.actualizarVendedor(this.editandoId, this.vendedorForm)
      : this.api.crearVendedor(this.vendedorForm);

    accion.subscribe({
      next: () => {
        this.mostrarFormulario = false;
        this.editandoId = null;
        this.error = '';
        this.cargarTodo();
        this.resumenActualizado.emit();
      },
      error: (error) => {
        this.error = error.error?.mensaje || 'No se pudo guardar el vendedor.';
        this.cdr.detectChanges();
      }
    });
  }

  desactivar(vendedor: any): void {
    if (!confirm(`¿Desactivar a ${vendedor.nombre}?`)) {
      return;
    }

    this.api.desactivarVendedor(vendedor.id).subscribe({
      next: () => {
        if (this.vendedorSeleccionado?.id === vendedor.id) {
          this.vendedorSeleccionado = null;
          this.stockViaje = [];
          this.movimientos = [];
        }
        this.cargarTodo();
        this.resumenActualizado.emit();
      },
      error: (error) => {
        this.error = error.error?.mensaje || 'No se pudo desactivar el vendedor.';
        this.cdr.detectChanges();
      }
    });
  }

  seleccionarVendedor(vendedor: any): void {
    this.vendedorSeleccionado = vendedor;
    this.cargarStockSeleccionado();
  }

  cargarStockSeleccionado(): void {
    if (!this.vendedorSeleccionado?.id) {
      return;
    }

    const vendedorId = this.vendedorSeleccionado.id;
    this.error = '';

    this.api.obtenerStockViaje(vendedorId).subscribe({
      next: (stock) => {
        this.stockViaje = stock || [];
        this.devoluciones = {};
        this.api.obtenerMovimientosStockViaje(vendedorId).subscribe({
          next: (movimientos) => {
            this.movimientos = movimientos || [];
            this.cdr.detectChanges();
          },
          error: () => {
            this.movimientos = [];
            this.cdr.detectChanges();
          }
        });
      },
      error: (error) => {
        this.error = error.error?.mensaje || 'No se pudo cargar el stock en viaje.';
        this.cdr.detectChanges();
      }
    });
  }

  asignarStock(): void {
    if (!this.vendedorSeleccionado?.id) {
      this.error = 'Seleccioná un vendedor.';
      return;
    }

    const productoId = Number(this.asignacionForm.producto_id || 0);
    const cantidad = Number(this.asignacionForm.cantidad || 0);

    if (!productoId || cantidad <= 0) {
      this.error = 'Seleccioná un producto e ingresá una cantidad válida.';
      return;
    }

    this.api.asignarStockViaje(this.vendedorSeleccionado.id, {
      producto_id: productoId,
      cantidad,
      descripcion: this.asignacionForm.descripcion
    }).subscribe({
      next: () => {
        this.asignacionForm = {
          producto_id: '',
          cantidad: 1,
          descripcion: ''
        };
        this.cargarStockSeleccionado();
        this.api.obtenerProductos().subscribe({
          next: (productos) => {
            this.productos = productos || [];
            this.resumenActualizado.emit();
            this.cdr.detectChanges();
          }
        });
      },
      error: (error) => {
        this.error = error.error?.mensaje || 'No se pudo asignar la mercadería.';
        this.cdr.detectChanges();
      }
    });
  }

  devolver(item: any): void {
    const cantidad = Number(this.devoluciones[item.producto_id] || 0);

    if (cantidad <= 0) {
      this.error = 'Ingresá una cantidad para devolver.';
      return;
    }

    this.api.devolverStockViaje(this.vendedorSeleccionado.id, {
      producto_id: item.producto_id,
      cantidad
    }).subscribe({
      next: () => {
        this.cargarStockSeleccionado();
        this.api.obtenerProductos().subscribe({
          next: (productos) => {
            this.productos = productos || [];
            this.resumenActualizado.emit();
            this.cdr.detectChanges();
          }
        });
      },
      error: (error) => {
        this.error = error.error?.mensaje || 'No se pudo registrar la devolución.';
        this.cdr.detectChanges();
      }
    });
  }

  get productosFiltrados(): any[] {
    const filtro = this.filtroProducto.trim().toLowerCase();

    const disponibles = this.productos.filter((producto) => Number(producto.stock || 0) > 0);

    if (!filtro) {
      return disponibles.slice(0, 120);
    }

    return disponibles
      .filter((producto) => {
        const texto = `${producto.codigo || ''} ${producto.nombre || ''} ${producto.proveedor || ''}`.toLowerCase();
        return texto.includes(filtro);
      })
      .slice(0, 120);
  }

  get ventasSeleccionadas(): any[] {
    if (!this.vendedorSeleccionado?.id) {
      return [];
    }

    return this.ventas.filter((venta) => venta.vendedor_id === this.vendedorSeleccionado.id);
  }

  get totalUnidadesViaje(): number {
    return this.stockViaje.reduce((total, item) => total + Number(item.cantidad || 0), 0);
  }

  formatearMoneda(valor: any): string {
    return Number(valor || 0).toLocaleString('es-AR', {
      minimumFractionDigits: 0,
      maximumFractionDigits: 2
    });
  }
}

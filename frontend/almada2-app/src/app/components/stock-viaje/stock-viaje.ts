import { CommonModule } from '@angular/common';
import { ChangeDetectorRef, Component, OnInit, inject } from '@angular/core';
import { FormsModule } from '@angular/forms';

import { ApiService } from '../../services/api.service';

@Component({
  selector: 'app-stock-viaje',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './stock-viaje.html',
  styleUrl: './stock-viaje.css'
})
export class StockViajeComponent implements OnInit {
  private api = inject(ApiService);
  private cdr = inject(ChangeDetectorRef);

  vendedores: any[] = [];
  productos: any[] = [];
  stockViaje: any[] = [];
  movimientos: any[] = [];
  ventas: any[] = [];

  vendedorSeleccionado: any = null;
  error = '';
  cargando = false;
  filtroProducto = '';

  asignacionForm: any = {
    producto_id: '',
    cantidad: 1,
    descripcion: ''
  };

  devoluciones: Record<number, number> = {};

  ngOnInit(): void {
    this.cargarBase();
  }

  cargarBase(): void {
    this.cargando = true;
    this.error = '';

    this.api.obtenerVendedores().subscribe({
      next: (vendedores) => {
        this.vendedores = (vendedores || []).filter((v: any) => Boolean(v.activo));
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
        this.asignacionForm = { producto_id: '', cantidad: 1, descripcion: '' };
        this.refrescarTrasMovimiento();
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
      next: () => this.refrescarTrasMovimiento(),
      error: (error) => {
        this.error = error.error?.mensaje || 'No se pudo registrar la devolución.';
        this.cdr.detectChanges();
      }
    });
  }

  private refrescarTrasMovimiento(): void {
    this.cargarStockSeleccionado();
    this.api.obtenerProductos().subscribe({
      next: (productos) => {
        this.productos = productos || [];
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

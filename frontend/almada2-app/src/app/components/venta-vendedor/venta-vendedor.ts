import { CommonModule } from '@angular/common';
import {
  ChangeDetectorRef,
  Component,
  Input,
  OnChanges,
  SimpleChanges,
  inject
} from '@angular/core';
import { FormsModule } from '@angular/forms';

import { ApiService } from '../../services/api.service';

@Component({
  selector: 'app-venta-vendedor',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './venta-vendedor.html',
  styleUrl: './venta-vendedor.css'
})
export class VentaVendedorComponent implements OnChanges {
  private api = inject(ApiService);
  private cdr = inject(ChangeDetectorRef);

  @Input() vendedorId: number | null = null;
  @Input() vendedorNombre = '';

  stockViaje: any[] = [];
  clientes: any[] = [];
  ventas: any[] = [];
  carrito: any[] = [];
  cantidades: Record<number, number> = {};
  filtro = '';
  error = '';
  mensaje = '';
  enviando = false;

  ventaForm: any = {
    cliente_id: '',
    forma_pago: 'Efectivo',
    observaciones: ''
  };

  ngOnChanges(changes: SimpleChanges): void {
    if (changes['vendedorId'] && this.vendedorId) {
      this.cargarDatos();
    }
  }

  cargarDatos(): void {
    if (!this.vendedorId) {
      return;
    }

    this.error = '';

    this.api.obtenerStockViaje(this.vendedorId).subscribe({
      next: (stock) => {
        this.stockViaje = stock || [];
        this.api.obtenerClientes().subscribe({
          next: (clientes) => {
            this.clientes = clientes || [];
            this.api.obtenerVentasVendedor(this.vendedorId as number).subscribe({
              next: (ventas) => {
                this.ventas = ventas || [];
                this.cdr.detectChanges();
              },
              error: () => {
                this.ventas = [];
                this.cdr.detectChanges();
              }
            });
          },
          error: () => {
            this.clientes = [];
            this.cdr.detectChanges();
          }
        });
      },
      error: (error) => {
        this.error = error.error?.mensaje || 'No se pudo cargar tu stock en viaje.';
        this.cdr.detectChanges();
      }
    });
  }

  get stockFiltrado(): any[] {
    const filtro = this.filtro.trim().toLowerCase();

    if (!filtro) {
      return this.stockViaje;
    }

    return this.stockViaje.filter((item) => {
      const texto = `${item.codigo || ''} ${item.nombre || ''} ${item.proveedor || ''}`.toLowerCase();
      return texto.includes(filtro);
    });
  }

  agregar(item: any): void {
    const cantidad = Number(this.cantidades[item.producto_id] || 1);

    if (cantidad <= 0 || cantidad > Number(item.cantidad || 0)) {
      this.error = `Cantidad inválida para ${item.nombre}.`;
      return;
    }

    const existente = this.carrito.find((fila) => fila.producto_id === item.producto_id);

    if (existente) {
      const nuevaCantidad = existente.cantidad + cantidad;
      if (nuevaCantidad > Number(item.cantidad || 0)) {
        this.error = `No podés superar el stock disponible de ${item.nombre}.`;
        return;
      }
      existente.cantidad = nuevaCantidad;
    } else {
      this.carrito.push({
        producto_id: item.producto_id,
        codigo: item.codigo,
        nombre: item.nombre,
        cantidad,
        precio_unitario: Number(item.precio_venta || 0),
        stock_disponible: Number(item.cantidad || 0)
      });
    }

    this.cantidades[item.producto_id] = 1;
    this.error = '';
    this.cdr.detectChanges();
  }

  cambiarCantidad(item: any): void {
    item.cantidad = Math.max(1, Math.min(Number(item.cantidad || 1), item.stock_disponible));
    this.cdr.detectChanges();
  }

  quitar(productoId: number): void {
    this.carrito = this.carrito.filter((item) => item.producto_id !== productoId);
    this.cdr.detectChanges();
  }

  get totalUnidadesViaje(): number {
    return this.stockViaje.reduce(
      (total, item) => total + Number(item.cantidad || 0),
      0
    );
  }

  get totalVenta(): number {
    return this.carrito.reduce(
      (total, item) => total + Number(item.cantidad || 0) * Number(item.precio_unitario || 0),
      0
    );
  }

  confirmarVenta(): void {
    if (!this.vendedorId) {
      return;
    }

    if (this.carrito.length === 0) {
      this.error = 'Agregá al menos un producto a la venta.';
      return;
    }

    if (!this.ventaForm.cliente_id) {
      this.error = 'Seleccioná un cliente para registrar la venta.';
      return;
    }

    this.enviando = true;
    this.error = '';
    this.mensaje = '';

    const payload = {
      cliente_id: this.ventaForm.cliente_id || null,
      forma_pago: this.ventaForm.forma_pago,
      observaciones: this.ventaForm.observaciones,
      items: this.carrito.map((item) => ({
        producto_id: item.producto_id,
        cantidad: Number(item.cantidad)
      }))
    };

    this.api.registrarVentaVendedor(this.vendedorId, payload).subscribe({
      next: (respuesta) => {
        this.enviando = false;
        this.mensaje = `Venta #${respuesta.venta_id} registrada. Total $${this.formatearMoneda(respuesta.total)}.`;
        this.carrito = [];
        this.ventaForm = {
          cliente_id: '',
          forma_pago: 'Efectivo',
          observaciones: ''
        };
        this.cargarDatos();
        this.cdr.detectChanges();
      },
      error: (error) => {
        this.enviando = false;
        this.error = error.error?.mensaje || 'No se pudo registrar la venta.';
        this.cdr.detectChanges();
      }
    });
  }

  formatearMoneda(valor: any): string {
    return Number(valor || 0).toLocaleString('es-AR', {
      minimumFractionDigits: 0,
      maximumFractionDigits: 2
    });
  }
}

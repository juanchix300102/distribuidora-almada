import { CommonModule } from '@angular/common';
import { Component, ChangeDetectorRef, EventEmitter, OnInit, Output, inject } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { ApiService } from '../../services/api.service';

@Component({
  selector: 'app-proveedores',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './proveedores.html',
  styleUrl: './proveedores.css'
})
export class ProveedoresComponent implements OnInit {
  private api = inject(ApiService);
  private cdr = inject(ChangeDetectorRef);

  @Output() resumenActualizado = new EventEmitter<void>();

  proveedores: any[] = [];
  proveedorSeleccionado: any = null;
  productosProveedor: any[] = [];

  busquedaProveedor = '';
  error = '';
  cargando = false;

  mostrarFormularioProveedor = false;

  proveedorForm = {
    nombre: '',
    telefono: '',
    direccion: '',
    localidad: '',
    contacto: '',
    observaciones: ''
  };

  nuevoProductoProveedor: any = {
    codigo: '',
    nombre: '',
    descripcion: '',
    categoria: '',
    stock: 0,
    precio_base: 0,
    bonificacion_1: 0,
    bonificacion_2: 0,
    bonificacion_3: 0,
    iva: 21,
    flete: 0,
    ganancia: 40,
    cantidad_caja: 1
  };

  ngOnInit(): void {
    this.cargarProveedores();
  }

  cargarProveedores(): void {
    this.cargando = true;
    this.error = '';

    this.api.obtenerProveedores().subscribe({
      next: (respuesta) => {
        this.proveedores = respuesta || [];
        this.cargando = false;
        this.cdr.detectChanges();
      },
      error: () => {
        this.error = 'No se pudieron cargar los proveedores.';
        this.cargando = false;
        this.cdr.detectChanges();
      }
    });
  }

  abrirFormularioProveedor(): void {
    this.mostrarFormularioProveedor = true;

    this.proveedorForm = {
      nombre: '',
      telefono: '',
      direccion: '',
      localidad: '',
      contacto: '',
      observaciones: ''
    };

    this.cdr.detectChanges();
  }

  cerrarFormularioProveedor(): void {
    this.mostrarFormularioProveedor = false;
    this.cdr.detectChanges();
  }

  agregarProveedor(): void {
    if (!this.proveedorForm.nombre.trim()) {
      alert('El nombre del proveedor es obligatorio.');
      return;
    }

    this.api.crearProveedor(this.proveedorForm).subscribe({
      next: () => {
        alert('Proveedor agregado correctamente.');
        this.cerrarFormularioProveedor();
        this.cargarProveedores();
        this.resumenActualizado.emit();
      },
      error: (error) => {
        this.error = error.error?.mensaje || 'No se pudo agregar el proveedor.';
        this.cdr.detectChanges();
      }
    });
  }

  seleccionarProveedor(proveedor: any): void {
    this.proveedorSeleccionado = proveedor;
    this.busquedaProveedor = '';
    this.cargarProductosProveedor(proveedor.id);
  }

  volverAProveedores(): void {
    this.proveedorSeleccionado = null;
    this.productosProveedor = [];
    this.busquedaProveedor = '';
    this.cargarProveedores();
    this.cdr.detectChanges();
  }

  cargarProductosProveedor(proveedorId: number): void {
    this.error = '';

    this.api.obtenerProductosProveedor(proveedorId).subscribe({
      next: (respuesta) => {
        this.productosProveedor = respuesta || [];
        this.cdr.detectChanges();
      },
      error: () => {
        this.error = 'No se pudieron cargar los productos del proveedor.';
        this.cdr.detectChanges();
      }
    });
  }

  productosProveedorFiltrados(): any[] {
    const texto = this.busquedaProveedor.toLowerCase().trim();

    if (!texto) {
      return this.productosProveedor;
    }

    return this.productosProveedor.filter(producto =>
      String(producto.producto || '').toLowerCase().includes(texto) ||
      String(producto.codigo || '').toLowerCase().includes(texto) ||
      String(producto.categoria || '').toLowerCase().includes(texto)
    );
  }

  agregarProductoProveedor(): void {
    if (!this.proveedorSeleccionado) {
      alert('Seleccioná un proveedor.');
      return;
    }

    if (!String(this.nuevoProductoProveedor.nombre || '').trim()) {
      alert('El nombre del producto es obligatorio.');
      return;
    }

    this.api.crearProductoProveedor(
      this.proveedorSeleccionado.id,
      this.nuevoProductoProveedor
    ).subscribe({
      next: () => {
        alert('Producto agregado al proveedor.');

        this.nuevoProductoProveedor = {
          codigo: '',
          nombre: '',
          descripcion: '',
          categoria: '',
          stock: 0,
          precio_base: 0,
          bonificacion_1: 0,
          bonificacion_2: 0,
          bonificacion_3: 0,
          iva: 21,
          flete: 0,
          ganancia: 40,
          cantidad_caja: 1
        };

        this.cargarProductosProveedor(this.proveedorSeleccionado.id);
        this.resumenActualizado.emit();
      },
      error: (error) => {
        this.error = error.error?.mensaje || 'No se pudo agregar el producto.';
        this.cdr.detectChanges();
      }
    });
  }

  actualizarPrecioProveedor(producto: any): void {
    if (!producto.precio_id) {
      alert('No se encontró el ID del precio.');
      return;
    }

    this.api.actualizarPrecioProveedor(producto.precio_id, {
      precio_base: producto.precio_base,
      bonificacion_1: producto.bonificacion_1,
      bonificacion_2: producto.bonificacion_2,
      bonificacion_3: producto.bonificacion_3,
      iva: producto.iva,
      flete: producto.flete,
      ganancia: producto.ganancia
    }).subscribe({
      next: () => {
        alert('Precio actualizado correctamente.');

        if (this.proveedorSeleccionado) {
          this.cargarProductosProveedor(this.proveedorSeleccionado.id);
        }

        this.resumenActualizado.emit();
      },
      error: (error) => {
        this.error = error.error?.mensaje || 'No se pudo actualizar el precio.';
        this.cdr.detectChanges();
      }
    });
  }

  formatearMoneda(valor: any): string {
    const numero = Number(valor || 0);

    return numero.toLocaleString('es-AR', {
      minimumFractionDigits: 0,
      maximumFractionDigits: 0
    });
  }
}

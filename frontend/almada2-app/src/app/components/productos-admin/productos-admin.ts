import { CommonModule } from '@angular/common';
import {
  Component,
  ChangeDetectorRef,
  EventEmitter,
  Input,
  OnInit,
  Output,
  inject
} from '@angular/core';
import { FormsModule } from '@angular/forms';

import { ApiService } from '../../services/api.service';

@Component({
  selector: 'app-productos-admin',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './productos-admin.html',
  styleUrl: './productos-admin.css'
})
export class ProductosAdminComponent implements OnInit {
  private api = inject(ApiService);
  private cdr = inject(ChangeDetectorRef);

  @Input() resumen: any = null;
  @Output() resumenActualizado = new EventEmitter<void>();

  productos: any[] = [];
  proveedores: any[] = [];

  busqueda = '';
  error = '';
  cargando = false;
  guardando = false;

  mostrarFormulario = false;
  modoEditar = false;
  productoEditandoId: number | null = null;

  productoForm: any = this.obtenerProductoVacio();

  ngOnInit(): void {
    this.cargarProductos();
    this.cargarProveedores();
  }

  obtenerVarianteVacia(nombreVariante: string = 'Única'): any {
    return {
      id: null,
      nombre_variante: nombreVariante,
      codigo: '',
      cantidad_caja: 1,
      precio_unidad: 0,
      precio_caja: 0,
      precio_venta: 0,
      stock: 0
    };
  }

  obtenerProductoVacio(): any {
    return {
      proveedor_id: null,
      nombre: '',
      descripcion: '',
      categoria: '',
      foto: '',

      codigo: '',
      cantidad_caja: 1,
      precio_unidad: 0,
      precio_caja: 0,
      precio_venta: 0,
      stock: 0,

      precio_base: 0,
      bonificacion_1: 0,
      bonificacion_2: 0,
      bonificacion_3: 0,
      iva: 21,
      flete: 0,
      ganancia: 40,

      variantes: [
        this.obtenerVarianteVacia()
      ]
    };
  }

  cargarProductos(): void {
    this.cargando = true;
    this.error = '';

    this.api.obtenerProductos().subscribe({
      next: (respuesta) => {
        this.productos = respuesta || [];
        this.cargando = false;
        this.cdr.detectChanges();
      },
      error: () => {
        this.error = 'No se pudieron cargar los productos.';
        this.cargando = false;
        this.cdr.detectChanges();
      }
    });
  }

  cargarProveedores(): void {
    this.api.obtenerProveedores().subscribe({
      next: (respuesta) => {
        this.proveedores = respuesta || [];
        this.cdr.detectChanges();
      },
      error: () => {
        this.error = 'No se pudieron cargar los proveedores.';
        this.cdr.detectChanges();
      }
    });
  }

  productosFiltrados(): any[] {
    const texto = this.busqueda.toLowerCase().trim();

    if (!texto) {
      return this.productos;
    }

    return this.productos.filter(producto => {
      const coincideProducto =
        String(producto.nombre || '').toLowerCase().includes(texto) ||
        String(producto.categoria || '').toLowerCase().includes(texto) ||
        String(producto.proveedor || '').toLowerCase().includes(texto) ||
        String(producto.codigo || '').toLowerCase().includes(texto);

      const variantes = producto.variantes || [];

      const coincideVariante = variantes.some((variante: any) =>
        String(variante.nombre_variante || '').toLowerCase().includes(texto) ||
        String(variante.codigo || '').toLowerCase().includes(texto)
      );

      return coincideProducto || coincideVariante;
    });
  }

  abrirFormulario(): void {
    this.mostrarFormulario = true;
    this.modoEditar = false;
    this.productoEditandoId = null;
    this.error = '';
    this.productoForm = this.obtenerProductoVacio();

    this.cdr.detectChanges();
  }

  cerrarFormulario(): void {
    this.mostrarFormulario = false;
    this.modoEditar = false;
    this.productoEditandoId = null;
    this.guardando = false;
    this.error = '';
    this.productoForm = this.obtenerProductoVacio();

    this.cdr.detectChanges();
  }

  agregarVariante(): void {
    if (!Array.isArray(this.productoForm.variantes)) {
      this.productoForm.variantes = [];
    }

    if (
      this.productoForm.variantes.length === 1 &&
      this.productoForm.variantes[0].nombre_variante === 'Única'
    ) {
      this.productoForm.variantes[0].nombre_variante = '';
    }

    this.productoForm.variantes.push(
      this.obtenerVarianteVacia('')
    );

    this.cdr.detectChanges();
  }

  eliminarVariante(indice: number): void {
    if (!this.productoForm.variantes) {
      return;
    }

    if (this.productoForm.variantes.length <= 1) {
      alert('El producto debe tener al menos una variante.');

      return;
    }

    const variante = this.productoForm.variantes[indice];

    const nombre =
      String(variante?.nombre_variante || '').trim() ||
      `variante ${indice + 1}`;

    const confirmar = confirm(
      `¿Quitar "${nombre}" de este producto?`
    );

    if (!confirmar) {
      return;
    }

    this.productoForm.variantes.splice(indice, 1);

    this.cdr.detectChanges();
  }

  validarFormulario(): boolean {
    if (!String(this.productoForm.nombre || '').trim()) {
      alert('El nombre del producto es obligatorio.');
      return false;
    }

    if (!this.productoForm.proveedor_id) {
      alert('Seleccioná un proveedor.');
      return false;
    }

    if (
      !Array.isArray(this.productoForm.variantes) ||
      this.productoForm.variantes.length === 0
    ) {
      alert('El producto debe tener al menos una variante.');
      return false;
    }

    for (
      let indice = 0;
      indice < this.productoForm.variantes.length;
      indice++
    ) {
      const variante = this.productoForm.variantes[indice];

      if (!String(variante.nombre_variante || '').trim()) {
        alert(
          `Completá la medida, modelo u opción de la variante ${indice + 1}.`
        );

        return false;
      }

      if (Number(variante.cantidad_caja || 0) <= 0) {
        alert(
          `La cantidad por caja de "${variante.nombre_variante}" debe ser mayor a cero.`
        );

        return false;
      }

      if (Number(variante.stock || 0) < 0) {
        alert(
          `El stock de "${variante.nombre_variante}" no puede ser negativo.`
        );

        return false;
      }

      if (Number(variante.precio_venta || 0) < 0) {
        alert(
          `El precio de venta de "${variante.nombre_variante}" no puede ser negativo.`
        );

        return false;
      }
    }

    const codigos = this.productoForm.variantes
      .map((variante: any) =>
        String(variante.codigo || '').trim().toLowerCase()
      )
      .filter((codigo: string) => codigo !== '');

    const codigosUnicos = new Set(codigos);

    if (codigos.length !== codigosUnicos.size) {
      alert(
        'Hay códigos repetidos entre las variantes. Cada código debe ser diferente.'
      );

      return false;
    }

    return true;
  }

  prepararProductoParaGuardar(): any {
    const variantes = (this.productoForm.variantes || []).map(
      (variante: any) => ({
        id: variante.id || null,
        nombre_variante: String(
          variante.nombre_variante || ''
        ).trim(),
        codigo: String(variante.codigo || '').trim(),
        cantidad_caja: Number(variante.cantidad_caja || 1),
        precio_unidad: Number(variante.precio_unidad || 0),
        precio_caja: Number(variante.precio_caja || 0),
        precio_venta: Number(variante.precio_venta || 0),
        stock: Number(variante.stock || 0)
      })
    );

    const primeraVariante =
      variantes[0] || this.obtenerVarianteVacia();

    const stockTotal = variantes.reduce(
      (total: number, variante: any) =>
        total + Number(variante.stock || 0),
      0
    );

    return {
      ...this.productoForm,

      proveedor_id: Number(this.productoForm.proveedor_id),
      nombre: String(this.productoForm.nombre || '').trim(),
      descripcion: String(
        this.productoForm.descripcion || ''
      ).trim(),
      categoria: String(
        this.productoForm.categoria || ''
      ).trim(),

      codigo: primeraVariante.codigo,
      cantidad_caja: primeraVariante.cantidad_caja,
      precio_unidad: primeraVariante.precio_unidad,
      precio_caja: primeraVariante.precio_caja,
      precio_venta: primeraVariante.precio_venta,
      stock: stockTotal,

      variantes
    };
  }

  guardarProducto(): void {
    this.error = '';

    if (!this.validarFormulario()) {
      return;
    }

    const datos = this.prepararProductoParaGuardar();

    this.guardando = true;

    if (this.modoEditar && this.productoEditandoId) {
      this.api
        .actualizarProducto(
          this.productoEditandoId,
          datos
        )
        .subscribe({
          next: () => {
            alert('Producto actualizado correctamente.');

            this.guardando = false;
            this.cerrarFormulario();
            this.cargarProductos();
            this.resumenActualizado.emit();
          },
          error: (error) => {
            this.guardando = false;

            this.error =
              error.error?.mensaje ||
              'No se pudo actualizar el producto.';

            this.cdr.detectChanges();
          }
        });

      return;
    }

    this.api
      .crearProductoProveedor(
        datos.proveedor_id,
        datos
      )
      .subscribe({
        next: (respuesta) => {
          const cantidadVariantes =
            respuesta?.cantidad_variantes ??
            datos.variantes.length;

          alert(
            `Producto guardado correctamente con ${cantidadVariantes} variante(s).`
          );

          this.guardando = false;
          this.cerrarFormulario();
          this.cargarProductos();
          this.resumenActualizado.emit();
        },
        error: (error) => {
          this.guardando = false;

          this.error =
            error.error?.mensaje ||
            'No se pudo guardar el producto.';

          this.cdr.detectChanges();
        }
      });
  }

  editarProducto(producto: any): void {
    this.mostrarFormulario = true;
    this.modoEditar = true;
    this.productoEditandoId = producto.id;
    this.error = '';

    let variantes: any[] = [];

    if (
      Array.isArray(producto.variantes) &&
      producto.variantes.length > 0
    ) {
      variantes = producto.variantes.map(
        (variante: any) => ({
          id: variante.id,
          nombre_variante:
            variante.nombre_variante || '',
          codigo: variante.codigo || '',
          cantidad_caja:
            Number(variante.cantidad_caja || 1),
          precio_unidad:
            Number(variante.precio_unidad || 0),
          precio_caja:
            Number(variante.precio_caja || 0),
          precio_venta:
            Number(variante.precio_venta || 0),
          stock:
            Number(variante.stock || 0)
        })
      );
    } else {
      /*
       * Compatibilidad con productos antiguos.
       * Al editarlos y guardarlos pasan automáticamente
       * a tener una variante "Única".
       */
      variantes = [
        {
          id: null,
          nombre_variante: 'Única',
          codigo: producto.codigo || '',
          cantidad_caja:
            Number(producto.cantidad_caja || 1),
          precio_unidad:
            Number(producto.precio_unidad || 0),
          precio_caja:
            Number(producto.precio_caja || 0),
          precio_venta:
            Number(producto.precio_venta || 0),
          stock:
            Number(producto.stock || 0)
        }
      ];
    }

    this.productoForm = {
      proveedor_id: producto.proveedor_id || null,
      nombre: producto.nombre || '',
      descripcion: producto.descripcion || '',
      categoria: producto.categoria || '',
      foto: producto.foto || '',

      codigo: producto.codigo || '',
      cantidad_caja:
        Number(producto.cantidad_caja || 1),
      precio_unidad:
        Number(producto.precio_unidad || 0),
      precio_caja:
        Number(producto.precio_caja || 0),
      precio_venta:
        Number(producto.precio_venta || 0),
      stock:
        Number(producto.stock || 0),

      precio_base:
        Number(producto.precio_base || 0),
      bonificacion_1:
        Number(producto.bonificacion_1 || 0),
      bonificacion_2:
        Number(producto.bonificacion_2 || 0),
      bonificacion_3:
        Number(producto.bonificacion_3 || 0),
      iva:
        Number(producto.iva || 21),
      flete:
        Number(producto.flete || 0),
      ganancia:
        Number(producto.ganancia || 40),

      variantes
    };

    this.cdr.detectChanges();
  }

  eliminarProducto(id: number): void {
    const confirmar = confirm(
      '¿Eliminar este producto y todas sus variantes?'
    );

    if (!confirmar) {
      return;
    }

    this.api.eliminarProducto(id).subscribe({
      next: () => {
        alert(
          'Producto y variantes eliminados correctamente.'
        );

        this.cargarProductos();
        this.resumenActualizado.emit();
      },
      error: (error) => {
        this.error =
          error.error?.mensaje ||
          'No se pudo eliminar el producto.';

        this.cdr.detectChanges();
      }
    });
  }

  cantidadVariantesProducto(producto: any): number {
    if (Array.isArray(producto?.variantes)) {
      return producto.variantes.length;
    }

    return Number(producto?.cantidad_variantes || 0);
  }

  stockTotalProducto(producto: any): number {
    if (
      Array.isArray(producto?.variantes) &&
      producto.variantes.length > 0
    ) {
      return producto.variantes.reduce(
        (total: number, variante: any) =>
          total + Number(variante.stock || 0),
        0
      );
    }

    return Number(producto?.stock || 0);
  }

  precioDesdeProducto(producto: any): number {
    if (
      Array.isArray(producto?.variantes) &&
      producto.variantes.length > 0
    ) {
      const precios = producto.variantes
        .map((variante: any) =>
          Number(variante.precio_venta || 0)
        )
        .filter((precio: number) => precio > 0);

      if (precios.length > 0) {
        return Math.min(...precios);
      }
    }

    return Number(producto?.precio_venta || 0);
  }

  stockBajoProducto(producto: any): boolean {
    if (
      Array.isArray(producto?.variantes) &&
      producto.variantes.length > 0
    ) {
      return producto.variantes.some(
        (variante: any) =>
          Number(variante.stock || 0) <= 5
      );
    }

    return Number(producto?.stock || 0) <= 5;
  }

  formatearMoneda(valor: any): string {
    const numero = Number(valor || 0);

    return numero.toLocaleString('es-AR', {
      minimumFractionDigits: 0,
      maximumFractionDigits: 0
    });
  }
}

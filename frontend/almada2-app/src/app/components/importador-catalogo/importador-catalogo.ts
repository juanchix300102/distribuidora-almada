import { CommonModule } from '@angular/common';
import { Component, ChangeDetectorRef, EventEmitter, Output, inject } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { ApiService } from '../../services/api.service';

@Component({
  selector: 'app-importador-catalogo',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './importador-catalogo.html',
  styleUrl: './importador-catalogo.css'
})
export class ImportadorCatalogoComponent {
  private api = inject(ApiService);
  private cdr = inject(ChangeDetectorRef);

  @Output() importacionFinalizada = new EventEmitter<void>();

  archivoSeleccionado: File | null = null;
  tipoImportacion = 'catalogo_completo';

  cargando = false;
  error = '';
  resultado: any = null;

  tiposImportacion = [
    {
      valor: 'catalogo_venta',
      titulo: 'Catálogo de venta',
      descripcion: 'Para cargar los productos propios de Almada 2.'
    },
    {
      valor: 'lista_proveedores',
      titulo: 'Lista de proveedores / costos',
      descripcion: 'Para cargar costos, proveedor, bonificaciones, IVA, flete y ganancia.'
    },
    {
      valor: 'catalogo_completo',
      titulo: 'Catálogo completo',
      descripcion: 'Para cargar todo junto: productos, proveedor, precios de venta, costos y stock.'
    }
  ];

  seleccionarArchivo(evento: Event): void {
    const input = evento.target as HTMLInputElement;

    if (!input.files || input.files.length === 0) {
      this.archivoSeleccionado = null;
      return;
    }

    this.archivoSeleccionado = input.files[0];
    this.resultado = null;
    this.error = '';

    this.cdr.detectChanges();
  }

  importar(): void {
    if (!this.archivoSeleccionado) {
      this.error = 'Seleccioná un archivo CSV o Excel.';
      this.cdr.detectChanges();
      return;
    }

    const nombre = this.archivoSeleccionado.name.toLowerCase();

    if (!nombre.endsWith('.csv') && !nombre.endsWith('.xlsx')) {
      this.error = 'El archivo debe ser CSV o XLSX.';
      this.cdr.detectChanges();
      return;
    }

    this.cargando = true;
    this.error = '';
    this.resultado = null;

    this.api.importarCatalogo(this.archivoSeleccionado, this.tipoImportacion).subscribe({
      next: (respuesta) => {
        this.resultado = respuesta;
        this.cargando = false;
        this.importacionFinalizada.emit();
        this.cdr.detectChanges();
      },
      error: (error) => {
        this.error = error.error?.mensaje || 'No se pudo importar el catálogo.';
        this.cargando = false;
        this.cdr.detectChanges();
      }
    });
  }

  obtenerTipoActual(): any {
    return this.tiposImportacion.find(tipo => tipo.valor === this.tipoImportacion);
  }
}

import { CommonModule } from '@angular/common';
import { ChangeDetectorRef, Component, OnInit, inject } from '@angular/core';
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

  vendedores: any[] = [];
  error = '';
  cargando = false;
  mostrarFormulario = false;
  editandoId: number | null = null;

  vendedorForm: any = this.vendedorVacio();

  ngOnInit(): void {
    this.cargarVendedores();
  }

  vendedorVacio(): any {
    return {
      nombre: '',
      usuario: '',
      contrasena: '',
      telefono: '',
      zona: '',
      observaciones: '',
      activo: true
    };
  }

  cargarVendedores(): void {
    this.cargando = true;
    this.error = '';

    this.api.obtenerVendedores().subscribe({
      next: (vendedores) => {
        this.vendedores = vendedores || [];
        this.cargando = false;
        this.cdr.detectChanges();
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
    this.vendedorForm = this.vendedorVacio();
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
    this.vendedorForm = this.vendedorVacio();
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
        this.vendedorForm = this.vendedorVacio();
        this.error = '';
        this.cargarVendedores();
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
      next: () => this.cargarVendedores(),
      error: (error) => {
        this.error = error.error?.mensaje || 'No se pudo desactivar el vendedor.';
        this.cdr.detectChanges();
      }
    });
  }

  get vendedoresActivos(): number {
    return this.vendedores.filter((vendedor) => Boolean(vendedor.activo)).length;
  }
}

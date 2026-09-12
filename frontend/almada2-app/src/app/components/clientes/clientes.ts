import { CommonModule } from '@angular/common';
import { Component, ChangeDetectorRef, EventEmitter, OnInit, Output, inject } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { ApiService } from '../../services/api.service';

@Component({
  selector: 'app-clientes',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './clientes.html',
  styleUrl: './clientes.css'
})
export class ClientesComponent implements OnInit {
  private api = inject(ApiService);
  private cdr = inject(ChangeDetectorRef);

  @Output() verCuenta = new EventEmitter<any>();
  @Output() clientesActualizados = new EventEmitter<void>();

  clientes: any[] = [];
  error = '';
  cargando = false;

  mostrarFormularioCliente = false;
  modoEditarCliente = false;
  clienteEditandoId: number | null = null;

  clienteForm: any = {
    numero_cliente: '',
    nombre: '',
    direccion: '',
    localidad: '',
    telefono: '',
    email: '',
    observaciones: '',
    saldo_actual: 0
  };

  ngOnInit(): void {
    this.cargarClientes();
  }

  cargarClientes(): void {
    this.cargando = true;
    this.error = '';

    this.api.obtenerClientes().subscribe({
      next: (respuesta) => {
        this.clientes = respuesta || [];
        this.cargando = false;
        this.cdr.detectChanges();
      },
      error: () => {
        this.error = 'No se pudieron cargar los clientes.';
        this.cargando = false;
        this.cdr.detectChanges();
      }
    });
  }

  abrirFormularioCliente(): void {
    this.mostrarFormularioCliente = true;
    this.modoEditarCliente = false;
    this.clienteEditandoId = null;

    this.clienteForm = {
      numero_cliente: '',
      nombre: '',
      direccion: '',
      localidad: '',
      telefono: '',
      email: '',
      observaciones: '',
      saldo_actual: 0
    };

    this.cdr.detectChanges();
  }

  cerrarFormularioCliente(): void {
    this.mostrarFormularioCliente = false;
    this.modoEditarCliente = false;
    this.clienteEditandoId = null;
    this.cdr.detectChanges();
  }

  guardarCliente(): void {
    if (!String(this.clienteForm.nombre || '').trim()) {
      alert('El nombre del cliente es obligatorio.');
      return;
    }

    if (this.modoEditarCliente && this.clienteEditandoId) {
      this.api.actualizarCliente(this.clienteEditandoId, this.clienteForm).subscribe({
        next: () => {
          alert('Cliente actualizado correctamente.');
          this.cerrarFormularioCliente();
          this.cargarClientes();
          this.clientesActualizados.emit();
        },
        error: (error) => {
          this.error = error.error?.mensaje || 'No se pudo actualizar el cliente.';
          this.cdr.detectChanges();
        }
      });

      return;
    }

    this.api.crearCliente(this.clienteForm).subscribe({
      next: () => {
        alert('Cliente guardado correctamente.');
        this.cerrarFormularioCliente();
        this.cargarClientes();
        this.clientesActualizados.emit();
      },
      error: (error) => {
        this.error = error.error?.mensaje || 'No se pudo guardar el cliente.';
        this.cdr.detectChanges();
      }
    });
  }

  editarCliente(cliente: any): void {
    this.mostrarFormularioCliente = true;
    this.modoEditarCliente = true;
    this.clienteEditandoId = cliente.id;

    this.clienteForm = {
      numero_cliente: cliente.numero_cliente || '',
      nombre: cliente.nombre || '',
      direccion: cliente.direccion || '',
      localidad: cliente.localidad || '',
      telefono: cliente.telefono || '',
      email: cliente.email || '',
      observaciones: cliente.observaciones || '',
      saldo_actual: cliente.saldo_actual || 0
    };

    this.cdr.detectChanges();
  }

  eliminarCliente(id: number): void {
    const confirmar = confirm('¿Eliminar este cliente?');

    if (!confirmar) {
      return;
    }

    this.api.eliminarCliente(id).subscribe({
      next: () => {
        alert('Cliente eliminado correctamente.');
        this.cargarClientes();
        this.clientesActualizados.emit();
      },
      error: (error) => {
        this.error = error.error?.mensaje || 'No se pudo eliminar el cliente.';
        this.cdr.detectChanges();
      }
    });
  }

  abrirCuentaCliente(cliente: any): void {
    this.verCuenta.emit(cliente);
  }

  formatearMoneda(valor: any): string {
    const numero = Number(valor || 0);

    return numero.toLocaleString('es-AR', {
      minimumFractionDigits: 0,
      maximumFractionDigits: 0
    });
  }
}

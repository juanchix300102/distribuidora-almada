import { CommonModule } from '@angular/common';
import { Component, ChangeDetectorRef, EventEmitter, Input, OnChanges, OnInit, Output, SimpleChanges, inject } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { ApiService } from '../../services/api.service';

@Component({
  selector: 'app-cuentas-corrientes',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './cuentas-corrientes.html',
  styleUrl: './cuentas-corrientes.css'
})
export class CuentasCorrientesComponent implements OnInit, OnChanges {
  private api = inject(ApiService);
  private cdr = inject(ChangeDetectorRef);

  @Input() clienteInicial: any = null;
  @Output() resumenActualizado = new EventEmitter<void>();

  clientes: any[] = [];

  busquedaCuenta = '';
  filtroCuenta = 'todos';

  clienteCuentaSeleccionado: any = null;
  cuentaCliente: any = null;
  movimientosCuenta: any[] = [];

  cargandoClientes = false;
  cargandoCuenta = false;
  error = '';

  movimientoCuentaForm: any = {
    tipo: 'Venta',
    descripcion: '',
    monto: 0,
    comprobante: ''
  };

  pagoClienteForm: any = {
    monto: 0,
    medio_pago: 'Efectivo',
    comprobante: '',
    observaciones: ''
  };

  ngOnInit(): void {
    this.cargarClientes();

    if (this.clienteInicial) {
      this.abrirCuentaCorriente(this.clienteInicial);
    }
  }

  ngOnChanges(changes: SimpleChanges): void {
    if (changes['clienteInicial'] && changes['clienteInicial'].currentValue) {
      this.abrirCuentaCorriente(changes['clienteInicial'].currentValue);
    }
  }

  cargarClientes(): void {
    this.cargandoClientes = true;
    this.error = '';

    this.api.obtenerClientes().subscribe({
      next: (respuesta) => {
        this.clientes = respuesta || [];
        this.cargandoClientes = false;
        this.cdr.detectChanges();
      },
      error: () => {
        this.error = 'No se pudieron cargar los clientes.';
        this.cargandoClientes = false;
        this.cdr.detectChanges();
      }
    });
  }

  clientesCuentaFiltrados(): any[] {
    const texto = this.busquedaCuenta.toLowerCase().trim();

    return this.clientes.filter(cliente => {
      const coincideBusqueda =
        !texto ||
        String(cliente.nombre || '').toLowerCase().includes(texto) ||
        String(cliente.numero_cliente || '').toLowerCase().includes(texto) ||
        String(cliente.localidad || '').toLowerCase().includes(texto) ||
        String(cliente.telefono || '').toLowerCase().includes(texto) ||
        String(cliente.usuario || '').toLowerCase().includes(texto);

      const saldo = Number(cliente.saldo_actual || 0);

      const coincideFiltro =
        this.filtroCuenta === 'todos' ||
        (this.filtroCuenta === 'con-deuda' && saldo > 0) ||
        (this.filtroCuenta === 'sin-deuda' && saldo <= 0);

      return coincideBusqueda && coincideFiltro;
    });
  }

  totalClientesConDeuda(): number {
    return this.clientes.filter(cliente => Number(cliente.saldo_actual || 0) > 0).length;
  }

  totalSaldoClientes(): number {
    return this.clientes.reduce((total, cliente) => {
      return total + Number(cliente.saldo_actual || 0);
    }, 0);
  }

  abrirCuentaCorriente(cliente: any): void {
    this.clienteCuentaSeleccionado = cliente;

    this.movimientoCuentaForm = {
      tipo: 'Venta',
      descripcion: '',
      monto: 0,
      comprobante: ''
    };

    this.pagoClienteForm = {
      monto: 0,
      medio_pago: 'Efectivo',
      comprobante: '',
      observaciones: ''
    };

    this.cargarCuentaCorriente();
  }

  volverALista(): void {
    this.clienteCuentaSeleccionado = null;
    this.cuentaCliente = null;
    this.movimientosCuenta = [];
    this.cargarClientes();
    this.cdr.detectChanges();
  }

  cargarCuentaCorriente(): void {
    if (!this.clienteCuentaSeleccionado?.id) {
      return;
    }

    this.cargandoCuenta = true;
    this.error = '';

    this.api.obtenerCuentaCorriente(this.clienteCuentaSeleccionado.id).subscribe({
      next: (respuesta) => {
        this.cuentaCliente = respuesta?.cliente || respuesta || this.clienteCuentaSeleccionado;

        if (respuesta?.saldo_actual !== undefined) {
          this.cuentaCliente.saldo_actual = respuesta.saldo_actual;
        }

        this.movimientosCuenta =
          respuesta?.movimientos ||
          respuesta?.cuenta_corriente ||
          [];

        this.cargandoCuenta = false;
        this.cdr.detectChanges();
      },
      error: () => {
        this.error = 'No se pudo cargar la cuenta corriente.';
        this.cargandoCuenta = false;
        this.cdr.detectChanges();
      }
    });
  }

  agregarMovimientoCuenta(): void {
    if (!this.clienteCuentaSeleccionado?.id) {
      alert('No hay cliente seleccionado.');
      return;
    }

    if (!String(this.movimientoCuentaForm.descripcion || '').trim()) {
      alert('La descripción es obligatoria.');
      return;
    }

    if (Number(this.movimientoCuentaForm.monto || 0) <= 0) {
      alert('El monto debe ser mayor a cero.');
      return;
    }

    this.api.agregarMovimientoCuenta(
      this.clienteCuentaSeleccionado.id,
      this.movimientoCuentaForm
    ).subscribe({
      next: () => {
        alert('Movimiento cargado correctamente.');

        this.movimientoCuentaForm = {
          tipo: 'Venta',
          descripcion: '',
          monto: 0,
          comprobante: ''
        };

        this.cargarCuentaCorriente();
        this.cargarClientes();
        this.resumenActualizado.emit();
      },
      error: (error) => {
        alert(error.error?.mensaje || 'No se pudo cargar el movimiento.');
        this.cdr.detectChanges();
      }
    });
  }

  registrarPagoCliente(): void {
    if (!this.clienteCuentaSeleccionado?.id) {
      alert('No hay cliente seleccionado.');
      return;
    }

    if (Number(this.pagoClienteForm.monto || 0) <= 0) {
      alert('El monto del pago debe ser mayor a cero.');
      return;
    }

    this.api.registrarPagoCliente(
      this.clienteCuentaSeleccionado.id,
      this.pagoClienteForm
    ).subscribe({
      next: () => {
        alert('Pago registrado correctamente.');

        this.pagoClienteForm = {
          monto: 0,
          medio_pago: 'Efectivo',
          comprobante: '',
          observaciones: ''
        };

        this.cargarCuentaCorriente();
        this.cargarClientes();
        this.resumenActualizado.emit();
      },
      error: (error) => {
        alert(error.error?.mensaje || 'No se pudo registrar el pago.');
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
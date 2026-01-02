/**
 * Payment Service - Lógica de negocio para procesamiento de pagos
 */
import {
  Injectable,
  NotFoundException,
  BadRequestException,
} from '@nestjs/common';
import { InjectRepository } from '@nestjs/typeorm';
import { Repository } from 'typeorm';
import { Payment } from './entities/payment.entity';
import { CreatePaymentDto } from './dto/create-payment.dto';
import { PaymentResponseDto, PaymentStatsDto } from './dto/payment-response.dto';
import { PaymentProvider, PaymentStatus } from './interfaces/payment-provider.interface';
import { MockAdapter } from './adapters/mock.adapter';

@Injectable()
export class PaymentService {
  private providers: Map<string, PaymentProvider> = new Map();

  constructor(
    @InjectRepository(Payment)
    private paymentRepository: Repository<Payment>,
    private mockAdapter: MockAdapter,
  ) {
    // Registrar providers disponibles
    this.registerProvider(mockAdapter);
  }

  /**
   * Registrar un proveedor de pago en el registry
   */
  private registerProvider(provider: PaymentProvider): void {
    this.providers.set(provider.name, provider);
    console.log(`✅ Provider registrado: ${provider.name}`);
  }

  /**
   * Obtener un proveedor por nombre
   */
  private getProvider(name: string): PaymentProvider {
    const provider = this.providers.get(name);
    if (!provider) {
      throw new BadRequestException(
        `Proveedor '${name}' no disponible. Providers registrados: ${Array.from(this.providers.keys()).join(', ')}`,
      );
    }
    return provider;
  }

  /**
   * Crear y procesar un pago
   */
  async createPayment(dto: CreatePaymentDto): Promise<PaymentResponseDto> {
    // Obtener proveedor (por defecto 'mock')
    const providerName = dto.provider || 'mock';
    const provider = this.getProvider(providerName);

    // Procesar pago con el proveedor
    const result = await provider.processPayment({
      reservaId: dto.reservaId,
      usuarioId: dto.usuarioId,
      amount: dto.amount,
      currency: dto.currency || 'USD',
      description: dto.description,
      metadata: dto.metadata,
    });

    // Guardar en base de datos
    const payment = this.paymentRepository.create({
      reservaId: dto.reservaId,
      usuarioId: dto.usuarioId,
      amount: dto.amount,
      currency: dto.currency || 'USD',
      status: result.status,
      providerName: provider.name,
      transactionId: result.transactionId,
      description: dto.description,
      extraMetadata: {
        ...dto.metadata,
        providerData: result.providerData,
        message: result.message,
      },
    });

    const saved = await this.paymentRepository.save(payment);
    return this.toResponseDto(saved);
  }

  /**
   * Obtener pago por ID
   */
  async getPaymentById(id: number): Promise<PaymentResponseDto> {
    const payment = await this.paymentRepository.findOne({ where: { id } });
    if (!payment) {
      throw new NotFoundException(`Pago con ID ${id} no encontrado`);
    }
    return this.toResponseDto(payment);
  }

  /**
   * Obtener pago por transaction ID
   */
  async getPaymentByTransactionId(transactionId: string): Promise<PaymentResponseDto> {
    const payment = await this.paymentRepository.findOne({
      where: { transactionId },
    });
    if (!payment) {
      throw new NotFoundException(
        `Pago con transaction_id '${transactionId}' no encontrado`,
      );
    }
    return this.toResponseDto(payment);
  }

  /**
   * Obtener pagos por reserva
   */
  async getPaymentsByReserva(reservaId: number): Promise<PaymentResponseDto[]> {
    const payments = await this.paymentRepository.find({
      where: { reservaId },
      order: { createdAt: 'DESC' },
    });
    return payments.map((p) => this.toResponseDto(p));
  }

  /**
   * Obtener pagos por usuario
   */
  async getPaymentsByUsuario(usuarioId: number): Promise<PaymentResponseDto[]> {
    const payments = await this.paymentRepository.find({
      where: { usuarioId },
      order: { createdAt: 'DESC' },
    });
    return payments.map((p) => this.toResponseDto(p));
  }

  /**
   * Obtener estadísticas de pagos
   */
  async getPaymentStats(): Promise<PaymentStatsDto> {
    const [payments, count] = await this.paymentRepository.findAndCount();

    const completed = payments.filter((p) => p.status === PaymentStatus.COMPLETED);
    const pending = payments.filter((p) => p.status === PaymentStatus.PENDING);
    const failed = payments.filter((p) => p.status === PaymentStatus.FAILED);
    const refunded = payments.filter((p) => p.status === PaymentStatus.REFUNDED);

    const totalAmount = completed.reduce(
      (sum, p) => sum + parseFloat(p.amount.toString()),
      0,
    );

    return {
      total_payments: count,
      completed_payments: completed.length,
      pending_payments: pending.length,
      failed_payments: failed.length,
      refunded_payments: refunded.length,
      total_amount: parseFloat(totalAmount.toFixed(2)),
      currency: 'USD',
    };
  }

  /**
   * Convertir entidad a DTO de respuesta
   */
  private toResponseDto(payment: Payment): PaymentResponseDto {
    return {
      id: payment.id,
      reservaId: payment.reservaId,
      usuarioId: payment.usuarioId,
      amount: parseFloat(payment.amount.toString()),
      currency: payment.currency,
      status: payment.status,
      providerName: payment.providerName,
      transactionId: payment.transactionId,
      description: payment.description,
      extraMetadata: payment.extraMetadata,
      createdAt: payment.createdAt,
      updatedAt: payment.updatedAt,
    };
  }
}

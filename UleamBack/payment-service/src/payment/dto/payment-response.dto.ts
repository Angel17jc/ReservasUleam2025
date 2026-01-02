/**
 * Payment Response DTO - Formato de respuesta de pagos
 */
import { ApiProperty } from '@nestjs/swagger';
import { PaymentStatus } from '../interfaces/payment-provider.interface';

export class PaymentResponseDto {
  @ApiProperty({ example: 1 })
  id: number;

  @ApiProperty({ example: 123 })
  reservaId: number;

  @ApiProperty({ example: 456 })
  usuarioId: number;

  @ApiProperty({ example: 50.99 })
  amount: number;

  @ApiProperty({ example: 'USD' })
  currency: string;

  @ApiProperty({ enum: PaymentStatus, example: PaymentStatus.COMPLETED })
  status: PaymentStatus;

  @ApiProperty({ example: 'mock' })
  providerName: string;

  @ApiProperty({ example: 'mock_txn_1234567890abcdef' })
  transactionId: string;

  @ApiProperty({ example: 'Pago por reserva de cancha #123', required: false })
  description?: string;

  @ApiProperty({
    example: { source: 'web', campaign: 'summer2025' },
    required: false,
  })
  extraMetadata?: Record<string, any>;

  @ApiProperty({ example: '2025-01-01T12:00:00Z' })
  createdAt: Date;

  @ApiProperty({ example: '2025-01-01T12:00:00Z' })
  updatedAt: Date;
}

export class PaymentStatsDto {
  @ApiProperty({ example: 150 })
  total_payments: number;

  @ApiProperty({ example: 120 })
  completed_payments: number;

  @ApiProperty({ example: 10 })
  pending_payments: number;

  @ApiProperty({ example: 5 })
  failed_payments: number;

  @ApiProperty({ example: 15 })
  refunded_payments: number;

  @ApiProperty({ example: 5250.50 })
  total_amount: number;

  @ApiProperty({ example: 'USD' })
  currency: string;
}

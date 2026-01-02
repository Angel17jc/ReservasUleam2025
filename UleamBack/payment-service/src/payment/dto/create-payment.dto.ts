/**
 * Create Payment DTO - Validación para crear pagos
 */
import { ApiProperty } from '@nestjs/swagger';
import {
  IsInt,
  IsNumber,
  IsPositive,
  IsString,
  IsOptional,
  Length,
  IsObject,
} from 'class-validator';

export class CreatePaymentDto {
  @ApiProperty({
    description: 'ID de la reserva asociada',
    example: 123,
  })
  @IsInt()
  @IsPositive()
  reservaId: number;

  @ApiProperty({
    description: 'ID del usuario que realiza el pago',
    example: 456,
  })
  @IsInt()
  @IsPositive()
  usuarioId: number;

  @ApiProperty({
    description: 'Monto del pago',
    example: 50.99,
  })
  @IsNumber()
  @IsPositive()
  amount: number;

  @ApiProperty({
    description: 'Código de moneda ISO 4217',
    example: 'USD',
    default: 'USD',
  })
  @IsString()
  @Length(3, 3)
  @IsOptional()
  currency?: string;

  @ApiProperty({
    description: 'Descripción del pago',
    example: 'Pago por reserva de cancha #123',
    required: false,
  })
  @IsString()
  @IsOptional()
  description?: string;

  @ApiProperty({
    description: 'Metadatos adicionales en formato JSON',
    example: { source: 'web', campaign: 'summer2025' },
    required: false,
  })
  @IsObject()
  @IsOptional()
  metadata?: Record<string, any>;

  @ApiProperty({
    description: 'Proveedor de pago a utilizar (mock, stripe, mercadopago)',
    example: 'mock',
    default: 'mock',
  })
  @IsString()
  @IsOptional()
  provider?: string;
}

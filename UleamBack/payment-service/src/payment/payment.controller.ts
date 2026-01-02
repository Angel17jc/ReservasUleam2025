/**
 * Payment Controller - Endpoints REST para gestión de pagos
 */
import {
  Controller,
  Post,
  Get,
  Body,
  Param,
  ParseIntPipe,
} from '@nestjs/common';
import { ApiTags, ApiOperation, ApiResponse } from '@nestjs/swagger';
import { PaymentService } from './payment.service';
import { CreatePaymentDto } from './dto/create-payment.dto';
import {
  PaymentResponseDto,
  PaymentStatsDto,
} from './dto/payment-response.dto';

@ApiTags('payments')
@Controller('payments')
export class PaymentController {
  constructor(private readonly paymentService: PaymentService) {}

  @Post()
  @ApiOperation({ summary: 'Crear y procesar un nuevo pago' })
  @ApiResponse({
    status: 201,
    description: 'Pago creado y procesado exitosamente',
    type: PaymentResponseDto,
  })
  @ApiResponse({ status: 400, description: 'Datos inválidos' })
  async createPayment(
    @Body() dto: CreatePaymentDto,
  ): Promise<PaymentResponseDto> {
    return this.paymentService.createPayment(dto);
  }

  @Get(':id')
  @ApiOperation({ summary: 'Obtener pago por ID' })
  @ApiResponse({
    status: 200,
    description: 'Pago encontrado',
    type: PaymentResponseDto,
  })
  @ApiResponse({ status: 404, description: 'Pago no encontrado' })
  async getPaymentById(
    @Param('id', ParseIntPipe) id: number,
  ): Promise<PaymentResponseDto> {
    return this.paymentService.getPaymentById(id);
  }

  @Get('transaction/:transactionId')
  @ApiOperation({ summary: 'Obtener pago por transaction ID' })
  @ApiResponse({
    status: 200,
    description: 'Pago encontrado',
    type: PaymentResponseDto,
  })
  @ApiResponse({ status: 404, description: 'Pago no encontrado' })
  async getPaymentByTransactionId(
    @Param('transactionId') transactionId: string,
  ): Promise<PaymentResponseDto> {
    return this.paymentService.getPaymentByTransactionId(transactionId);
  }

  @Get('reserva/:reservaId')
  @ApiOperation({ summary: 'Obtener todos los pagos de una reserva' })
  @ApiResponse({
    status: 200,
    description: 'Lista de pagos',
    type: [PaymentResponseDto],
  })
  async getPaymentsByReserva(
    @Param('reservaId', ParseIntPipe) reservaId: number,
  ): Promise<PaymentResponseDto[]> {
    return this.paymentService.getPaymentsByReserva(reservaId);
  }

  @Get('usuario/:usuarioId')
  @ApiOperation({ summary: 'Obtener todos los pagos de un usuario' })
  @ApiResponse({
    status: 200,
    description: 'Lista de pagos',
    type: [PaymentResponseDto],
  })
  async getPaymentsByUsuario(
    @Param('usuarioId', ParseIntPipe) usuarioId: number,
  ): Promise<PaymentResponseDto[]> {
    return this.paymentService.getPaymentsByUsuario(usuarioId);
  }

  @Get('stats/summary')
  @ApiOperation({ summary: 'Obtener estadísticas de pagos' })
  @ApiResponse({
    status: 200,
    description: 'Estadísticas de pagos',
    type: PaymentStatsDto,
  })
  async getPaymentStats(): Promise<PaymentStatsDto> {
    return this.paymentService.getPaymentStats();
  }
}

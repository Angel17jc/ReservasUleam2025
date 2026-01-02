/**
 * Mock Adapter - Implementación simulada de proveedor de pago
 * 
 * Este adaptador es OBLIGATORIO para desarrollo y testing.
 * NO realiza cargos reales, solo simula transacciones exitosas.
 * 
 * Características:
 * - Genera transaction_id único con formato: mock_txn_{uuid sin guiones}
 * - Siempre retorna estado "completed"
 * - Retraso simulado de 500ms para emular latencia de red
 * - Útil para testing sin necesidad de credenciales reales
 */
import { Injectable } from '@nestjs/common';
import { v4 as uuidv4 } from 'uuid';
import {
  PaymentProvider,
  PaymentData,
  PaymentResult,
  PaymentStatus,
} from '../interfaces/payment-provider.interface';

@Injectable()
export class MockAdapter extends PaymentProvider {
  readonly name = 'mock';

  /**
   * Procesar un pago simulado
   * - Genera transaction_id único
   * - Siempre retorna "completed"
   * - Simula 500ms de latencia de red
   */
  async processPayment(data: PaymentData): Promise<PaymentResult> {
    // Simular latencia de red
    await this.delay(500);

    // Generar transaction ID único: mock_txn_{uuid sin guiones}
    const uuid = uuidv4().replace(/-/g, '');
    const transactionId = `mock_txn_${uuid}`;

    return {
      transactionId,
      status: PaymentStatus.COMPLETED,
      message: `Pago simulado exitoso por ${data.amount} ${data.currency}`,
      providerData: {
        mock: true,
        processedAt: new Date().toISOString(),
        reservaId: data.reservaId,
        usuarioId: data.usuarioId,
      },
    };
  }

  /**
   * Verificar estado de pago simulado
   * - Siempre retorna "completed" para cualquier transaction_id que comience con "mock_txn_"
   */
  async verifyPayment(transactionId: string): Promise<PaymentResult> {
    await this.delay(200);

    if (!transactionId.startsWith('mock_txn_')) {
      return {
        transactionId,
        status: PaymentStatus.FAILED,
        message: 'Transaction ID no pertenece a MockAdapter',
      };
    }

    return {
      transactionId,
      status: PaymentStatus.COMPLETED,
      message: 'Pago simulado verificado',
      providerData: {
        mock: true,
        verifiedAt: new Date().toISOString(),
      },
    };
  }

  /**
   * Reembolsar un pago simulado
   * - Siempre retorna "refunded" exitosamente
   */
  async refundPayment(transactionId: string): Promise<PaymentResult> {
    await this.delay(300);

    if (!transactionId.startsWith('mock_txn_')) {
      return {
        transactionId,
        status: PaymentStatus.FAILED,
        message: 'Transaction ID no pertenece a MockAdapter',
      };
    }

    return {
      transactionId,
      status: PaymentStatus.REFUNDED,
      message: 'Reembolso simulado exitoso',
      providerData: {
        mock: true,
        refundedAt: new Date().toISOString(),
      },
    };
  }

  /**
   * Simular latencia de red
   */
  private delay(ms: number): Promise<void> {
    return new Promise((resolve) => setTimeout(resolve, ms));
  }
}

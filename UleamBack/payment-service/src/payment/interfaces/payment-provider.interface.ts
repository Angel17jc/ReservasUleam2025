/**
 * Payment Provider Interface - Patrón Adapter
 * 
 * Esta interfaz abstracta define el contrato que deben cumplir todos
 * los proveedores de pago (MockAdapter, StripeAdapter, MercadoPagoAdapter, etc.)
 * 
 * Ventajas del patrón Adapter:
 * - Desacopla la lógica de negocio de las implementaciones específicas
 * - Facilita agregar nuevos proveedores sin modificar código existente
 * - Permite simular pagos en desarrollo con MockAdapter
 */

export enum PaymentStatus {
  PENDING = 'pending',
  COMPLETED = 'completed',
  FAILED = 'failed',
  REFUNDED = 'refunded',
}

export interface PaymentData {
  /** ID de la reserva asociada */
  reservaId: number;
  /** ID del usuario que realiza el pago */
  usuarioId: number;
  /** Monto en la moneda configurada */
  amount: number;
  /** Código de moneda ISO 4217 (USD, EUR, etc.) */
  currency: string;
  /** Descripción del pago */
  description?: string;
  /** Metadatos adicionales en formato JSON */
  metadata?: Record<string, any>;
}

export interface PaymentResult {
  /** ID de la transacción en el sistema del proveedor */
  transactionId: string;
  /** Estado del pago */
  status: PaymentStatus;
  /** Mensaje descriptivo del resultado */
  message?: string;
  /** Datos adicionales del proveedor */
  providerData?: Record<string, any>;
}

export abstract class PaymentProvider {
  /**
   * Nombre del proveedor (mock, stripe, mercadopago, etc.)
   */
  abstract readonly name: string;

  /**
   * Procesar un pago
   * @param data - Datos del pago a procesar
   * @returns Resultado del procesamiento
   */
  abstract processPayment(data: PaymentData): Promise<PaymentResult>;

  /**
   * Verificar el estado de una transacción existente
   * @param transactionId - ID de la transacción en el proveedor
   * @returns Estado actualizado de la transacción
   */
  abstract verifyPayment(transactionId: string): Promise<PaymentResult>;

  /**
   * Reembolsar un pago
   * @param transactionId - ID de la transacción a reembolsar
   * @returns Resultado del reembolso
   */
  abstract refundPayment(transactionId: string): Promise<PaymentResult>;
}

import { paymentClient, isPaymentApiConfigured } from './paymentClient';

export type PaymentCreateInput = {
  reserva_id: number;
  amount?: number;
  currency?: string;
  provider?: 'mock' | 'stripe' | 'mercadopago';
  metadata?: Record<string, any>;
};

type BackendPayment = {
  id: number;
  external_payment_id: string;
  reserva_id: number;
  usuario_id: number;
  provider_name: string;
  amount: number;
  currency: string;
  status: string;
  metadata_json: Record<string, any>;
  error_message?: string | null;
  creado_en: string;
  actualizado_en?: string | null;
};

type PaymentListResponse = {
  total: number;
  page: number;
  page_size: number;
  payments: BackendPayment[];
};

export type Payment = {
  id: number;
  externalPaymentId: string;
  reservaId: number;
  usuarioId: number;
  provider: string;
  amount: number;
  currency: string;
  status: string;
  metadata: Record<string, any>;
  errorMessage?: string | null;
  createdAt: string;
  updatedAt?: string | null;
};

export type PaymentListResult = {
  items: Payment[];
  total: number;
  page: number;
  pageSize: number;
};

function ensureConfigured() {
  if (!isPaymentApiConfigured()) {
    throw new Error('Configura VITE_PAYMENT_BASE_URL para consumir el servicio de pagos');
  }
}

function mapPayment(p: BackendPayment): Payment {
  return {
    id: p.id,
    externalPaymentId: p.external_payment_id,
    reservaId: p.reserva_id,
    usuarioId: p.usuario_id,
    provider: p.provider_name,
    amount: Number(p.amount),
    currency: p.currency,
    status: p.status,
    metadata: p.metadata_json ?? {},
    errorMessage: p.error_message,
    createdAt: p.creado_en,
    updatedAt: p.actualizado_en,
  };
}

export const paymentsApi = {
  async create(payload: PaymentCreateInput): Promise<Payment> {
    ensureConfigured();
    const created = await paymentClient.post<BackendPayment>('/payments', {
      amount: 20,
      currency: 'USD',
      provider: 'stripe',
      ...payload,
    });
    return mapPayment(created);
  },

  async list(params?: { reservaId?: number; provider?: string; status?: string; page?: number; perPage?: number }): Promise<PaymentListResult> {
    ensureConfigured();
    const response = await paymentClient.get<PaymentListResponse>('/payments', {
      query: {
        reserva_id: params?.reservaId,
        provider: params?.provider,
        status: params?.status,
        page: params?.page ?? 1,
        per_page: params?.perPage ?? 10,
      },
    });

    const items = response.payments.map(mapPayment);
    return {
      items,
      total: response.total,
      page: response.page,
      pageSize: response.page_size,
    };
  },

  async detail(id: number): Promise<Payment> {
    ensureConfigured();
    const payment = await paymentClient.get<BackendPayment>(`/payments/${id}`);
    return mapPayment(payment);
  },
};

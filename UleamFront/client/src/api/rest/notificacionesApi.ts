import { isRestConfigured, restClient } from './client';

export type Notificacion = {
  id: number;
  usuario_id: number;
  titulo: string;
  mensaje: string;
  leida: boolean;
  reserva_id?: number | null;
  espacio_id?: number | null;
  metadata?: Record<string, any>;
  leida_at?: string | null;
  creado_en?: string;
};

export const notificacionesApi = {
  async list(usuario_id: number, limit = 100): Promise<Notificacion[]> {
    if (!isRestConfigured()) throw new Error('Configura VITE_REST_BASE_URL');
    return restClient.get<Notificacion[]>('/notificaciones', { query: { usuario_id, limit } });
  },
  async create(payload: Omit<Notificacion, 'id' | 'leida' | 'creado_en' | 'leida_at'>) {
    if (!isRestConfigured()) throw new Error('Configura VITE_REST_BASE_URL');
    return restClient.post<{ success: boolean; id: number }>('/notificaciones', payload);
  },
};

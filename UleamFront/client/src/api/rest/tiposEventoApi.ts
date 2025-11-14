import { isRestConfigured, restClient } from './client';

export type TipoEvento = {
  id: number;
  nombre: string;
  descripcion?: string | null;
  requiere_aprobacion?: boolean;
  color_hex?: string | null;
};

export const tiposEventoApi = {
  async list(): Promise<TipoEvento[]> {
    if (!isRestConfigured()) throw new Error('Configura VITE_REST_BASE_URL para consumir /api/tipos-evento');
    return restClient.get<TipoEvento[]>('/tipos-evento');
  },
  async create(payload: Omit<TipoEvento, 'id'>): Promise<TipoEvento> {
    if (!isRestConfigured()) throw new Error('Configura VITE_REST_BASE_URL para consumir /api/tipos-evento');
    return restClient.post<TipoEvento>('/tipos-evento', payload);
  },
  async update(id: number, payload: Partial<Omit<TipoEvento, 'id'>>): Promise<TipoEvento> {
    if (!isRestConfigured()) throw new Error('Configura VITE_REST_BASE_URL para consumir /api/tipos-evento');
    return restClient.put<TipoEvento>(`/tipos-evento/${id}`, payload);
  },
  async remove(id: number): Promise<void> {
    if (!isRestConfigured()) throw new Error('Configura VITE_REST_BASE_URL para consumir /api/tipos-evento');
    await restClient.delete(`/tipos-evento/${id}`);
  },
};

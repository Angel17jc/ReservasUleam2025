import { isRestConfigured, restClient } from './client';

export type Categoria = {
  id: number;
  nombre: string;
  descripcion?: string | null;
  requiere_aprobacion?: boolean;
  capacidad_maxima?: number | null;
};

export const categoriasApi = {
  async list(): Promise<Categoria[]> {
    if (!isRestConfigured()) {
      throw new Error('Configura VITE_REST_BASE_URL para consumir /api/categorias-espacio');
    }
    return restClient.get<Categoria[]>('/categorias-espacio');
  },
  async create(payload: Omit<Categoria, 'id'>): Promise<Categoria> {
    if (!isRestConfigured()) {
      throw new Error('Configura VITE_REST_BASE_URL para consumir /api/categorias-espacio');
    }
    return restClient.post<Categoria>('/categorias-espacio', payload);
  },
  async update(id: number, payload: Partial<Omit<Categoria, 'id'>>): Promise<Categoria> {
    if (!isRestConfigured()) {
      throw new Error('Configura VITE_REST_BASE_URL para consumir /api/categorias-espacio');
    }
    return restClient.put<Categoria>(`/categorias-espacio/${id}`, payload);
  },
  async remove(id: number): Promise<void> {
    if (!isRestConfigured()) {
      throw new Error('Configura VITE_REST_BASE_URL para consumir /api/categorias-espacio');
    }
    await restClient.delete(`/categorias-espacio/${id}`);
  },
};

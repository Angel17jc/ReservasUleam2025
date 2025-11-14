import { PagedResult, isRestConfigured, restClient } from './client';

export type Espacio = {
  id: string;
  nombre: string;
  codigo: string;
  categoriaId: number;
  capacidadMaxima: number;
  imagenUrl?: string | null;
  estado?: 'activo' | 'inactivo' | string;
};

export type EspacioInput = {
  codigo: string;
  nombre: string;
  categoria_id: number;
  capacidad_maxima: number;
  imagen_url?: string | null;
  estado?: string;
};

type BackendEspacio = {
  id: number;
  codigo: string;
  nombre: string;
  categoria_id: number;
  capacidad_maxima: number;
  imagen_url?: string | null;
  estado?: string;
};

function mapEspacio(e: BackendEspacio): Espacio {
  return {
    id: String(e.id),
    codigo: e.codigo,
    nombre: e.nombre,
    categoriaId: e.categoria_id,
    capacidadMaxima: e.capacidad_maxima,
    imagenUrl: e.imagen_url,
    estado: e.estado,
  };
}

export const espaciosApi = {
  async list(params?: { categoria_id?: number; estado?: string }): Promise<PagedResult<Espacio>> {
    if (!isRestConfigured()) {
      throw new Error('Configura VITE_REST_BASE_URL para consumir /api/espacios');
    }

    const items = await restClient.get<BackendEspacio[]>('/espacios', { query: params });
    const mapped = items.map(mapEspacio);
    return {
      items: mapped,
      total: mapped.length,
      page: 1,
      pageSize: mapped.length,
    };
  },
  async detail(id: string): Promise<Espacio> {
    if (!isRestConfigured()) {
      throw new Error('Configura VITE_REST_BASE_URL para consumir /api/espacios/{id}');
    }
    const data = await restClient.get<BackendEspacio>(`/espacios/${id}`);
    return mapEspacio(data);
  },
  async create(payload: EspacioInput): Promise<Espacio> {
    if (!isRestConfigured()) {
      throw new Error('Configura VITE_REST_BASE_URL para consumir /api/espacios');
    }
    const created = await restClient.post<BackendEspacio>('/espacios', payload);
    return mapEspacio(created);
  },
  async update(id: string, payload: Partial<EspacioInput>): Promise<Espacio> {
    if (!isRestConfigured()) {
      throw new Error('Configura VITE_REST_BASE_URL para consumir /api/espacios');
    }
    const updated = await restClient.put<BackendEspacio>(`/espacios/${id}`, payload);
    return mapEspacio(updated);
  },
  async remove(id: string): Promise<void> {
    if (!isRestConfigured()) return;
    await restClient.delete(`/espacios/${id}`);
  },
};

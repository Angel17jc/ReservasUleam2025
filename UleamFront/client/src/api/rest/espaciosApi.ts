import { PagedResult, isRestConfigured, restClient } from './client';

export type Espacio = {
  id: string;
  nombre: string;
  codigo: string;
  categoria: string;
  capacidad: number;
  ubicacion?: string;
  estado?: 'activo' | 'inactivo';
};

export type EspacioInput = Omit<Espacio, 'id'>;

const mockEspacios: Espacio[] = [
  { id: '1', nombre: 'Auditorio Principal', codigo: 'AUD-001', categoria: 'Auditorio', capacidad: 300, ubicacion: 'Edificio A', estado: 'activo' },
  { id: '2', nombre: 'Laboratorio de Cómputo 1', codigo: 'LAB-001', categoria: 'Laboratorio', capacidad: 30, ubicacion: 'Edificio B', estado: 'activo' },
  { id: '3', nombre: 'Cancha de Fútbol', codigo: 'DEP-001', categoria: 'Deportivo', capacidad: 50, ubicacion: 'Área Deportiva', estado: 'activo' },
];

export const espaciosApi = {
  async list(params?: { page?: number; pageSize?: number; categoria?: string; search?: string }): Promise<PagedResult<Espacio>> {
    if (!isRestConfigured()) {
      return {
        items: mockEspacios,
        total: mockEspacios.length,
        page: params?.page ?? 1,
        pageSize: params?.pageSize ?? mockEspacios.length,
      };
    }

    return restClient.get<PagedResult<Espacio>>('/espacios', { query: params });
  },
  async detail(id: string): Promise<Espacio> {
    if (!isRestConfigured()) {
      return mockEspacios.find((e) => e.id === id) ?? mockEspacios[0];
    }

    return restClient.get<Espacio>(`/espacios/${id}`);
  },
  async create(payload: EspacioInput): Promise<Espacio> {
    if (!isRestConfigured()) {
      const created: Espacio = { ...payload, id: `mock-${Date.now()}` };
      mockEspacios.push(created);
      return created;
    }

    return restClient.post<Espacio>('/espacios', payload);
  },
  async update(id: string, payload: Partial<EspacioInput>): Promise<Espacio> {
    if (!isRestConfigured()) {
      const current = mockEspacios.find((e) => e.id === id) ?? mockEspacios[0];
      Object.assign(current, payload);
      return current;
    }

    return restClient.put<Espacio>(`/espacios/${id}`, payload);
  },
  async remove(id: string): Promise<void> {
    if (!isRestConfigured()) return;
    await restClient.delete(`/espacios/${id}`);
  },
};

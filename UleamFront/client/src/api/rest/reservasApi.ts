import { PagedResult, isRestConfigured, restClient } from './client';

export type Reserva = {
  id: string;
  espacioId: string;
  usuarioId: string;
  fecha: string;
  horaInicio: string;
  horaFin: string;
  estado: 'pendiente' | 'aprobada' | 'rechazada' | 'cancelada' | 'completada';
  tipoEvento?: string;
  descripcion?: string;
};

export type ReservaInput = Omit<Reserva, 'id' | 'estado'> & { requiereAprobacion?: boolean };

const mockReservas: Reserva[] = [
  {
    id: 'mock-r-1',
    espacioId: '1',
    usuarioId: 'mock-user',
    fecha: '2025-11-15',
    horaInicio: '14:00',
    horaFin: '16:00',
    estado: 'aprobada',
    tipoEvento: 'Reunión Académica',
    descripcion: 'Reserva demo',
  },
];

export const reservasApi = {
  async list(params?: { page?: number; pageSize?: number; estado?: string; usuarioId?: string }): Promise<PagedResult<Reserva>> {
    if (!isRestConfigured()) {
      return {
        items: mockReservas,
        total: mockReservas.length,
        page: 1,
        pageSize: mockReservas.length,
      };
    }

    return restClient.get<PagedResult<Reserva>>('/reservas', { query: params });
  },
  async detail(id: string): Promise<Reserva> {
    if (!isRestConfigured()) {
      return mockReservas.find((r) => r.id === id) ?? mockReservas[0];
    }

    return restClient.get<Reserva>(`/reservas/${id}`);
  },
  async create(payload: ReservaInput): Promise<Reserva> {
    if (!isRestConfigured()) {
      const created: Reserva = { ...payload, estado: 'pendiente', id: `mock-${Date.now()}` };
      mockReservas.push(created);
      return created;
    }

    return restClient.post<Reserva>('/reservas', payload);
  },
  async update(id: string, payload: Partial<ReservaInput>): Promise<Reserva> {
    if (!isRestConfigured()) {
      const existing = mockReservas.find((r) => r.id === id) ?? mockReservas[0];
      Object.assign(existing, payload);
      return existing;
    }

    return restClient.put<Reserva>(`/reservas/${id}`, payload);
  },
  async cancel(id: string): Promise<void> {
    if (!isRestConfigured()) return;
    await restClient.post(`/reservas/${id}/cancelar`);
  },
};

import { PagedResult, isRestConfigured, restClient } from './client';

export type Reserva = {
  id: string;
  codigo: string;
  usuarioId: number;
  espacioId: number;
  tipoEvento?: string;
  estado?: string; // nombre legible
  fecha: string;
  horaInicio: string;
  horaFin: string;
  titulo?: string;
  descripcion?: string;
  esBloqueo?: boolean;
};

const estadoLabel = (estado?: string | number | null) => {
  const id = typeof estado === 'string' ? Number(estado) : Number(estado ?? NaN);
  if (!Number.isNaN(id)) {
    switch (id) {
      case 1:
        return 'Pendiente';
      case 2:
        return 'Aprobada';
      case 3:
        return 'Rechazada';
      case 4:
        return 'Completada';
      case 5:
        return 'Cancelada';
      default:
        return 'Pendiente';
    }
  }
  if (typeof estado === 'string' && estado.length > 2) return estado;
  return 'Pendiente';
};

export type ReservaInput = {
  espacio_id: number;
  tipo_evento_id?: number;
  fecha: string; // YYYY-MM-DD
  hora_inicio: string;
  hora_fin: string;
  titulo?: string;
  descripcion?: string;
  es_bloqueo?: boolean;
  motivo_bloqueo?: string | null;
  asistentes_estimada?: number | null;
};

type BackendReserva = {
  id: number;
  codigo: string;
  usuario_id: number;
  espacio_id: number;
  tipo_evento_id?: number | null;
  estado_id?: number | null;
  fecha: string;
  hora_inicio: string;
  hora_fin: string;
  titulo?: string | null;
  descripcion?: string | null;
  es_bloqueo: boolean;
  motivo_bloqueo?: string | null;
};

function mapReserva(r: BackendReserva): Reserva {
  return {
    id: String(r.id),
    codigo: r.codigo,
    usuarioId: r.usuario_id,
    espacioId: r.espacio_id,
    tipoEvento: r.tipo_evento_id ? String(r.tipo_evento_id) : undefined,
    estado: estadoLabel(r.estado_id),
    fecha: r.fecha,
    horaInicio: r.hora_inicio,
    horaFin: r.hora_fin,
    titulo: r.titulo ?? undefined,
    descripcion: r.descripcion ?? undefined,
    esBloqueo: r.es_bloqueo,
  };
}

export const reservasApi = {
  async list(params?: { usuario_id?: number; espacio_id?: number; estado_id?: number }): Promise<PagedResult<Reserva>> {
    if (!isRestConfigured()) {
      throw new Error('Configura VITE_REST_BASE_URL para consumir /api/reservas');
    }

    const data = await restClient.get<BackendReserva[]>('/reservas', { query: params });
    const mapped = data.map(mapReserva);
    return { items: mapped, total: mapped.length, page: 1, pageSize: mapped.length };
  },
  async detail(id: string): Promise<Reserva> {
    if (!isRestConfigured()) {
      throw new Error('Configura VITE_REST_BASE_URL para consumir /api/reservas/{id}');
    }

    const r = await restClient.get<any>(`/reservas/${id}`);
    const base: BackendReserva = {
      id: r.id,
      codigo: r.codigo,
      usuario_id: r.usuario?.id ?? r.usuario_id ?? 0,
      espacio_id: r.espacio?.id ?? r.espacio_id ?? 0,
      tipo_evento_id: r.tipo_evento_id,
      estado_id: r.estado_id ?? null,
      fecha: r.fecha,
      hora_inicio: r.hora_inicio,
      hora_fin: r.hora_fin,
      titulo: r.titulo,
      descripcion: r.descripcion,
      es_bloqueo: Boolean(r.es_bloqueo),
      motivo_bloqueo: r.motivo_bloqueo,
    };
    return mapReserva(base);
  },
  async create(payload: ReservaInput): Promise<Reserva> {
    if (!isRestConfigured()) {
      throw new Error('Configura VITE_REST_BASE_URL para consumir /api/reservas');
    }
    const created = await restClient.post<BackendReserva>('/reservas', payload);
    return mapReserva(created);
  },
  async updateEstado(id: string, estado_id: number): Promise<void> {
    if (!isRestConfigured()) return;
    await restClient.patch(`/reservas/${id}/estado`, { estado_id });
  },
  async cancel(id: string): Promise<void> {
    if (!isRestConfigured()) return;
    await restClient.delete(`/reservas/${id}`);
  },
};

import { graphqlRequest, isGraphqlConfigured } from '../client';

export type ReservaNode = {
  id: string;
  codigo: string;
  usuarioId: number;
  espacioId: number;
  tipoEvento?: string;
  estado?: string;
  fecha: string;
  horaInicio: string;
  horaFin: string;
  titulo?: string;
  descripcion?: string;
  esBloqueo?: boolean;
};

const LIST_RESERVAS_QUERY = /* GraphQL */ `
  query Reservas(
    $usuario_id: Int
    $espacio_id: Int
    $estado_id: Int
    $fecha_desde: String
    $fecha_hasta: String
    $limit: Int
    $offset: Int
  ) {
    reservas(
      usuario_id: $usuario_id
      espacio_id: $espacio_id
      estado_id: $estado_id
      fecha_desde: $fecha_desde
      fecha_hasta: $fecha_hasta
      limit: $limit
      offset: $offset
    ) {
      id
      codigo
      usuario_id
      espacio_id
      tipo_evento
      estado
      fecha
      hora_inicio
      hora_fin
      titulo
      descripcion
      es_bloqueo
    }
  }
`;

const RESERVA_DETAIL_QUERY = /* GraphQL */ `
  query Reserva($id: Int!) {
    reserva(id: $id) {
      id
      codigo
      usuario_id
      espacio_id
      tipo_evento
      estado
      fecha
      hora_inicio
      hora_fin
      titulo
      descripcion
      es_bloqueo
    }
  }
`;

function mapNode(r: any): ReservaNode {
  // Debug: Log de datos crudos de GraphQL (solo primeras 3 reservas)
  if (process.env.NODE_ENV === 'development' && Math.random() < 0.15) {
    console.log(`🔍 GraphQL → usuario_id: ${r.usuario_id}, espacio_id: ${r.espacio_id}, titulo: ${r.titulo}`);
  }
  
  return {
    id: String(r.id),
    codigo: r.codigo,
    usuarioId: r.usuario_id,
    espacioId: r.espacio_id,
    tipoEvento: r.tipo_evento ?? undefined,
    estado: r.estado ?? undefined,
    fecha: r.fecha,
    horaInicio: r.hora_inicio,
    horaFin: r.hora_fin,
    titulo: r.titulo ?? undefined,
    descripcion: r.descripcion ?? undefined,
    esBloqueo: r.es_bloqueo,
  };
}

export async function fetchReservas(filters?: Partial<Record<string, string | number>>) {
  if (!isGraphqlConfigured()) {
    return [] as ReservaNode[];
  }
  const res = await graphqlRequest<{ reservas: any[] }>(LIST_RESERVAS_QUERY, filters);
  return (res.reservas ?? []).map(mapNode);
}

export async function fetchReservaById(id: string) {
  if (!isGraphqlConfigured()) {
    return null as ReservaNode | null;
  }
  const res = await graphqlRequest<{ reserva: any }>(RESERVA_DETAIL_QUERY, { id: Number(id) });
  return res?.reserva ? mapNode(res.reserva) : null;
}

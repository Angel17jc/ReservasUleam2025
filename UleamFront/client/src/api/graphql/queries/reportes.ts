import { graphqlRequest, isGraphqlConfigured } from '../client';

export type EstadisticasGenerales = {
  totalReservas: number;
  reservasPendientes: number;
  reservasAprobadas: number;
  reservasRechazadas: number;
  reservasCanceladas: number;
  espaciosActivos: number;
  usuariosActivos: number;
};

const ESTADISTICAS_QUERY = /* GraphQL */ `
  query Estadisticas($fecha_desde: String, $fecha_hasta: String) {
    estadisticas(fecha_desde: $fecha_desde, fecha_hasta: $fecha_hasta) {
      totalReservas
      reservasPendientes
      reservasAprobadas
      reservasRechazadas
      reservasCanceladas
      espaciosActivos
      usuariosActivos
    }
  }
`;

export async function fetchEstadisticasGenerales(rango?: { fecha_desde?: string; fecha_hasta?: string }) {
  if (!isGraphqlConfigured()) {
    return {
      totalReservas: 0,
      reservasPendientes: 0,
      reservasAprobadas: 0,
      reservasRechazadas: 0,
      reservasCanceladas: 0,
      espaciosActivos: 0,
      usuariosActivos: 0,
    } as EstadisticasGenerales;
  }

  try {
    const res = await graphqlRequest<{ estadisticas: EstadisticasGenerales }>(ESTADISTICAS_QUERY, rango);
    return res.estadisticas;
  } catch (error) {
    // Para usuarios no admin GraphQL devuelve admin only; mejor degradar a ceros sin romper UI.
    return {
      totalReservas: 0,
      reservasPendientes: 0,
      reservasAprobadas: 0,
      reservasRechazadas: 0,
      reservasCanceladas: 0,
      espaciosActivos: 0,
      usuariosActivos: 0,
    };
  }
}

export type TopSpace = { label: string; cantidad: number };

const TOP_SPACES_QUERY = /* GraphQL */ `
  query TopEspacios($limit: Int) {
    espaciosMasReservados(limit: $limit) {
      label
      cantidad
    }
  }
`;

export async function fetchTopEspacios(limit = 5): Promise<TopSpace[]> {
  if (!isGraphqlConfigured()) return [];
  const res = await graphqlRequest<{ espaciosMasReservados: TopSpace[] }>(TOP_SPACES_QUERY, { limit });
  return res.espaciosMasReservados ?? [];
}

export type GroupedMetric = { label: string; cantidad: number };

const RESERVAS_ESTADO_QUERY = /* GraphQL */ `
  query ReservasPorEstado {
    reservasPorEstado {
      label
      cantidad
    }
  }
`;

const RESERVAS_TIPO_EVENTO_QUERY = /* GraphQL */ `
  query ReservasPorTipoEvento {
    reservasPorTipoEvento {
      label
      cantidad
    }
  }
`;

const TOP_USUARIOS_QUERY = /* GraphQL */ `
  query UsuariosMasActivos($limit: Int) {
    usuariosMasActivos(limit: $limit) {
      label
      cantidad
    }
  }
`;

export async function fetchReservasPorEstado(): Promise<GroupedMetric[]> {
  if (!isGraphqlConfigured()) return [];
  const res = await graphqlRequest<{ reservasPorEstado: GroupedMetric[] }>(RESERVAS_ESTADO_QUERY);
  return res.reservasPorEstado ?? [];
}

export async function fetchReservasPorTipoEvento(): Promise<GroupedMetric[]> {
  if (!isGraphqlConfigured()) return [];
  const res = await graphqlRequest<{ reservasPorTipoEvento: GroupedMetric[] }>(RESERVAS_TIPO_EVENTO_QUERY);
  return res.reservasPorTipoEvento ?? [];
}

export async function fetchTopUsuarios(limit = 5): Promise<GroupedMetric[]> {
  if (!isGraphqlConfigured()) return [];
  const res = await graphqlRequest<{ usuariosMasActivos: GroupedMetric[] }>(TOP_USUARIOS_QUERY, { limit });
  return res.usuariosMasActivos ?? [];
}

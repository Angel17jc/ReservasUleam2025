import { graphqlRequest, isGraphqlConfigured } from '../client';

export type EstadisticasGenerales = {
  totalReservas: number;
  tasaAprobacion: number;
  espacioMasUsado?: string;
  usuarioMasActivo?: string;
};

const ESTADISTICAS_QUERY = /* GraphQL */ `
  query EstadisticasGenerales($desde: String, $hasta: String) {
    estadisticasGenerales(desde: $desde, hasta: $hasta) {
      totalReservas
      tasaAprobacion
      espacioMasUsado
      usuarioMasActivo
    }
  }
`;

export async function fetchEstadisticasGenerales(rango?: { desde?: string; hasta?: string }) {
  if (!isGraphqlConfigured()) {
    return { totalReservas: 0, tasaAprobacion: 0 } as EstadisticasGenerales;
  }

  return graphqlRequest<{ estadisticasGenerales: EstadisticasGenerales }>(ESTADISTICAS_QUERY, rango).then(
    (res) => res.estadisticasGenerales,
  );
}

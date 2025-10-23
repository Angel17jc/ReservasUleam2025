import { graphqlRequest, isGraphqlConfigured } from '../client';

export type DisponibilidadItem = {
  fecha: string;
  disponible: boolean;
};

const DISPONIBILIDAD_QUERY = /* GraphQL */ `
  query DisponibilidadEspacio($espacioId: ID!, $desde: String, $hasta: String) {
    disponibilidadEspacio(espacioId: $espacioId, desde: $desde, hasta: $hasta) {
      fecha
      disponible
    }
  }
`;

export async function fetchDisponibilidad(espacioId: string, rango?: { desde?: string; hasta?: string }) {
  if (!isGraphqlConfigured()) {
    return [] as DisponibilidadItem[];
  }

  return graphqlRequest<{ disponibilidadEspacio: DisponibilidadItem[] }>(DISPONIBILIDAD_QUERY, {
    espacioId,
    ...rango,
  }).then((res) => res.disponibilidadEspacio);
}

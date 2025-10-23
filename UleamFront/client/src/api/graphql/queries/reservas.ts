import { graphqlRequest, isGraphqlConfigured } from '../client';

export type ReservaNode = {
  id: string;
  espacioId: string;
  usuario: { id: string; nombre: string };
  fecha: string;
  horaInicio: string;
  horaFin: string;
  estado: string;
};

const LIST_RESERVAS_QUERY = /* GraphQL */ `
  query Reservas($search: String, $estado: String) {
    reservas(search: $search, estado: $estado) {
      id
      espacioId
      usuario { id nombre }
      fecha
      horaInicio
      horaFin
      estado
    }
  }
`;

const RESERVA_DETAIL_QUERY = /* GraphQL */ `
  query Reserva($id: ID!) {
    reserva(id: $id) {
      id
      espacioId
      usuario { id nombre }
      fecha
      horaInicio
      horaFin
      estado
      tipoEvento
      descripcion
    }
  }
`;

export async function fetchReservas(filters?: { search?: string; estado?: string }) {
  if (!isGraphqlConfigured()) {
    return [] as ReservaNode[];
  }
  return graphqlRequest<{ reservas: ReservaNode[] }>(LIST_RESERVAS_QUERY, filters).then((res) => res.reservas);
}

export async function fetchReservaById(id: string) {
  if (!isGraphqlConfigured()) {
    return null as ReservaNode | null;
  }
  return graphqlRequest<{ reserva: ReservaNode }>(RESERVA_DETAIL_QUERY, { id }).then((res) => res.reserva);
}

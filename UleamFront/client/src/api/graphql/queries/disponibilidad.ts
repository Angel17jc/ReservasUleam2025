import { graphqlRequest, isGraphqlConfigured } from '../client';

export type DisponibilidadSlot = {
  hora_inicio: string;
  hora_fin: string;
};

export type DisponibilidadPayload = {
  espacio_id: number;
  espacio_nombre: string;
  fecha: string;
  dia_semana: string;
  ocupados: Array<DisponibilidadSlot & { id: number; estado: string; titulo?: string; usuario_id: number }>;
  libres: DisponibilidadSlot[];
};

const DISPONIBILIDAD_QUERY = /* GraphQL */ `
  query Disponibilidad($espacio_id: Int!, $fecha: String!, $incluir_pendientes: Boolean) {
    disponibilidad(espacio_id: $espacio_id, fecha: $fecha, incluir_pendientes: $incluir_pendientes) {
      espacio_id
      espacio_nombre
      fecha
      dia_semana
      ocupados {
        id
        estado
        hora_inicio
        hora_fin
        titulo
        usuario_id
      }
      libres {
        hora_inicio
        hora_fin
      }
    }
  }
`;

export async function fetchDisponibilidad(espacioId: number, fecha: string, incluirPendientes = true) {
  if (!isGraphqlConfigured()) {
    return null as DisponibilidadPayload | null;
  }

  const res = await graphqlRequest<{ disponibilidad: DisponibilidadPayload }>(DISPONIBILIDAD_QUERY, {
    espacio_id: espacioId,
    fecha,
    incluir_pendientes: incluirPendientes,
  });
  return res.disponibilidad;
}

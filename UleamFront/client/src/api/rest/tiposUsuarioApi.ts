import { isRestConfigured, restClient } from './client';

export type TipoUsuario = {
  id: number;
  nombre: string;
  descripcion?: string | null;
  nivel_prioridad: number;
  permisos?: Record<string, any>;
};

export const tiposUsuarioApi = {
  async list(): Promise<TipoUsuario[]> {
    if (!isRestConfigured()) throw new Error('Configura VITE_REST_BASE_URL para consumir /api/tipos-usuario');
    return restClient.get<TipoUsuario[]>('/tipos-usuario');
  },
};

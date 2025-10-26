import { PagedResult, isRestConfigured, restClient } from './client';
import { UserProfile } from './authApi';

export type UsuarioInput = Omit<UserProfile, 'id' | 'role'> & { role?: UserProfile['role']; password?: string };

export const usuariosApi = {
  async list(params?: { page?: number; pageSize?: number; role?: string; search?: string }): Promise<PagedResult<UserProfile>> {
    if (!isRestConfigured()) {
      return {
        items: [
          { id: 'mock-user', nombre: 'Usuario Demo', email: 'demo@uleam.edu.ec', role: 'admin', estado: 'activo' },
        ],
        total: 1,
        page: 1,
        pageSize: 10,
      };
    }

    return restClient.get<PagedResult<UserProfile>>('/usuarios', { query: params });
  },
  async detail(id: string): Promise<UserProfile> {
    if (!isRestConfigured()) {
      return { id, nombre: 'Usuario Demo', email: 'demo@uleam.edu.ec', role: 'user', estado: 'activo' };
    }

    return restClient.get<UserProfile>(`/usuarios/${id}`);
  },
  async update(id: string, payload: Partial<UsuarioInput>): Promise<UserProfile> {
    if (!isRestConfigured()) {
      return { id, ...payload } as UserProfile;
    }

    return restClient.put<UserProfile>(`/usuarios/${id}`, payload);
  },
  async create(payload: UsuarioInput): Promise<UserProfile> {
    if (!isRestConfigured()) {
      return { id: `mock-${Date.now()}`, role: payload.role ?? 'user', ...payload } as UserProfile;
    }

    return restClient.post<UserProfile>('/usuarios', payload);
  },
  async remove(id: string): Promise<void> {
    if (!isRestConfigured()) return;
    await restClient.delete(`/usuarios/${id}`);
  },
};

import { PagedResult, isRestConfigured, restClient } from './client';
import { UserProfile } from './authApi';

export type UsuarioInput = {
  email: string;
  nombre: string;
  apellido: string;
  telefono?: string;
  tipo_usuario_id?: number;
  estado?: string;
  password_hash?: string;
};

type BackendUser = {
  id: number;
  email: string;
  nombre: string;
  apellido?: string;
  telefono?: string;
  tipo_usuario_id: number;
  estado?: string;
  avatar_url?: string;
};

function mapUser(u: BackendUser): UserProfile {
  return {
    id: String(u.id),
    nombre: `${u.nombre}${u.apellido ? ` ${u.apellido}` : ''}`.trim(),
    email: u.email,
    role: u.tipo_usuario_id === 1 ? 'admin' : 'user',
    estado: u.estado,
    avatar: u.avatar_url,
    tipoUsuarioId: u.tipo_usuario_id,
  };
}

export const usuariosApi = {
  async list(): Promise<PagedResult<UserProfile>> {
    if (!isRestConfigured()) {
      throw new Error('Configura VITE_REST_BASE_URL para consumir /api/usuarios');
    }
    const users = await restClient.get<BackendUser[]>('/usuarios');
    const mapped = users.map(mapUser);
    return { items: mapped, total: mapped.length, page: 1, pageSize: mapped.length };
  },
  async detail(id: string): Promise<UserProfile> {
    if (!isRestConfigured()) {
      throw new Error('Configura VITE_REST_BASE_URL para consumir /api/usuarios/{id}');
    }
    const user = await restClient.get<BackendUser>(`/usuarios/${id}`);
    return mapUser(user);
  },
  async update(id: string, payload: Partial<UsuarioInput>): Promise<UserProfile> {
    if (!isRestConfigured()) {
      throw new Error('Configura VITE_REST_BASE_URL para consumir /api/usuarios/{id}');
    }
    const updated = await restClient.put<BackendUser>(`/usuarios/${id}`, payload);
    return mapUser(updated);
  },
  async create(payload: UsuarioInput): Promise<UserProfile> {
    if (!isRestConfigured()) {
      throw new Error('Configura VITE_REST_BASE_URL para consumir /api/usuarios');
    }
    const created = await restClient.post<BackendUser>('/usuarios', payload);
    return mapUser(created);
  },
  async remove(id: string): Promise<void> {
    if (!isRestConfigured()) return;
    await restClient.delete(`/usuarios/${id}`);
  },
};

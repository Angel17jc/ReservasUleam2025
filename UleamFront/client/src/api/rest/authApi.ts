import { isRestConfigured, restClient } from './client';

export type Credentials = { email: string; password: string };
export type RegisterInput = Credentials & { nombre: string; apellido?: string; telefono?: string; tipo_usuario_id?: number };

export type UserProfile = {
  id: string;
  nombre: string;
  apellido?: string;
  email: string;
  role: 'admin' | 'user';
  avatar?: string;
  estado?: 'activo' | 'inactivo' | string;
  tipoUsuarioId?: number;
  tipoUsuarioNombre?: string;
};

export type AuthResponse = { token: string; user: UserProfile };

// El auth-service retorna campos en camelCase: accessToken, refreshToken, expiresIn
type BackendAuthResponse = {
  accessToken: string;
  refreshToken?: string;
  expiresIn?: number;
  tokenType?: string;
  user: {
    id: number;
    email: string;
    nombre: string;
    apellido?: string;
    telefono?: string;
    tipo_usuario_id: number;
    tipo_usuario?: { id: number; nombre: string };
    estado?: string;
    avatar_url?: string;
  };
};

function mapBackendUser(input: BackendAuthResponse['user']): UserProfile {
  return {
    id: String(input.id),
    nombre: input.nombre,
    apellido: input.apellido,
    email: input.email,
    role: input.tipo_usuario_id === 1 ? 'admin' : 'user',
    estado: input.estado,
    avatar: input.avatar_url,
    tipoUsuarioId: input.tipo_usuario_id,
    tipoUsuarioNombre: input.tipo_usuario?.nombre,
  };
}

export const authApi = {
  async login(input: Credentials): Promise<AuthResponse> {
    if (!isRestConfigured()) {
      throw new Error('Configura VITE_REST_BASE_URL para usar el backend REST');
    }
    const res = await restClient.post<BackendAuthResponse>('/auth/login', input);
    // Mapear la respuesta del backend (accessToken en camelCase)
    return { token: (res as any).accessToken ?? (res as any).access_token ?? '', user: mapBackendUser(res.user) };
  },
  async register(input: RegisterInput): Promise<AuthResponse> {
    if (!isRestConfigured()) {
      throw new Error('Configura VITE_REST_BASE_URL para usar el backend REST');
    }
    const res = await restClient.post<BackendAuthResponse>('/auth/register', input);
    return { token: (res as any).accessToken ?? (res as any).access_token ?? '', user: mapBackendUser(res.user) };
  },
  async me(): Promise<UserProfile> {
    if (!isRestConfigured()) {
      throw new Error('Configura VITE_REST_BASE_URL para usar el backend REST');
    }
    const me = await restClient.get<BackendAuthResponse['user']>('/auth/me');
    return mapBackendUser(me);
  },
  async logout(): Promise<void> {
    if (!isRestConfigured()) return;
    await restClient.post('/auth/logout');
  },
};

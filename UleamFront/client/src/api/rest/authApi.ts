import { isRestConfigured, restClient } from './client';

export type Credentials = { email: string; password: string };
// Prefer camelCase (tipoUsuarioId) to match DTO; keep snake for backward compatibility and map it.
export type RegisterInput = Credentials & {
  nombre: string;
  apellido?: string;
  telefono?: string;
  tipoUsuarioId?: number;
  tipo_usuario_id?: number;
};

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

// El auth-service puede devolver snake_case o camelCase según la versión; aceptamos ambos.
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
    // soportar ambas variantes
    tipo_usuario_id?: number;
    tipoUsuarioId?: number;
    tipo_usuario?: { id: number; nombre: string };
    tipoUsuario?: { id: number; nombre: string };
    estado?: string;
    avatar_url?: string;
    avatarUrl?: string;
  };
};

function mapBackendUser(input: BackendAuthResponse['user']): UserProfile {
  // tolerar snake_case y camelCase provenientes del backend
  const tipoUsuarioId = input.tipo_usuario_id ?? input.tipoUsuarioId ?? input.tipo_usuario?.id ?? input.tipoUsuario?.id;
  const tipoUsuarioNombre = input.tipo_usuario?.nombre ?? input.tipoUsuario?.nombre;
  const avatar = input.avatar_url ?? input.avatarUrl;
  const role = tipoUsuarioId === 1 ? 'admin' : 'user';

  return {
    id: String(input.id),
    nombre: input.nombre,
    apellido: input.apellido,
    email: input.email,
    role,
    estado: input.estado,
    avatar,
    tipoUsuarioId,
    tipoUsuarioNombre,
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
    const payload: any = { ...input };
    // Normalizar a camelCase para el auth-service (RegisterDto espera tipoUsuarioId)
    payload.tipoUsuarioId = input.tipoUsuarioId ?? input.tipo_usuario_id;
    delete payload.tipo_usuario_id;
    const res = await restClient.post<BackendAuthResponse>('/auth/register', payload);
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

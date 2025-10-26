import { isRestConfigured, restClient } from './client';

export type Credentials = { email: string; password: string };
export type RegisterInput = Credentials & { nombre: string };

export type UserProfile = {
  id: string;
  nombre: string;
  email: string;
  role: 'admin' | 'user';
  avatar?: string;
  estado?: 'activo' | 'inactivo';
};

export type AuthResponse = { token: string; user: UserProfile };

const mockUsers: Record<string, UserProfile & { password: string }> = {
  'demo@uleam.edu.ec': {
    id: 'mock-user',
    nombre: 'Usuario Demo',
    email: 'demo@uleam.edu.ec',
    password: 'demo123',
    role: 'user',
    estado: 'activo',
  },
  'admin@uleam.edu.ec': {
    id: 'mock-admin',
    nombre: 'Admin Demo',
    email: 'admin@uleam.edu.ec',
    password: 'admin123',
    role: 'admin',
    estado: 'activo',
  },
};

export const authApi = {
  async login(input: Credentials): Promise<AuthResponse> {
    if (!isRestConfigured()) {
      const match = mockUsers[input.email];
      if (!match || match.password !== input.password) {
        throw new Error('Credenciales inválidas (mock)');
      }
      const { password, ...user } = match;
      return { token: 'mock-token', user };
    }

    return restClient.post<AuthResponse>('/auth/login', input);
  },
  async register(input: RegisterInput): Promise<AuthResponse> {
    if (!isRestConfigured()) {
      const user: UserProfile = {
        id: `mock-${Date.now()}`,
        nombre: input.nombre,
        email: input.email,
        role: 'user',
        estado: 'activo',
      };
      return { token: 'mock-token', user };
    }

    return restClient.post<AuthResponse>('/auth/register', input);
  },
  async me(): Promise<UserProfile> {
    if (!isRestConfigured()) {
      const { password, ...user } = mockUsers['demo@uleam.edu.ec'];
      return user;
    }

    return restClient.get<UserProfile>('/auth/me');
  },
  async logout(): Promise<void> {
    if (!isRestConfigured()) return;
    await restClient.post('/auth/logout');
  },
};

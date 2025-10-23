import { isRestConfigured, restClient } from './client';

export type Credentials = { email: string; password: string };
export type RegisterInput = Credentials & { nombre: string };

export type UserProfile = {
  id: string;
  nombre: string;
  email: string;
  rol: 'admin' | 'usuario';
  avatar?: string;
  estado?: 'activo' | 'inactivo';
};

export type AuthResponse = { token: string; user: UserProfile };

const mockUser: UserProfile = {
  id: 'mock-user',
  nombre: 'Usuario Demo',
  email: 'demo@uleam.edu.ec',
  rol: 'admin',
  estado: 'activo',
};

export const authApi = {
  async login(input: Credentials): Promise<AuthResponse> {
    if (!isRestConfigured()) {
      return { token: 'mock-token', user: mockUser };
    }

    return restClient.post<AuthResponse>('/auth/login', input);
  },
  async register(input: RegisterInput): Promise<AuthResponse> {
    if (!isRestConfigured()) {
      return { token: 'mock-token', user: { ...mockUser, ...input, rol: 'usuario', id: 'mock-registered' } };
    }

    return restClient.post<AuthResponse>('/auth/register', input);
  },
  async me(): Promise<UserProfile> {
    if (!isRestConfigured()) {
      return mockUser;
    }

    return restClient.get<UserProfile>('/auth/me');
  },
  async logout(): Promise<void> {
    if (!isRestConfigured()) return;
    await restClient.post('/auth/logout');
  },
};

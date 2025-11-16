import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { authApi } from '../authApi';

describe('authApi', () => {
  const mockToken = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.test';
  const mockUser = {
    id: 1,
    email: 'test@uleam.edu.ec',
    nombre: 'Test',
    apellido: 'User',
    tipo_usuario_id: 2,
    estado: 'activo',
  };

  beforeEach(() => {
    // Limpiar localStorage antes de cada test
    localStorage.clear();
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  describe('login', () => {
    it('debe hacer login exitosamente y retornar token + user', async () => {
      // Arrange
      const credentials = {
        email: 'test@uleam.edu.ec',
        password: 'password123',
      };

      global.fetch = vi.fn(() =>
        Promise.resolve({
          ok: true,
          status: 200,
          headers: new Headers({ 'content-type': 'application/json' }),
          json: () =>
            Promise.resolve({
              access_token: mockToken,
              token_type: 'bearer',
              user: mockUser,
            }),
        } as Response)
      );

      // Act
      const result = await authApi.login(credentials);

      // Assert
      expect(result).toHaveProperty('token');
      expect(result).toHaveProperty('user');
      expect(result.token).toBe(mockToken);
      expect(result.user.email).toBe('test@uleam.edu.ec');
      expect(result.user.role).toBe('user'); // tipo_usuario_id=2 → user
    });

    it('debe lanzar error si las credenciales son inválidas', async () => {
      // Arrange
      global.fetch = vi.fn(() =>
        Promise.resolve({
          ok: false,
          status: 401,
          statusText: 'Unauthorized',
          headers: new Headers({ 'content-type': 'application/json' }),
          json: () => Promise.resolve({ detail: 'Credenciales inválidas' }),
        } as Response)
      );

      // Act & Assert
      await expect(
        authApi.login({ email: 'wrong@test.com', password: 'wrong' })
      ).rejects.toThrow();
    });

    it('debe mapear admin correctamente (tipo_usuario_id=1)', async () => {
      // Arrange
      global.fetch = vi.fn(() =>
        Promise.resolve({
          ok: true,
          headers: new Headers({ 'content-type': 'application/json' }),
          json: () =>
            Promise.resolve({
              access_token: mockToken,
              token_type: 'bearer',
              user: { ...mockUser, tipo_usuario_id: 1 }, // Admin
            }),
        } as Response)
      );

      // Act
      const result = await authApi.login({
        email: 'admin@uleam.edu.ec',
        password: 'admin123',
      });

      // Assert
      expect(result.user.role).toBe('admin');
    });
  });

  describe('register', () => {
    it('debe registrar un nuevo usuario', async () => {
      // Arrange
      const registerData = {
        email: 'nuevo@uleam.edu.ec',
        password: 'password123',
        nombre: 'Nuevo',
        apellido: 'Usuario',
      };

      global.fetch = vi.fn(() =>
        Promise.resolve({
          ok: true,
          headers: new Headers({ 'content-type': 'application/json' }),
          json: () =>
            Promise.resolve({
              access_token: mockToken,
              token_type: 'bearer',
              user: { ...mockUser, ...registerData, id: 999 },
            }),
        } as Response)
      );

      // Act
      const result = await authApi.register(registerData);

      // Assert
      expect(result.user.email).toBe(registerData.email);
      expect(result.user.nombre).toBe(registerData.nombre);
    });
  });

  describe('me', () => {
    it('debe obtener el perfil del usuario actual', async () => {
      // Arrange
      // Simular que hay un token en localStorage
      localStorage.setItem('auth_token', mockToken);

      global.fetch = vi.fn(() =>
        Promise.resolve({
          ok: true,
          headers: new Headers({ 'content-type': 'application/json' }),
          json: () => Promise.resolve(mockUser),
        } as Response)
      );

      // Act
      const result = await authApi.me();

      // Assert
      expect(result.email).toBe(mockUser.email);
      expect(result.id).toBe(String(mockUser.id));
    });

    it('debe lanzar error si el token es inválido', async () => {
      // Arrange
      global.fetch = vi.fn(() =>
        Promise.resolve({
          ok: false,
          status: 401,
          statusText: 'Unauthorized',
          headers: new Headers({ 'content-type': 'application/json' }),
        } as Response)
      );

      // Act & Assert
      await expect(authApi.me()).rejects.toThrow();
    });
  });

  describe('logout', () => {
    it('debe hacer logout correctamente', async () => {
      // Arrange
      localStorage.setItem('uleam_token', mockToken);
      localStorage.setItem('uleam_user', JSON.stringify(mockUser));

      // Mock de fetch para logout
      global.fetch = vi.fn(() =>
        Promise.resolve({
          ok: true,
          status: 200,
          headers: new Headers({ 'content-type': 'application/json' }),
          json: () => Promise.resolve({}),
        } as Response)
      );

      // Verificar que están guardados
      expect(localStorage.getItem('uleam_token')).not.toBeNull();

      // Act
      await authApi.logout();

      // Assert - El authApi.logout NO limpia localStorage, eso lo hace AuthContext
      // Verificar solo que la llamada se ejecutó sin errores
      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining('/auth/logout'),
        expect.any(Object)
      );
    });
  });
});

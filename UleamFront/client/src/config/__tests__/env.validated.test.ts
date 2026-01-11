import { describe, it, expect, beforeEach, vi } from 'vitest';

describe('env.validated', () => {
  // Nota: Este test es más simple porque la validación ocurre en import-time
  // En un setup real, necesitarías mockear import.meta.env antes de importar

  beforeEach(() => {
    // Reset de módulos para cada test
    vi.resetModules();
  });

  it('debe validar correctamente las variables de entorno', async () => {
    // Arrange
    vi.stubGlobal('import.meta', {
      env: {
        VITE_REST_BASE_URL: 'http://localhost:8000',
        VITE_GRAPHQL_URL: 'http://localhost:8081/graphql',
        VITE_WS_URL: 'http://localhost:3001',
        MODE: 'test',
        DEV: true,
        PROD: false,
      },
    });

    // Act
    const { env } = await import('../env.validated');

    // Assert
    expect(env.restBaseUrl).toBe('http://localhost:8000');
    expect(env.graphqlUrl).toBe('http://localhost:8080/graphql');
    expect(env.wsUrl).toBe('http://localhost:3001');
    expect(env.mode).toBe('test');
    expect(env.isDev).toBe(true);
  });

  it('debe tener helper ensureEnvValue', async () => {
    // Arrange
    vi.stubGlobal('import.meta', {
      env: {
        VITE_REST_BASE_URL: 'http://localhost:8000',
        VITE_GRAPHQL_URL: 'http://localhost:8081/graphql',
        VITE_WS_URL: 'http://localhost:3001',
        MODE: 'test',
        DEV: true,
        PROD: false,
      },
    });

    // Act
    const { ensureEnvValue } = await import('../env.validated');
    const value = ensureEnvValue('restBaseUrl');

    // Assert
    expect(value).toBe('http://localhost:8000');
  });

  it('debe tener helper areServicesConfigured', async () => {
    // Arrange
    vi.stubGlobal('import.meta', {
      env: {
        VITE_REST_BASE_URL: 'http://localhost:8000',
        VITE_GRAPHQL_URL: 'http://localhost:8081/graphql',
        VITE_WS_URL: 'http://localhost:3001',
        MODE: 'test',
        DEV: false,
        PROD: true,
      },
    });

    // Act
    const { areServicesConfigured } = await import('../env.validated');
    const result = areServicesConfigured();

    // Assert
    expect(result).toBe(true);
  });
});

import { expect, afterEach, beforeAll, vi, afterAll } from 'vitest';
import { cleanup } from '@testing-library/react';
import * as matchers from '@testing-library/jest-dom/matchers';

// Extend Vitest's expect con matchers de jest-dom
expect.extend(matchers);

// Cleanup después de cada test
afterEach(() => {
  cleanup();
  localStorage.clear();
});

// Mock de import.meta.env para tests
vi.stubGlobal('import.meta', {
  env: {
    VITE_REST_BASE_URL: 'http://localhost:8000',
    VITE_GRAPHQL_URL: 'http://localhost:8080/graphql',
    VITE_WS_URL: 'http://localhost:3001',
    MODE: 'test',
    DEV: false,
    PROD: false,
  },
});

// Mock de localStorage
const localStorageMock = (() => {
  let store: Record<string, string> = {};

  return {
    getItem: (key: string) => store[key] || null,
    setItem: (key: string, value: string) => {
      store[key] = value.toString();
    },
    removeItem: (key: string) => {
      delete store[key];
    },
    clear: () => {
      store = {};
    },
  };
})();

Object.defineProperty(window, 'localStorage', {
  value: localStorageMock,
});

// Mock de console.error para tests más limpios
const originalError = console.error;
beforeAll(() => {
  console.error = vi.fn((...args: any[]) => {
    // Ignorar errores comunes de React Testing Library y ErrorBoundary tests
    if (typeof args[0] === 'string') {
      if (
        args[0].includes('Not implemented: HTMLFormElement.prototype.submit') ||
        args[0].includes('Not implemented: navigation') ||
        args[0].includes('Error de prueba') ||
        args[0].includes('The above error occurred')
      ) {
        return;
      }
    }
    originalError.call(console, ...args);
  });
});

afterAll(() => {
  console.error = originalError;
});

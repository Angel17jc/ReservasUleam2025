import { defineConfig } from 'vitest/config';
import react from '@vitejs/plugin-react';
import path from 'path';

export default defineConfig({
  plugins: [react()] as any,
  test: {
    // Entorno de ejecución
    environment: 'jsdom',
    
    // Globals (permite usar describe, it, expect sin importar)
    globals: true,
    
    // Setup files
    setupFiles: ['./client/src/test/setup.ts'],
    
    // Coverage
    coverage: {
      provider: 'v8',
      reporter: ['text', 'json', 'html'],
      exclude: [
        'node_modules/',
        'client/src/test/',
        '**/*.d.ts',
        '**/*.config.*',
        '**/mockData',
        'dist/',
      ],
      // Umbrales de cobertura (Vitest 4 syntax)
      thresholds: {
        statements: 30,
        branches: 30,
        functions: 30,
        lines: 30,
      },
    },
    
    // Incluir archivos de test
    include: ['**/*.{test,spec}.{js,mjs,cjs,ts,mts,cts,jsx,tsx}'],
    
    // Excluir
    exclude: [
      'node_modules',
      'dist',
      '.idea',
      '.git',
      '.cache',
    ],
    
    // Timeouts
    testTimeout: 10000,
    hookTimeout: 10000,
    
    // Modo silencioso para reducir noise en tests
    silent: false,
    
    // Pool de threads para mejor rendimiento
    pool: 'threads',
  },
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './client/src'),
    },
  },
});

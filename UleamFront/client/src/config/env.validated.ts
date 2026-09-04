import { z } from 'zod';

/**
 * Schema de validación para variables de entorno
 * 
 * Falla en startup si faltan variables críticas o tienen formato inválido
 */
const envSchema = z.object({
  restBaseUrl: z
    .string()
    .url('VITE_REST_BASE_URL debe ser una URL válida (ej: http://localhost:8004)')
    .describe('URL base del servicio REST (Python FastAPI)'),

  paymentBaseUrl: z
    .string()
    .url('VITE_PAYMENT_BASE_URL debe ser una URL válida (ej: http://localhost:8024)')
    .optional()
    .describe('URL base del payment-service (FastAPI)'),

  graphqlUrl: z
    .string()
    .url('VITE_GRAPHQL_URL debe ser una URL válida (ej: http://localhost:8014/graphql)')
    .describe('URL del servicio GraphQL (Go)'),

  wsUrl: z
    .string()
    .url('VITE_WS_URL debe ser una URL válida (ej: http://localhost:3014)')
    .describe('URL del servicio WebSocket (Socket.IO)'),

  mode: z
    .enum(['development', 'production', 'test'])
    .default('development')
    .describe('Modo de ejecución de la aplicación'),

  isDev: z.boolean().describe('Indica si está en modo desarrollo'),
  isProd: z.boolean().describe('Indica si está en modo producción'),
});

export type EnvConfig = z.infer<typeof envSchema>;

/**
 * Valida y retorna las variables de entorno tipadas
 * 
 * @throws {Error} Si alguna variable es inválida o falta
 */
function validateEnv(): EnvConfig {
  const rawEnv = {
    restBaseUrl: import.meta.env.VITE_REST_BASE_URL?.trim(),
    paymentBaseUrl: import.meta.env.VITE_PAYMENT_BASE_URL?.trim(),
    graphqlUrl: import.meta.env.VITE_GRAPHQL_URL?.trim(),
    wsUrl: import.meta.env.VITE_WS_URL?.trim(),
    mode: import.meta.env.MODE || 'development',
    isDev: import.meta.env.DEV === true,
    isProd: import.meta.env.PROD === true,
  };

  try {
    return envSchema.parse(rawEnv);
  } catch (error) {
    if (error instanceof z.ZodError) {
      const messages = error.errors.map((err) => {
        const path = err.path.join('.');
        return `  ❌ ${path}: ${err.message}`;
      });

      const errorMessage = [
        '🔴 Error en la configuración de variables de entorno:',
        '',
        ...messages,
        '',
        '💡 Asegúrate de crear un archivo .env.local en la raíz de UleamFront con:',
        '',
        '  VITE_REST_BASE_URL=http://localhost:8004',
        '  VITE_PAYMENT_BASE_URL=http://localhost:8024',
        '  VITE_GRAPHQL_URL=http://localhost:8014/graphql',
        '  VITE_WS_URL=http://localhost:3014',
        '',
      ].join('\n');

      console.error(errorMessage);
      throw new Error('Configuración de entorno inválida. Ver consola para detalles.');
    }
    throw error;
  }
}

/**
 * Variables de entorno validadas y tipadas
 * 
 * Usar esto en lugar de `import.meta.env` directamente
 * 
 * @example
 * import { env } from '@/config/env.validated';
 * 
 * const apiUrl = env.restBaseUrl;
 */
export const env = validateEnv();

/**
 * Helper para obtener una variable específica con validación
 * 
 * @deprecated Usar `env.restBaseUrl` directamente
 */
export function ensureEnvValue(name: keyof typeof env): string {
  const value = env[name];
  if (!value) {
    throw new Error(`Variable de entorno '${name}' no está definida`);
  }
  return String(value);
}

/**
 * Verifica si todas las URLs de servicios están configuradas
 */
export function areServicesConfigured() {
  return Boolean(env.restBaseUrl && env.graphqlUrl && env.wsUrl);
}

/**
 * Logs de configuración en desarrollo
 */
if (env.isDev) {
  console.log('✅ Variables de entorno validadas correctamente:');
  console.table({
    'REST API': env.restBaseUrl,
    'Payment API': env.paymentBaseUrl ?? '(opcional)',
    'GraphQL API': env.graphqlUrl,
    'WebSocket': env.wsUrl,
    'Modo': env.mode,
  });
}

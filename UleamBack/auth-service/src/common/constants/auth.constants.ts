export const TIPO_USUARIO = {
  ADMIN: 1,
  PROFESOR: 2,
  ESTUDIANTE: 3,
} as const;

export const TIPO_USUARIO_LABELS = {
  [TIPO_USUARIO.ADMIN]: 'Administrador',
  [TIPO_USUARIO.PROFESOR]: 'Profesor',
  [TIPO_USUARIO.ESTUDIANTE]: 'Estudiante',
} as const;

export const JWT_CONSTANTS = {
  ACCESS_TOKEN_EXPIRATION: 15 * 60, // 15 minutes in seconds
  REFRESH_TOKEN_EXPIRATION: 7 * 24 * 60 * 60, // 7 days in seconds
  BLACKLIST_PREFIX: 'blacklist:',
  REFRESH_TOKEN_PREFIX: 'refresh_token:',
} as const;

export const RATE_LIMIT = {
  TTL: 60, // seconds
  LIMIT: 10, // requests per TTL
} as const;

export const ACCOUNT_SECURITY = {
  MAX_FAILED_ATTEMPTS: 5,
  LOCKOUT_DURATION_MINUTES: 15,
} as const;

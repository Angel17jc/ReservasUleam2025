export interface JwtPayload {
  sub: number; // User ID
  email: string;
  tipo_usuario_id?: number;
  type: 'access' | 'refresh';
  iat?: number;
  exp?: number;
}

export interface TokenResponse {
  accessToken: string;
  refreshToken: string;
  expiresIn: number;
  tokenType: string;
}

export interface UserResponse {
  id: number;
  nombre: string;
  apellido: string;
  email: string;
  tipoUsuarioId: number;
  telefono: string | null;
  avatarUrl: string | null;
  activo: boolean;
  fechaCreacion: Date;
}

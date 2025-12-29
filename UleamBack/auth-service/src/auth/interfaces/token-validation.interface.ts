export interface TokenValidationResponse {
  valid: boolean;
  user?: {
    id: number;
    email: string;
    nombre: string;
    apellido: string;
    tipoUsuarioId: number;
    estado: string;
  };
  error?: string;
}

export interface PublicKeyResponse {
  algorithm: string;
  issuer: string;
  expiresIn: number;
}

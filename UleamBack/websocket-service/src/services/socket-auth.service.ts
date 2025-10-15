import { Injectable, UnauthorizedException } from '@nestjs/common';
import { ConfigService } from '@nestjs/config';
import { verify } from 'jsonwebtoken';
import { Socket } from 'socket.io';
import { UsersService } from './users.service';
import { ConnectedUser, JwtPayload } from '../interfaces/socket.interface';

@Injectable()
export class SocketAuthService {
  private readonly jwtSecret: string;

  constructor(
    private readonly configService: ConfigService,
    private readonly usersService: UsersService,
  ) {
    this.jwtSecret =
      this.configService.get<string>('JWT_SECRET') ||
      this.configService.get<string>('SECRET_KEY') ||
      'your-secret-key-change-in-production-09f26e402edf8c5d56c0';
  }

  extractToken(client: Socket): string | null {
    const authHeader = client.handshake?.headers?.authorization;
    if (authHeader && authHeader.startsWith('Bearer ')) {
      return authHeader.replace('Bearer ', '').trim();
    }

    const tokenFromQuery = client.handshake?.query?.token;
    if (typeof tokenFromQuery === 'string' && tokenFromQuery.length > 0) {
      return tokenFromQuery;
    }

    const tokenFromAuth = client.handshake?.auth?.token;
    if (typeof tokenFromAuth === 'string' && tokenFromAuth.length > 0) {
      return tokenFromAuth;
    }

    return null;
  }

  verifyToken(token: string): JwtPayload {
    try {
      return verify(token, this.jwtSecret) as JwtPayload;
    } catch (error) {
      throw new UnauthorizedException('Token inválido o expirado');
    }
  }

  async authenticateClient(client: Socket): Promise<ConnectedUser> {
    const token = this.extractToken(client);
    if (!token) {
      throw new UnauthorizedException('Token requerido para iniciar la conexión');
    }

    const payload = this.verifyToken(token);
    if (!payload?.sub) {
      throw new UnauthorizedException('El token no incluye el identificador de usuario');
    }

    const user = await this.usersService.findById(Number(payload.sub));
    const nivelPrioridad = user.tipoUsuario?.nivelPrioridad ?? 99;

    return {
      id: user.id,
      email: user.email,
      nombre: user.nombre,
      apellido: user.apellido,
      tipoUsuarioId: user.tipoUsuarioId,
      nivelPrioridad,
      avatarUrl: user.avatarUrl,
      role: nivelPrioridad === 1 ? 'admin' : 'user',
    };
  }
}

import { Injectable, UnauthorizedException } from '@nestjs/common';
import { PassportStrategy } from '@nestjs/passport';
import { ExtractJwt, Strategy } from 'passport-jwt';
import { ConfigService } from '@nestjs/config';
import { UsersService } from '../../users/users.service';
import { RedisService } from '../../redis/redis.service';
import { JwtPayload } from '../interfaces/auth.interface';

@Injectable()
export class JwtStrategy extends PassportStrategy(Strategy) {
  constructor(
    private readonly configService: ConfigService,
    private readonly usersService: UsersService,
    private readonly redisService: RedisService,
  ) {
    super({
      jwtFromRequest: ExtractJwt.fromAuthHeaderAsBearerToken(),
      ignoreExpiration: false,
      secretOrKey: configService.get<string>('JWT_SECRET'),
      passReqToCallback: true, // Para acceder al token completo
    });
  }

  async validate(req: any, payload: JwtPayload) {
    // Validar que el token no esté en blacklist
    const token = ExtractJwt.fromAuthHeaderAsBearerToken()(req);
    if (token) {
      const isBlacklisted = await this.redisService.isTokenBlacklisted(token);
      if (isBlacklisted) {
        throw new UnauthorizedException('Token revocado');
      }
    }

    // Validar que sea un access token
    if (payload.type !== 'access') {
      throw new UnauthorizedException('Token inválido');
    }

    // Obtener usuario de la base de datos
    const user = await this.usersService.findById(payload.sub);
    if (!user) {
      throw new UnauthorizedException('Usuario no encontrado');
    }

    // Validar que el usuario esté activo
    if (user.estado !== 'activo') {
      throw new UnauthorizedException('Usuario inactivo o bloqueado');
    }

    // Retornar usuario (se agrega a request.user)
    return {
      id: user.id,
      email: user.email,
      nombre: user.nombre,
      apellido: user.apellido,
      tipoUsuarioId: user.tipoUsuarioId,
      estado: user.estado,
    };
  }
}
import { Injectable, Logger } from '@nestjs/common';
import { InjectRepository } from '@nestjs/typeorm';
import { Repository } from 'typeorm';
import { JwtService } from '@nestjs/jwt';
import { ConfigService } from '@nestjs/config';
import { RefreshToken } from './entities/refresh-token.entity';
import { UsersService } from '../users/users.service';
import { RedisService } from '../redis/redis.service';

@Injectable()
export class AuthService {
  private readonly logger = new Logger(AuthService.name);

  constructor(
    @InjectRepository(RefreshToken)
    private readonly refreshTokenRepository: Repository<RefreshToken>,
    private readonly usersService: UsersService,
    private readonly jwtService: JwtService,
    private readonly configService: ConfigService,
    private readonly redisService: RedisService,
  ) {}

  /**
   * Generate JWT Access Token
   */
  async generateAccessToken(userId: number, email: string, tipoUsuarioId: number): Promise<string> {
    const payload = {
      sub: userId,
      email,
      tipo_usuario_id: tipoUsuarioId,
      type: 'access',
    };

    return this.jwtService.sign(payload);
  }

  /**
   * Generate JWT Refresh Token
   */
  async generateRefreshToken(
    userId: number,
    email: string,
    ipAddress?: string,
    userAgent?: string,
  ): Promise<string> {
    const payload = {
      sub: userId,
      email,
      type: 'refresh',
    };

    const expiresIn = this.configService.get<string>('JWT_REFRESH_EXPIRATION', '7d');
    const refreshToken = this.jwtService.sign(payload, { expiresIn });

    // Calculate expiration date
    const expiresAt = new Date();
    const daysMatch = expiresIn.match(/(\d+)d/);
    if (daysMatch) {
      expiresAt.setDate(expiresAt.getDate() + parseInt(daysMatch[1], 10));
    }

    // Store in database
    const tokenEntity = this.refreshTokenRepository.create({
      token: refreshToken,
      usuarioId: userId,
      expiraEn: expiresAt,
      revocado: false,
      ipAddress,
      userAgent,
    });

    await this.refreshTokenRepository.save(tokenEntity);
    this.logger.debug(`Refresh token generated for user ${userId}`);

    return refreshToken;
  }

  /**
   * Validate and decode token
   */
  async validateToken(token: string): Promise<any> {
    try {
      return this.jwtService.verify(token);
    } catch (error) {
      return null;
    }
  }

  /**
   * Check if refresh token is valid in database
   */
  async isRefreshTokenValid(token: string): Promise<boolean> {
    const tokenEntity = await this.refreshTokenRepository.findOne({
      where: { token, revocado: false },
    });

    if (!tokenEntity) return false;

    // Check if expired
    const now = new Date();
    if (now > tokenEntity.expiraEn) {
      return false;
    }

    return true;
  }

  /**
   * Revoke refresh token
   */
  async revokeRefreshToken(token: string): Promise<void> {
    await this.refreshTokenRepository.update(
      { token },
      { revocado: true },
    );
    this.logger.debug(`Refresh token revoked: ${token.substring(0, 20)}...`);
  }

  /**
   * Revoke all refresh tokens for a user
   */
  async revokeAllUserRefreshTokens(userId: number): Promise<void> {
    await this.refreshTokenRepository.update(
      { usuarioId: userId, revocado: false },
      { revocado: true },
    );
    this.logger.log(`All refresh tokens revoked for user ${userId}`);
  }

  /**
   * Clean expired tokens (can be run as a scheduled job)
   */
  async cleanExpiredTokens(): Promise<void> {
    const result = await this.refreshTokenRepository
      .createQueryBuilder()
      .delete()
      .where('expira_en < :now', { now: new Date() })
      .execute();

    this.logger.log(`Cleaned ${result.affected} expired refresh tokens`);
  }
}

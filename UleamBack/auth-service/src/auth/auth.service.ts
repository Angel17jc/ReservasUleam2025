import {
  Injectable,
  Logger,
  UnauthorizedException,
  ConflictException,
  BadRequestException,
} from '@nestjs/common';
import { InjectRepository } from '@nestjs/typeorm';
import { Repository } from 'typeorm';
import { JwtService } from '@nestjs/jwt';
import { ConfigService } from '@nestjs/config';
import { RefreshToken } from './entities/refresh-token.entity';
import { UsersService } from '../users/users.service';
import { RedisService } from '../redis/redis.service';
import { RegisterDto } from './dto/register.dto';
import { LoginDto } from './dto/login.dto';
import { TokenResponse, UserResponse } from './interfaces/auth.interface';

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
   * Register a new user
   */
  async register(
    registerDto: RegisterDto,
    ipAddress?: string,
    userAgent?: string,
  ): Promise<TokenResponse & { user: UserResponse }> {
    try {
      // Create user (UsersService already validates email uniqueness)
      const user = await this.usersService.create({
        nombre: registerDto.nombre,
        apellido: registerDto.apellido,
        email: registerDto.email,
        password: registerDto.password,
        tipoUsuarioId: registerDto.tipoUsuarioId,
        telefono: registerDto.telefono,
      });

      // Generate tokens
      const accessToken = await this.generateAccessToken(
        user.id,
        user.email,
        user.tipoUsuarioId,
      );

      const refreshToken = await this.generateRefreshToken(
        user.id,
        user.email,
        ipAddress,
        userAgent,
      );

      this.logger.log(`Usuario registrado exitosamente: ${user.email} (ID: ${user.id})`);

      // Return user data without sensitive fields
      const userResponse: UserResponse = {
        id: user.id,
        nombre: user.nombre,
        apellido: user.apellido,
        email: user.email,
        tipoUsuarioId: user.tipoUsuarioId,
        telefono: user.telefono,
        avatarUrl: user.avatarUrl,
        estado: user.estado,
        creadoEn: user.creadoEn,
      };

      return {
        user: userResponse,
        accessToken,
        refreshToken,
        expiresIn: 900, // 15 minutes in seconds
        tokenType: 'Bearer',
      };
    } catch (error) {
      if (error instanceof ConflictException) {
        throw error;
      }
      this.logger.error(`Error en registro: ${error.message}`, error.stack);
      throw new BadRequestException('Error al registrar usuario');
    }
  }

  /**
   * Login user with credentials
   */
  async login(
    loginDto: LoginDto,
    ipAddress?: string,
    userAgent?: string,
  ): Promise<TokenResponse & { user: UserResponse }> {
    const { email, password } = loginDto;

    try {
      // Find user by email
      const user = await this.usersService.findByEmail(email.toLowerCase());

      if (!user) {
        this.logger.warn(`Intento de login fallido: usuario no encontrado (${email})`);
        throw new UnauthorizedException('Credenciales inválidas');
      }

      // Check if user is blocked
      const isBlocked = await this.usersService.isUserBlocked(user);
      if (isBlocked) {
        const blockedUntil = user.bloqueadoHasta?.toLocaleString('es-ES');
        this.logger.warn(`Intento de login con usuario bloqueado: ${email}`);
        throw new UnauthorizedException(
          `Cuenta bloqueada temporalmente. Inténtelo de nuevo después de ${blockedUntil}`,
        );
      }

      // Check if user is active
      if (user.estado !== 'activo') {
        this.logger.warn(`Intento de login con usuario inactivo o bloqueado: ${email}`);
        throw new UnauthorizedException('Cuenta desactivada o bloqueada. Contacte al administrador');
      }

      // Validate password
      const isPasswordValid = await this.usersService.validatePassword(user, password);

      if (!isPasswordValid) {
        // Increment failed login attempts
        await this.usersService.incrementFailedLoginAttempts(user.id);
        this.logger.warn(`Contraseña incorrecta para usuario: ${email}`);
        throw new UnauthorizedException('Credenciales inválidas');
      }

      // Update last login timestamp
      await this.usersService.updateLastLogin(user.id);

      // Generate tokens
      const accessToken = await this.generateAccessToken(
        user.id,
        user.email,
        user.tipoUsuarioId,
      );

      const refreshToken = await this.generateRefreshToken(
        user.id,
        user.email,
        ipAddress,
        userAgent,
      );

      this.logger.log(`Login exitoso: ${user.email} (ID: ${user.id})`);

      // Return user data without sensitive fields
      const userResponse: UserResponse = {
        id: user.id,
        nombre: user.nombre,
        apellido: user.apellido,
        email: user.email,
        tipoUsuarioId: user.tipoUsuarioId,
        telefono: user.telefono,
        avatarUrl: user.avatarUrl,
        estado: user.estado,
        creadoEn: user.creadoEn,
      };

      return {
        user: userResponse,
        accessToken,
        refreshToken,
        expiresIn: 900, // 15 minutes in seconds
        tokenType: 'Bearer',
      };
    } catch (error) {
      if (
        error instanceof UnauthorizedException ||
        error instanceof BadRequestException
      ) {
        throw error;
      }
      this.logger.error(`Error en login: ${error.message}`, error.stack);
      throw new UnauthorizedException('Error al iniciar sesión');
    }
  }

  /**
   * Generate JWT Access Token
   */
  async generateAccessToken(userId: number, email: string, tipoUsuarioId: number): Promise<string> {
    const payload = {
      sub: String(userId),  // Convert to string for compatibility with python-jose
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
      sub: String(userId),  // Convert to string for compatibility with python-jose
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
   * Validate token for P1 services (REST/GraphQL/WebSocket)
   * Returns user info if token is valid, null otherwise
   */
  async validateTokenForP1(token: string): Promise<{
    valid: boolean;
    user?: any;
    error?: string;
  }> {
    try {
      // Verify JWT signature and expiration
      const payload = await this.validateToken(token);
      if (!payload) {
        return { valid: false, error: 'Invalid or expired token' };
      }

      // Check if token is blacklisted
      const isBlacklisted = await this.redisService.isTokenBlacklisted(token);
      if (isBlacklisted) {
        return { valid: false, error: 'Token has been revoked' };
      }

      // Validate token type
      if (payload.type !== 'access') {
        return { valid: false, error: 'Invalid token type' };
      }

      // Get user from database
      const user = await this.usersService.findById(payload.sub);
      if (!user) {
        return { valid: false, error: 'User not found' };
      }

      // Check user status
      if (user.estado !== 'activo') {
        return { valid: false, error: 'User account is inactive or blocked' };
      }

      // Return user info
      return {
        valid: true,
        user: {
          id: user.id,
          email: user.email,
          nombre: user.nombre,
          apellido: user.apellido,
          tipoUsuarioId: user.tipoUsuarioId,
          estado: user.estado,
        },
      };
    } catch (error) {
      this.logger.error(`Token validation error: ${error.message}`);
      return { valid: false, error: 'Token validation failed' };
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
   * Refresh access token using refresh token
   */
  async refreshAccessToken(
    refreshToken: string,
    ipAddress?: string,
    userAgent?: string,
  ): Promise<TokenResponse> {
    try {
      // Validate refresh token format
      const payload = await this.validateToken(refreshToken);
      if (!payload || payload.type !== 'refresh') {
        throw new UnauthorizedException('Refresh token inválido');
      }

      // Check if refresh token exists in database and is not revoked
      const isValid = await this.isRefreshTokenValid(refreshToken);
      if (!isValid) {
        throw new UnauthorizedException('Refresh token expirado o revocado');
      }

      // Get user
      const user = await this.usersService.findById(payload.sub);
      if (!user) {
        throw new UnauthorizedException('Usuario no encontrado');
      }

      if (user.estado !== 'activo') {
        throw new UnauthorizedException('Usuario desactivado o bloqueado');
      }

      // Generate new access token
      const newAccessToken = await this.generateAccessToken(
        user.id,
        user.email,
        user.tipoUsuarioId,
      );

      // Optionally generate new refresh token (rotation)
      const newRefreshToken = await this.generateRefreshToken(
        user.id,
        user.email,
        ipAddress,
        userAgent,
      );

      // Revoke old refresh token
      await this.revokeRefreshToken(refreshToken);

      this.logger.log(`Access token refreshed for user ${user.id}`);

      return {
        accessToken: newAccessToken,
        refreshToken: newRefreshToken,
        expiresIn: 900, // 15 minutes
        tokenType: 'Bearer',
      };
    } catch (error) {
      if (error instanceof UnauthorizedException) {
        throw error;
      }
      this.logger.error(`Error refreshing token: ${error.message}`, error.stack);
      throw new UnauthorizedException('Error al refrescar token');
    }
  }

  /**
   * Logout user - revoke tokens and add to blacklist
   */
  async logout(userId: number, accessToken: string): Promise<{ message: string }> {
    try {
      // Revoke all refresh tokens for user
      await this.revokeAllUserRefreshTokens(userId);

      // Add access token to blacklist
      // Calculate remaining TTL (15 minutes = 900 seconds)
      const ttl = 900;
      await this.redisService.blacklistToken(accessToken, ttl);

      this.logger.log(`User ${userId} logged out successfully`);

      return { message: 'Sesión cerrada exitosamente' };
    } catch (error) {
      this.logger.error(`Error during logout: ${error.message}`, error.stack);
      throw new UnauthorizedException('Error al cerrar sesión');
    }
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
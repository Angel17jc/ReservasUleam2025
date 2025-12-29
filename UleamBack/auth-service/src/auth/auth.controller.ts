import {
  Controller,
  Post,
  Get,
  Body,
  HttpCode,
  HttpStatus,
  Ip,
  Headers,
  UseGuards,
  Request,
} from '@nestjs/common';
import { ApiTags, ApiOperation, ApiResponse, ApiBadRequestResponse, ApiUnauthorizedResponse, ApiBearerAuth, ApiSecurity } from '@nestjs/swagger';
import { Throttle } from '@nestjs/throttler';
import { AuthService } from './auth.service';
import { RegisterDto } from './dto/register.dto';
import { LoginDto } from './dto/login.dto';
import { RefreshTokenDto } from './dto/refresh-token.dto';
import { ValidateTokenDto } from './dto/validate-token.dto';
import { JwtAuthGuard } from './guards/jwt-auth.guard';

@ApiTags('auth')
@Controller('auth')
export class AuthController {
  constructor(private readonly authService: AuthService) {}

  @Post('register')
  @HttpCode(HttpStatus.CREATED)
  @ApiOperation({ 
    summary: 'Registrar nuevo usuario',
    description: 'Crea un nuevo usuario en el sistema con validación de datos y hash de contraseña'
  })
  @ApiResponse({ 
    status: 201, 
    description: 'Usuario registrado exitosamente con tokens JWT',
    schema: {
      example: {
        user: {
          id: 1,
          nombre: 'Juan',
          apellido: 'Pérez',
          email: 'juan.perez@uleam.edu.ec',
          tipoUsuarioId: 2,
          estado: 'activo'
        },
        accessToken: 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...',
        refreshToken: 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...',
        expiresIn: 900
      }
    }
  })
  @ApiBadRequestResponse({ description: 'Datos inválidos o email ya registrado' })
  async register(
    @Body() registerDto: RegisterDto,
    @Ip() ip: string,
    @Headers('user-agent') userAgent: string,
  ) {
    return await this.authService.register(registerDto, ip, userAgent);
  }

  @Post('login')
  @HttpCode(HttpStatus.OK)
  @Throttle({ default: { limit: 5, ttl: 60000 } }) // 5 intentos por minuto
  @ApiOperation({ 
    summary: 'Iniciar sesión',
    description: 'Autentica un usuario y retorna tokens JWT. Protegido con rate limiting (5 req/min)'
  })
  @ApiResponse({ 
    status: 200, 
    description: 'Login exitoso con tokens JWT',
    schema: {
      example: {
        user: {
          id: 1,
          nombre: 'Juan',
          apellido: 'Pérez',
          email: 'juan.perez@uleam.edu.ec',
          tipoUsuarioId: 2,
          estado: 'activo',
          ultimoLogin: '2026-01-10T21:00:00.000Z'
        },
        accessToken: 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...',
        refreshToken: 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...',
        expiresIn: 900
      }
    }
  })
  @ApiUnauthorizedResponse({ description: 'Credenciales inválidas o cuenta bloqueada' })
  @ApiBadRequestResponse({ description: 'Datos de login inválidos' })
  async login(
    @Body() loginDto: LoginDto,
    @Ip() ip: string,
    @Headers('user-agent') userAgent: string,
  ) {
    return await this.authService.login(loginDto, ip, userAgent);
  }

  @Post('refresh')
  @HttpCode(HttpStatus.OK)
  @ApiOperation({ 
    summary: 'Refrescar access token',
    description: 'Genera un nuevo access token usando un refresh token válido. Implementa rotation de refresh tokens.'
  })
  @ApiResponse({ 
    status: 200, 
    description: 'Token refrescado exitosamente',
    schema: {
      example: {
        accessToken: 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...',
        refreshToken: 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...',
        expiresIn: 900,
        tokenType: 'Bearer'
      }
    }
  })
  @ApiUnauthorizedResponse({ description: 'Refresh token inválido, expirado o revocado' })
  async refresh(
    @Body() refreshTokenDto: RefreshTokenDto,
    @Ip() ip: string,
    @Headers('user-agent') userAgent: string,
  ) {
    return await this.authService.refreshAccessToken(
      refreshTokenDto.refreshToken,
      ip,
      userAgent,
    );
  }

  @Post('logout')
  @HttpCode(HttpStatus.OK)
  @UseGuards(JwtAuthGuard)
  @ApiBearerAuth('access-token')
  @ApiOperation({ 
    summary: 'Cerrar sesión',
    description: 'Revoca todos los refresh tokens del usuario y agrega el access token a blacklist'
  })
  @ApiResponse({ 
    status: 200, 
    description: 'Sesión cerrada exitosamente',
    schema: {
      example: {
        message: 'Sesión cerrada exitosamente'
      }
    }
  })
  @ApiUnauthorizedResponse({ description: 'Token inválido o expirado' })
  async logout(
    @Request() req: any,
    @Headers('authorization') authorization: string,
  ) {
    // Extraer token del header Authorization
    const token = authorization?.replace('Bearer ', '');
    return await this.authService.logout(req.user.id, token);
  }

  @Get('me')
  @UseGuards(JwtAuthGuard)
  @ApiBearerAuth('access-token')
  @ApiOperation({ 
    summary: 'Obtener perfil del usuario autenticado',
    description: 'Retorna la información del usuario actual basado en el JWT'
  })
  @ApiResponse({ 
    status: 200, 
    description: 'Perfil del usuario',
    schema: {
      example: {
        id: 1,
        nombre: 'Juan',
        apellido: 'Pérez',
        email: 'juan.perez@uleam.edu.ec',
        tipoUsuarioId: 2,
        estado: 'activo'
      }
    }
  })
  @ApiUnauthorizedResponse({ description: 'Token inválido o expirado' })
  async getProfile(@Request() req: any) {
    return req.user;
  }

  /**
   * Endpoint de validaci�n para servicios P1
   * Permite a REST, GraphQL y WebSocket verificar tokens JWT
   */
  @Post('validate')
  @HttpCode(HttpStatus.OK)
  @ApiOperation({ 
    summary: 'Validar token JWT (Para servicios P1)',
    description: 'Endpoint para que servicios REST, GraphQL y WebSocket validen tokens JWT. Verifica firma, expiraci�n, blacklist y estado del usuario.'
  })
  @ApiResponse({ 
    status: 200, 
    description: 'Token validado correctamente',
    schema: {
      example: {
        valid: true,
        user: {
          id: 1,
          email: 'juan.perez@uleam.edu.ec',
          nombre: 'Juan',
          apellido: 'P�rez',
          tipoUsuarioId: 2,
          estado: 'activo'
        }
      }
    }
  })
  @ApiResponse({ 
    status: 200, 
    description: 'Token inv�lido',
    schema: {
      example: {
        valid: false,
        error: 'Token expirado'
      }
    }
  })
  @ApiBadRequestResponse({ description: 'Datos de entrada inv�lidos' })
  async validateToken(@Body() validateTokenDto: ValidateTokenDto) {
    return await this.authService.validateTokenForP1(validateTokenDto.token);
  }

  /**
   * Endpoint para obtener configuraci�n p�blica del JWT
   * Permite a servicios P1 conocer la configuraci�n del emisor
   */
  @Get('public-key')
  @HttpCode(HttpStatus.OK)
  @ApiOperation({ 
    summary: 'Obtener configuraci�n p�blica JWT',
    description: 'Retorna informaci�n p�blica sobre la configuraci�n JWT (algoritmo, issuer, expiraci�n). �til para servicios P1.'
  })
  @ApiResponse({ 
    status: 200, 
    description: 'Configuraci�n p�blica del JWT',
    schema: {
      example: {
        algorithm: 'HS256',
        issuer: 'auth-service',
        accessTokenExpiration: '15m',
        refreshTokenExpiration: '7d'
      }
    }
  })
  async getPublicKey() {
    return {
      algorithm: 'HS256',
      issuer: 'auth-service',
      accessTokenExpiration: '15m',
      refreshTokenExpiration: '7d'
    };
  }
}
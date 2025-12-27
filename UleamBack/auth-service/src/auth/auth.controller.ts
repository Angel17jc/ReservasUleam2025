import {
  Controller,
  Post,
  Body,
  HttpCode,
  HttpStatus,
  Ip,
  Headers,
} from '@nestjs/common';
import { ApiTags, ApiOperation, ApiResponse, ApiBadRequestResponse, ApiUnauthorizedResponse } from '@nestjs/swagger';
import { Throttle } from '@nestjs/throttler';
import { AuthService } from './auth.service';
import { RegisterDto } from './dto/register.dto';
import { LoginDto } from './dto/login.dto';

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
          activo: true
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
          activo: true,
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
  @ApiOperation({ summary: 'Refrescar access token' })
  @ApiOperation({ description: 'Se implementará completamente en Commit 3' })
  async refresh() {
    return { message: 'Endpoint disponible en Commit 3' };
  }

  @Post('logout')
  @HttpCode(HttpStatus.OK)
  @ApiOperation({ summary: 'Cerrar sesión' })
  @ApiOperation({ description: 'Se implementará completamente en Commit 3' })
  async logout() {
    return { message: 'Endpoint disponible en Commit 3' };
  }
}
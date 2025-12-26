import { Controller, Post, Body } from '@nestjs/common';
import { ApiTags, ApiOperation } from '@nestjs/swagger';
import { AuthService } from './auth.service';

@ApiTags('auth')
@Controller('auth')
export class AuthController {
  constructor(private readonly authService: AuthService) {}

  @Post('register')
  @ApiOperation({ summary: 'Registrar nuevo usuario' })
  @ApiOperation({ description: 'Se implementará completamente en Commit 2' })
  async register() {
    return { message: 'Endpoint disponible en Commit 2' };
  }

  @Post('login')
  @ApiOperation({ summary: 'Iniciar sesión' })
  @ApiOperation({ description: 'Se implementará completamente en Commit 2' })
  async login() {
    return { message: 'Endpoint disponible en Commit 2' };
  }

  @Post('refresh')
  @ApiOperation({ summary: 'Refrescar access token' })
  @ApiOperation({ description: 'Se implementará completamente en Commit 3' })
  async refresh() {
    return { message: 'Endpoint disponible en Commit 3' };
  }

  @Post('logout')
  @ApiOperation({ summary: 'Cerrar sesión' })
  @ApiOperation({ description: 'Se implementará completamente en Commit 3' })
  async logout() {
    return { message: 'Endpoint disponible en Commit 3' };
  }
}

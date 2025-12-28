import { Controller, Get, UseGuards, Request } from '@nestjs/common';
import { ApiTags, ApiBearerAuth, ApiOperation, ApiResponse, ApiUnauthorizedResponse } from '@nestjs/swagger';
import { JwtAuthGuard } from '../auth/guards/jwt-auth.guard';
import { UsersService } from './users.service';

@ApiTags('users')
@Controller('users')
export class UsersController {
  constructor(private readonly usersService: UsersService) {}

  @Get('me')
  @UseGuards(JwtAuthGuard)
  @ApiBearerAuth('access-token')
  @ApiOperation({ 
    summary: 'Obtener perfil del usuario autenticado',
    description: 'Retorna información completa del usuario actual'
  })
  @ApiResponse({
    status: 200,
    description: 'Perfil del usuario con datos completos',
    schema: {
      example: {
        id: 1,
        nombre: 'Juan',
        apellido: 'Pérez',
        email: 'juan.perez@uleam.edu.ec',
        tipoUsuarioId: 2,
        telefono: '0987654321',
        avatarUrl: null,
        estado: 'activo',
        creadoEn: '2026-01-10T...',
        ultimoLogin: '2026-01-10T...'
      }
    }
  })
  @ApiUnauthorizedResponse({ description: 'Token inválido o expirado' })
  async getProfile(@Request() req: any) {
    const user = await this.usersService.findById(req.user.id);
    
    if (!user) {
      return { message: 'Usuario no encontrado' };
    }
    
    // Remover información sensible
    const { passwordHash, intentosFallidosLogin, bloqueadoHasta, ...userResponse } = user as any;
    
    return userResponse;
  }
}
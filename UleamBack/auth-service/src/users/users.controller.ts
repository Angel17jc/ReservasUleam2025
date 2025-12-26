import { Controller, Get, UseGuards, Request } from '@nestjs/common';
import { ApiTags, ApiBearerAuth, ApiOperation } from '@nestjs/swagger';
import { UsersService } from './users.service';

@ApiTags('users')
@Controller('users')
export class UsersController {
  constructor(private readonly usersService: UsersService) {}

  @Get('me')
  @ApiOperation({ summary: 'Obtener perfil del usuario autenticado' })
  @ApiOperation({ description: 'Endpoint protegido - requiere autenticación en Commit 3' })
  async getProfile() {
    // Este endpoint se implementará completamente en Commit 3 con JWT Guard
    return { message: 'Endpoint disponible en Commit 3' };
  }
}

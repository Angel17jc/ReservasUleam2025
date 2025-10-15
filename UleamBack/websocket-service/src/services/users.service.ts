import { Injectable, NotFoundException } from '@nestjs/common';
import { InjectRepository } from '@nestjs/typeorm';
import { Repository } from 'typeorm';
import { Usuario } from '../entities/usuario.entity';

@Injectable()
export class UsersService {
  constructor(
    @InjectRepository(Usuario)
    private readonly usersRepository: Repository<Usuario>,
  ) {}

  async findById(userId: number): Promise<Usuario> {
    const user = await this.usersRepository.findOne({
      where: { id: userId },
      relations: { tipoUsuario: true },
    });
    if (!user) {
      throw new NotFoundException('Usuario no encontrado para el token recibido');
    }
    return user;
  }
}

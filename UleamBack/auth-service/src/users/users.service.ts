import {
  Injectable,
  NotFoundException,
  ConflictException,
  Logger,
} from '@nestjs/common';
import { InjectRepository } from '@nestjs/typeorm';
import { Repository } from 'typeorm';
import { User } from './entities/user.entity';
import * as bcrypt from 'bcrypt';
import { ConfigService } from '@nestjs/config';

@Injectable()
export class UsersService {
  private readonly logger = new Logger(UsersService.name);

  constructor(
    @InjectRepository(User)
    private readonly userRepository: Repository<User>,
    private readonly configService: ConfigService,
  ) {}

  /**
   * Find user by ID
   */
  async findById(id: number): Promise<User | null> {
    return await this.userRepository.findOne({ where: { id } });
  }

  /**
   * Find user by email
   */
  async findByEmail(email: string): Promise<User | null> {
    return await this.userRepository.findOne({ where: { email } });
  }

  /**
   * Find user by email or throw exception
   */
  async findByEmailOrFail(email: string): Promise<User> {
    const user = await this.findByEmail(email);
    if (!user) {
      throw new NotFoundException(`Usuario con email ${email} no encontrado`);
    }
    return user;
  }

  /**
   * Create a new user
   */
  async create(userData: {
    nombre: string;
    apellido: string;
    email: string;
    password: string;
    tipoUsuarioId: number;
    telefono?: string;
  }): Promise<User> {
    // Check if email already exists
    const existingUser = await this.findByEmail(userData.email);
    if (existingUser) {
      throw new ConflictException(`El email ${userData.email} ya está registrado`);
    }

    // Hash password
    const bcryptRounds = this.configService.get<number>('BCRYPT_ROUNDS', 12);
    const passwordHash = await bcrypt.hash(userData.password, bcryptRounds);

    // Create user entity
    const user = this.userRepository.create({
      nombre: userData.nombre,
      apellido: userData.apellido,
      email: userData.email.toLowerCase(),
      passwordHash,
      tipoUsuarioId: userData.tipoUsuarioId,
      telefono: userData.telefono || null,
      activo: true,
      intentosFallidosLogin: 0,
    });

    const savedUser = await this.userRepository.save(user);
    this.logger.log(`Usuario creado: ${savedUser.email} (ID: ${savedUser.id})`);

    return savedUser;
  }

  /**
   * Validate user password
   */
  async validatePassword(user: User, password: string): Promise<boolean> {
    return await bcrypt.compare(password, user.passwordHash);
  }

  /**
   * Update user's last login timestamp
   */
  async updateLastLogin(userId: number): Promise<void> {
    await this.userRepository.update(userId, {
      ultimoLogin: new Date(),
      intentosFallidosLogin: 0,
    });
  }

  /**
   * Increment failed login attempts
   */
  async incrementFailedLoginAttempts(userId: number): Promise<void> {
    const user = await this.findById(userId);
    if (!user) return;

    const failedAttempts = user.intentosFallidosLogin + 1;
    const updateData: any = { intentosFallidosLogin: failedAttempts };

    // Block user for 15 minutes after 5 failed attempts
    if (failedAttempts >= 5) {
      const blockUntil = new Date();
      blockUntil.setMinutes(blockUntil.getMinutes() + 15);
      updateData.bloqueadoHasta = blockUntil;
      this.logger.warn(`Usuario ${user.email} bloqueado hasta ${blockUntil}`);
    }

    await this.userRepository.update(userId, updateData);
  }

  /**
   * Check if user is blocked
   */
  async isUserBlocked(user: User): Promise<boolean> {
    if (!user.bloqueadoHasta) return false;
    
    const now = new Date();
    if (now < user.bloqueadoHasta) {
      return true;
    }

    // Unblock user if time has passed
    await this.userRepository.update(user.id, {
      bloqueadoHasta: null,
      intentosFallidosLogin: 0,
    });

    return false;
  }

  /**
   * Update user data
   */
  async update(
    userId: number,
    updateData: Partial<Omit<User, 'id' | 'passwordHash'>>,
  ): Promise<User> {
    const user = await this.findById(userId);
    if (!user) {
      throw new NotFoundException(`Usuario con ID ${userId} no encontrado`);
    }

    await this.userRepository.update(userId, updateData);
    
    const updatedUser = await this.findById(userId);
    if (!updatedUser) {
      throw new NotFoundException(`Error al obtener usuario actualizado`);
    }
    
    return updatedUser;
  }

  /**
   * Change user password
   */
  async changePassword(userId: number, newPassword: string): Promise<void> {
    const bcryptRounds = this.configService.get<number>('BCRYPT_ROUNDS', 12);
    const passwordHash = await bcrypt.hash(newPassword, bcryptRounds);

    await this.userRepository.update(userId, { passwordHash });
    this.logger.log(`Contraseña actualizada para usuario ID: ${userId}`);
  }

  /**
   * Deactivate user account
   */
  async deactivate(userId: number): Promise<void> {
    await this.userRepository.update(userId, { activo: false });
    this.logger.log(`Usuario ID: ${userId} desactivado`);
  }

  /**
   * Activate user account
   */
  async activate(userId: number): Promise<void> {
    await this.userRepository.update(userId, { activo: true });
    this.logger.log(`Usuario ID: ${userId} activado`);
  }
}

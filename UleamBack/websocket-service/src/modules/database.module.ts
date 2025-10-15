import { Module } from '@nestjs/common';
import { TypeOrmModule } from '@nestjs/typeorm';
import { ConfigModule } from '@nestjs/config';
import { Notification } from '../entities/notification.entity';
import { Usuario } from '../entities/usuario.entity';
import { TipoUsuario } from '../entities/tipo-usuario.entity';

@Module({
  imports: [
    ConfigModule.forRoot(),
    TypeOrmModule.forRoot({
      type: 'postgres',
      host: process.env.DB_HOST || 'localhost',
      port: parseInt(process.env.DB_PORT || '5432'),
      username: process.env.DB_USER || 'Reservas_ULEAM',
      password: process.env.DB_PASSWORD || '123456789',
      database: process.env.DB_NAME || 'reservasuleam',
      entities: [Notification, Usuario, TipoUsuario],
      synchronize: false, // No sincronizar automáticamente en producción
    }),
    TypeOrmModule.forFeature([Notification, Usuario, TipoUsuario])
  ],
  exports: [TypeOrmModule]
})
export class DatabaseModule {}

/**
 * App Module - Módulo raíz de la aplicación
 */
import { Module } from '@nestjs/common';
import { ConfigModule } from '@nestjs/config';
import { DatabaseModule } from './database/database.module';
import { PaymentModule } from './payment/payment.module';
import { HealthController } from './health.controller';

@Module({
  imports: [
    // Configuración global de variables de entorno
    ConfigModule.forRoot({
      isGlobal: true,
      envFilePath: '.env',
    }),
    // Base de datos
    DatabaseModule,
    // Módulo de pagos
    PaymentModule,
  ],
  controllers: [HealthController],
})
export class AppModule {}

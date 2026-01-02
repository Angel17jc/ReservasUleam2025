/**
 * Payment Service - Microservicio de Pagos
 * Sistema de Reservas ULEAM - Pilar 2
 * 
 * Punto de entrada principal de la aplicación NestJS.
 */
import { NestFactory } from '@nestjs/core';
import { ValidationPipe } from '@nestjs/common';
import { SwaggerModule, DocumentBuilder } from '@nestjs/swagger';
import { AppModule } from './app.module';

async function bootstrap() {
  const app = await NestFactory.create(AppModule);

  // Configurar CORS
  app.enableCors({
    origin: process.env.ALLOWED_ORIGINS?.split(',') || '*',
    credentials: true,
  });

  // Configurar validación global con class-validator
  app.useGlobalPipes(
    new ValidationPipe({
      whitelist: true,
      forbidNonWhitelisted: true,
      transform: true,
    }),
  );

  // Configurar Swagger/OpenAPI
  const config = new DocumentBuilder()
    .setTitle('Payment Service API')
    .setDescription(
      `Microservicio de procesamiento de pagos para el Sistema de Reservas ULEAM.
      
      **Características principales:**
      - Patrón Adapter para múltiples proveedores de pago
      - MockAdapter para desarrollo y testing
      - Soporte para Stripe, MercadoPago, etc.
      - PostgreSQL con TypeORM
      - Procesamiento asíncrono
      
      **Pilar 2 - Componentes:**
      1. ✅ Payment Service Wrapper (patrón Adapter)
      2. 🔄 Registro de Partners (próximamente)
      3. 🔄 Autenticación HMAC-SHA256 (próximamente)
      4. 🔄 Eventos bidireccionales con Tours (próximamente)`,
    )
    .setVersion('1.0.0')
    .addTag('health', 'Health check endpoints')
    .addTag('payments', 'Payment processing endpoints')
    .build();

  const document = SwaggerModule.createDocument(app, config);
  SwaggerModule.setup('api', app, document);

  const port = process.env.PORT || 9001;
  await app.listen(port);

  console.log('');
  console.log('🚀 Payment Service started successfully!');
  console.log(`📡 Running on: http://localhost:${port}`);
  console.log(`📚 Swagger docs: http://localhost:${port}/api`);
  console.log(`🔍 Health check: http://localhost:${port}/health`);
  console.log('');
}

bootstrap();

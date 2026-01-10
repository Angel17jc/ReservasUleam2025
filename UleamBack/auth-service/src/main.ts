import { NestFactory } from '@nestjs/core';
import { ValidationPipe, Logger } from '@nestjs/common';
import { DocumentBuilder, SwaggerModule } from '@nestjs/swagger';
import { ConfigService } from '@nestjs/config';
import helmet from 'helmet';
import { AppModule } from './app.module';
import { GlobalExceptionFilter } from './common/filters/global-exception.filter';
import { LoggingInterceptor } from './common/interceptors/logging.interceptor';

async function bootstrap() {
  const logger = new Logger('Bootstrap');
  const app = await NestFactory.create(AppModule);

  // Config Service
  const configService = app.get(ConfigService);
  const port = configService.get<number>('PORT', 9000);
  const apiPrefix = configService.get<string>('API_PREFIX', 'api/v1');
  const corsOriginEnv = configService.get<string>('CORS_ORIGIN', 'http://localhost:5173');

  // Security - Helmet
  app.use(helmet());

  // CORS
  // Support a single origin, a comma-separated list, or a function that validates origin.
  let corsOrigin: string | string[] | ((origin: string | undefined, callback: (err: Error | null, allow?: boolean) => void) => void) = corsOriginEnv;

  if (corsOriginEnv.includes(',')) {
    const allowed = corsOriginEnv.split(',').map((s) => s.trim());
    corsOrigin = (origin: string | undefined, callback: (err: Error | null, allow?: boolean) => void) => {
      if (!origin) return callback(null, true);
      if (allowed.indexOf(origin) !== -1) return callback(null, true);
      return callback(new Error('Not allowed by CORS'));
    };
  }

  app.enableCors({
    origin: corsOrigin,
    credentials: true,
    methods: ['GET', 'POST', 'PUT', 'PATCH', 'DELETE', 'OPTIONS'],
    allowedHeaders: ['Content-Type', 'Authorization', 'X-Requested-With'],
  });

  // Global Prefix
  app.setGlobalPrefix(apiPrefix);

  // Global Exception Filter
  app.useGlobalFilters(new GlobalExceptionFilter());

  // Global Logging Interceptor
  app.useGlobalInterceptors(new LoggingInterceptor());

  // Global Validation Pipe
  app.useGlobalPipes(
    new ValidationPipe({
      whitelist: true,
      forbidNonWhitelisted: true,
      transform: true,
      transformOptions: {
        enableImplicitConversion: true,
      },
    }),
  );

  // Swagger Documentation
  const config = new DocumentBuilder()
    .setTitle('Auth Service API')
    .setDescription('Servicio de Autenticación - Sistema de Reservas ULEAM')
    .setVersion('1.0')
    .addBearerAuth(
      {
        type: 'http',
        scheme: 'bearer',
        bearerFormat: 'JWT',
        name: 'JWT',
        description: 'Enter JWT token',
        in: 'header',
      },
      'access-token',
    )
    .addTag('auth', 'Endpoints de autenticación')
    .addTag('users', 'Endpoints de usuarios')
    .build();

  const document = SwaggerModule.createDocument(app, config);
  SwaggerModule.setup(`${apiPrefix}/docs`, app, document, {
    swaggerOptions: {
      persistAuthorization: true,
    },
  });

  await app.listen(port);

  logger.log(`🚀 Auth Service running on: http://localhost:${port}/${apiPrefix}`);
  logger.log(`📚 Swagger docs available at: http://localhost:${port}/${apiPrefix}/docs`);
  logger.log(`🌍 CORS enabled for: ${corsOrigin}`);
}

bootstrap();

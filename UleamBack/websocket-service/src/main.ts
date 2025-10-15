import { NestFactory } from '@nestjs/core';
import { AppModule } from './app.module';

async function bootstrap() {
  const app = await NestFactory.create(AppModule, {
    cors: {
      origin: '*',
      credentials: true,
    },
  });

  await app.listen(3001);
  console.log('🚀 WebSocket Service running on http://0.0.0.0:3001');
}

bootstrap();

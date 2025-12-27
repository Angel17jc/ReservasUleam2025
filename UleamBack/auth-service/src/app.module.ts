import { Module } from '@nestjs/common';
import { ConfigModule } from '@nestjs/config';
import { ThrottlerModule, ThrottlerGuard } from '@nestjs/throttler';
import { APP_GUARD } from '@nestjs/core';
import { DatabaseModule } from './database/database.module';
import { RedisModule } from './redis/redis.module';
import { AuthModule } from './auth/auth.module';
import { UsersModule } from './users/users.module';

@Module({
  imports: [
    // Configuration Module
    ConfigModule.forRoot({
      isGlobal: true,
      envFilePath: '.env',
      cache: true,
    }),

    // Rate Limiting Global
    ThrottlerModule.forRoot([
      {
        ttl: 60000, // 1 minute
        limit: 20, // 20 requests per minute (aumentado para permitir operaciones normales)
      },
    ]),

    // Custom Modules
    DatabaseModule,
    RedisModule,
    UsersModule,
    AuthModule,
  ],
  controllers: [],
  providers: [
    // Global rate limiting guard
    {
      provide: APP_GUARD,
      useClass: ThrottlerGuard,
    },
  ],
})
export class AppModule {}
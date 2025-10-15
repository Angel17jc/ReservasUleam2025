import { Module } from '@nestjs/common';
import { ConfigModule } from '@nestjs/config';
import { NotificationsGateway } from './gateways/notifications.gateway';
import { NotificationsController } from './controllers/notifications.controller';
import { DatabaseModule } from './modules/database.module';
import { UsersService } from './services/users.service';
import { SocketAuthService } from './services/socket-auth.service';
import { PresenceService } from './services/presence.service';
import { NotificationsService } from './services/notifications.service';

@Module({
  imports: [
    ConfigModule.forRoot({
      isGlobal: true,
    }),
    DatabaseModule,
  ],
  controllers: [NotificationsController],
  providers: [
    NotificationsGateway,
    UsersService,
    SocketAuthService,
    PresenceService,
    NotificationsService,
  ],
})
export class AppModule {}

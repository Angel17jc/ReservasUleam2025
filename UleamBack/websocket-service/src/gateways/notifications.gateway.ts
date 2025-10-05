import {
  WebSocketGateway,
  WebSocketServer,
  SubscribeMessage,
  OnGatewayConnection,
  OnGatewayDisconnect,
  MessageBody,
  ConnectedSocket,
  WsResponse,
} from '@nestjs/websockets';
import { Server, Socket } from 'socket.io';
import { Logger } from '@nestjs/common';
import {
  SubscriptionRequest,
  NotificationPayload,
  StatsUpdatePayload,
  DisponibilidadPayload,
  RecordatorioPayload,
  ConnectedUser,
} from '../interfaces/socket.interface';
import { SocketAuthService } from '../services/socket-auth.service';
import { PresenceService } from '../services/presence.service';
import { NotificationsService } from '../services/notifications.service';

@WebSocketGateway({
  cors: {
    origin: '*',
    credentials: true,
  },
  namespace: '/',
  pingInterval: 10000,
  pingTimeout: 5000,
})
export class NotificationsGateway
  implements OnGatewayConnection, OnGatewayDisconnect
{
  @WebSocketServer()
  server: Server;

  private readonly logger = new Logger(NotificationsGateway.name);

  constructor(
    private readonly socketAuthService: SocketAuthService,
    private readonly presenceService: PresenceService,
    private readonly notificationsService: NotificationsService,
  ) {}

  async handleConnection(client: Socket) {
    try {
      const user = await this.socketAuthService.authenticateClient(client);
      this.presenceService.registerConnection(client.id, user);
      client.data.user = user;

      this.joinDefaultChannels(client, user);

      client.emit('connected', {
        message: 'Conexión establecida con el servicio WebSocket',
        user,
        timestamp: new Date().toISOString(),
      });
      this.logger.log(`Client ${client.id} authenticated as user #${user.id}`);

      this.broadcastPresenceChange('usuario_online', user);
    } catch (error) {
      this.logger.warn(
        `Connection rejected for client ${client.id}: ${error.message}`,
      );
      client.emit('error', {
        message: 'No autorizado para abrir la conexión',
        details: error.message,
      });
      client.disconnect(true);
    }
  }

  handleDisconnect(client: Socket) {
    const user = this.presenceService.removeConnection(client.id);
    if (user) {
      this.logger.log(`Client ${client.id} disconnected (user #${user.id})`);
      this.broadcastPresenceChange('usuario_offline', user);
    }
  }

  @SubscribeMessage('ping')
  handlePing(@ConnectedSocket() client: Socket): WsResponse<{ pong: boolean }> {
    return { event: 'pong', data: { pong: true } };
  }

  @SubscribeMessage('subscribe')
  handleSubscribe(
    @MessageBody() data: SubscriptionRequest,
    @ConnectedSocket() client: Socket,
  ): void {
    if (!Array.isArray(data.channels)) {
      client.emit('error', { message: 'Formato inválido para canales' });
      return;
    }
    const user = this.presenceService.getUserFromSocket(client.id);
    if (!user) {
      client.emit('error', { message: 'Usuario no autenticado' });
      return;
    }

    const authorized: string[] = [];
    const rejected: string[] = [];

    data.channels.forEach((channel) => {
      if (this.canJoinChannel(channel, user)) {
        this.joinChannel(client, channel);
        authorized.push(channel);
      } else {
        rejected.push(channel);
      }
    });

    if (authorized.length > 0) {
      client.emit('subscribed', {
        channels: authorized,
        message: 'Suscripción correcta',
      });
    }
    if (rejected.length > 0) {
      client.emit('subscription_error', {
        channels: rejected,
        message: 'No tienes permiso para esos canales',
      });
    }
  }

  @SubscribeMessage('unsubscribe')
  handleUnsubscribe(
    @MessageBody() data: SubscriptionRequest,
    @ConnectedSocket() client: Socket,
  ): void {
    if (!Array.isArray(data.channels)) {
      client.emit('error', { message: 'Formato inválido para canales' });
      return;
    }
    data.channels.forEach((channel) => {
      client.leave(channel);
      this.presenceService.removeChannel(client.id, channel);
    });
    client.emit('unsubscribed', {
      channels: data.channels,
      message: 'Se cancelaron las suscripciones solicitadas',
    });
  }

  @SubscribeMessage('marcar_leida')
  async handleMarcarLeida(
    @MessageBody() data: { notificacion_id: number },
    @ConnectedSocket() client: Socket,
  ): Promise<void> {
    if (!data?.notificacion_id) {
      client.emit('error', { message: 'El id de la notificación es obligatorio' });
      return;
    }
    const user = this.presenceService.getUserFromSocket(client.id);
    if (!user) {
      client.emit('error', { message: 'Usuario no autenticado' });
      return;
    }
    try {
      const notification = await this.notificationsService.markAsRead(
        data.notificacion_id,
        user.id,
      );
      const payload = {
        notificacion_id: notification.id,
        leida_at: notification.leidaAt,
        timestamp: new Date().toISOString(),
      };
      client.emit('notificacion_leida', payload);
      this.emitToChannel(
        `notificaciones:user:${user.id}`,
        'notificacion_actualizada',
        payload,
      );
    } catch (error) {
      client.emit('error', { message: error.message });
    }
  }

  notifyReservaCreada(reservaData: any): void {
    const channels = [
      `notificaciones:user:${reservaData.usuario_id}`,
      `reservas:usuario:${reservaData.usuario_id}`,
      `reservas:espacio:${reservaData.espacio_id}`,
      'reservas:todas',
      'dashboard:admin',
    ];
    channels.forEach((channel) =>
      this.emitToChannel(channel, 'reserva_creada', reservaData),
    );
    this.emitDashboardStats();
  }

  notifyReservaActualizada(reservaData: any): void {
    const channels = [
      `notificaciones:user:${reservaData.usuario_id}`,
      `reservas:usuario:${reservaData.usuario_id}`,
      `reservas:espacio:${reservaData.espacio_id}`,
      'reservas:todas',
      'dashboard:admin',
    ];
    channels.forEach((channel) =>
      this.emitToChannel(channel, 'reserva_actualizada', reservaData),
    );

    const stateEvent = this.mapEstadoToEvent(reservaData?.nuevo_estado);
    if (stateEvent) {
      channels.forEach((channel) =>
        this.emitToChannel(channel, stateEvent, reservaData),
      );
    }
    this.emitDashboardStats();
  }

  notifyReservaCancelada(reservaData: any): void {
    const channels = [
      `notificaciones:user:${reservaData.usuario_id}`,
      `reservas:usuario:${reservaData.usuario_id}`,
      `reservas:espacio:${reservaData.espacio_id}`,
      'reservas:todas',
      'dashboard:admin',
    ];
    channels.forEach((channel) =>
      this.emitToChannel(channel, 'reserva_cancelada', reservaData),
    );
    this.emitDashboardStats();
  }

  notifyNuevaNotificacion(notificacionData: NotificationPayload): void {
    this.emitToChannel(
      `notificaciones:user:${notificacionData.usuario_id}`,
      'nueva_notificacion',
      notificacionData,
    );
  }

  notifyDisponibilidadActualizada(payload: DisponibilidadPayload): void {
    const channels = [
      `disponibilidad:espacio:${payload.espacio_id}`,
      'disponibilidad:all',
      'dashboard:admin',
    ];
    channels.forEach((channel) =>
      this.emitToChannel(channel, 'disponibilidad_actualizada', payload),
    );
  }

  notifyRecordatorio(payload: RecordatorioPayload): void {
    const channels = [
      `notificaciones:user:${payload.usuario_id}`,
      `reservas:usuario:${payload.usuario_id}`,
    ];
    channels.forEach((channel) =>
      this.emitToChannel(channel, 'recordatorio', payload),
    );
  }

  emitGlobalStats(data: StatsUpdatePayload): void {
    this.emitDashboardStats(data);
  }

  private emitDashboardStats(extra?: Partial<StatsUpdatePayload>): void {
    const presenceSnapshot = this.presenceService.getSnapshot();
    this.server.to('dashboard:admin').emit('stats_update', {
      ...presenceSnapshot,
      ...extra,
      timestamp: new Date().toISOString(),
    });
  }

  private broadcastPresenceChange(event: string, user: ConnectedUser): void {
    this.emitToChannel('dashboard:admin', event, {
      user_id: user.id,
      nombre: user.nombre,
      apellido: user.apellido,
      role: user.role,
    });
    this.emitDashboardStats();
  }

  private joinDefaultChannels(client: Socket, user: ConnectedUser): void {
    const defaults = [
      `notificaciones:user:${user.id}`,
      `reservas:usuario:${user.id}`,
    ];
    if (this.isAdmin(user)) {
      defaults.push('dashboard:admin', 'reservas:todas', 'disponibilidad:all');
    }
    defaults.forEach((channel) => this.joinChannel(client, channel));
  }

  private joinChannel(client: Socket, channel: string) {
    client.join(channel);
    this.presenceService.addChannel(client.id, channel);
    this.logger.debug(
      `Client ${client.id} joined channel ${channel} (${this.presenceService.getChannels(client.id).length} total)`,
    );
  }

  private canJoinChannel(channel: string, user: ConnectedUser): boolean {
    if (channel.startsWith('notificaciones:user:')) {
      const id = Number(channel.split(':').pop());
      return this.isAdmin(user) || id === user.id;
    }
    if (channel.startsWith('reservas:usuario:')) {
      const id = Number(channel.split(':').pop());
      return this.isAdmin(user) || id === user.id;
    }
    if (channel.startsWith('dashboard:')) {
      return this.isAdmin(user);
    }
    if (channel.startsWith('disponibilidad:all')) {
      return this.isAdmin(user);
    }
    return true;
  }

  private isAdmin(user: ConnectedUser): boolean {
    return user.nivelPrioridad === 1;
  }

  private mapEstadoToEvent(estado?: string): string | null {
    if (!estado) {
      return null;
    }
    const normalized = estado.toLowerCase();
    if (normalized === 'aprobada') {
      return 'reserva_aprobada';
    }
    if (normalized === 'rechazada') {
      return 'reserva_rechazada';
    }
    if (normalized === 'cancelada') {
      return 'reserva_cancelada';
    }
    return null;
  }

  private emitToChannel(channel: string, event: string, data: any): void {
    this.server.to(channel).emit(event, {
      ...data,
      timestamp: new Date().toISOString(),
    });
  }
}

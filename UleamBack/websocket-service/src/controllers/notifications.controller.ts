import { Controller, Post, Body, Get } from '@nestjs/common';
import { NotificationsGateway } from '../gateways/notifications.gateway';

@Controller()
export class NotificationsController {
  constructor(private readonly notificationsGateway: NotificationsGateway) {}

  @Get()
  getInfo() {
    return {
      message: 'ULEAM Reservas - WebSocket Service',
      version: '1.1.0',
      status: 'running',
      webhooks: {
        reserva_creada: 'POST /api/webhooks/reserva-creada',
        reserva_actualizada: 'POST /api/webhooks/reserva-actualizada',
        reserva_cancelada: 'POST /api/webhooks/reserva-cancelada',
        notificacion: 'POST /api/webhooks/notificacion',
        stats_update: 'POST /api/webhooks/stats-update',
        disponibilidad_actualizada: 'POST /api/webhooks/disponibilidad-actualizada',
        recordatorio_evento: 'POST /api/webhooks/recordatorio-evento',
      },
    };
  }

  @Post('/api/webhooks/reserva-creada')
  handleReservaCreada(@Body() data: any) {
    this.notificationsGateway.notifyReservaCreada(data);
    return { success: true };
  }

  @Post('/api/webhooks/reserva-actualizada')
  handleReservaActualizada(@Body() data: any) {
    this.notificationsGateway.notifyReservaActualizada(data);
    return { success: true };
  }

  @Post('/api/webhooks/reserva-cancelada')
  handleReservaCancelada(@Body() data: any) {
    this.notificationsGateway.notifyReservaCancelada(data);
    return { success: true };
  }

  @Post('/api/webhooks/notificacion')
  handleNotificacion(@Body() data: any) {
    this.notificationsGateway.notifyNuevaNotificacion(data);
    return { success: true };
  }

  @Post('/api/webhooks/stats-update')
  handleStatsUpdate(@Body() data: any) {
    this.notificationsGateway.emitGlobalStats(data);
    return { success: true };
  }

  @Post('/api/webhooks/disponibilidad-actualizada')
  handleDisponibilidad(@Body() data: any) {
    this.notificationsGateway.notifyDisponibilidadActualizada(data);
    return { success: true };
  }

  @Post('/api/webhooks/recordatorio-evento')
  handleRecordatorio(@Body() data: any) {
    this.notificationsGateway.notifyRecordatorio(data);
    return { success: true };
  }
}

import { Injectable, NotFoundException, ForbiddenException } from '@nestjs/common';
import { InjectRepository } from '@nestjs/typeorm';
import { Repository } from 'typeorm';
import { Notification } from '../entities/notification.entity';

@Injectable()
export class NotificationsService {
  constructor(
    @InjectRepository(Notification)
    private readonly notificationsRepository: Repository<Notification>,
  ) {}

  async markAsRead(notificationId: number, userId: number): Promise<Notification> {
    const notification = await this.notificationsRepository.findOne({
      where: { id: notificationId },
    });

    if (!notification) {
      throw new NotFoundException('Notificación no encontrada');
    }

    if (notification.userId !== userId) {
      throw new ForbiddenException('No puedes modificar notificaciones de otro usuario');
    }

    if (!notification.leida) {
      notification.leida = true;
      notification.leidaAt = new Date();
      await this.notificationsRepository.save(notification);
    }

    return notification;
  }
}

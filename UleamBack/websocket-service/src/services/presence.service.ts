import { Injectable } from '@nestjs/common';
import { ConnectedUser, PresenceSnapshot } from '../interfaces/socket.interface';

@Injectable()
export class PresenceService {
  private socketsToUsers = new Map<string, ConnectedUser>();
  private usersToSockets = new Map<number, Set<string>>();
  private socketChannels = new Map<string, Set<string>>();

  registerConnection(socketId: string, user: ConnectedUser): ConnectedUser {
    this.socketsToUsers.set(socketId, user);
    const sockets = this.usersToSockets.get(user.id) || new Set<string>();
    sockets.add(socketId);
    this.usersToSockets.set(user.id, sockets);
    this.socketChannels.set(socketId, new Set());
    return user;
  }

  removeConnection(socketId: string): ConnectedUser | undefined {
    const user = this.socketsToUsers.get(socketId);
    if (!user) {
      return undefined;
    }

    this.socketsToUsers.delete(socketId);
    this.socketChannels.delete(socketId);

    const sockets = this.usersToSockets.get(user.id);
    if (sockets) {
      sockets.delete(socketId);
      if (sockets.size === 0) {
        this.usersToSockets.delete(user.id);
      }
    }
    return user;
  }

  addChannel(socketId: string, channel: string): void {
    const channels = this.socketChannels.get(socketId);
    if (channels) {
      channels.add(channel);
    }
  }

  removeChannel(socketId: string, channel: string): void {
    const channels = this.socketChannels.get(socketId);
    if (channels) {
      channels.delete(channel);
    }
  }

  getChannels(socketId: string): string[] {
    return Array.from(this.socketChannels.get(socketId) || []);
  }

  getUserFromSocket(socketId: string): ConnectedUser | undefined {
    return this.socketsToUsers.get(socketId);
  }

  isUserOnline(userId: number): boolean {
    return this.usersToSockets.has(userId);
  }

  getSnapshot(): PresenceSnapshot {
    return {
      online_users: this.usersToSockets.size,
      active_connections: this.socketsToUsers.size,
      tracked_channels: Array.from(
        new Set(
          Array.from(this.socketChannels.values()).flatMap((ch) => Array.from(ch)),
        ),
      ).length,
    };
  }
}

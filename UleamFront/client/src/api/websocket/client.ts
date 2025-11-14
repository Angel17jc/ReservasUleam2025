import { io, Socket } from 'socket.io-client';
import { env, ensureEnvValue } from '@/config/env';
import { authStorage } from '@/lib/auth-storage';

export type WsEvent =
  | 'nueva_notificacion'
  | 'reserva_creada'
  | 'reserva_aprobada'
  | 'reserva_rechazada'
  | 'reserva_cancelada'
  | 'reserva_actualizada'
  | 'stats_update'
  | 'disponibilidad_actualizada'
  | 'recordatorio';

type Listener = (payload: any) => void;

export class WebSocketClient {
  private socket: Socket | null = null;
  private listeners: Map<WsEvent, Set<Listener>> = new Map();
  private status: 'disconnected' | 'connecting' | 'connected' = 'disconnected';

  constructor(private getToken: () => string | null) {}

  get connectionStatus() {
    return this.status;
  }

  connect(defaultChannels: string[] = []) {
    if (this.status === 'connected' || this.status === 'connecting') return;
    const baseUrl = ensureEnvValue('wsUrl');
    const token = this.getToken();

    this.status = 'connecting';
    this.socket = io(baseUrl, {
      transports: ['websocket'],
      auth: { token },
      query: token ? { token } : undefined,
    });

    this.socket.on('connect', () => {
      this.status = 'connected';
      if (defaultChannels.length) {
        this.socket?.emit('subscribe', { channels: defaultChannels });
      }
    });
    this.socket.on('disconnect', () => {
      this.status = 'disconnected';
    });

    const forward: WsEvent[] = [
      'nueva_notificacion',
      'reserva_creada',
      'reserva_aprobada',
      'reserva_rechazada',
      'reserva_cancelada',
      'reserva_actualizada',
      'stats_update',
      'disponibilidad_actualizada',
      'recordatorio',
    ];
    forward.forEach((event) => {
      this.socket?.on(event, (payload: any) => this.emit(event, payload));
    });
  }

  disconnect() {
    this.socket?.disconnect();
    this.socket = null;
    this.status = 'disconnected';
  }

  on(event: WsEvent, listener: Listener) {
    if (!this.listeners.has(event)) {
      this.listeners.set(event, new Set());
    }
    this.listeners.get(event)!.add(listener);
    return () => this.listeners.get(event)?.delete(listener);
  }

  emit(event: WsEvent, payload: any) {
    this.listeners.get(event)?.forEach((listener) => listener(payload));
  }
}

export const webSocketClient = new WebSocketClient(() => authStorage.getToken());

export function isWebSocketConfigured() {
  return Boolean(env.wsUrl);
}

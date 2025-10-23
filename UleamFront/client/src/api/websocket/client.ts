import { env, ensureEnvValue } from '@/config/env';
import { authStorage } from '@/lib/auth-storage';

export type WsEvent =
  | 'nueva_notificacion'
  | 'reserva_creada'
  | 'reserva_aprobada'
  | 'reserva_rechazada'
  | 'stats_update'
  | 'disponibilidad_actualizada';

export type WsMessage = { type: WsEvent; payload: unknown };

type Listener = (payload: unknown) => void;

export class WebSocketClient {
  private socket: WebSocket | null = null;
  private listeners: Map<WsEvent, Set<Listener>> = new Map();
  private status: 'disconnected' | 'connecting' | 'connected' = 'disconnected';

  constructor(private getToken: () => string | null) {}

  get connectionStatus() {
    return this.status;
  }

  connect() {
    if (this.status === 'connected' || this.status === 'connecting') return;
    const baseUrl = ensureEnvValue('wsUrl');
    const token = this.getToken();
    const url = new URL(baseUrl);
    if (token) {
      url.searchParams.set('token', token);
    }

    this.status = 'connecting';
    this.socket = new WebSocket(url.toString());

    this.socket.addEventListener('open', () => {
      this.status = 'connected';
    });

    this.socket.addEventListener('message', (event) => {
      try {
        const message = JSON.parse(event.data) as WsMessage;
        this.emit(message.type, message.payload);
      } catch (error) {
        console.warn('[ws] Mensaje no parseable', error);
      }
    });

    this.socket.addEventListener('close', () => {
      this.status = 'disconnected';
      this.socket = null;
    });
  }

  disconnect() {
    this.socket?.close();
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

  send(message: WsMessage) {
    if (this.socket?.readyState === WebSocket.OPEN) {
      this.socket.send(JSON.stringify(message));
    }
  }

  private emit(event: WsEvent, payload: unknown) {
    this.listeners.get(event)?.forEach((listener) => listener(payload));
  }
}

export const webSocketClient = new WebSocketClient(() => authStorage.getToken());

export function isWebSocketConfigured() {
  return Boolean(env.wsUrl);
}

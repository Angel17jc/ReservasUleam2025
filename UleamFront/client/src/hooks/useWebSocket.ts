import { useEffect, useMemo, useState } from 'react';
import { isWebSocketConfigured, webSocketClient, WsEvent } from '@/api/websocket/client';
import { useAuth } from '@/contexts/AuthContext';

function buildDefaultChannels(userId: string | number | undefined, isAdmin: boolean) {
  const channels: string[] = [];
  if (!userId) return channels;
  channels.push(`notificaciones:user:${userId}`, `reservas:usuario:${userId}`);
  if (isAdmin) {
    channels.push('dashboard:admin', 'reservas:todas', 'disponibilidad:all');
  }
  return channels;
}

export function useWebSocket(subscriptions: WsEvent[] = [], extraChannels: string[] = []) {
  const { token, user, isAdmin } = useAuth();
  const [status, setStatus] = useState(webSocketClient.connectionStatus);

  const isReady = Boolean(token) && isWebSocketConfigured();
  const defaultChannels = useMemo(
    () => buildDefaultChannels(user?.id, isAdmin).concat(extraChannels || []),
    [user?.id, isAdmin, extraChannels.join('|')],
  );

  useEffect(() => {
    if (!isReady) {
      webSocketClient.disconnect();
      setStatus('disconnected');
      return;
    }

    webSocketClient.connect(defaultChannels);
    setStatus(webSocketClient.connectionStatus);

    const interval = setInterval(() => setStatus(webSocketClient.connectionStatus), 500);

    const unsubscribers = subscriptions.map((event) =>
      webSocketClient.on(event, () => undefined),
    );

    return () => {
      clearInterval(interval);
      unsubscribers.forEach((unsub) => unsub());
    };
  }, [isReady, subscriptions.join(','), defaultChannels.join('|')]);

  return { status } as const;
}

export function useWebSocketSubscription<T = unknown>(event: WsEvent, handler: (payload: T) => void) {
  const { token, user, isAdmin } = useAuth();
  const isReady = Boolean(token) && isWebSocketConfigured();

  useEffect(() => {
    if (!isReady) return;

    const unsubscribe = webSocketClient.on(event, handler as (payload: unknown) => void);
    webSocketClient.connect(buildDefaultChannels(user?.id, isAdmin));

    return () => unsubscribe();
  }, [event, handler, isReady, token, user?.id, isAdmin]);
}

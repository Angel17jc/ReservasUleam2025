import { useEffect, useMemo, useState } from 'react';
import { isWebSocketConfigured, webSocketClient, WsEvent } from '@/api/websocket/client';
import { useAuth } from '@/contexts/AuthContext';

export function useWebSocket(subscriptions: WsEvent[] = []) {
  const { token } = useAuth();
  const [status, setStatus] = useState(webSocketClient.connectionStatus);

  const isReady = Boolean(token) && isWebSocketConfigured();

  useEffect(() => {
    if (!isReady) {
      webSocketClient.disconnect();
      setStatus('disconnected');
      return;
    }

    webSocketClient.connect();
    setStatus(webSocketClient.connectionStatus);

    const interval = setInterval(() => setStatus(webSocketClient.connectionStatus), 500);

    const unsubscribers = subscriptions.map((event) =>
      webSocketClient.on(event, () => undefined),
    );

    return () => {
      clearInterval(interval);
      unsubscribers.forEach((unsub) => unsub());
    };
  }, [isReady, subscriptions.join(',')]);

  const send = useMemo(() => webSocketClient.send.bind(webSocketClient), []);

  return { status, send } as const;
}

export function useWebSocketSubscription<T = unknown>(event: WsEvent, handler: (payload: T) => void) {
  const { token } = useAuth();
  const isReady = Boolean(token) && isWebSocketConfigured();

  useEffect(() => {
    if (!isReady) return;

    const unsubscribe = webSocketClient.on(event, handler as (payload: unknown) => void);
    webSocketClient.connect();

    return () => unsubscribe();
  }, [event, handler, isReady, token]);
}

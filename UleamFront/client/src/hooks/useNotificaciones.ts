import { useEffect, useState } from 'react';
import { useWebSocketSubscription } from './useWebSocket';
import { useAuth } from '@/contexts/AuthContext';

export type Notificacion = {
  id: string;
  tipo: string;
  titulo: string;
  mensaje: string;
  fecha: string;
};

export function useNotificaciones() {
  const { isAuthenticated } = useAuth();
  const [notificaciones, setNotificaciones] = useState<Notificacion[]>([]);

  useEffect(() => {
    if (!isAuthenticated) {
      setNotificaciones([]);
    }
  }, [isAuthenticated]);

  useWebSocketSubscription<Partial<Notificacion>>('nueva_notificacion', (payload) => {
    if (!payload || typeof payload !== 'object') return;
    const parsed = payload as Partial<Notificacion>;
    setNotificaciones((prev) => [
      {
        id: parsed.id ?? crypto.randomUUID(),
        tipo: parsed.tipo ?? 'info',
        titulo: parsed.titulo ?? 'Notificación',
        mensaje: parsed.mensaje ?? '',
        fecha: parsed.fecha ?? new Date().toISOString(),
      },
      ...prev,
    ]);
  });

  return { notificaciones, setNotificaciones } as const;
}

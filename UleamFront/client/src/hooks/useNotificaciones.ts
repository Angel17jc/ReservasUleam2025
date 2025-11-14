import { useEffect, useState } from 'react';
import { useWebSocketSubscription } from './useWebSocket';
import { useAuth } from '@/contexts/AuthContext';
import { notificacionesApi } from '@/api/rest/notificacionesApi';

export type Notificacion = {
  id: string;
  titulo: string;
  mensaje: string;
  fecha: string;
  tipo?: string;
};

export function useNotificaciones() {
  const { isAuthenticated, user } = useAuth();
  const [notificaciones, setNotificaciones] = useState<Notificacion[]>([]);

  useEffect(() => {
    if (!isAuthenticated) {
      setNotificaciones([]);
      return;
    }
    // Cargar historial desde REST
    if (user?.id) {
      notificacionesApi
        .list(Number(user.id), 100)
        .then((rows) =>
          setNotificaciones(
            rows.map((r) => ({
              id: String(r.id),
              titulo: r.titulo,
              mensaje: r.mensaje,
              fecha: r.creado_en ?? new Date().toISOString(),
              tipo: r.metadata?.tipo ?? 'info',
            })),
          ),
        )
        .catch(() => {
          /* ignore */
        });
    }
  }, [isAuthenticated]);

  useWebSocketSubscription<Partial<Notificacion>>('nueva_notificacion', (payload) => {
    if (!payload || typeof payload !== 'object') return;
    const parsed = payload as any;
    setNotificaciones((prev) => [
      {
        id: String(parsed.notificacion_id ?? parsed.id ?? crypto.randomUUID()),
        tipo: parsed.tipo ?? 'info',
        titulo: parsed.titulo ?? 'Notificación',
        mensaje: parsed.mensaje ?? '',
        fecha: parsed.fecha ?? new Date().toISOString(),
      },
      ...prev,
    ]);
  });

  // También reflejar eventos de reserva como pseudo-notificaciones de tiempo real
  const pushReservaEvent = (evento: string, payload: any) => {
    setNotificaciones((prev) => [
      {
        id: crypto.randomUUID(),
        tipo: 'reserva',
        titulo: `Reserva ${evento.replace('reserva_', '').replace('_', ' ')}`,
        mensaje: `Reserva #${payload?.reserva_id ?? payload?.id ?? ''} - ${payload?.titulo ?? ''}`,
        fecha: new Date().toISOString(),
      },
      ...prev,
    ]);
  };
  useWebSocketSubscription('reserva_creada', (p) => pushReservaEvent('reserva_creada', p));
  useWebSocketSubscription('reserva_aprobada', (p) => pushReservaEvent('reserva_aprobada', p));
  useWebSocketSubscription('reserva_rechazada', (p) => pushReservaEvent('reserva_rechazada', p));
  useWebSocketSubscription('reserva_cancelada', (p) => pushReservaEvent('reserva_cancelada', p));
  useWebSocketSubscription('reserva_actualizada', (p) => pushReservaEvent('reserva_actualizada', p));

  return { notificaciones, setNotificaciones } as const;
}

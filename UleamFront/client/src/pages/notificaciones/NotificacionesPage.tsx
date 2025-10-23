import { useNotificaciones } from '@/hooks/useNotificaciones';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';

export default function NotificacionesPage() {
  const { notificaciones } = useNotificaciones();

  return (
    <div className="p-6 space-y-4">
      <h1 className="text-3xl font-bold text-foreground">Notificaciones</h1>
      <p className="text-muted-foreground">Suscrito al WebSocket externo para recibir eventos en tiempo real.</p>

      <div className="grid gap-3">
        {notificaciones.length === 0 && (
          <p className="text-muted-foreground">Sin notificaciones aún.</p>
        )}
        {notificaciones.map((notif) => (
          <Card key={notif.id}>
            <CardHeader>
              <CardTitle>{notif.titulo}</CardTitle>
              <p className="text-xs text-muted-foreground">{new Date(notif.fecha).toLocaleString()}</p>
            </CardHeader>
            <CardContent>
              <p className="text-sm text-muted-foreground">{notif.mensaje}</p>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
}

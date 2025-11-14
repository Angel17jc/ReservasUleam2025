import { useQuery } from '@tanstack/react-query';
import { fetchReservas } from '@/api/graphql/queries/reservas';
import { ReservationCard } from '@/components/ReservationCard';
import { Button } from '@/components/ui/button';
import { Link } from 'wouter';
import { useWebSocketSubscription } from '@/hooks/useWebSocket';
import { useQueryClient } from '@tanstack/react-query';

export default function ReservasListPage() {
  const queryClient = useQueryClient();
  const { data: reservas = [], isLoading, error, refetch } = useQuery({
    queryKey: ['reservas'],
    queryFn: () => fetchReservas(),
  });

  useWebSocketSubscription('reserva_creada', () => {
    queryClient.invalidateQueries({ queryKey: ['reservas'] });
  });
  useWebSocketSubscription('reserva_aprobada', () => {
    queryClient.invalidateQueries({ queryKey: ['reservas'] });
  });
  useWebSocketSubscription('reserva_rechazada', () => {
    queryClient.invalidateQueries({ queryKey: ['reservas'] });
  });
  useWebSocketSubscription('reserva_cancelada', () => {
    queryClient.invalidateQueries({ queryKey: ['reservas'] });
  });

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-foreground">Reservas</h1>
          <p className="text-muted-foreground">Consultando al servicio GraphQL externo.</p>
        </div>
        <Link href="/app/reservas/nueva">
          <Button data-testid="link-new-reservation">Nueva Reserva</Button>
        </Link>
      </div>

      {isLoading && <p className="text-muted-foreground">Cargando reservas...</p>}
      {error && <p className="text-destructive">No se pudieron cargar las reservas ({(error as Error).message}).</p>}

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {reservas.map((reserva) => (
          <ReservationCard
            key={reserva.id}
            id={reserva.id}
            espacio={reserva.espacioId}
            usuario={reserva.usuarioId}
            fecha={reserva.fecha}
            horaInicio={reserva.horaInicio}
            horaFin={reserva.horaFin}
            tipoEvento={reserva.titulo ?? reserva.tipoEvento}
            estado={(reserva.estado ?? 'pendiente') as any}
            showActions={false}
          />
        ))}
        {!isLoading && reservas.length === 0 && (
          <p className="text-muted-foreground">No hay reservas para mostrar.</p>
        )}
      </div>
    </div>
  );
}

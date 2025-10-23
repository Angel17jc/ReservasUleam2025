import { useQuery } from '@tanstack/react-query';
import { fetchReservaById } from '@/api/graphql/queries/reservas';
import { ReservationCard } from '@/components/ReservationCard';

interface Props {
  params: { id: string };
}

export default function ReservaDetailPage({ params }: Props) {
  const { data, isLoading, error } = useQuery({
    queryKey: ['reserva', params.id],
    queryFn: () => fetchReservaById(params.id),
  });

  return (
    <div className="p-6 space-y-4">
      <div>
        <h1 className="text-3xl font-bold text-foreground">Detalle de Reserva</h1>
        <p className="text-muted-foreground">Fuente: servicio GraphQL externo.</p>
      </div>

      {isLoading && <p className="text-muted-foreground">Cargando...</p>}
      {error && <p className="text-destructive">No se pudo cargar la reserva.</p>}

      {data && (
        <ReservationCard
          id={data.id}
          espacio={data.espacioId}
          usuario={data.usuario?.nombre}
          fecha={data.fecha}
          horaInicio={data.horaInicio}
          horaFin={data.horaFin}
          tipoEvento={data.estado}
          estado={data.estado as any}
          showActions={false}
        />
      )}
    </div>
  );
}

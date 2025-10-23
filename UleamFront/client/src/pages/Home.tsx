import { useMemo } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Button } from '@/components/ui/button';
import { SpaceCard } from '@/components/SpaceCard';
import { ReservationCard } from '@/components/ReservationCard';
import { Calendar, Building2, Clock, TrendingUp, Target, BookOpen } from 'lucide-react';
import { useAuth } from '@/contexts/AuthContext';
import { fetchEstadisticasGenerales } from '@/api/graphql/queries/reportes';
import { espaciosApi } from '@/api/rest/espaciosApi';
import { reservasApi } from '@/api/rest/reservasApi';

const accentByCategory: Record<string, { from: string; to: string; icon: JSX.Element }> = {
  Auditorio: { from: '#E63946', to: '#C1121F', icon: <Building2 className="text-white" size={20} /> },
  Deportivo: { from: '#0EA5E9', to: '#0284C7', icon: <Target className="text-white" size={20} /> },
  Laboratorio: { from: '#10B981', to: '#0F766E', icon: <BookOpen className="text-white" size={20} /> },
};

export default function Home() {
  const { user } = useAuth();

  const { data: stats } = useQuery({
    queryKey: ['estadisticas-dashboard'],
    queryFn: () => fetchEstadisticasGenerales(),
  });

  const { data: espacios } = useQuery({
    queryKey: ['espacios-destacados'],
    queryFn: () => espaciosApi.list({ pageSize: 3 }),
  });

  const { data: reservas } = useQuery({
    queryKey: ['reservas-proximas'],
    queryFn: () => reservasApi.list({ pageSize: 2 }),
  });

  const featuredSpaces = useMemo(() => espacios?.items ?? [], [espacios]);
  const upcomingReservations = useMemo(() => reservas?.items ?? [], [reservas]);

  return (
    <div className="p-6 space-y-8">
      <div>
        <h1 className="text-3xl font-bold text-foreground">
          Bienvenido, {user?.nombre}
        </h1>
        <p className="text-muted-foreground mt-2">
          Sistema de Reserva de Espacios ULEAM (frontend consumiendo REST + GraphQL + WebSocket externos)
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <div className="bg-gradient-to-br from-primary/10 to-primary/5 rounded-lg p-6 border border-primary/20">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-muted-foreground">Mis Reservas</p>
              <p className="text-3xl font-bold text-foreground mt-2">{stats?.totalReservas ?? 0}</p>
            </div>
            <Calendar className="text-primary" size={32} />
          </div>
        </div>
        <div className="bg-gradient-to-br from-blue-500/10 to-blue-500/5 rounded-lg p-6 border border-blue-500/20">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-muted-foreground">Tasa Aprobación</p>
              <p className="text-3xl font-bold text-foreground mt-2">{stats?.tasaAprobacion ?? 0}%</p>
            </div>
            <TrendingUp className="text-blue-600" size={32} />
          </div>
        </div>
        <div className="bg-gradient-to-br from-green-500/10 to-green-500/5 rounded-lg p-6 border border-green-500/20">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-muted-foreground">Próxima Reserva</p>
              <p className="text-3xl font-bold text-foreground mt-2">{upcomingReservations[0]?.fecha ?? '—'}</p>
            </div>
            <Clock className="text-green-600" size={32} />
          </div>
        </div>
        <div className="bg-gradient-to-br from-purple-500/10 to-purple-500/5 rounded-lg p-6 border border-purple-500/20">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-muted-foreground">Espacio más usado</p>
              <p className="text-3xl font-bold text-foreground mt-2">{stats?.espacioMasUsado ?? '—'}</p>
            </div>
            <Building2 className="text-purple-600" size={32} />
          </div>
        </div>
      </div>

      <div>
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-2xl font-semibold text-foreground">Espacios Destacados</h2>
          <Button variant="outline" data-testid="button-view-all-spaces">
            Ver Todos
          </Button>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {featuredSpaces.map((space) => {
            const accent = accentByCategory[space.categoria] ?? accentByCategory.Auditorio;
            return (
              <SpaceCard
                key={space.id}
                {...space}
                accentColors={{ from: accent.from, to: accent.to }}
                bannerIcon={accent.icon}
              />
            );
          })}
        </div>
      </div>

      <div>
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-2xl font-semibold text-foreground">Mis Próximas Reservas</h2>
          <Button data-testid="button-new-reservation">
            Nueva Reserva
          </Button>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {upcomingReservations.map((reservation) => (
            <ReservationCard
              key={reservation.id}
              id={reservation.id}
              espacio={reservation.espacioId}
              usuario={reservation.usuarioId}
              fecha={reservation.fecha}
              horaInicio={reservation.horaInicio}
              horaFin={reservation.horaFin}
              tipoEvento={reservation.tipoEvento ?? 'Reserva'}
              estado={reservation.estado as any}
              onCancel={() => console.log(`Cancelar ${reservation.id}`)}
            />
          ))}
          {upcomingReservations.length === 0 && (
            <p className="text-muted-foreground">No tienes reservas próximas.</p>
          )}
        </div>
      </div>
    </div>
  );
}

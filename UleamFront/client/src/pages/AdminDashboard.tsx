import { useMemo } from 'react';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { MetricCard } from '@/components/MetricCard';
import { ReservationCard } from '@/components/ReservationCard';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Users, Calendar, Building2, CheckCircle, TrendingUp } from 'lucide-react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { fetchEstadisticasGenerales, fetchTopEspacios } from '@/api/graphql/queries/reportes';
import { fetchReservas } from '@/api/graphql/queries/reservas';
import { useWebSocketSubscription } from '@/hooks/useWebSocket';
import { usuariosApi } from '@/api/rest/usuariosApi';
import { espaciosApi } from '@/api/rest/espaciosApi';

export default function AdminDashboard() {
  const queryClient = useQueryClient();

  const { data: stats } = useQuery({
    queryKey: ['admin-estadisticas'],
    queryFn: () => fetchEstadisticasGenerales(),
  });

  const { data: topEspacios = [] } = useQuery({
    queryKey: ['admin-top-espacios'],
    queryFn: () => fetchTopEspacios(5),
  });

  const { data: usuarios } = useQuery({
    queryKey: ['admin-usuarios'],
    queryFn: () => usuariosApi.list(),
  });

  const { data: espacios } = useQuery({
    queryKey: ['admin-espacios'],
    queryFn: () => espaciosApi.list(),
  });

  const { data: reservasTodas = [] } = useQuery({
    queryKey: ['admin-reservas'],
    queryFn: () => fetchReservas(),
  });

  const hoy = new Date().toISOString().slice(0, 10);
  const reservasHoy = useMemo(
    () => reservasTodas.filter((r) => r.fecha === hoy),
    [reservasTodas, hoy],
  );
  const pendientes = useMemo(
    () => reservasTodas.filter((r) => (r.estado ?? '').toLowerCase() === 'pendiente'),
    [reservasTodas],
  );

  // Datos para gráfica: reservas por día últimos 7 días
  const chartData = useMemo(() => {
    const days: { fecha: string; reservas: number }[] = [];
    for (let i = 6; i >= 0; i--) {
      const d = new Date();
      d.setDate(d.getDate() - i);
      const key = d.toISOString().slice(0, 10);
      const count = reservasTodas.filter((r) => r.fecha === key).length;
      const label = d.toLocaleDateString(undefined, { day: '2-digit', month: 'short' });
      days.push({ fecha: label, reservas: count });
    }
    return days;
  }, [reservasTodas]);

  // Manejo de eventos en vivo
  const invalidateAdmin = () => {
    queryClient.invalidateQueries({ queryKey: ['admin-estadisticas'] });
    queryClient.invalidateQueries({ queryKey: ['admin-top-espacios'] });
    queryClient.invalidateQueries({ queryKey: ['admin-reservas'] });
  };
  useWebSocketSubscription('reserva_creada', invalidateAdmin);
  useWebSocketSubscription('reserva_aprobada', invalidateAdmin);
  useWebSocketSubscription('reserva_rechazada', invalidateAdmin);
  useWebSocketSubscription('reserva_cancelada', invalidateAdmin);
  useWebSocketSubscription('reserva_actualizada', invalidateAdmin);
  useWebSocketSubscription('stats_update', invalidateAdmin);

  const totalUsuarios = usuarios?.items?.length ?? 0;
  const espaciosActivos = (espacios?.items ?? []).filter((e) => (e.estado ?? '').toLowerCase() === 'activo').length;

  return (
    <div className="p-6 space-y-8">
      <div>
        <h1 className="text-3xl font-bold text-foreground">Panel de Administración</h1>
        <p className="text-muted-foreground mt-2">Vista general del sistema de reservas</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <MetricCard title="Total Usuarios" value={String(totalUsuarios)} icon={Users} />
        <MetricCard
          title="Reservas Pendientes"
          value={String(pendientes.length)}
          icon={Calendar}
          description="Requieren aprobación"
        />
        <MetricCard
          title="Espacios Activos"
          value={String(espaciosActivos)}
          icon={Building2}
        />
        <MetricCard
          title="Reservas Hoy"
          value={String(reservasHoy.length)}
          icon={CheckCircle}
          description="En curso y programadas"
        />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <CardTitle>Reservas Últimos 7 Días</CardTitle>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={chartData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="fecha" />
                <YAxis />
                <Tooltip />
                <Line
                  type="monotone"
                  dataKey="reservas"
                  stroke="#E63946"
                  strokeWidth={2}
                  dot={{ fill: '#E63946' }}
                />
              </LineChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <TrendingUp size={20} />
              Espacios Más Reservados
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {topEspacios.map((space, index) => (
                <div key={index} className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <div className="w-8 h-8 rounded-full bg-primary/10 flex items-center justify-center text-sm font-bold text-primary">
                      {index + 1}
                    </div>
                    <span className="text-sm font-medium">{space.label}</span>
                  </div>
                  <span className="text-sm text-muted-foreground">{space.cantidad} reservas</span>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>

      <div>
        <h2 className="text-2xl font-semibold text-foreground mb-6">Reservas Pendientes de Aprobación</h2>
        <div className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-6">
          {pendientes.map((reservation) => (
            <ReservationCard
              key={reservation.id}
              id={reservation.id}
              espacio={String(reservation.espacioId)}
              usuario={String(reservation.usuarioId)}
              fecha={reservation.fecha}
              horaInicio={reservation.horaInicio}
              horaFin={reservation.horaFin}
              tipoEvento={reservation.titulo ?? reservation.tipoEvento ?? 'Reserva'}
              estado={(reservation.estado ?? 'pendiente') as any}
              showActions={false}
              onApprove={() => window.open(`/admin/aprobar/${reservation.id}`, '_self')}
              onReject={() => window.open(`/admin/aprobar/${reservation.id}`, '_self')}
            />
          ))}
          {pendientes.length === 0 && <p className="text-muted-foreground">No hay reservas pendientes.</p>}
        </div>
      </div>
    </div>
  );
}

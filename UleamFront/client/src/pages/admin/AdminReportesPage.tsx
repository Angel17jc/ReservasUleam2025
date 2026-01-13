import { useMemo } from 'react';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { fetchEstadisticasGenerales } from '@/api/graphql/queries/reportes';
import { fetchReservas } from '@/api/graphql/queries/reservas';
import { isGraphqlConfigured } from '@/api/graphql/client';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { MetricCard } from '@/components/MetricCard';
import { Users, Calendar, CheckCircle, Building2, Download } from 'lucide-react';
import { ResponsiveContainer, BarChart, Bar, XAxis, YAxis, Tooltip, PieChart, Pie, Cell } from 'recharts';
import { useWebSocketSubscription } from '@/hooks/useWebSocket';
import { usuariosApi } from '@/api/rest/usuariosApi';
import { espaciosApi } from '@/api/rest/espaciosApi';
import { reservasApi } from '@/api/rest/reservasApi';
import { tiposEventoApi } from '@/api/rest/tiposEventoApi';

const COLORS = ['#E63946', '#3B82F6', '#10B981', '#F59E0B', '#8B5CF6', '#EF4444', '#6366F1'];

export default function AdminReportesPage() {
  const queryClient = useQueryClient();

  const { data: reservas } = useQuery({
    queryKey: ['reportes-reservas'],
    queryFn: async () => {
      if (isGraphqlConfigured()) {
        try {
          return await fetchReservas({ ver_todas: true });
        } catch (err) {
          console.warn('GraphQL reservas falló, usando REST', err);
        }
      }
      const res = await reservasApi.list();
      return res.items ?? [];
    },
  });

  const { data: usuarios } = useQuery({
    queryKey: ['reportes-usuarios'],
    queryFn: () => usuariosApi.list(),
  });

  const { data: espacios } = useQuery({
    queryKey: ['reportes-espacios'],
    queryFn: () => espaciosApi.list(),
  });

  const { data: tiposEvento } = useQuery({
    queryKey: ['reportes-tipos-evento'],
    queryFn: () => tiposEventoApi.list(),
  });

  const { data: stats } = useQuery({
    queryKey: ['reportes-estadisticas'],
    queryFn: async () => {
      const buildFromRest = async () => {
        const reservasList = reservas ?? (await reservasApi.list()).items ?? [];
        const espaciosList = espacios?.items ?? (await espaciosApi.list()).items ?? [];
        const usuariosList = usuarios?.items ?? (await usuariosApi.list()).items ?? [];

        const normalizaEstado = (estado?: string) => (estado ?? '').toLowerCase();
        const totalReservas = reservasList.length;
        const reservasPendientes = reservasList.filter((r) => normalizaEstado(r.estado) === 'pendiente').length;
        const reservasAprobadas = reservasList.filter((r) => {
          const estado = normalizaEstado(r.estado);
          return estado === 'aprobada' || estado === 'pagada' || estado === 'completada';
        }).length;
        const reservasRechazadas = reservasList.filter((r) => normalizaEstado(r.estado) === 'rechazada').length;
        const reservasCanceladas = reservasList.filter((r) => normalizaEstado(r.estado) === 'cancelada').length;
        const espaciosActivos = espaciosList.filter((e) => (e.estado ?? '').toLowerCase() === 'activo').length;
        const usuariosActivos = usuariosList.length;

        return {
          totalReservas,
          reservasPendientes,
          reservasAprobadas,
          reservasRechazadas,
          reservasCanceladas,
          espaciosActivos,
          usuariosActivos,
        };
      };

      if (isGraphqlConfigured()) {
        try {
          const g = await fetchEstadisticasGenerales();
          const looksEmpty =
            g.totalReservas === 0 &&
            g.reservasPendientes === 0 &&
            g.reservasAprobadas === 0 &&
            g.reservasRechazadas === 0 &&
            g.reservasCanceladas === 0;
          if (!looksEmpty) return g;
          return await buildFromRest();
        } catch (err) {
          console.warn('GraphQL estadísticas falló, usando REST', err);
        }
      }
      return await buildFromRest();
    },
  });

  // Agrupar reservas por día (últimos 14 días)
  const chartData = useMemo(() => {
    const today = new Date();
    const days: { fecha: string; reservas: number }[] = [];
    for (let i = 13; i >= 0; i--) {
      const d = new Date(today);
      d.setDate(d.getDate() - i);
      const key = d.toISOString().slice(0, 10);
      const label = d.toLocaleDateString(undefined, { day: '2-digit', month: 'short' });
      const count = (reservas ?? []).filter((r) => r.fecha === key).length;
      days.push({ fecha: label, reservas: count });
    }
    return days;
  }, [reservas]);

  // Derivar stats y datasets desde REST si GraphQL vino vacío
  const derivedStats = useMemo(() => {
    const totalReservas = reservas?.length ?? 0;
    const pend = reservas?.filter((r) => (r.estado ?? '').toLowerCase() === 'pendiente').length ?? 0;
    const apro = reservas?.filter((r) => {
      const e = (r.estado ?? '').toLowerCase();
      return e === 'aprobada' || e === 'pagada' || e === 'completada';
    }).length ?? 0;
    const rech = reservas?.filter((r) => (r.estado ?? '').toLowerCase() === 'rechazada').length ?? 0;
    const canc = reservas?.filter((r) => (r.estado ?? '').toLowerCase() === 'cancelada').length ?? 0;
    const espAct = (espacios?.items ?? []).filter((e) => (e.estado ?? '').toLowerCase() === 'activo').length;
    const usuAct = usuarios?.items?.length ?? 0;
    return {
      totalReservas,
      reservasPendientes: pend,
      reservasAprobadas: apro,
      reservasRechazadas: rech,
      reservasCanceladas: canc,
      espaciosActivos: espAct,
      usuariosActivos: usuAct,
    };
  }, [reservas, espacios, usuarios]);

  const topEspacios = useMemo(() => {
    const counts = new Map<number, number>();
    (reservas ?? []).forEach((r) => {
      const id = Number(r.espacioId);
      if (!Number.isNaN(id)) counts.set(id, (counts.get(id) ?? 0) + 1);
    });
    return Array.from(counts.entries())
      .map(([id, cantidad]) => ({
        label: espacios?.items?.find((e) => Number(e.id) === id)?.nombre ?? `Espacio #${id}`,
        cantidad,
      }))
      .sort((a, b) => b.cantidad - a.cantidad)
      .slice(0, 5);
  }, [reservas, espacios]);

  const reservasEstado = useMemo(() => {
    const groups = new Map<string, number>();
    (reservas ?? []).forEach((r) => {
      const key = (r.estado ?? 'Pendiente').toString();
      groups.set(key, (groups.get(key) ?? 0) + 1);
    });
    return Array.from(groups.entries()).map(([label, cantidad]) => ({ label, cantidad }));
  }, [reservas]);

  const reservasTipoEvento = useMemo(() => {
    const mapTipos = new Map<number, string>();
    (tiposEvento ?? []).forEach((t) => mapTipos.set(Number(t.id), t.nombre));
    const groups = new Map<string, number>();
    (reservas ?? []).forEach((r) => {
      const id = Number((r as any).tipo_evento_id ?? r.tipoEvento ?? NaN);
      if (Number.isNaN(id)) return;
      const label = mapTipos.get(id) ?? `Tipo #${id}`;
      groups.set(label, (groups.get(label) ?? 0) + 1);
    });
    return Array.from(groups.entries()).map(([label, cantidad]) => ({ label, cantidad }));
  }, [reservas, tiposEvento]);

  const topUsuarios = useMemo(() => {
    const usersMap = new Map<number, string>();
    (usuarios?.items ?? []).forEach((u) => usersMap.set(Number(u.id), u.nombre ?? u.email ?? `Usuario #${u.id}`));
    const counts = new Map<number, number>();
    (reservas ?? []).forEach((r) => {
      const id = Number(r.usuarioId);
      if (!Number.isNaN(id)) counts.set(id, (counts.get(id) ?? 0) + 1);
    });
    return Array.from(counts.entries())
      .map(([id, cantidad]) => ({ label: usersMap.get(id) ?? `Usuario #${id}`, cantidad }))
      .sort((a, b) => b.cantidad - a.cantidad)
      .slice(0, 5);
  }, [reservas, usuarios]);

  const invalidateReportes = () =>
    queryClient.invalidateQueries({
      predicate: (q) => Array.isArray(q.queryKey) && String(q.queryKey[0]).startsWith('reportes'),
    });

  useWebSocketSubscription('reserva_creada', invalidateReportes);
  useWebSocketSubscription('reserva_aprobada', invalidateReportes);
  useWebSocketSubscription('reserva_rechazada', invalidateReportes);
  useWebSocketSubscription('reserva_cancelada', invalidateReportes);
  useWebSocketSubscription('reserva_actualizada', invalidateReportes);
  useWebSocketSubscription('stats_update', invalidateReportes);

  const pickStat = (statValue?: number | null, derivedValue?: number | null) => {
    const derived = derivedValue ?? 0;
    if (statValue === undefined || statValue === null) return derived;
    if (statValue === 0 && derived > 0) return derived;
    return statValue;
  };

  const handleDownload = () => {
    // Usa la impresión del navegador para exportar a PDF
    window.print();
  };

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-foreground">Reportes y Estadísticas</h1>
          <p className="text-muted-foreground">Resumen global del sistema. Actualizado en tiempo real.</p>
        </div>
        <Button onClick={handleDownload} variant="outline">
          <Download className="w-4 h-4 mr-2" /> Descargar PDF
        </Button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <MetricCard
          title="Total Reservas"
          value={String(pickStat(stats?.totalReservas, derivedStats.totalReservas))}
          icon={Calendar}
        />
        <MetricCard
          title="Pendientes"
          value={String(pickStat(stats?.reservasPendientes, derivedStats.reservasPendientes))}
          icon={Calendar}
        />
        <MetricCard
          title="Aprobadas"
          value={String(pickStat(stats?.reservasAprobadas, derivedStats.reservasAprobadas))}
          icon={CheckCircle}
        />
        <MetricCard
          title="Usuarios"
          value={String(pickStat(stats?.usuariosActivos, derivedStats.usuariosActivos))}
          icon={Users}
        />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <Card>
          <CardHeader>
            <CardTitle>Reservas últimos 14 días</CardTitle>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={280}>
              <BarChart data={chartData}>
                <XAxis dataKey="fecha" />
                <YAxis allowDecimals={false} />
                <Tooltip />
                <Bar dataKey="reservas" fill="#E63946" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Top Espacios</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            {topEspacios.map((e, idx) => (
              <div key={idx} className="flex items-center justify-between text-sm">
                <div className="flex items-center gap-2">
                  <span className="w-6 h-6 rounded-full bg-primary/10 flex items-center justify-center text-xs font-semibold text-primary">
                    {idx + 1}
                  </span>
                  <span>{e.label}</span>
                </div>
                <span className="text-muted-foreground">{e.cantidad} reservas</span>
              </div>
            ))}
            {topEspacios.length === 0 && <p className="text-muted-foreground">Sin datos.</p>}
          </CardContent>
        </Card>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <Card>
          <CardHeader>
            <CardTitle>Reservas por Estado</CardTitle>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={260}>
              <PieChart>
                <Pie
                  data={reservasEstado}
                  dataKey="cantidad"
                  nameKey="label"
                  cx="50%"
                  cy="50%"
                  outerRadius={90}
                  label
                >
                  {reservasEstado.map((_, idx) => (
                    <Cell key={idx} fill={COLORS[idx % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Reservas por Tipo de Evento</CardTitle>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={260}>
              <PieChart>
                <Pie
                  data={reservasTipoEvento}
                  dataKey="cantidad"
                  nameKey="label"
                  cx="50%"
                  cy="50%"
                  outerRadius={90}
                  label
                >
                  {reservasTipoEvento.map((_, idx) => (
                    <Cell key={idx} fill={COLORS[idx % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <Card>
          <CardHeader>
            <CardTitle>Usuarios más activos</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            {topUsuarios.map((u, idx) => (
              <div key={idx} className="flex items-center justify-between text-sm">
                <div className="flex items-center gap-2">
                  <span className="w-6 h-6 rounded-full bg-primary/10 flex items-center justify-center text-xs font-semibold text-primary">
                    {idx + 1}
                  </span>
                  <span>{u.label}</span>
                </div>
                <span className="text-muted-foreground">{u.cantidad} reservas</span>
              </div>
            ))}
            {topUsuarios.length === 0 && <p className="text-muted-foreground">Sin datos.</p>}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Resumen rápido</CardTitle>
          </CardHeader>
          <CardContent className="grid grid-cols-2 gap-3 text-sm text-muted-foreground">
            <div>
            <p>Pendientes</p>
            <p className="text-lg font-semibold text-foreground">
              {pickStat(stats?.reservasPendientes, derivedStats.reservasPendientes)}
            </p>
          </div>
          <div>
            <p>Rechazadas</p>
            <p className="text-lg font-semibold text-foreground">
              {pickStat(stats?.reservasRechazadas, derivedStats.reservasRechazadas)}
            </p>
          </div>
          <div>
            <p>Canceladas</p>
            <p className="text-lg font-semibold text-foreground">
              {pickStat(stats?.reservasCanceladas, derivedStats.reservasCanceladas)}
            </p>
          </div>
          <div>
            <p>Espacios activos</p>
            <p className="text-lg font-semibold text-foreground">
              {pickStat(stats?.espaciosActivos, derivedStats.espaciosActivos)}
            </p>
          </div>
        </CardContent>
      </Card>
      </div>
    </div>
  );
}

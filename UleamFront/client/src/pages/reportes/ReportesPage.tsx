import { useQuery } from '@tanstack/react-query';
import { fetchEstadisticasGenerales } from '@/api/graphql/queries/reportes';
import { isGraphqlConfigured } from '@/api/graphql/client';
import { reservasApi } from '@/api/rest/reservasApi';
import { espaciosApi } from '@/api/rest/espaciosApi';
import { usuariosApi } from '@/api/rest/usuariosApi';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';

export default function ReportesPage() {
  const { data, isLoading, error } = useQuery({
    queryKey: ['estadisticas-generales'],
    queryFn: async () => {
      const buildFromRest = async () => {
        const [reservasRes, espaciosRes, usuariosRes] = await Promise.all([
          reservasApi.list(),
          espaciosApi.list(),
          usuariosApi.list(),
        ]);

        const reservas = reservasRes.items ?? [];
        const espacios = espaciosRes.items ?? [];
        const usuarios = usuariosRes.items ?? [];

        const normalizaEstado = (estado?: string) => (estado ?? '').toLowerCase();
        const totalReservas = reservas.length;
        const reservasPendientes = reservas.filter((r) => normalizaEstado(r.estado) === 'pendiente').length;
        const reservasAprobadas = reservas.filter((r) => {
          const estado = normalizaEstado(r.estado);
          return estado === 'aprobada' || estado === 'pagada' || estado === 'completada';
        }).length;
        const reservasRechazadas = reservas.filter((r) => normalizaEstado(r.estado) === 'rechazada').length;
        const reservasCanceladas = reservas.filter((r) => normalizaEstado(r.estado) === 'cancelada').length;

        const espaciosActivos = espacios.filter((e) => (e.estado ?? '').toLowerCase() === 'activo').length;
        const usuariosActivos = usuarios.length;

        const usoEspacios = new Map<number, number>();
        reservas.forEach((r) => {
          const id = Number(r.espacioId);
          if (!Number.isNaN(id)) {
            usoEspacios.set(id, (usoEspacios.get(id) ?? 0) + 1);
          }
        });

        let espacioMasUsado = '—';
        if (usoEspacios.size > 0) {
          const [idTop] = Array.from(usoEspacios.entries()).sort((a, b) => b[1] - a[1])[0];
          const nombre = espacios.find((e) => Number(e.id) === idTop)?.nombre;
          espacioMasUsado = nombre ?? `Espacio #${idTop}`;
        }

        const tasaAprobacion = totalReservas > 0 ? Math.round((reservasAprobadas / totalReservas) * 100) : 0;

        return {
          totalReservas,
          reservasPendientes,
          reservasAprobadas,
          reservasRechazadas,
          reservasCanceladas,
          espaciosActivos,
          usuariosActivos,
          espacioMasUsado,
          tasaAprobacion,
        } as any;
      };

      if (isGraphqlConfigured()) {
        try {
          const stats = await fetchEstadisticasGenerales();
          const tasaAprobacionGraph = stats.totalReservas > 0
            ? Math.round((stats.reservasAprobadas / stats.totalReservas) * 100)
            : 0;
          const graphqlStats = {
            ...stats,
            tasaAprobacion: tasaAprobacionGraph,
            espacioMasUsado: (stats as any).espacioMasUsado ?? '—',
          } as any;
          const looksEmpty =
            graphqlStats.totalReservas === 0 &&
            graphqlStats.reservasPendientes === 0 &&
            graphqlStats.reservasAprobadas === 0 &&
            graphqlStats.reservasRechazadas === 0 &&
            graphqlStats.reservasCanceladas === 0;
          if (!looksEmpty) {
            return graphqlStats;
          }
          // Si GraphQL responde vacío (p.ej. admin only, DB distinta), usa REST
          return await buildFromRest();
        } catch (err) {
          console.warn('GraphQL estadísticas falló, usando REST como respaldo', err);
        }
      }
      return await buildFromRest();
    },
  });

  return (
    <div className="p-6 space-y-4">
      <div>
        <h1 className="text-3xl font-bold text-foreground">Reportes y Estadísticas</h1>
        <p className="text-muted-foreground">Consultando al servicio GraphQL externo.</p>
      </div>

      {isLoading && <p className="text-muted-foreground">Cargando...</p>}
      {error && <p className="text-destructive">No se pudieron obtener estadísticas.</p>}

      {data && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          <Card>
            <CardHeader>
              <CardTitle>Total Reservas</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-3xl font-bold">{data.totalReservas}</p>
            </CardContent>
          </Card>
          <Card>
            <CardHeader>
              <CardTitle>Tasa de Aprobación</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-3xl font-bold">{data.tasaAprobacion}%</p>
            </CardContent>
          </Card>
          <Card>
            <CardHeader>
              <CardTitle>Espacio más usado</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-lg">{data.espacioMasUsado ?? '—'}</p>
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  );
}

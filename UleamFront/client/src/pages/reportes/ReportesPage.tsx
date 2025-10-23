import { useQuery } from '@tanstack/react-query';
import { fetchEstadisticasGenerales } from '@/api/graphql/queries/reportes';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';

export default function ReportesPage() {
  const { data, isLoading, error } = useQuery({
    queryKey: ['estadisticas-generales'],
    queryFn: () => fetchEstadisticasGenerales(),
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

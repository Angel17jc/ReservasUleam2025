import { MetricCard } from '@/components/MetricCard';
import { ReservationCard } from '@/components/ReservationCard';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Users, Calendar, Building2, CheckCircle, TrendingUp } from 'lucide-react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';

export default function AdminDashboard() {
  // Datos para la gráfica de reservas de los últimos 7 días
  const chartData = [
    { fecha: '01 Nov', reservas: 12 },
    { fecha: '02 Nov', reservas: 15 },
    { fecha: '03 Nov', reservas: 8 },
    { fecha: '04 Nov', reservas: 20 },
    { fecha: '05 Nov', reservas: 18 },
    { fecha: '06 Nov', reservas: 22 },
    { fecha: '07 Nov', reservas: 25 },
  ];

  // Reservas pendientes de aprobación
  const pendingReservations = [
    {
      id: '1',
      espacio: 'Auditorio Principal',
      usuario: 'María García',
      fecha: '2025-11-15',
      horaInicio: '14:00',
      horaFin: '16:00',
      tipoEvento: 'Conferencia Académica',
      estado: 'pendiente' as const,
    },
    {
      id: '2',
      espacio: 'Cancha de Fútbol',
      usuario: 'Carlos López',
      fecha: '2025-11-16',
      horaInicio: '16:00',
      horaFin: '18:00',
      tipoEvento: 'Torneo Deportivo',
      estado: 'pendiente' as const,
    },
    {
      id: '3',
      espacio: 'Sala de Conferencias',
      usuario: 'Ana Martínez',
      fecha: '2025-11-17',
      horaInicio: '10:00',
      horaFin: '12:00',
      tipoEvento: 'Reunión Departamental',
      estado: 'pendiente' as const,
    },
  ];

  // Espacios más reservados del mes
  const topSpaces = [
    { nombre: 'Auditorio Principal', reservas: 45 },
    { nombre: 'Laboratorio de Cómputo 1', reservas: 38 },
    { nombre: 'Cancha de Fútbol', reservas: 32 },
    { nombre: 'Sala de Conferencias A', reservas: 28 },
    { nombre: 'Biblioteca - Sala de Estudio', reservas: 25 },
  ];

  return (
    <div className="p-6 space-y-8">
      <div>
        <h1 className="text-3xl font-bold text-foreground">Panel de Administración</h1>
        <p className="text-muted-foreground mt-2">
          Vista general del sistema de reservas
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <MetricCard
          title="Total Usuarios"
          value="1,234"
          icon={Users}
          trend="up"
          trendValue="12%"
        />
        <MetricCard
          title="Reservas Pendientes"
          value="23"
          icon={Calendar}
          description="Requieren aprobación"
        />
        <MetricCard
          title="Espacios Activos"
          value="45"
          icon={Building2}
          trend="up"
          trendValue="3"
        />
        <MetricCard
          title="Reservas Hoy"
          value="18"
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
              {topSpaces.map((space, index) => (
                <div key={index} className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <div className="w-8 h-8 rounded-full bg-primary/10 flex items-center justify-center text-sm font-bold text-primary">
                      {index + 1}
                    </div>
                    <span className="text-sm font-medium">{space.nombre}</span>
                  </div>
                  <span className="text-sm text-muted-foreground">{space.reservas} reservas</span>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>

      <div>
        <h2 className="text-2xl font-semibold text-foreground mb-6">
          Reservas Pendientes de Aprobación
        </h2>
        <div className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-6">
          {pendingReservations.map((reservation) => (
            <ReservationCard
              key={reservation.id}
              {...reservation}
              onApprove={() => console.log(`Aprobar ${reservation.id}`)}
              onReject={() => console.log(`Rechazar ${reservation.id}`)}
            />
          ))}
        </div>
      </div>
    </div>
  );
}

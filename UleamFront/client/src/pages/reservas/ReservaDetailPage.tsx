import { useMemo } from 'react';
import { useQuery } from '@tanstack/react-query';
import { reservasApi } from '@/api/rest/reservasApi';
import { paymentsApi } from '@/api/rest/paymentsApi';
import { authStorage } from '@/lib/auth-storage';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { StatusBadge } from '@/components/StatusBadge';
import { Badge } from '@/components/ui/badge';
import { Calendar, Clock, CreditCard } from 'lucide-react';

interface Props {
  params: { id: string };
}

export default function ReservaDetailPage({ params }: Props) {
  const token = authStorage.getToken();
  const { data, isLoading, error } = useQuery({
    queryKey: ['reserva', params.id, 'rest'],
    queryFn: () => reservasApi.detail(params.id),
  });

  const { data: paymentData } = useQuery({
    queryKey: ['payments', 'reserva', params.id],
    queryFn: () => paymentsApi.list({ page: 1, perPage: 10, reservaId: Number(params.id) }),
    enabled: Boolean(token),
  });

  const payment = useMemo(() => paymentData?.items?.[0], [paymentData]);

  return (
    <div className="p-6 space-y-4">
      <div>
        <h1 className="text-3xl font-bold text-foreground">Detalle de Reserva</h1>
        <p className="text-muted-foreground">Fuente: servicio REST.</p>
      </div>

      {isLoading && <p className="text-muted-foreground">Cargando...</p>}
      {error && <p className="text-destructive">No se pudo cargar la reserva.</p>}

      {data && (
        <Card className="border">
          <CardHeader className="flex flex-row items-center justify-between">
            <div>
              <CardTitle className="text-xl">{data.titulo ?? data.tipoEvento ?? 'Reserva'}</CardTitle>
              <p className="text-sm text-muted-foreground">Código: {data.codigo}</p>
            </div>
            <StatusBadge estado={(data.estado as any) ?? 'pendiente'} />
          </CardHeader>
          <CardContent className="space-y-3 text-sm text-muted-foreground">
            <div className="flex items-center gap-2">
              <Calendar size={14} /> {data.fecha}
            </div>
            <div className="flex items-center gap-2">
              <Clock size={14} /> {data.horaInicio} - {data.horaFin}
            </div>

            {payment && (
              <div className="flex items-center gap-2 text-emerald-700">
                <CreditCard size={14} /> Pago {payment.status} · Ref: {payment.externalPaymentId}
              </div>
            )}

            {!payment && (data.estado ?? '').toLowerCase() === 'aprobada' && (
              <Badge variant="outline">Aprobada, pendiente de pago (USD 20)</Badge>
            )}
          </CardContent>
        </Card>
      )}
    </div>
  );
}

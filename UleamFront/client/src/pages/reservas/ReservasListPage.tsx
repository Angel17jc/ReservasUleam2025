import { useMemo, useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { reservasApi } from '@/api/rest/reservasApi';
import { paymentsApi } from '@/api/rest/paymentsApi';
import { authStorage } from '@/lib/auth-storage';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Separator } from '@/components/ui/separator';
import { Link } from 'wouter';
import { useWebSocketSubscription } from '@/hooks/useWebSocket';
import { Calendar, Clock, CreditCard } from 'lucide-react';
import { StatusBadge } from '@/components/StatusBadge';
import type { Reserva } from '@/api/rest/reservasApi';

export default function ReservasListPage() {
  const queryClient = useQueryClient();
  const currentUser = authStorage.getUser();
  const token = authStorage.getToken();
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [selectedReserva, setSelectedReserva] = useState<Reserva | null>(null);
  const [payMsg, setPayMsg] = useState<string | null>(null);

  const { data: reservasData, isLoading, error } = useQuery({
    queryKey: ['reservas', 'rest', 'mine'],
    queryFn: () => {
      if (!currentUser) throw new Error('Inicia sesión para ver tus reservas');
      return reservasApi.list({ usuario_id: Number(currentUser.id) });
    },
  });

  const { data: paymentsData } = useQuery({
    queryKey: ['payments', 'reservas', 'mine'],
    queryFn: () => paymentsApi.list({ page: 1, perPage: 50 }),
    enabled: Boolean(token),
  });

  const payMutation = useMutation({
    mutationFn: (reservaId: string) => paymentsApi.create({ reserva_id: Number(reservaId) }),
    onSuccess: () => {
      setErrorMsg(null);
      setPayMsg('Pago creado. Revisa el estado en unos segundos.');
      queryClient.invalidateQueries({ queryKey: ['reservas', 'rest', 'mine'] });
      queryClient.invalidateQueries({ queryKey: ['payments', 'reservas', 'mine'] });
    },
    onError: (err: any) => {
      const detail = err?.body?.detail || err?.message || 'No se pudo crear el pago';
      setErrorMsg(String(detail));
      setPayMsg(null);
    },
  });

  useWebSocketSubscription('reserva_creada', () => {
    queryClient.invalidateQueries({ queryKey: ['reservas', 'rest', 'mine'] });
  });
  useWebSocketSubscription('reserva_aprobada', () => {
    queryClient.invalidateQueries({ queryKey: ['reservas', 'rest', 'mine'] });
  });
  useWebSocketSubscription('reserva_rechazada', () => {
    queryClient.invalidateQueries({ queryKey: ['reservas', 'rest', 'mine'] });
  });
  useWebSocketSubscription('reserva_cancelada', () => {
    queryClient.invalidateQueries({ queryKey: ['reservas', 'rest', 'mine'] });
  });

  const reservas = useMemo(() => reservasData?.items ?? [], [reservasData]);
  const paymentsByReserva = useMemo(() => {
    const items = paymentsData?.items ?? [];
    return items.reduce<Record<string, typeof items[number]>>((acc, item) => {
      acc[String(item.reservaId)] = item;
      return acc;
    }, {});
  }, [paymentsData]);

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-foreground">Reservas</h1>
          <p className="text-muted-foreground">Vista de mis reservas (REST) con opción de pago Stripe (USD 20).</p>
        </div>
        <Link href="/app/reservas/nueva">
          <Button data-testid="link-new-reservation">Nueva Reserva</Button>
        </Link>
      </div>

      {isLoading && <p className="text-muted-foreground">Cargando reservas...</p>}
      {error && <p className="text-destructive">{(error as Error).message}</p>}
      {errorMsg && <p className="text-destructive">{errorMsg}</p>}

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {reservas.map((reserva) => {
          const estado = (reserva.estado ?? 'pendiente').toLowerCase();
          const isAprobada = estado === 'aprobada';
          const isPagada = estado === 'pagada';
          const payment = paymentsByReserva[reserva.id];

          return (
            <Card key={reserva.id} className="border">
              <CardHeader className="flex flex-row items-center justify-between">
                <div>
                  <CardTitle className="text-lg">{reserva.titulo ?? reserva.tipoEvento ?? `Reserva #${reserva.id}`}</CardTitle>
                  <p className="text-sm text-muted-foreground">Código: {reserva.codigo}</p>
                </div>
                <StatusBadge estado={(estado as any) ?? 'pendiente'} />
              </CardHeader>
              <CardContent className="space-y-3 text-sm text-muted-foreground">
                <div className="flex items-center gap-2">
                  <Calendar size={14} /> {reserva.fecha}
                </div>
                <div className="flex items-center gap-2">
                  <Clock size={14} /> {reserva.horaInicio} - {reserva.horaFin}
                </div>

                {isPagada && payment && (
                  <div className="flex items-center gap-2 text-emerald-700">
                    <CreditCard size={14} /> Pago confirmado · Código: {payment.externalPaymentId}
                  </div>
                )}

                {isAprobada && !isPagada && (
                  <div className="pt-2">
                    <p className="text-xs text-muted-foreground">Monto fijo: USD 20 · Proveedor: Stripe</p>
                    <Button
                      size="sm"
                      className="mt-2"
                      variant="outline"
                      onClick={() => {
                        setSelectedReserva(reserva);
                        setPayMsg(null);
                      }}
                    >
                      Ver más
                    </Button>
                  </div>
                )}
              </CardContent>
            </Card>
          );
        })}
        {!isLoading && reservas.length === 0 && (
          <p className="text-muted-foreground">No hay reservas para mostrar.</p>
        )}
      </div>

      <Dialog open={Boolean(selectedReserva)} onOpenChange={(open) => {
        if (!open) {
          setSelectedReserva(null);
          setPayMsg(null);
        }
      }}>
        <DialogContent>
          {selectedReserva && (
            <div className="space-y-4">
              <DialogHeader>
                <DialogTitle>Pago de reserva #{selectedReserva.id}</DialogTitle>
              </DialogHeader>

              <div className="text-sm text-muted-foreground space-y-2">
                <p className="text-foreground font-semibold">{selectedReserva.titulo ?? selectedReserva.tipoEvento ?? 'Reserva'}</p>
                <div className="flex items-center gap-2">
                  <Calendar size={14} /> {selectedReserva.fecha}
                </div>
                <div className="flex items-center gap-2">
                  <Clock size={14} /> {selectedReserva.horaInicio} - {selectedReserva.horaFin}
                </div>
                <p>Código: {selectedReserva.codigo}</p>
                <p>Importe: USD 20.00 · Método: Stripe</p>
                {paymentsByReserva[selectedReserva.id] && (
                  <p className="flex items-center gap-2 text-emerald-700">
                    <CreditCard size={14} /> Pago existente · Ref: {paymentsByReserva[selectedReserva.id].externalPaymentId}
                  </p>
                )}
              </div>

              <Separator />

              {payMsg && <p className="text-sm text-green-700">{payMsg}</p>}
              {errorMsg && <p className="text-sm text-destructive">{errorMsg}</p>}

              <Button
                className="w-full"
                disabled={payMutation.isPending || paymentsByReserva[selectedReserva.id] !== undefined}
                onClick={() => payMutation.mutate(selectedReserva.id)}
              >
                {payMutation.isPending ? 'Procesando…' : paymentsByReserva[selectedReserva.id] ? 'Pago ya registrado' : 'Pagar ahora'}
              </Button>
            </div>
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
}

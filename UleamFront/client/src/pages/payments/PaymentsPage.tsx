import { useMemo } from 'react';
import { useQuery } from '@tanstack/react-query';
import { paymentsApi } from '@/api/rest/paymentsApi';
import { isPaymentApiConfigured } from '@/api/rest/paymentClient';
import { authStorage } from '@/lib/auth-storage';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { Badge } from '@/components/ui/badge';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { AlertCircle, CreditCard } from 'lucide-react';

export default function PaymentsPage() {
  const paymentApiReady = isPaymentApiConfigured();
  const token = authStorage.getToken();
  const currentUser = authStorage.getUser();

  const { data: payments, isLoading: loadingPayments, error: errorPayments } = useQuery({
    queryKey: ['payments', 'list'],
    queryFn: () => paymentsApi.list({ page: 1, perPage: 25 }),
    enabled: paymentApiReady && Boolean(token),
  });

  const paymentItems = useMemo(() => {
    const items = payments?.items ?? [];
    if (!currentUser) return items;
    return items.filter((p) => String(p.usuarioId) === currentUser.id);
  }, [currentUser, payments]);
  const unauthorized = (errorPayments as any)?.status === 401;

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm text-muted-foreground flex items-center gap-2">
            <CreditCard className="h-4 w-4" />
            Historial de pagos vinculados a tus reservas
          </p>
          <h1 className="text-3xl font-bold text-foreground">Pagos</h1>
        </div>
        <Badge variant="outline" className="text-xs">Stripe · USD 20</Badge>
      </div>

      {!paymentApiReady && (
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertTitle>Falta configurar VITE_PAYMENT_BASE_URL</AlertTitle>
          <AlertDescription>
            Define VITE_PAYMENT_BASE_URL en tu .env.local (ej: http://localhost:8024) para consumir el servicio de pagos.
          </AlertDescription>
        </Alert>
      )}

      <Card>
        <CardHeader>
          <CardTitle>Historial de pagos</CardTitle>
        </CardHeader>
        <CardContent>
          {!paymentApiReady && (
            <p className="text-sm text-muted-foreground">Configura la URL de pagos para ver el historial.</p>
          )}
          {paymentApiReady && !token && (
            <Alert className="mt-3" variant="destructive">
              <AlertCircle className="h-4 w-4" />
              <AlertTitle>Inicia sesión</AlertTitle>
              <AlertDescription>Necesitas iniciar sesión para consultar tus pagos.</AlertDescription>
            </Alert>
          )}
          {paymentApiReady && loadingPayments && <p className="text-sm text-muted-foreground">Cargando pagos...</p>}
          {paymentApiReady && unauthorized && (
            <p className="text-destructive text-sm">No autorizado. Vuelve a iniciar sesión para ver tu historial.</p>
          )}
          {paymentApiReady && errorPayments && !unauthorized && (
            <p className="text-destructive text-sm">No se pudieron cargar los pagos.</p>
          )}
          {paymentApiReady && !loadingPayments && paymentItems.length === 0 && token && (
            <p className="text-sm text-muted-foreground">Aún no tienes pagos registrados.</p>
          )}

          {paymentApiReady && paymentItems.length > 0 && (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="text-left text-muted-foreground">
                    <th className="py-2">ID</th>
                    <th className="py-2">Reserva</th>
                    <th className="py-2">Monto</th>
                    <th className="py-2">Estado</th>
                    <th className="py-2">Código pago</th>
                  </tr>
                </thead>
                <tbody>
                  {paymentItems.map((p) => (
                    <tr key={p.id} className="border-t">
                      <td className="py-2">#{p.id}</td>
                      <td className="py-2">{p.reservaId}</td>
                      <td className="py-2 font-medium">{p.currency} {p.amount.toFixed(2)}</td>
                      <td className="py-2">
                        <Badge variant={p.status === 'completed' ? 'default' : p.status === 'failed' ? 'destructive' : 'outline'}>
                          {p.status}
                        </Badge>
                      </td>
                      <td className="py-2 text-xs text-muted-foreground break-all">{p.externalPaymentId}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}

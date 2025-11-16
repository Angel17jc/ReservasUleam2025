/**
 * 🌐 Ejemplos de Integración del WebSocketIndicator
 * 
 * Este archivo muestra diferentes formas de integrar el indicador
 * de estado de WebSocket en tu aplicación.
 * 
 * Copia los ejemplos que necesites y pégalos en tus componentes.
 */

// ========================================
// EJEMPLO 1: Badge simple en Navbar
// ========================================

// En: client/src/components/layouts/UserLayout.tsx o AdminLayout.tsx
import { WebSocketIndicator } from '@/components/WebSocketIndicator';

export function UserLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="min-h-screen">
      <nav className="border-b bg-white px-4 py-3">
        <div className="flex items-center justify-between">
          <h1>ULEAM Reservas</h1>
          
          {/* Indicador WebSocket - solo muestra cuando hay problemas */}
          <div className="flex items-center gap-4">
            <WebSocketIndicator 
              variant="badge" 
              showOnlyWhenDisconnected 
            />
            <UserMenu />
          </div>
        </div>
      </nav>
      
      <main>{children}</main>
    </div>
  );
}

// ========================================
// EJEMPLO 2: Ícono minimalista en esquina
// ========================================

// En: client/src/components/layouts/UserLayout.tsx
import { WebSocketIndicator } from '@/components/WebSocketIndicator';

export function UserLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="relative min-h-screen">
      {/* Ícono fijo en esquina superior derecha */}
      <div className="fixed right-4 top-4 z-50">
        <WebSocketIndicator 
          variant="icon" 
          showOnlyWhenDisconnected 
        />
      </div>
      
      <nav>...</nav>
      <main>{children}</main>
    </div>
  );
}

// ========================================
// EJEMPLO 3: Banner global de desconexión
// ========================================

// En: client/src/App.tsx
import { QueryClientProvider } from '@tanstack/react-query';
import { queryClient } from './lib/queryClient';
import { TooltipProvider } from '@/components/ui/tooltip';
import { AuthProvider } from '@/contexts/AuthContext';
import { Toaster } from '@/components/ui/toaster';
import { WebSocketDisconnectedBanner } from '@/components/WebSocketIndicator';
import AppRouter from '@/router/AppRouter';

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <TooltipProvider>
        <AuthProvider>
          {/* Banner que aparece automáticamente si se desconecta */}
          <WebSocketDisconnectedBanner />
          
          <AppRouter />
        </AuthProvider>
        <Toaster />
      </TooltipProvider>
    </QueryClientProvider>
  );
}

// ========================================
// EJEMPLO 4: Status completo en Dashboard
// ========================================

// En: client/src/pages/dashboard/DashboardPage.tsx
import { WebSocketIndicator } from '@/components/WebSocketIndicator';
import { useWebSocketStatus } from '@/hooks/useWebSocketStatus';

export default function DashboardPage() {
  const wsStatus = useWebSocketStatus();

  return (
    <div className="p-6">
      <div className="mb-6 flex items-center justify-between">
        <h1 className="text-2xl font-bold">Dashboard</h1>
        
        {/* Indicador completo con info */}
        <WebSocketIndicator variant="full" />
      </div>

      {/* Mostrar alerta si hay problemas */}
      {!wsStatus.isConnected && (
        <div className="mb-4 rounded-lg border border-amber-200 bg-amber-50 p-4">
          <p className="text-sm text-amber-900">
            ⚠️ Sin conexión en tiempo real. 
            Las notificaciones no se actualizarán automáticamente.
          </p>
        </div>
      )}

      <div className="grid gap-6">
        {/* Contenido del dashboard */}
      </div>
    </div>
  );
}

// ========================================
// EJEMPLO 5: Hook personalizado con lógica
// ========================================

// En: client/src/pages/reservas/ReservasListPage.tsx
import { useWebSocketStatus, useIsWebSocketConnected } from '@/hooks/useWebSocketStatus';
import { useToast } from '@/hooks/use-toast';
import { useEffect, useRef } from 'react';

export default function ReservasListPage() {
  const { isConnected } = useWebSocketStatus();
  const wasConnected = useRef(isConnected);
  const { toast } = useToast();

  // Notificar cuando se reconecta
  useEffect(() => {
    if (isConnected && !wasConnected.current) {
      toast({
        title: 'Reconectado',
        description: 'Conexión en tiempo real restaurada',
        variant: 'default',
      });
    } else if (!isConnected && wasConnected.current) {
      toast({
        title: 'Desconectado',
        description: 'Se perdió la conexión en tiempo real',
        variant: 'destructive',
      });
    }
    
    wasConnected.current = isConnected;
  }, [isConnected, toast]);

  return (
    <div>
      {/* Contenido */}
    </div>
  );
}

// ========================================
// EJEMPLO 6: Deshabilitar funciones sin conexión
// ========================================

// En: client/src/pages/reservas/NuevaReservaPage.tsx
import { useIsWebSocketConnected } from '@/hooks/useWebSocketStatus';
import { Button } from '@/components/ui/button';
import { Alert, AlertDescription } from '@/components/ui/alert';

export default function NuevaReservaPage() {
  const isWsConnected = useIsWebSocketConnected();

  return (
    <div className="p-6">
      <h1 className="text-2xl font-bold">Nueva Reserva</h1>

      {!isWsConnected && (
        <Alert variant="warning" className="my-4">
          <AlertDescription>
            Sin conexión en tiempo real. La disponibilidad puede no estar actualizada.
          </AlertDescription>
        </Alert>
      )}

      <form>
        {/* Campos del formulario */}
        
        <Button 
          type="submit"
          disabled={!isWsConnected}
        >
          {isWsConnected ? 'Crear Reserva' : 'Esperando conexión...'}
        </Button>
      </form>
    </div>
  );
}

// ========================================
// EJEMPLO 7: Status card en Admin Dashboard
// ========================================

// En: client/src/pages/admin/AdminDashboardPage.tsx
import { useWebSocketStatus } from '@/hooks/useWebSocketStatus';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';

export default function AdminDashboardPage() {
  const wsStatus = useWebSocketStatus();

  return (
    <div className="p-6">
      <div className="grid gap-6 md:grid-cols-3">
        {/* Tarjeta de estado del sistema */}
        <Card>
          <CardHeader>
            <CardTitle>Estado del Sistema</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-sm text-muted-foreground">WebSocket</span>
              <Badge 
                variant={wsStatus.isConnected ? 'default' : 'destructive'}
              >
                {wsStatus.isConnected ? 'Conectado' : 'Desconectado'}
              </Badge>
            </div>

            {wsStatus.lastConnectedAt && (
              <div className="text-xs text-muted-foreground">
                Última conexión: {wsStatus.lastConnectedAt.toLocaleTimeString()}
              </div>
            )}

            {wsStatus.reconnectAttempts > 0 && (
              <div className="text-xs text-amber-600">
                Intentos de reconexión: {wsStatus.reconnectAttempts}
              </div>
            )}
          </CardContent>
        </Card>

        {/* Otras tarjetas de métricas */}
      </div>
    </div>
  );
}

// ========================================
// EJEMPLO 8: Componente de notificaciones
// ========================================

// En: client/src/components/NotificationsBell.tsx
import { Bell, BellOff } from 'lucide-react';
import { useIsWebSocketConnected } from '@/hooks/useWebSocketStatus';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';

export function NotificationsBell() {
  const isWsConnected = useIsWebSocketConnected();
  const [unreadCount, setUnreadCount] = useState(0);

  return (
    <div className="relative">
      <Button variant="ghost" size="icon">
        {isWsConnected ? (
          <Bell className="h-5 w-5" />
        ) : (
          <BellOff className="h-5 w-5 text-muted-foreground" />
        )}
      </Button>

      {/* Badge de contador solo si está conectado */}
      {isWsConnected && unreadCount > 0 && (
        <Badge 
          className="absolute -right-1 -top-1 h-5 w-5 rounded-full p-0 text-xs"
          variant="destructive"
        >
          {unreadCount}
        </Badge>
      )}

      {/* Tooltip si está desconectado */}
      {!isWsConnected && (
        <span className="absolute -bottom-1 -right-1 h-2 w-2 rounded-full bg-red-500" />
      )}
    </div>
  );
}

// ========================================
// EJEMPLO 9: Hook para refetch automático
// ========================================

// En: client/src/hooks/useAutoRefetch.ts
import { useIsWebSocketConnected } from '@/hooks/useWebSocketStatus';
import { useQuery } from '@tanstack/react-query';
import { useEffect } from 'react';

/**
 * Hook que hace refetch automático cuando WebSocket se reconecta
 * Útil para sincronizar datos después de una desconexión
 */
export function useAutoRefetchOnReconnect<T>(
  queryKey: string[],
  queryFn: () => Promise<T>
) {
  const isConnected = useIsWebSocketConnected();
  const wasConnected = useRef(isConnected);

  const query = useQuery({
    queryKey,
    queryFn,
  });

  // Refetch cuando se reconecta
  useEffect(() => {
    if (isConnected && !wasConnected.current) {
      console.log('WebSocket reconectado, refetching data...');
      query.refetch();
    }
    wasConnected.current = isConnected;
  }, [isConnected, query]);

  return query;
}

// Uso:
function MiComponente() {
  const { data, isLoading } = useAutoRefetchOnReconnect(
    ['reservas'],
    () => reservasApi.getReservas()
  );
  
  // Los datos se refetchearán automáticamente al reconectarse
}

// ========================================
// EJEMPLO 10: Custom toast de conexión
// ========================================

// En: client/src/hooks/useWebSocketToast.ts
import { useWebSocketStatus } from '@/hooks/useWebSocketStatus';
import { useToast } from '@/hooks/use-toast';
import { useEffect, useRef } from 'react';

/**
 * Hook que muestra toasts automáticamente cuando cambia el estado de WebSocket
 */
export function useWebSocketToast() {
  const { isConnected, isReconnecting } = useWebSocketStatus();
  const { toast } = useToast();
  const prevConnected = useRef(isConnected);

  useEffect(() => {
    // Solo mostrar si cambió el estado
    if (prevConnected.current === isConnected) return;

    if (isConnected && prevConnected.current === false) {
      toast({
        title: '✅ Conexión restaurada',
        description: 'Las notificaciones en tiempo real están activas',
        duration: 3000,
      });
    } else if (!isConnected && !isReconnecting) {
      toast({
        title: '⚠️ Conexión perdida',
        description: 'Intentando reconectar...',
        variant: 'destructive',
        duration: 5000,
      });
    }

    prevConnected.current = isConnected;
  }, [isConnected, isReconnecting, toast]);
}

// Uso en App.tsx o layout principal:
export function AppLayout() {
  useWebSocketToast(); // Automático
  
  return (
    <div>
      {/* Layout content */}
    </div>
  );
}

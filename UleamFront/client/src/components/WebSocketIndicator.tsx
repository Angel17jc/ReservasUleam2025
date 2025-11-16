import { useWebSocketStatus } from '@/hooks/useWebSocketStatus';
import { Wifi, WifiOff, RefreshCw } from 'lucide-react';
import { cn } from '@/lib/utils';

interface WebSocketIndicatorProps {
  /** Mostrar solo cuando hay problemas (default: false) */
  showOnlyWhenDisconnected?: boolean;
  
  /** Variante de estilo */
  variant?: 'badge' | 'icon' | 'full';
  
  /** Clase CSS adicional */
  className?: string;
}

/**
 * Indicador visual del estado de conexión WebSocket
 * 
 * Muestra el estado de conexión con Socket.IO:
 * - Verde: Conectado
 * - Amarillo/Naranja: Reconectando
 * - Rojo: Desconectado
 * 
 * @example
 * // En el navbar
 * <WebSocketIndicator variant="icon" showOnlyWhenDisconnected />
 * 
 * // Badge completo
 * <WebSocketIndicator variant="full" />
 */
export function WebSocketIndicator({
  showOnlyWhenDisconnected = false,
  variant = 'badge',
  className,
}: WebSocketIndicatorProps) {
  const { 
    isConnected, 
    isReconnecting, 
    isDisconnected,
    reconnectAttempts,
    error 
  } = useWebSocketStatus();

  // No mostrar nada si está configurado para solo mostrar cuando desconectado
  if (showOnlyWhenDisconnected && isConnected) {
    return null;
  }

  const getStatusConfig = () => {
    if (isConnected) {
      return {
        icon: Wifi,
        text: 'Conectado',
        color: 'text-green-600',
        bgColor: 'bg-green-50',
        borderColor: 'border-green-200',
        dotColor: 'bg-green-500',
      };
    }

    if (isReconnecting) {
      return {
        icon: RefreshCw,
        text: `Reconectando${reconnectAttempts > 0 ? ` (${reconnectAttempts})` : ''}`,
        color: 'text-amber-600',
        bgColor: 'bg-amber-50',
        borderColor: 'border-amber-200',
        dotColor: 'bg-amber-500',
        animate: 'animate-spin',
      };
    }

    return {
      icon: WifiOff,
      text: 'Desconectado',
      color: 'text-red-600',
      bgColor: 'bg-red-50',
      borderColor: 'border-red-200',
      dotColor: 'bg-red-500',
    };
  };

  const config = getStatusConfig();
  const Icon = config.icon;

  // Variante: solo ícono
  if (variant === 'icon') {
    return (
      <div
        className={cn('relative', className)}
        title={`WebSocket: ${config.text}${error ? ` - ${error}` : ''}`}
      >
        <Icon className={cn('h-4 w-4', config.color, config.animate)} />
        {/* Dot indicator */}
        <span
          className={cn(
            'absolute -right-0.5 -top-0.5 h-2 w-2 rounded-full',
            config.dotColor
          )}
        />
      </div>
    );
  }

  // Variante: badge (ícono + texto)
  if (variant === 'badge') {
    return (
      <div
        className={cn(
          'flex items-center gap-1.5 rounded-full border px-2 py-1 text-xs font-medium',
          config.bgColor,
          config.borderColor,
          config.color,
          className
        )}
        title={error || undefined}
      >
        <Icon className={cn('h-3.5 w-3.5', config.animate)} />
        <span>{config.text}</span>
      </div>
    );
  }

  // Variante: full (badge con más info)
  return (
    <div
      className={cn(
        'flex items-center gap-2 rounded-lg border px-3 py-2',
        config.bgColor,
        config.borderColor,
        className
      )}
    >
      <div className="relative">
        <Icon className={cn('h-4 w-4', config.color, config.animate)} />
        <span
          className={cn(
            'absolute -right-1 -top-1 h-2 w-2 rounded-full',
            config.dotColor,
            isConnected && 'animate-pulse'
          )}
        />
      </div>

      <div className="flex flex-col">
        <span className={cn('text-sm font-medium', config.color)}>
          {config.text}
        </span>
        {error && (
          <span className="text-xs text-gray-500">
            {error}
          </span>
        )}
      </div>
    </div>
  );
}

/**
 * Banner de alerta cuando WebSocket está desconectado
 * 
 * Se muestra en la parte superior de la app cuando hay problemas de conexión
 * 
 * @example
 * <WebSocketDisconnectedBanner />
 */
export function WebSocketDisconnectedBanner() {
  const { isDisconnected, isReconnecting, reconnectAttempts } = useWebSocketStatus();

  if (!isDisconnected && !isReconnecting) {
    return null;
  }

  return (
    <div className="border-b border-amber-200 bg-amber-50 px-4 py-2">
      <div className="mx-auto flex max-w-7xl items-center justify-between">
        <div className="flex items-center gap-2">
          <RefreshCw className="h-4 w-4 animate-spin text-amber-600" />
          <span className="text-sm font-medium text-amber-900">
            {isReconnecting 
              ? `Reconectando al servidor${reconnectAttempts > 0 ? ` (intento ${reconnectAttempts})` : ''}...`
              : 'Conexión perdida. Las actualizaciones en tiempo real no están disponibles.'
            }
          </span>
        </div>
        
        <button
          onClick={() => window.location.reload()}
          className="text-sm text-amber-700 underline hover:text-amber-900"
        >
          Recargar página
        </button>
      </div>
    </div>
  );
}

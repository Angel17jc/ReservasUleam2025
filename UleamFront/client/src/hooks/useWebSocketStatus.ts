import { useEffect, useState, useCallback } from 'react';
import { webSocketClient } from '@/api/websocket/client';

export interface WebSocketStatus {
  /** Si está actualmente conectado */
  isConnected: boolean;
  
  /** Si está en proceso de reconexión */
  isReconnecting: boolean;
  
  /** Si está desconectado */
  isDisconnected: boolean;
  
  /** Mensaje de error si hay alguno */
  error?: string;
  
  /** Número de intentos de reconexión */
  reconnectAttempts: number;
  
  /** Timestamp de la última conexión exitosa */
  lastConnectedAt?: Date;
  
  /** Timestamp de la última desconexión */
  lastDisconnectedAt?: Date;
}

interface WebSocketStatusInternal extends WebSocketStatus {
  setReconnecting: (value: boolean) => void;
  setError: (error: string | undefined) => void;
  incrementAttempts: () => void;
  resetAttempts: () => void;
  setConnectedAt: () => void;
  setDisconnectedAt: () => void;
}

/**
 * Hook para monitorear el estado de conexión de WebSocket
 * 
 * Proporciona información detallada sobre:
 * - Estado de conexión actual
 * - Intentos de reconexión
 * - Errores de conexión
 * - Timestamps de eventos
 * 
 * @example
 * ```tsx
 * function ConnectionIndicator() {
 *   const { isConnected, isReconnecting, error } = useWebSocketStatus();
 *   
 *   if (isReconnecting) {
 *     return <Badge variant="warning">Reconectando...</Badge>;
 *   }
 *   
 *   if (!isConnected) {
 *     return <Badge variant="destructive">Desconectado</Badge>;
 *   }
 *   
 *   return <Badge variant="success">Conectado</Badge>;
 * }
 * ```
 */
export function useWebSocketStatus(): WebSocketStatus {
  const [state, setState] = useState<WebSocketStatusInternal>(() => {
    const currentStatus = webSocketClient.connectionStatus;
    return {
      isConnected: currentStatus === 'connected',
      isReconnecting: currentStatus === 'connecting',
      isDisconnected: currentStatus === 'disconnected',
      error: undefined,
      reconnectAttempts: 0,
      lastConnectedAt: undefined,
      lastDisconnectedAt: undefined,
      
      // Helper methods (no expuestos)
      setReconnecting: (value: boolean) => 
        setState(prev => ({ ...prev, isReconnecting: value })),
      setError: (error: string | undefined) => 
        setState(prev => ({ ...prev, error })),
      incrementAttempts: () => 
        setState(prev => ({ ...prev, reconnectAttempts: prev.reconnectAttempts + 1 })),
      resetAttempts: () => 
        setState(prev => ({ ...prev, reconnectAttempts: 0 })),
      setConnectedAt: () => 
        setState(prev => ({ ...prev, lastConnectedAt: new Date() })),
      setDisconnectedAt: () => 
        setState(prev => ({ ...prev, lastDisconnectedAt: new Date() })),
    };
  });

  const updateStatus = useCallback(() => {
    const status = webSocketClient.connectionStatus;
    
    setState(prev => ({
      ...prev,
      isConnected: status === 'connected',
      isReconnecting: status === 'connecting',
      isDisconnected: status === 'disconnected',
    }));
  }, []);

  useEffect(() => {
    // Polling para detectar cambios de estado
    // Socket.IO no expone eventos de reconexión directamente en nuestro wrapper
    const interval = setInterval(updateStatus, 500);

    // Cleanup
    return () => {
      clearInterval(interval);
    };
  }, [updateStatus]);

  // Actualizar timestamps cuando cambia el estado
  useEffect(() => {
    if (state.isConnected) {
      state.setConnectedAt();
      state.resetAttempts();
      state.setError(undefined);
      
      if (import.meta.env.DEV) {
        console.log('✅ WebSocket conectado');
      }
    }
  }, [state.isConnected]);

  useEffect(() => {
    if (state.isDisconnected && !state.isReconnecting) {
      state.setDisconnectedAt();
      
      if (import.meta.env.DEV) {
        console.log('⚠️ WebSocket desconectado');
      }
    }
  }, [state.isDisconnected, state.isReconnecting]);

  useEffect(() => {
    if (state.isReconnecting) {
      state.incrementAttempts();
      
      if (import.meta.env.DEV) {
        console.log(`🔄 Intento de reconexión #${state.reconnectAttempts + 1}`);
      }
    }
  }, [state.isReconnecting]);

  // Retornar solo las propiedades públicas
  return {
    isConnected: state.isConnected,
    isReconnecting: state.isReconnecting,
    isDisconnected: state.isDisconnected,
    error: state.error,
    reconnectAttempts: state.reconnectAttempts,
    lastConnectedAt: state.lastConnectedAt,
    lastDisconnectedAt: state.lastDisconnectedAt,
  };
}

/**
 * Hook simplificado que solo retorna si está conectado
 * 
 * @example
 * ```tsx
 * const isOnline = useIsWebSocketConnected();
 * if (!isOnline) return <OfflineMessage />;
 * ```
 */
export function useIsWebSocketConnected(): boolean {
  const { isConnected } = useWebSocketStatus();
  return isConnected;
}

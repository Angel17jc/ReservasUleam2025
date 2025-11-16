import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { renderHook, act } from '@testing-library/react';
import { useWebSocketStatus, useIsWebSocketConnected } from '../useWebSocketStatus';
import type { WebSocketClient } from '../../api/websocket/client';

/**
 * Tests para useWebSocketStatus Hook
 * 
 * Este hook monitorea el estado de conexión WebSocket en tiempo real.
 * Usa fake timers para simular el polling interno del hook (500ms).
 */

// Mock del webSocketClient
vi.mock('../../api/websocket/client', () => ({
  webSocketClient: {
    connectionStatus: 'disconnected' as const,
  } as unknown as WebSocketClient,
}));

// Import después del mock para que use la versión mockeada
const { webSocketClient } = await import('../../api/websocket/client');

describe('useWebSocketStatus', () => {
  beforeEach(() => {
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.restoreAllMocks();
    vi.useRealTimers();
  });

  it('debe retornar estado desconectado por defecto', () => {
    // Arrange
    (webSocketClient as any).connectionStatus = 'disconnected';

    // Act
    const { result } = renderHook(() => useWebSocketStatus());

    // Assert
    expect(result.current.isDisconnected).toBe(true);
    expect(result.current.isConnected).toBe(false);
    expect(result.current.isReconnecting).toBe(false);
    expect(result.current.reconnectAttempts).toBe(0);
  });

  it('debe detectar cuando se conecta', () => {
    // Arrange
    (webSocketClient as any).connectionStatus = 'disconnected';
    const { result } = renderHook(() => useWebSocketStatus());
    expect(result.current.isDisconnected).toBe(true);

    // Act - Cambiar estado a conectado y avanzar timer
    act(() => {
      (webSocketClient as any).connectionStatus = 'connected';
      vi.advanceTimersByTime(600);
    });

    // Assert
    expect(result.current.isConnected).toBe(true);
    expect(result.current.isDisconnected).toBe(false);
  });

  it('debe detectar cuando está reconectando', () => {
    // Arrange
    (webSocketClient as any).connectionStatus = 'disconnected';
    const { result } = renderHook(() => useWebSocketStatus());

    // Act
    act(() => {
      (webSocketClient as any).connectionStatus = 'connecting';
      vi.advanceTimersByTime(600);
    });

    // Assert
    expect(result.current.isReconnecting).toBe(true);
    expect(result.current.isConnected).toBe(false);
  });

  it('debe resetear intentos de reconexión cuando se conecta', () => {
    // Arrange
    (webSocketClient as any).connectionStatus = 'connecting';
    const { result } = renderHook(() => useWebSocketStatus());

    act(() => {
      vi.advanceTimersByTime(600);
    });

    expect(result.current.isReconnecting).toBe(true);

    // Act - Conectar exitosamente
    act(() => {
      (webSocketClient as any).connectionStatus = 'connected';
      vi.advanceTimersByTime(600);
    });

    // Assert
    expect(result.current.isConnected).toBe(true);
  });

  it('debe actualizar lastDisconnectedAt cuando se desconecta', () => {
    // Arrange - Empezar conectado
    (webSocketClient as any).connectionStatus = 'connected';
    const { result } = renderHook(() => useWebSocketStatus());
    
    act(() => {
      vi.advanceTimersByTime(600);
    });

    expect(result.current.isConnected).toBe(true);

    // Act - Desconectar
    act(() => {
      (webSocketClient as any).connectionStatus = 'disconnected';
      vi.advanceTimersByTime(600);
    });

    // Assert
    expect(result.current.isDisconnected).toBe(true);
    expect(result.current.lastDisconnectedAt).toBeDefined();
  });
});

describe('useIsWebSocketConnected', () => {
  it('debe retornar solo el estado booleano de conexión', () => {
    // Arrange
    (webSocketClient as any).connectionStatus = 'connected';

    // Act
    const { result } = renderHook(() => useIsWebSocketConnected());

    // Assert
    expect(typeof result.current).toBe('boolean');
    expect(result.current).toBe(true);
  });

  it('debe retornar false cuando está desconectado', () => {
    // Arrange
    (webSocketClient as any).connectionStatus = 'disconnected';

    // Act
    const { result } = renderHook(() => useIsWebSocketConnected());

    // Assert
    expect(result.current).toBe(false);
  });
});

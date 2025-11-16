import { describe, it, expect, vi, beforeAll, afterAll } from 'vitest';
import { render, screen } from '@testing-library/react';
import '@testing-library/jest-dom';
import { ErrorBoundary } from '../ErrorBoundary';

/**
 * Tests para ErrorBoundary Component
 * 
 * ErrorBoundary captura errores de JavaScript en componentes hijos
 * y muestra una UI de fallback en lugar de crashear toda la app.
 * 
 * Nota: Los logs de "Error de prueba" en el output son ESPERADOS - 
 * son errores que el componente está capturando intencionalmente.
 */

// Componente que lanza error para testing
function ThrowError({ shouldThrow = false }: { shouldThrow?: boolean }) {
  if (shouldThrow) {
    throw new Error('Error de prueba');
  }
  return <div>Contenido sin error</div>;
}

describe('ErrorBoundary', () => {
  // Suprimir console.error durante los tests (ErrorBoundary logea errores)
  let consoleErrorSpy: ReturnType<typeof vi.spyOn>;
  
  beforeAll(() => {
    consoleErrorSpy = vi.spyOn(console, 'error').mockImplementation(() => {});
  });

  afterAll(() => {
    consoleErrorSpy.mockRestore();
  });

  it('debe renderizar children cuando no hay error', () => {
    // Act
    render(
      <ErrorBoundary>
        <ThrowError shouldThrow={false} />
      </ErrorBoundary>
    );

    // Assert
    expect(screen.getByText('Contenido sin error')).toBeInTheDocument();
  });

  it('debe capturar error y mostrar fallback UI', () => {
    // Act
    render(
      <ErrorBoundary>
        <ThrowError shouldThrow={true} />
      </ErrorBoundary>
    );

    // Assert
    expect(screen.getByText('Algo salió mal')).toBeInTheDocument();
    expect(screen.getByText(/ha ocurrido un error inesperado/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /recargar página/i })).toBeInTheDocument();
  });

  it('debe mostrar botón de "Volver atrás"', () => {
    // Act
    render(
      <ErrorBoundary>
        <ThrowError shouldThrow={true} />
      </ErrorBoundary>
    );

    // Assert
    const backButton = screen.getByRole('button', { name: /volver atrás/i });
    expect(backButton).toBeInTheDocument();
  });

  it('debe usar fallback personalizado si se provee', () => {
    // Arrange
    const customFallback = <div>Fallback personalizado</div>;

    // Act
    render(
      <ErrorBoundary fallback={customFallback}>
        <ThrowError shouldThrow={true} />
      </ErrorBoundary>
    );

    // Assert
    expect(screen.getByText('Fallback personalizado')).toBeInTheDocument();
    expect(screen.queryByText('Algo salió mal')).not.toBeInTheDocument();
  });

  it('debe llamar a console.error cuando captura un error', () => {
    // Arrange - Limpiar llamadas anteriores al spy global
    consoleErrorSpy.mockClear();

    // Act
    render(
      <ErrorBoundary>
        <ThrowError shouldThrow={true} />
      </ErrorBoundary>
    );

    // Assert - Usar el spy global configurado en beforeAll
    expect(consoleErrorSpy).toHaveBeenCalled();
  });
});

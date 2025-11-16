import { Component, ReactNode } from 'react';

interface Props {
  children: ReactNode;
  fallback?: ReactNode;
}

interface State {
  hasError: boolean;
  error?: Error;
  errorInfo?: string;
}

/**
 * ErrorBoundary global para capturar errores de React
 * 
 * @example
 * <ErrorBoundary>
 *   <App />
 * </ErrorBoundary>
 */
export class ErrorBoundary extends Component<Props, State> {
  state: State = { hasError: false };

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: any) {
    // Log a la consola en desarrollo
    console.error('🔴 ErrorBoundary capturó un error:', error);
    console.error('Stack trace:', errorInfo.componentStack);

    // Aquí puedes integrar Sentry, LogRocket, etc:
    // Sentry.captureException(error, { contexts: { react: { componentStack: errorInfo.componentStack } } });

    this.setState({
      errorInfo: errorInfo.componentStack,
    });
  }

  private handleReset = () => {
    this.setState({ hasError: false, error: undefined, errorInfo: undefined });
    window.location.reload();
  };

  render() {
    if (this.state.hasError) {
      // Usar fallback personalizado si se provee
      if (this.props.fallback) {
        return this.props.fallback;
      }

      // Fallback por defecto
      return (
        <div className="flex min-h-screen items-center justify-center bg-gray-50 px-4">
          <div className="w-full max-w-md space-y-6 rounded-lg border border-red-200 bg-white p-8 shadow-lg">
            <div className="text-center">
              <div className="mx-auto flex h-16 w-16 items-center justify-center rounded-full bg-red-100">
                <svg
                  className="h-8 w-8 text-red-600"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
                  />
                </svg>
              </div>

              <h2 className="mt-4 text-2xl font-bold text-gray-900">
                Algo salió mal
              </h2>

              <p className="mt-2 text-sm text-gray-600">
                Ha ocurrido un error inesperado. Por favor, intenta recargar la página.
              </p>
            </div>

            {/* Mostrar error en desarrollo */}
            {import.meta.env.DEV && this.state.error && (
              <details className="mt-4 rounded-md bg-red-50 p-4 text-left">
                <summary className="cursor-pointer font-semibold text-red-900">
                  Detalles del error (solo en desarrollo)
                </summary>
                <div className="mt-2 space-y-2 text-xs">
                  <p className="font-mono text-red-800">
                    <strong>Error:</strong> {this.state.error.message}
                  </p>
                  {this.state.errorInfo && (
                    <pre className="overflow-auto whitespace-pre-wrap text-red-700">
                      {this.state.errorInfo}
                    </pre>
                  )}
                </div>
              </details>
            )}

            <div className="flex flex-col gap-2">
              <button
                onClick={this.handleReset}
                className="rounded-md bg-red-600 px-4 py-2 font-medium text-white transition-colors hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-red-500 focus:ring-offset-2"
              >
                Recargar página
              </button>

              <button
                onClick={() => window.history.back()}
                className="rounded-md border border-gray-300 px-4 py-2 font-medium text-gray-700 transition-colors hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-gray-500 focus:ring-offset-2"
              >
                Volver atrás
              </button>
            </div>

            <div className="mt-6 text-center text-xs text-gray-500">
              Si el problema persiste, contacta al soporte técnico
            </div>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}

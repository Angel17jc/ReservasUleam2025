import { ReactNode, useEffect, lazy, Suspense } from 'react';
import { Route, Switch, useLocation } from 'wouter';
import { useAuth } from '@/contexts/AuthContext';
import { UserLayout } from '@/components/layouts/UserLayout';
import { AdminLayout } from '@/components/layouts/AdminLayout';
import { LoadingSpinner } from '@/components/LoadingSpinner';

// Páginas públicas (no lazy, se cargan inmediatamente)
import LandingPage from '@/pages/public/LandingPage';
import LoginPage from '@/pages/auth/LoginPage';
import NotFound from '@/pages/not-found';

// Lazy loading para páginas de usuario (solo se cargan cuando se accede)
const DashboardPage = lazy(() => import('@/pages/dashboard/DashboardPage'));
const EspaciosListPage = lazy(() => import('@/pages/espacios/EspaciosListPage'));
const ReservasListPage = lazy(() => import('@/pages/reservas/ReservasListPage'));
const ReservaDetailPage = lazy(() => import('@/pages/reservas/ReservaDetailPage'));
const NuevaReservaPage = lazy(() => import('@/pages/reservas/NuevaReservaPage'));
const ReportesPage = lazy(() => import('@/pages/reportes/ReportesPage'));
const PerfilUsuarioPage = lazy(() => import('@/pages/perfil/PerfilUsuarioPage'));
const NotificacionesPage = lazy(() => import('@/pages/notificaciones/NotificacionesPage'));
const CalendarioPage = lazy(() => import('@/pages/calendario/CalendarioPage'));

// Lazy loading para páginas de administrador
const AdminDashboardPage = lazy(() => import('@/pages/admin/AdminDashboardPage'));
const AdminPlaceholderPage = lazy(() => import('@/pages/admin/AdminPlaceholderPage'));
const AdminEspaciosPage = lazy(() => import('@/pages/admin/AdminEspaciosPage'));
const AdminCategoriasPage = lazy(() => import('@/pages/admin/AdminCategoriasPage'));
const AdminEventosPage = lazy(() => import('@/pages/admin/AdminEventosPage'));
const AdminAprobacionesPage = lazy(() => import('@/pages/admin/AdminAprobacionesPage'));
const AdminReportesPage = lazy(() => import('@/pages/admin/AdminReportesPage'));
const AdminUsuariosPage = lazy(() => import('@/pages/admin/AdminUsuariosPage'));

/**
 * PrivateUser - Protege rutas de usuario
 * 
 * Permite acceso a:
 * - Usuarios normales (role: 'user')
 * - Administradores (role: 'admin')
 * 
 * Justificación: Los administradores son superusuarios que necesitan
 * acceder a funcionalidades de usuario para gestionar el sistema
 * (ej: crear reservas, ver espacios, etc.)
 */
function PrivateUser({ children }: { children: ReactNode }) {
  const { isAuthenticated, isLoading } = useAuth();
  const [, navigate] = useLocation();

  useEffect(() => {
    if (isLoading) return;
    if (!isAuthenticated) navigate('/');
  }, [isAuthenticated, isLoading, navigate]);

  if (isLoading) return <div className="flex h-screen items-center justify-center">Cargando sesión...</div>;
  if (!isAuthenticated) return null;

  return <>{children}</>;
}

/**
 * PrivateAdmin - Protege rutas administrativas
 * 
 * Permite acceso SOLO a:
 * - Administradores (role: 'admin')
 * 
 * Los usuarios normales son redirigidos a /app/inicio
 * Mantiene la seguridad de las funciones administrativas
 */
function PrivateAdmin({ children }: { children: ReactNode }) {
  const { isAuthenticated, isLoading, isAdmin } = useAuth();
  const [, navigate] = useLocation();

  useEffect(() => {
    if (isLoading) return;
    if (!isAuthenticated) {
      navigate('/');
      return;
    }
    if (!isAdmin) {
      navigate('/app/inicio');
    }
  }, [isAuthenticated, isAdmin, isLoading, navigate]);

  if (isLoading) return <div className="flex h-screen items-center justify-center">Cargando sesión...</div>;
  if (!isAuthenticated || !isAdmin) return null;

  return <>{children}</>;
}

export default function AppRouter() {
  return (
    <Switch>
      {/* Rutas públicas */}
      <Route path="/" component={LandingPage} />
      <Route path="/login" component={LoginPage} />
      
      {/* Rutas de usuario (con layout) */}
      <Route path="/app/reservas/nueva">
        <PrivateUser><UserLayout><Suspense fallback={<LoadingSpinner text="Cargando..." />}><NuevaReservaPage /></Suspense></UserLayout></PrivateUser>
      </Route>
      <Route path="/app/reservas/new">
        <PrivateUser><UserLayout><Suspense fallback={<LoadingSpinner text="Cargando..." />}><NuevaReservaPage /></Suspense></UserLayout></PrivateUser>
      </Route>
      <Route path="/app/reservas/:id">
        {(params) => (
          <PrivateUser><UserLayout><Suspense fallback={<LoadingSpinner text="Cargando..." />}><ReservaDetailPage params={params} /></Suspense></UserLayout></PrivateUser>
        )}
      </Route>
      <Route path="/app/reservas">
        <PrivateUser><UserLayout><Suspense fallback={<LoadingSpinner text="Cargando..." />}><ReservasListPage /></Suspense></UserLayout></PrivateUser>
      </Route>
      <Route path="/app/inicio">
        <PrivateUser><UserLayout><Suspense fallback={<LoadingSpinner text="Cargando..." />}><DashboardPage /></Suspense></UserLayout></PrivateUser>
      </Route>
      <Route path="/app/espacios">
        <PrivateUser><UserLayout><Suspense fallback={<LoadingSpinner text="Cargando..." />}><EspaciosListPage /></Suspense></UserLayout></PrivateUser>
      </Route>
      <Route path="/app/reportes">
        <PrivateUser><UserLayout><Suspense fallback={<LoadingSpinner text="Cargando..." />}><ReportesPage /></Suspense></UserLayout></PrivateUser>
      </Route>
      <Route path="/app/perfil">
        <PrivateUser><UserLayout><Suspense fallback={<LoadingSpinner text="Cargando..." />}><PerfilUsuarioPage /></Suspense></UserLayout></PrivateUser>
      </Route>
      <Route path="/app/notificaciones">
        <PrivateUser><UserLayout><Suspense fallback={<LoadingSpinner text="Cargando..." />}><NotificacionesPage /></Suspense></UserLayout></PrivateUser>
      </Route>
      <Route path="/app/calendario">
        <PrivateUser><UserLayout><Suspense fallback={<LoadingSpinner text="Cargando..." />}><CalendarioPage /></Suspense></UserLayout></PrivateUser>
      </Route>
      
      {/* Rutas de admin (con layout admin) */}
      <Route path="/admin/nueva-reserva">
        <PrivateAdmin><AdminLayout><Suspense fallback={<LoadingSpinner text="Cargando..." />}><NuevaReservaPage /></Suspense></AdminLayout></PrivateAdmin>
      </Route>
      <Route path="/admin/mis-reservas">
        <PrivateAdmin><AdminLayout><Suspense fallback={<LoadingSpinner text="Cargando..." />}><ReservasListPage /></Suspense></AdminLayout></PrivateAdmin>
      </Route>
      <Route path="/admin/explorar-espacios">
        <PrivateAdmin><AdminLayout><Suspense fallback={<LoadingSpinner text="Cargando..." />}><EspaciosListPage /></Suspense></AdminLayout></PrivateAdmin>
      </Route>
      <Route path="/admin/reserva/:id">
        {(params) => (
          <PrivateAdmin><AdminLayout><Suspense fallback={<LoadingSpinner text="Cargando..." />}><ReservaDetailPage params={params} /></Suspense></AdminLayout></PrivateAdmin>
        )}
      </Route>
      <Route path="/admin/dashboard">
        <PrivateAdmin><AdminLayout><Suspense fallback={<LoadingSpinner text="Cargando..." />}><AdminDashboardPage /></Suspense></AdminLayout></PrivateAdmin>
      </Route>
      <Route path="/admin/usuarios">
        <PrivateAdmin><AdminLayout><Suspense fallback={<LoadingSpinner text="Cargando..." />}><AdminUsuariosPage /></Suspense></AdminLayout></PrivateAdmin>
      </Route>
      <Route path="/admin/espacios">
        <PrivateAdmin><AdminLayout><Suspense fallback={<LoadingSpinner text="Cargando..." />}><AdminEspaciosPage /></Suspense></AdminLayout></PrivateAdmin>
      </Route>
      <Route path="/admin/categorias">
        <PrivateAdmin><AdminLayout><Suspense fallback={<LoadingSpinner text="Cargando..." />}><AdminCategoriasPage /></Suspense></AdminLayout></PrivateAdmin>
      </Route>
      <Route path="/admin/eventos">
        <PrivateAdmin><AdminLayout><Suspense fallback={<LoadingSpinner text="Cargando..." />}><AdminEventosPage /></Suspense></AdminLayout></PrivateAdmin>
      </Route>
      <Route path="/admin/aprobaciones">
        <PrivateAdmin><AdminLayout><Suspense fallback={<LoadingSpinner text="Cargando..." />}><AdminAprobacionesPage /></Suspense></AdminLayout></PrivateAdmin>
      </Route>
      <Route path="/admin/reportes">
        <PrivateAdmin><AdminLayout><Suspense fallback={<LoadingSpinner text="Cargando..." />}><AdminReportesPage /></Suspense></AdminLayout></PrivateAdmin>
      </Route>
      <Route path="/admin/inicio">
        <PrivateAdmin><AdminLayout><Suspense fallback={<LoadingSpinner text="Cargando..." />}><DashboardPage /></Suspense></AdminLayout></PrivateAdmin>
      </Route>
      <Route path="/admin/notificaciones">
        <PrivateAdmin><AdminLayout><Suspense fallback={<LoadingSpinner text="Cargando..." />}><NotificacionesPage /></Suspense></AdminLayout></PrivateAdmin>
      </Route>
      <Route path="/admin/perfil">
        <PrivateAdmin><AdminLayout><Suspense fallback={<LoadingSpinner text="Cargando..." />}><PerfilUsuarioPage /></Suspense></AdminLayout></PrivateAdmin>
      </Route>
      <Route path="/admin/calendario">
        <PrivateAdmin><AdminLayout><Suspense fallback={<LoadingSpinner text="Cargando..." />}><CalendarioPage /></Suspense></AdminLayout></PrivateAdmin>
      </Route>
      <Route path="/admin/:section*">
        {(params) => (
          <PrivateAdmin><AdminLayout><Suspense fallback={<LoadingSpinner text="Cargando..." />}><AdminPlaceholderPage params={{ section: params['section*'] }} /></Suspense></AdminLayout></PrivateAdmin>
        )}
      </Route>
      
      {/* 404 */}
      <Route component={NotFound} />
    </Switch>
  );
}

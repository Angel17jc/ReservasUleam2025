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

function UserRoutes() {
  return (
    <PrivateUser>
      <UserLayout>
        <Suspense fallback={<LoadingSpinner text="Cargando página..." />}>
          <Switch>
            <Route path="/app/inicio" component={DashboardPage} />
            <Route path="/app/espacios" component={EspaciosListPage} />
            <Route path="/app/reservas/nueva" component={NuevaReservaPage} />
            <Route path="/app/reservas/new" component={NuevaReservaPage} />
            <Route path="/app/reservas/:id" component={ReservaDetailPage as any} />
            <Route path="/app/reservas" component={ReservasListPage} />
            <Route path="/app/reportes" component={ReportesPage} />
            <Route path="/app/perfil" component={PerfilUsuarioPage} />
            <Route path="/app/notificaciones" component={NotificacionesPage} />
            <Route path="/app/calendario" component={CalendarioPage} />
            <Route component={NotFound} />
          </Switch>
        </Suspense>
      </UserLayout>
    </PrivateUser>
  );
}

function AdminRoutes() {
  return (
    <PrivateAdmin>
      <AdminLayout>
        <Suspense fallback={<LoadingSpinner text="Cargando panel admin..." />}>
          <Switch>
            {/* Rutas administrativas */}
            <Route path="/admin/dashboard" component={AdminDashboardPage} />
            <Route path="/admin/usuarios" component={AdminUsuariosPage as any} />
            <Route path="/admin/espacios" component={AdminEspaciosPage as any} />
            <Route path="/admin/categorias" component={AdminCategoriasPage as any} />
            <Route path="/admin/eventos" component={AdminEventosPage as any} />
            <Route path="/admin/aprobaciones" component={AdminAprobacionesPage as any} />
            <Route path="/admin/reportes" component={AdminReportesPage as any} />
            
            {/* Funcionalidades de usuario accesibles para admin con AdminLayout */}
            <Route path="/admin/inicio" component={DashboardPage} />
            <Route path="/admin/explorar-espacios" component={EspaciosListPage} />
            <Route path="/admin/mis-reservas" component={ReservasListPage} />
            <Route path="/admin/nueva-reserva" component={NuevaReservaPage} />
            <Route path="/admin/reserva/:id" component={ReservaDetailPage as any} />
            <Route path="/admin/notificaciones" component={NotificacionesPage} />
            <Route path="/admin/perfil" component={PerfilUsuarioPage} />
            <Route path="/admin/calendario" component={CalendarioPage} />
            
            <Route path="/admin/:section*" component={AdminPlaceholderPage as any} />
            <Route component={NotFound} />
          </Switch>
        </Suspense>
      </AdminLayout>
    </PrivateAdmin>
  );
}

export default function AppRouter() {
  return (
    <Switch>
      <Route path="/" component={LandingPage} />
      <Route path="/login" component={LoginPage} />
      {/* Rutas de usuario - accesibles para users y admins */}
      <Route path="/app/:rest*" component={UserRoutes as any} />
      {/* Rutas de admin - solo para admins */}
      <Route path="/admin/:rest*" component={AdminRoutes as any} />
      <Route component={NotFound} />
    </Switch>
  );
}

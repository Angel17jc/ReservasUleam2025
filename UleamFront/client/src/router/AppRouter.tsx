import { ReactNode, useEffect } from 'react';
import { Route, Switch, useLocation } from 'wouter';
import { useAuth } from '@/contexts/AuthContext';
import DashboardPage from '@/pages/dashboard/DashboardPage';
import EspaciosListPage from '@/pages/espacios/EspaciosListPage';
import ReservasListPage from '@/pages/reservas/ReservasListPage';
import ReservaDetailPage from '@/pages/reservas/ReservaDetailPage';
import NuevaReservaPage from '@/pages/reservas/NuevaReservaPage';
import ReportesPage from '@/pages/reportes/ReportesPage';
import PerfilUsuarioPage from '@/pages/perfil/PerfilUsuarioPage';
import LoginPage from '@/pages/auth/LoginPage';
import NotFound from '@/pages/not-found';
import NotificacionesPage from '@/pages/notificaciones/NotificacionesPage';
import CalendarioPage from '@/pages/calendario/CalendarioPage';
import AdminDashboardPage from '@/pages/admin/AdminDashboardPage';
import AdminPlaceholderPage from '@/pages/admin/AdminPlaceholderPage';
import AdminEspaciosPage from '@/pages/admin/AdminEspaciosPage';
import AdminCategoriasPage from '@/pages/admin/AdminCategoriasPage';
import AdminEventosPage from '@/pages/admin/AdminEventosPage';
import AdminAprobacionesPage from '@/pages/admin/AdminAprobacionesPage';
import AdminReportesPage from '@/pages/admin/AdminReportesPage';
import AdminUsuariosPage from '@/pages/admin/AdminUsuariosPage';
import { UserLayout } from '@/components/layouts/UserLayout';
import { AdminLayout } from '@/components/layouts/AdminLayout';
import LandingPage from '@/pages/public/LandingPage';

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
      </UserLayout>
    </PrivateUser>
  );
}

function AdminRoutes() {
  return (
    <PrivateAdmin>
      <AdminLayout>
        <Switch>
          <Route path="/admin/dashboard" component={AdminDashboardPage} />
          <Route path="/admin/usuarios" component={AdminUsuariosPage as any} />
          <Route path="/admin/espacios" component={AdminEspaciosPage as any} />
          <Route path="/admin/categorias" component={AdminCategoriasPage as any} />
          <Route path="/admin/eventos" component={AdminEventosPage as any} />
          <Route path="/admin/aprobaciones" component={AdminAprobacionesPage as any} />
          <Route path="/admin/reportes" component={AdminReportesPage as any} />
          <Route path="/admin/:section*" component={AdminPlaceholderPage as any} />
          <Route component={NotFound} />
        </Switch>
      </AdminLayout>
    </PrivateAdmin>
  );
}

export default function AppRouter() {
  return (
    <Switch>
      <Route path="/" component={LandingPage} />
      <Route path="/login" component={LoginPage} />
      {/* Ruta directa para evitar cualquier coincidencia incorrecta hacia NotFound */}
      <Route
        path="/app/reservas/nueva"
        component={() => (
          <PrivateUser>
            <UserLayout>
              <NuevaReservaPage />
            </UserLayout>
          </PrivateUser>
        )}
      />
      <Route
        path="/app/reservas/new"
        component={() => (
          <PrivateUser>
            <UserLayout>
              <NuevaReservaPage />
            </UserLayout>
          </PrivateUser>
        )}
      />
      <Route path="/app/:rest*" component={UserRoutes as any} />
      <Route path="/admin/:rest*" component={AdminRoutes as any} />
      <Route component={NotFound} />
    </Switch>
  );
}

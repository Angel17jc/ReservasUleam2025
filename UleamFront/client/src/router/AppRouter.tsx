import { ReactNode, useEffect } from 'react';
import { Route, Switch, useLocation } from 'wouter';
import { SidebarProvider } from '@/components/ui/sidebar';
import { AppSidebar } from '@/components/app-sidebar';
import { Navbar } from '@/components/Navbar';
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

function ProtectedLayout({ children }: { children: ReactNode }) {
  const { isAuthenticated, isLoading } = useAuth();
  const [, navigate] = useLocation();

  useEffect(() => {
    if (!isLoading && !isAuthenticated) {
      navigate('/login');
    }
  }, [isAuthenticated, isLoading, navigate]);

  if (isLoading) {
    return <div className="flex h-screen items-center justify-center">Cargando sesión...</div>;
  }

  if (!isAuthenticated) return null;

  const style = {
    '--sidebar-width': '18rem',
    '--sidebar-width-icon': '4rem',
  } as React.CSSProperties;

  return (
    <SidebarProvider style={style}>
      <div className="flex h-screen w-full">
        <AppSidebar />
        <div className="flex flex-col flex-1 overflow-hidden">
          <Navbar />
          <main className="flex-1 overflow-auto bg-background">{children}</main>
        </div>
      </div>
    </SidebarProvider>
  );
}

function ProtectedRoutes() {
  return (
    <ProtectedLayout>
      <Switch>
        <Route path="/" component={DashboardPage} />
        <Route path="/espacios" component={EspaciosListPage} />
        <Route path="/reservas" component={ReservasListPage} />
        <Route path="/reservas/nueva" component={NuevaReservaPage} />
        <Route path="/reservas/:id" component={ReservaDetailPage as any} />
        <Route path="/reportes" component={ReportesPage} />
        <Route path="/perfil" component={PerfilUsuarioPage} />
        <Route path="/notificaciones" component={NotificacionesPage} />
        <Route path="/calendario" component={CalendarioPage} />
        <Route path="/admin" component={AdminDashboardPage} />
        <Route path="/admin/:section*" component={AdminPlaceholderPage as any} />
        <Route component={NotFound} />
      </Switch>
    </ProtectedLayout>
  );
}

export default function AppRouter() {
  return (
    <Switch>
      <Route path="/login" component={LoginPage} />
      <Route component={ProtectedRoutes} />
    </Switch>
  );
}

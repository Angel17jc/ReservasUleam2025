import {
  Home,
  Building2,
  Calendar,
  CalendarPlus,
  CalendarDays,
  Bell,
  User,
  Shield,
  Users,
  BookOpen,
  Target,
  PauseCircle,
  CheckCircle,
  BarChart3,
  Settings,
} from 'lucide-react';
import {
  Sidebar,
  SidebarContent,
  SidebarGroup,
  SidebarGroupContent,
  SidebarGroupLabel,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
  SidebarHeader,
  SidebarSeparator,
} from '@/components/ui/sidebar';
import { Link } from 'wouter';

const userMenuItems = [
  { title: 'Inicio', url: '/app/inicio', icon: Home },
  { title: 'Explorar Espacios', url: '/app/espacios', icon: Building2 },
  { title: 'Mis Reservas', url: '/app/reservas', icon: Calendar },
  { title: 'Nueva Reserva', url: '/app/reservas/nueva', icon: CalendarPlus },
  { title: 'Notificaciones', url: '/app/notificaciones', icon: Bell },
  { title: 'Mi Perfil', url: '/app/perfil', icon: User },
];

const adminMenuItems = [
  { title: 'Panel de Administración', url: '/admin/dashboard', icon: Shield },
  { title: 'Gestión de Usuarios', url: '/admin/usuarios', icon: Users },
  { title: 'Gestión de Espacios', url: '/admin/espacios', icon: Building2 },
  { title: 'Gestión de Categorías', url: '/admin/categorias', icon: BookOpen },
  { title: 'Tipos de Evento', url: '/admin/eventos', icon: Target },
  { title: 'Bloqueos de Espacios', url: '/admin/bloqueos', icon: PauseCircle },
  { title: 'Aprobar Reservas', url: '/admin/aprobaciones', icon: CheckCircle },
  { title: 'Reportes y Estadísticas', url: '/admin/reportes', icon: BarChart3 },
  { title: 'Configuración', url: '/admin/configuracion', icon: Settings },
];

interface AppSidebarProps {
  variant: 'user' | 'admin';
}

export function AppSidebar({ variant }: AppSidebarProps) {
  const showAdmin = variant === 'admin';

  return (
    <Sidebar>
      <SidebarHeader className="p-4">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 bg-primary rounded-md flex items-center justify-center">
            <Building2 className="text-primary-foreground" size={24} />
          </div>
          <div>
            <h2 className="text-lg font-bold text-foreground">ULEAM</h2>
            <p className="text-xs text-muted-foreground">Reserva de Espacios</p>
          </div>
        </div>
      </SidebarHeader>
      <SidebarContent>
        <SidebarGroup>
          <SidebarGroupLabel>Menú Principal</SidebarGroupLabel>
          <SidebarGroupContent>
            <SidebarMenu>
              {userMenuItems.map((item) => (
                <SidebarMenuItem key={item.title}>
                  <SidebarMenuButton asChild data-testid={`link-${item.title.toLowerCase().replace(/\s+/g, '-')}`}>
                    <Link href={item.url} className="flex items-center gap-3">
                      <item.icon size={20} />
                      <span>{item.title}</span>
                    </Link>
                  </SidebarMenuButton>
                </SidebarMenuItem>
              ))}
            </SidebarMenu>
          </SidebarGroupContent>
        </SidebarGroup>

        {showAdmin && (
          <>
            <SidebarSeparator />
            <SidebarGroup>
              <SidebarGroupLabel className="text-uleam-red">Administración</SidebarGroupLabel>
              <SidebarGroupContent>
                <SidebarMenu>
                  {adminMenuItems.map((item) => (
                    <SidebarMenuItem key={item.title}>
                      <SidebarMenuButton asChild data-testid={`link-admin-${item.title.toLowerCase().replace(/\s+/g, '-')}`}>
                        <Link href={item.url} className="flex items-center gap-3">
                          <item.icon size={20} />
                          <span>{item.title}</span>
                        </Link>
                      </SidebarMenuButton>
                    </SidebarMenuItem>
                  ))}
                </SidebarMenu>
              </SidebarGroupContent>
            </SidebarGroup>
          </>
        )}
      </SidebarContent>
    </Sidebar>
  );
}

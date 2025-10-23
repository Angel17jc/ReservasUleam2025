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
import { useAuth } from '@/contexts/AuthContext';

// Elementos del menú para usuarios normales
const userMenuItems = [
  { title: 'Inicio', url: '/', icon: Home },
  { title: 'Explorar Espacios', url: '/espacios', icon: Building2 },
  { title: 'Mis Reservas', url: '/reservas', icon: Calendar },
  { title: 'Nueva Reserva', url: '/reservas/nueva', icon: CalendarPlus },
  { title: 'Calendario', url: '/calendario', icon: CalendarDays },
  { title: 'Notificaciones', url: '/notificaciones', icon: Bell },
  { title: 'Mi Perfil', url: '/perfil', icon: User },
];

// Elementos del menú adicionales para administradores
const adminMenuItems = [
  { title: 'Panel de Administración', url: '/admin', icon: Shield },
  { title: 'Gestión de Usuarios', url: '/admin/usuarios', icon: Users },
  { title: 'Gestión de Espacios', url: '/admin/espacios', icon: Building2 },
  { title: 'Gestión de Categorías', url: '/admin/categorias', icon: BookOpen },
  { title: 'Tipos de Evento', url: '/admin/tipos-evento', icon: Target },
  { title: 'Bloqueos de Espacios', url: '/admin/bloqueos', icon: PauseCircle },
  { title: 'Aprobar Reservas', url: '/admin/aprobar-reservas', icon: CheckCircle },
  { title: 'Reportes y Estadísticas', url: '/admin/reportes', icon: BarChart3 },
  { title: 'Configuración', url: '/admin/configuracion', icon: Settings },
];

export function AppSidebar() {
  const { isAdmin } = useAuth();

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
                    <a href={item.url} className="flex items-center gap-3">
                      <item.icon size={20} />
                      <span>{item.title}</span>
                    </a>
                  </SidebarMenuButton>
                </SidebarMenuItem>
              ))}
            </SidebarMenu>
          </SidebarGroupContent>
        </SidebarGroup>

        {isAdmin && (
          <>
            <SidebarSeparator />
            <SidebarGroup>
              <SidebarGroupLabel className="text-uleam-red">Administración</SidebarGroupLabel>
              <SidebarGroupContent>
                <SidebarMenu>
                  {adminMenuItems.map((item) => (
                    <SidebarMenuItem key={item.title}>
                      <SidebarMenuButton asChild data-testid={`link-admin-${item.title.toLowerCase().replace(/\s+/g, '-')}`}>
                        <a href={item.url} className="flex items-center gap-3">
                          <item.icon size={20} />
                          <span>{item.title}</span>
                        </a>
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

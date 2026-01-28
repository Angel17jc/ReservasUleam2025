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
  CheckCircle,
  BarChart3,
  CreditCard,
  Bot,
  MessageSquare,
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
  SidebarFooter,
} from '@/components/ui/sidebar';
import { Link } from 'wouter';

// URLs dinámicas según el variant (user vs admin)
const getUserMenuItems = (variant: 'user' | 'admin') => {
  const prefix = variant === 'admin' ? '/admin' : '/app';
  return [
    { title: 'Inicio', url: `${prefix}/inicio`, icon: Home },
    { title: 'Explorar Espacios', url: `${prefix}/${variant === 'admin' ? 'explorar-espacios' : 'espacios'}`, icon: Building2 },
    { title: 'Mis Reservas', url: `${prefix}/${variant === 'admin' ? 'mis-reservas' : 'reservas'}`, icon: Calendar },
    { title: 'Nueva Reserva', url: `${prefix}/${variant === 'admin' ? 'nueva-reserva' : 'reservas/nueva'}`, icon: CalendarPlus },
    { title: 'Pagos', url: `${prefix}/pagos`, icon: CreditCard },
    { title: 'Notificaciones', url: `${prefix}/notificaciones`, icon: Bell },
    { title: 'Mi Perfil', url: `${prefix}/perfil`, icon: User },
  ];
};

const adminMenuItems = [
  { title: 'Panel de Administración', url: '/admin/dashboard', icon: Shield },
  { title: 'Gestión de Usuarios', url: '/admin/usuarios', icon: Users },
  { title: 'Gestión de Espacios', url: '/admin/espacios', icon: Building2 },
  { title: 'Gestión de Categorías', url: '/admin/categorias', icon: BookOpen },
  { title: 'Tipos de Evento', url: '/admin/eventos', icon: Target },
  { title: 'Aprobar Reservas', url: '/admin/aprobaciones', icon: CheckCircle },
  { title: 'Reportes y Estadísticas', url: '/admin/reportes', icon: BarChart3 },
];

interface AppSidebarProps {
  variant: 'user' | 'admin';
  onOpenChat?: () => void;
}

export function AppSidebar({ variant, onOpenChat }: AppSidebarProps) {
  const showAdmin = variant === 'admin';
  const userMenuItems = getUserMenuItems(variant);

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
      
      {/* Footer con botón del Chat de IA */}
      <SidebarFooter className="p-4 mt-auto border-t">
        <SidebarMenu>
          <SidebarMenuItem>
            <SidebarMenuButton
              onClick={onOpenChat}
              className="w-full bg-gradient-to-r from-primary to-primary/80 hover:from-primary hover:to-primary/90 text-primary-foreground font-medium"
              data-testid="chat-ai-button"
            >
              <div className="flex items-center gap-3 w-full">
                <div className="h-8 w-8 rounded-full bg-primary-foreground/20 flex items-center justify-center">
                  <Bot size={18} />
                </div>
                <div className="flex-1 text-left">
                  <div className="text-sm font-semibold">Chat de IA</div>
                  <div className="text-xs opacity-90">Asistente virtual</div>
                </div>
                <MessageSquare size={16} className="opacity-70" />
              </div>
            </SidebarMenuButton>
          </SidebarMenuItem>
        </SidebarMenu>
      </SidebarFooter>
    </Sidebar>
  );
}

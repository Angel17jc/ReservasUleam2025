import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Avatar, AvatarFallback } from '@/components/ui/avatar';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { SidebarTrigger } from '@/components/ui/sidebar';
import { AdminBadge } from './AdminBadge';
import { useAuth } from '@/contexts/AuthContext';
import { LogOut, User, Shield } from 'lucide-react';
import { LoginDialog } from '@/components/auth/LoginDialog';
import { useLocation } from 'wouter';

export function Navbar() {
  const { user, isAdmin, logout, isAuthenticated } = useAuth();
  const [loginOpen, setLoginOpen] = useState(false);
  const [, navigate] = useLocation();

  const goTo = (path: string) => {
    navigate(path);
  };

  return (
    <header className="flex items-center justify-between px-4 py-3 border-b bg-uleam-gray-dark text-white">
      <div className="flex items-center gap-4">
        <SidebarTrigger data-testid="button-sidebar-toggle" className="text-white" />
      </div>

      <div className="flex items-center gap-4">
        {isAdmin && <AdminBadge />}

        {!isAuthenticated && (
          <>
            <Button variant="secondary" onClick={() => setLoginOpen(true)} data-testid="button-open-login">
              Iniciar sesión
            </Button>
            <LoginDialog open={loginOpen} onOpenChange={setLoginOpen} />
          </>
        )}

        {isAuthenticated && (
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant="ghost" className="h-10 w-10 rounded-full" data-testid="button-user-menu">
                <Avatar className="h-10 w-10">
                  <AvatarFallback className="bg-primary text-primary-foreground">
                    {user?.nombre?.charAt(0) || 'U'}
                  </AvatarFallback>
                </Avatar>
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end" className="w-56">
              <DropdownMenuLabel>
                <div className="flex flex-col space-y-1">
                  <p className="text-sm font-medium">{user?.nombre}</p>
                  <p className="text-xs text-muted-foreground">{user?.email}</p>
                </div>
              </DropdownMenuLabel>
              <DropdownMenuSeparator />
              <DropdownMenuItem onClick={() => goTo('/app/perfil')} data-testid="button-profile">
                <User className="mr-2 h-4 w-4" />
                <span>Mi Perfil</span>
              </DropdownMenuItem>
              {isAdmin && (
                <DropdownMenuItem onClick={() => goTo('/admin/dashboard')} data-testid="button-go-admin">
                  <Shield className="mr-2 h-4 w-4" />
                  <span>Ir al Panel de Administración</span>
                </DropdownMenuItem>
              )}
              <DropdownMenuSeparator />
              <DropdownMenuItem onClick={logout} data-testid="button-logout">
                <LogOut className="mr-2 h-4 w-4" />
                <span>Cerrar Sesión</span>
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        )}
      </div>
    </header>
  );
}

import { Button } from '@/components/ui/button';
import { Building2 } from 'lucide-react';
import { useState } from 'react';
import { LoginDialog } from '@/components/auth/LoginDialog';
import { useAuth } from '@/contexts/AuthContext';
import { useLocation } from 'wouter';

export function PublicHeader() {
  const [loginOpen, setLoginOpen] = useState(false);
  const { isAuthenticated, isAdmin } = useAuth();
  const [, navigate] = useLocation();

  const goToDefault = () => navigate(isAdmin ? '/admin/dashboard' : '/app/inicio');

  return (
    <header className="flex items-center justify-between px-6 py-4 bg-uleam-gray-dark text-white shadow">
      <div className="flex items-center gap-3">
        <div className="w-10 h-10 bg-primary rounded-md flex items-center justify-center">
          <Building2 className="text-primary-foreground" size={24} />
        </div>
        <div>
          <h1 className="font-bold text-lg">ULEAM</h1>
          <p className="text-xs text-white/70">Reserva de Espacios</p>
        </div>
      </div>
      <div className="flex items-center gap-2">
        {isAuthenticated ? (
          <Button variant="secondary" onClick={goToDefault} data-testid="button-go-dashboard">
            Ir al panel
          </Button>
        ) : (
          <Button variant="secondary" onClick={() => setLoginOpen(true)} data-testid="button-open-login-public">
            Iniciar sesión
          </Button>
        )}
        <LoginDialog open={loginOpen} onOpenChange={setLoginOpen} />
      </div>
    </header>
  );
}

import { useEffect } from 'react';
import { Card, CardContent, CardFooter, CardHeader, CardTitle } from '@/components/ui/card';
import { LoginForm } from '@/components/auth/LoginDialog';
import { useAuth } from '@/contexts/AuthContext';
import { useLocation } from 'wouter';

export default function LoginPage() {
  const { isAuthenticated, isAdmin } = useAuth();
  const [, navigate] = useLocation();

  useEffect(() => {
    if (isAuthenticated) {
      navigate(isAdmin ? '/admin/dashboard' : '/app/inicio');
    }
  }, [isAuthenticated, isAdmin, navigate]);

  return (
    <div className="min-h-screen flex items-center justify-center bg-background p-6">
      <Card className="w-full max-w-md shadow-lg">
        <CardHeader>
          <CardTitle className="text-2xl">Iniciar sesión</CardTitle>
          <p className="text-muted-foreground text-sm">
            Puedes iniciar también desde el botón del header; esta ruta queda para accesos directos.
          </p>
        </CardHeader>
        <CardContent>
          <LoginForm />
        </CardContent>
        <CardFooter className="text-xs text-muted-foreground">
          demo@uleam.edu.ec / demo123 (user) · admin@uleam.edu.ec / admin123 (admin)
        </CardFooter>
      </Card>
    </div>
  );
}

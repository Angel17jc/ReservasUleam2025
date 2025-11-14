import { useState } from 'react';
import { PublicHeader } from '@/components/layouts/PublicHeader';
import { Button } from '@/components/ui/button';
import { CheckCircle2 } from 'lucide-react';
import { LoginDialog } from '@/components/auth/LoginDialog';
import { useAuth } from '@/contexts/AuthContext';
import { useLocation } from 'wouter';

export default function LandingPage() {
  const [loginOpen, setLoginOpen] = useState(false);
  const { isAuthenticated, isAdmin } = useAuth();
  const [, navigate] = useLocation();

  const handleLogin = () => setLoginOpen(true);
  const handleGuest = () => {
    if (isAuthenticated) {
      navigate(isAdmin ? '/admin/dashboard' : '/app/inicio');
    } else {
      window.scrollTo({ top: document.body.scrollHeight / 2, behavior: 'smooth' });
    }
  };

  return (
    <div className="min-h-screen bg-slate-50">
      <PublicHeader />
      <main className="min-h-[calc(100vh-64px)] flex items-center justify-center px-6 py-10">
        <div className="max-w-6xl w-full grid gap-10 md:grid-cols-2 items-center">
          <div className="w-full rounded-xl shadow-md overflow-hidden">
            <img
              src="/images/uleam-campus-map.jpg"
              alt="Mapa del campus ULEAM"
              className="w-full h-auto object-cover"
            />
          </div>

          <div className="space-y-6">
            <div className="space-y-3">
              <p className="text-sm font-semibold text-primary uppercase tracking-wide">Campus ULEAM</p>
              <h1 className="text-3xl md:text-4xl font-bold text-foreground leading-tight">
                Bienvenido al Sistema de Reserva de Espacios ULEAM
              </h1>
              <p className="text-lg text-muted-foreground">
                Administra reservas de espacios deportivos, laboratorios, parninfo del campus de forma rápida y organizada.
              </p>
              <p className="text-muted-foreground">
                Esta aplicación permite a estudiantes, docentes y personal administrativo gestionar reservas, ver
                disponibilidad y recibir notificaciones de manera centralizada.
              </p>
            </div>

            <div className="space-y-3">
              {[
                'Reservas en línea de espacios del campus.',
                'Panel de administración para gestionar usuarios y espacios.',
                'Reportes y estadísticas de uso.',
                'Notificaciones sobre cambios en reservas.',
              ].map((item) => (
                <div key={item} className="flex items-start gap-3">
                  <CheckCircle2 className="text-green-600 mt-1" size={20} />
                  <p className="text-muted-foreground">{item}</p>
                </div>
              ))}
            </div>

            <div className="flex flex-wrap gap-3">
              <Button onClick={handleLogin}>Iniciar sesión</Button>
              <Button variant="outline" onClick={handleGuest}>
                Ver como invitado
              </Button>
            </div>
          </div>
        </div>
      </main>

      <LoginDialog open={loginOpen} onOpenChange={setLoginOpen} />
    </div>
  );
}

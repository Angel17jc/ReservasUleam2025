import { PublicHeader } from '@/components/layouts/PublicHeader';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Building2, Calendar, Laptop, ShieldCheck } from 'lucide-react';

export default function LandingPage() {
  return (
    <div className="min-h-screen bg-background">
      <PublicHeader />
      <main className="max-w-6xl mx-auto px-6 py-10 space-y-10">
        <section className="grid lg:grid-cols-2 gap-8 items-center">
          <div className="space-y-4">
            <p className="text-sm font-semibold text-primary uppercase tracking-wide">Reserva de Espacios ULEAM</p>
            <h1 className="text-4xl font-bold text-foreground leading-tight">
              Gestiona reservas, reportes y notificaciones en un solo lugar
            </h1>
            <p className="text-muted-foreground text-lg">
              Frontend listo para conectarse a tus servicios REST (Python), GraphQL (Go) y WebSocket (TS/Node).
            </p>
            <div className="flex gap-3">
              <Button onClick={() => window.scrollTo({ top: 600, behavior: 'smooth' })}>Ver funcionalidades</Button>
              <Button variant="outline" onClick={() => (window.location.href = '/admin/dashboard')}>
                Ir al Panel (si eres admin)
              </Button>
            </div>
          </div>
          <Card className="shadow-lg">
            <CardHeader>
              <CardTitle>Acceso rápido</CardTitle>
              <p className="text-sm text-muted-foreground">Inicio público, inicia sesión desde el botón superior.</p>
            </CardHeader>
            <CardContent className="grid gap-4">
              <div className="flex items-start gap-3">
                <div className="p-2 rounded bg-primary/10 text-primary"><Building2 /></div>
                <div>
                  <p className="font-semibold">Front solo cliente</p>
                  <p className="text-sm text-muted-foreground">Consumimos servicios externos, sin backend embebido.</p>
                </div>
              </div>
              <div className="flex items-start gap-3">
                <div className="p-2 rounded bg-blue-500/10 text-blue-600"><Calendar /></div>
                <div>
                  <p className="font-semibold">Rutas separadas por rol</p>
                  <p className="text-sm text-muted-foreground">/app para usuarios y /admin para administradores.</p>
                </div>
              </div>
              <div className="flex items-start gap-3">
                <div className="p-2 rounded bg-green-500/10 text-green-700"><Laptop /></div>
                <div>
                  <p className="font-semibold">Login en el header</p>
                  <p className="text-sm text-muted-foreground">Modal de acceso desde el botón "Iniciar sesión".</p>
                </div>
              </div>
              <div className="flex items-start gap-3">
                <div className="p-2 rounded bg-amber-500/10 text-amber-700"><ShieldCheck /></div>
                <div>
                  <p className="font-semibold">Guardas de rol</p>
                  <p className="text-sm text-muted-foreground">Protegemos rutas admin para evitar accesos no autorizados.</p>
                </div>
              </div>
            </CardContent>
          </Card>
        </section>
      </main>
    </div>
  );
}

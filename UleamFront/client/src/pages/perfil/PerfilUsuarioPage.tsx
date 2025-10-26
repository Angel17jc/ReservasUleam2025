import { useAuth } from '@/contexts/AuthContext';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';

export default function PerfilUsuarioPage() {
  const { user, logout, isAdmin } = useAuth();

  return (
    <div className="p-6 space-y-4">
      <h1 className="text-3xl font-bold text-foreground">Perfil de Usuario</h1>
      <p className="text-muted-foreground">Datos provenientes del servicio REST de autenticación.</p>

      <Card>
        <CardHeader>
          <CardTitle>{user?.nombre ?? 'Usuario'}</CardTitle>
        </CardHeader>
        <CardContent className="space-y-2">
          <p className="text-muted-foreground">Email: {user?.email ?? '—'}</p>
          <p className="text-muted-foreground">Rol: {user?.role ?? '—'} {isAdmin && '(admin)'}</p>
          <Button variant="outline" onClick={logout}>Cerrar sesión</Button>
        </CardContent>
      </Card>
    </div>
  );
}

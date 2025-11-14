import { useState } from 'react';
import { useAuth } from '@/contexts/AuthContext';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { accountApi } from '@/api/rest/accountApi';

export default function PerfilUsuarioPage() {
  const { user, logout, isAdmin } = useAuth();
  const [currentPassword, setCurrentPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [passwordChanged, setPasswordChanged] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const handleChangePassword = async () => {
    try {
      setErrorMsg(null);
      await accountApi.changePassword({
        current_password: currentPassword,
        new_password: newPassword,
      });
      setPasswordChanged(true);
      setCurrentPassword('');
      setNewPassword('');
    } catch (err: any) {
      const msg = err?.body?.detail || err?.message || 'No se pudo cambiar la contraseña';
      setErrorMsg(String(msg));
      setPasswordChanged(false);
    }
  };

  return (
    <div className="p-6 space-y-4">
      <h1 className="text-3xl font-bold text-foreground">Perfil de Usuario</h1>
      <p className="text-muted-foreground">Datos provenientes del servicio REST de autenticación.</p>

      <Card>
        <CardHeader>
          <CardTitle>{user?.nombre ?? 'Usuario'}</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <p className="text-muted-foreground">Email: {user?.email ?? '—'}</p>
            <p className="text-muted-foreground">
              Rol: {user?.tipoUsuarioNombre ?? user?.role ?? '—'} {isAdmin && '(admin)'}
            </p>
          </div>

          <div className="space-y-2">
            <h2 className="text-lg font-semibold">Cambiar contraseña</h2>
            <div className="space-y-1">
              <Label>Contraseña actual</Label>
              <Input
                type="password"
                value={currentPassword}
                onChange={(e) => setCurrentPassword(e.target.value)}
                placeholder="Introduce tu contraseña actual"
              />
            </div>
            <div className="space-y-1">
              <Label>Nueva contraseña</Label>
              <Input
                type="password"
                value={newPassword}
                onChange={(e) => setNewPassword(e.target.value)}
                placeholder="Introduce la nueva contraseña"
              />
            </div>
            <Button onClick={handleChangePassword} disabled={!currentPassword || !newPassword}>
              Actualizar contraseña
            </Button>
            {passwordChanged && <p className="text-green-600 text-sm">Contraseña actualizada correctamente.</p>}
            {errorMsg && <p className="text-destructive text-sm">{errorMsg}</p>}
          </div>

          <Button variant="outline" onClick={logout} data-testid="button-logout">
            Cerrar sesión
          </Button>
        </CardContent>
      </Card>
    </div>
  );
}

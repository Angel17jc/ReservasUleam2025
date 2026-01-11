import { FormEvent, useState } from 'react';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { useAuth } from '@/contexts/AuthContext';
import { useLocation } from 'wouter';
import { Eye, EyeOff } from 'lucide-react';

export type RegisterFormProps = {
  onSuccess?: (role: 'user' | 'admin') => void;
};

export function RegisterForm({ onSuccess }: RegisterFormProps) {
  const { register } = useAuth();
  const [, navigate] = useLocation();
  const [form, setForm] = useState({
    nombre: '',
    apellido: '',
    email: '',
    password: '',
    telefono: '',
    tipoUsuarioId: 3,
  });
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (event: FormEvent) => {
    event.preventDefault();
    setError(null);
    setLoading(true);
    try {
      const user = await register({
        nombre: form.nombre,
        apellido: form.apellido,
        email: form.email,
        password: form.password,
        telefono: form.telefono || undefined,
        tipoUsuarioId: form.tipoUsuarioId,
      });
      onSuccess?.(user.role);
      navigate(user.role === 'admin' ? '/admin/dashboard' : '/app/inicio');
    } catch (err) {
      setError((err as Error).message ?? 'No se pudo registrar');
    } finally {
      setLoading(false);
    }
  };

  const togglePasswordVisibility = () => setShowPassword((prev) => !prev);

  return (
    <form onSubmit={handleSubmit} className="space-y-3">
      <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
        <div className="space-y-2">
          <label className="text-sm font-medium text-foreground">Nombre</label>
          <Input
            value={form.nombre}
            onChange={(e) => setForm((f) => ({ ...f, nombre: e.target.value }))}
            required
            disabled={loading}
          />
        </div>
        <div className="space-y-2">
          <label className="text-sm font-medium text-foreground">Apellido</label>
          <Input
            value={form.apellido}
            onChange={(e) => setForm((f) => ({ ...f, apellido: e.target.value }))}
            disabled={loading}
          />
        </div>
      </div>

      <div className="space-y-2">
        <label className="text-sm font-medium text-foreground">Correo electrónico</label>
        <Input
          type="email"
          value={form.email}
          onChange={(e) => setForm((f) => ({ ...f, email: e.target.value }))}
          placeholder="correo@uleam.edu.ec"
          required
          disabled={loading}
        />
      </div>

      <div className="space-y-2">
        <label className="text-sm font-medium text-foreground">Contraseña</label>
        <div className="relative">
          <Input
            type={showPassword ? 'text' : 'password'}
            value={form.password}
            onChange={(e) => setForm((f) => ({ ...f, password: e.target.value }))}
            placeholder="••••••••"
            required
            disabled={loading}
            className="pr-10"
          />
          <button
            type="button"
            onClick={togglePasswordVisibility}
            className="absolute inset-y-0 right-0 flex items-center pr-3 text-muted-foreground hover:text-foreground transition-colors"
            aria-label={showPassword ? 'Ocultar contraseña' : 'Mostrar contraseña'}
            disabled={loading}
          >
            {showPassword ? <EyeOff size={18} /> : <Eye size={18} />}
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
        <div className="space-y-2">
          <label className="text-sm font-medium text-foreground">Teléfono (opcional)</label>
          <Input
            value={form.telefono}
            onChange={(e) => setForm((f) => ({ ...f, telefono: e.target.value }))}
            disabled={loading}
          />
        </div>
        <div className="space-y-2">
          <label className="text-sm font-medium text-foreground">Tipo de usuario</label>
          <Input
            type="number"
            min={1}
            max={3}
            value={form.tipoUsuarioId}
            onChange={(e) => setForm((f) => ({ ...f, tipoUsuarioId: Number(e.target.value) }))}
            disabled={loading}
          />
          <p className="text-xs text-muted-foreground">1=Admin, 2=Profesor, 3=Estudiante</p>
        </div>
      </div>

      {error && (
        <div className="rounded-md bg-destructive/10 p-3">
          <p className="text-destructive text-sm">{error}</p>
        </div>
      )}

      <Button type="submit" className="w-full" disabled={loading}>
        {loading ? 'Creando cuenta...' : 'Crear cuenta'}
      </Button>
    </form>
  );
}

interface RegisterDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

export function RegisterDialog({ open, onOpenChange }: RegisterDialogProps) {
  const { isAuthenticated, user } = useAuth();
  const [, navigate] = useLocation();

  if (isAuthenticated && user) {
    onOpenChange(false);
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-lg">
        <DialogHeader>
          <DialogTitle>Crear cuenta</DialogTitle>
          <p className="text-muted-foreground text-sm">
            Regístrate para usar el sistema de reservas.
          </p>
        </DialogHeader>
        <RegisterForm onSuccess={() => onOpenChange(false)} />
      </DialogContent>
    </Dialog>
  );
}

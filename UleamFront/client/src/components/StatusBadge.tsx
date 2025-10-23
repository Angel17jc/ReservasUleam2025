import { Badge } from '@/components/ui/badge';
import { cn } from '@/lib/utils';

// Tipos de estados posibles para una reserva
export type ReservaEstado = 'pendiente' | 'aprobada' | 'rechazada' | 'completada' | 'cancelada' | 'enCurso';

interface StatusBadgeProps {
  estado: ReservaEstado;
  className?: string;
}

// Configuración de colores y etiquetas para cada estado
const estadoConfig = {
  pendiente: {
    label: 'Pendiente',
    className: 'bg-reserva-pendiente/20 text-reserva-pendiente border-reserva-pendiente/30',
  },
  aprobada: {
    label: 'Aprobada',
    className: 'bg-reserva-aprobada/20 text-reserva-aprobada border-reserva-aprobada/30',
  },
  rechazada: {
    label: 'Rechazada',
    className: 'bg-reserva-rechazada/20 text-reserva-rechazada border-reserva-rechazada/30',
  },
  completada: {
    label: 'Completada',
    className: 'bg-reserva-completada/20 text-reserva-completada border-reserva-completada/30',
  },
  cancelada: {
    label: 'Cancelada',
    className: 'bg-reserva-cancelada/20 text-reserva-cancelada border-reserva-cancelada/30',
  },
  enCurso: {
    label: 'En Curso',
    className: 'bg-reserva-enCurso/20 text-reserva-enCurso border-reserva-enCurso/30',
  },
};

export function StatusBadge({ estado, className }: StatusBadgeProps) {
  const config = estadoConfig[estado];
  
  return (
    <Badge 
      variant="outline" 
      className={cn(config.className, className)}
      data-testid={`badge-${estado}`}
    >
      {config.label}
    </Badge>
  );
}

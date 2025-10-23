import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { StatusBadge, type ReservaEstado } from './StatusBadge';
import { Calendar, Clock, MapPin, User } from 'lucide-react';
import { cn } from '@/lib/utils';

// Propiedades del componente de tarjeta de reserva
interface ReservationCardProps {
  id: string;
  espacio: string;
  usuario?: string;
  fecha: string;
  horaInicio: string;
  horaFin: string;
  tipoEvento: string;
  estado: ReservaEstado;
  ubicacion?: string;
  onCancel?: () => void;
  onApprove?: () => void;
  onReject?: () => void;
  showActions?: boolean;
  className?: string;
}

export function ReservationCard({
  id,
  espacio,
  usuario,
  fecha,
  horaInicio,
  horaFin,
  tipoEvento,
  estado,
  ubicacion,
  onCancel,
  onApprove,
  onReject,
  showActions = true,
  className,
}: ReservationCardProps) {
  // Determinar si se puede cancelar la reserva
  const canCancel = estado === 'pendiente' || estado === 'aprobada';

  return (
    <Card className={cn('hover-elevate', className)} data-testid={`card-reservation-${id}`}>
      <CardContent className="p-6">
        <div className="flex items-start justify-between mb-4">
          <div className="flex-1">
            <h3 className="text-lg font-semibold text-foreground">{espacio}</h3>
            <p className="text-sm text-muted-foreground">{tipoEvento}</p>
          </div>
          <StatusBadge estado={estado} />
        </div>

        <div className="space-y-2 mb-4">
          {usuario && (
            <div className="flex items-center gap-2 text-sm text-muted-foreground">
              <User size={16} />
              <span>{usuario}</span>
            </div>
          )}
          <div className="flex items-center gap-2 text-sm text-muted-foreground">
            <Calendar size={16} />
            <span>{fecha}</span>
          </div>
          <div className="flex items-center gap-2 text-sm text-muted-foreground">
            <Clock size={16} />
            <span>{horaInicio} - {horaFin}</span>
          </div>
          {ubicacion && (
            <div className="flex items-center gap-2 text-sm text-muted-foreground">
              <MapPin size={16} />
              <span>{ubicacion}</span>
            </div>
          )}
        </div>

        {showActions && (
          <div className="flex gap-2 mt-4">
            {onApprove && estado === 'pendiente' && (
              <Button
                size="sm"
                className="bg-reserva-aprobada hover:bg-reserva-aprobada/90"
                onClick={onApprove}
                data-testid={`button-approve-${id}`}
              >
                Aprobar
              </Button>
            )}
            {onReject && estado === 'pendiente' && (
              <Button
                size="sm"
                variant="destructive"
                onClick={onReject}
                data-testid={`button-reject-${id}`}
              >
                Rechazar
              </Button>
            )}
            {onCancel && canCancel && (
              <Button
                size="sm"
                variant="outline"
                onClick={onCancel}
                data-testid={`button-cancel-${id}`}
              >
                Cancelar
              </Button>
            )}
          </div>
        )}
      </CardContent>
    </Card>
  );
}

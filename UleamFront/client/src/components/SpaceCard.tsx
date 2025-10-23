import { Card, CardContent, CardFooter } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Users, MapPin } from 'lucide-react';
import { cn } from '@/lib/utils';
import { ReactNode } from 'react';

// Propiedades del componente de tarjeta de espacio
interface SpaceCardProps {
  id: string;
  nombre: string;
  codigo: string;
  categoria: string;
  capacidad: number;
  ubicacion?: string;
  disponible?: boolean;
  className?: string;
  accentColors?: {
    from: string;
    to: string;
  };
  bannerIcon?: ReactNode;
}

export function SpaceCard({
  id,
  nombre,
  codigo,
  categoria,
  capacidad,
  ubicacion,
  disponible = true,
  className,
  accentColors,
  bannerIcon,
}: SpaceCardProps) {
  const gradientFrom = accentColors?.from ?? '#E63946';
  const gradientTo = accentColors?.to ?? '#C1121F';

  return (
    <Card className={cn('overflow-hidden hover-elevate', className)} data-testid={`card-space-${id}`}>
      <div className="relative h-48">
        <div
          className="absolute inset-0"
          style={{ background: `linear-gradient(135deg, ${gradientFrom}, ${gradientTo})` }}
        />
        <div className="absolute inset-0 bg-[radial-gradient(circle_at_25%_25%,rgba(255,255,255,0.16),transparent_35%)]" />

        <div className="absolute top-3 right-3">
          <Badge className="bg-black/30 text-white border border-white/20">
            {categoria}
          </Badge>
        </div>

        <div className="relative h-full flex flex-col justify-end p-4 text-white drop-shadow-lg">
          <div className="flex items-center gap-3">
            {bannerIcon && (
              <div className="flex h-10 w-10 items-center justify-center rounded-full bg-white/15 backdrop-blur-sm">
                {bannerIcon}
              </div>
            )}
            <div>
              <p className="text-xs uppercase tracking-wide opacity-80">{categoria}</p>
              <p className="text-lg font-semibold leading-tight">{nombre}</p>
            </div>
          </div>
        </div>

        {!disponible && (
          <div className="absolute inset-0 bg-black/50 flex items-center justify-center">
            <Badge variant="destructive">No Disponible</Badge>
          </div>
        )}
      </div>
      <CardContent className="p-4 space-y-3">
        <div>
          <p className="text-sm text-muted-foreground">{codigo}</p>
        </div>
        <div className="flex items-center justify-between text-sm">
          <div className="flex items-center gap-2 text-muted-foreground">
            <Users size={16} />
            <span>{capacidad} personas</span>
          </div>
          {ubicacion && (
            <div className="flex items-center gap-1 text-muted-foreground">
              <MapPin size={14} />
              <span className="text-xs">{ubicacion}</span>
            </div>
          )}
        </div>
      </CardContent>
      <CardFooter className="p-4 pt-0">
        <Button 
          className="w-full" 
          disabled={!disponible}
          data-testid={`button-reserve-${id}`}
          onClick={() => console.log(`Reservar ${nombre}`)}
        >
          Reservar
        </Button>
      </CardFooter>
    </Card>
  );
}

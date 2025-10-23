import { Card, CardContent } from '@/components/ui/card';
import { LucideIcon } from 'lucide-react';
import { cn } from '@/lib/utils';

// Propiedades del componente de tarjeta de métrica
interface MetricCardProps {
  title: string;
  value: string | number;
  icon: LucideIcon;
  description?: string;
  trend?: 'up' | 'down';
  trendValue?: string;
  className?: string;
}

export function MetricCard({
  title,
  value,
  icon: Icon,
  description,
  trend,
  trendValue,
  className,
}: MetricCardProps) {
  return (
    <Card className={cn('hover-elevate', className)} data-testid={`card-metric-${title.toLowerCase().replace(/\s+/g, '-')}`}>
      <CardContent className="p-6">
        <div className="flex items-start justify-between">
          <div className="flex-1">
            <p className="text-sm font-medium text-muted-foreground">{title}</p>
            <p className="text-4xl font-bold text-foreground mt-2">{value}</p>
            {description && (
              <p className="text-sm text-muted-foreground mt-2">{description}</p>
            )}
            {trend && trendValue && (
              <div className="flex items-center gap-1 mt-2">
                <span className={cn(
                  'text-sm font-medium',
                  trend === 'up' ? 'text-green-600' : 'text-red-600'
                )}>
                  {trend === 'up' ? '↑' : '↓'} {trendValue}
                </span>
                <span className="text-xs text-muted-foreground">vs mes anterior</span>
              </div>
            )}
          </div>
          <div className="w-12 h-12 rounded-full bg-primary/10 flex items-center justify-center">
            <Icon className="text-primary" size={24} />
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

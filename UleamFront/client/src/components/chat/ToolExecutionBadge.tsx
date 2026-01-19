/**
 * ToolExecutionBadge Component
 * 
 * Displays MCP tool execution information in messages
 */

import { Badge } from '@/components/ui/badge';
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from '@/components/ui/tooltip';
import { CheckCircle2, XCircle, Wrench, Clock } from 'lucide-react';
import type { ToolExecutionInfo } from '@/types/aiService';
import { cn } from '@/lib/utils';

// ============================================
// TYPES
// ============================================

interface ToolExecutionBadgeProps {
  toolExecution: ToolExecutionInfo;
  className?: string;
}

// ============================================
// TOOL ICONS
// ============================================

const TOOL_ICONS: Record<string, string> = {
  buscarespacios: '🔍',
  verreservas: '📋',
  crearreserva: '✅',
  registrarusuario: '👤',
  estadisticasreservas: '📊',
};

// ============================================
// TOOL LABELS
// ============================================

const TOOL_LABELS: Record<string, string> = {
  buscarespacios: 'Buscar Espacios',
  verreservas: 'Ver Reservas',
  crearreserva: 'Crear Reserva',
  registrarusuario: 'Registrar Usuario',
  estadisticasreservas: 'Estadísticas',
};

// ============================================
// COMPONENT
// ============================================

export function ToolExecutionBadge({ toolExecution, className }: Readonly<ToolExecutionBadgeProps>) {
  const { tool_name, success, error_message, execution_time } = toolExecution;

  const icon = TOOL_ICONS[tool_name] || '🔧';
  const label = TOOL_LABELS[tool_name] || tool_name;

  // Build tooltip content
  const tooltipContent = (
    <div className="space-y-1 text-xs">
      <div className="font-semibold">{label}</div>
      {execution_time && (
        <div className="flex items-center gap-1 text-muted-foreground">
          <Clock className="h-3 w-3" />
          <span>{execution_time.toFixed(2)}s</span>
        </div>
      )}
      {error_message && (
        <div className="text-destructive">
          <span className="font-medium">Error:</span> {error_message}
        </div>
      )}
    </div>
  );

  return (
    <TooltipProvider>
      <Tooltip>
        <TooltipTrigger asChild>
          <Badge
            variant={success ? 'default' : 'destructive'}
            className={cn(
              'flex items-center gap-1.5 px-2.5 py-1 cursor-help',
              className,
            )}
          >
            <span>{icon}</span>
            <span className="text-xs font-medium">{label}</span>
            {success ? (
              <CheckCircle2 className="h-3 w-3" />
            ) : (
              <XCircle className="h-3 w-3" />
            )}
          </Badge>
        </TooltipTrigger>
        <TooltipContent side="top" className="max-w-xs">
          {tooltipContent}
        </TooltipContent>
      </Tooltip>
    </TooltipProvider>
  );
}

// ============================================
// TOOL EXECUTIONS LIST
// ============================================

interface ToolExecutionsListProps {
  toolExecutions: ToolExecutionInfo[];
  className?: string;
}

/**
 * Display multiple tool executions
 */
export function ToolExecutionsList({ toolExecutions, className }: Readonly<ToolExecutionsListProps>) {
  if (!toolExecutions || toolExecutions.length === 0) return null;

  return (
    <div className={cn('flex flex-wrap gap-1.5', className)}>
      {toolExecutions.map((tool, index) => (
        <ToolExecutionBadge key={`${tool.tool_name}-${index}`} toolExecution={tool} />
      ))}
    </div>
  );
}

// ============================================
// LOADING BADGE
// ============================================

interface ToolLoadingBadgeProps {
  toolName?: string;
  className?: string;
}

/**
 * Display loading state for tool execution
 */
export function ToolLoadingBadge({ toolName, className }: Readonly<ToolLoadingBadgeProps>) {
  return (
    <Badge variant="secondary" className={cn('flex items-center gap-1.5 px-2.5 py-1', className)}>
      <Wrench className="h-3 w-3 animate-pulse" />
      <span className="text-xs">
        {toolName ? `Ejecutando ${toolName}...` : 'Ejecutando herramienta...'}
      </span>
    </Badge>
  );
}

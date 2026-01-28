/**
 * ProviderSelector Component
 * 
 * Dropdown to select LLM provider (Gemini or Groq)
 */

import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Label } from '@/components/ui/label';
import { Info } from 'lucide-react';
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from '@/components/ui/tooltip';
import type { LLMProvider } from '@/types/aiService';
import { PROVIDER_OPTIONS } from '@/types/aiService';
import { cn } from '@/lib/utils';

// ============================================
// TYPES
// ============================================

interface ProviderSelectorProps {
  value: LLMProvider;
  onChange: (provider: LLMProvider) => void;
  disabled?: boolean;
  className?: string;
  showLabel?: boolean;
  showDescription?: boolean;
}

// ============================================
// COMPONENT
// ============================================

export function ProviderSelector({
  value,
  onChange,
  disabled = false,
  className,
  showLabel = true,
  showDescription = false,
}: Readonly<ProviderSelectorProps>) {
  const selectedProvider = PROVIDER_OPTIONS.find((p) => p.value === value);

  return (
    <div className={cn('space-y-2', className)}>
      {showLabel && (
        <div className="flex items-center gap-2">
          <Label htmlFor="provider-select" className="text-sm font-medium">
            Modelo de IA
          </Label>
          <TooltipProvider>
            <Tooltip>
              <TooltipTrigger asChild>
                <Info className="h-3.5 w-3.5 text-muted-foreground cursor-help" />
              </TooltipTrigger>
              <TooltipContent side="right" className="max-w-xs">
                <p className="text-xs">
                  <strong>Gemini Pro:</strong> Soporta análisis de imágenes (visión)
                </p>
                <p className="text-xs mt-1">
                  <strong>Groq Llama:</strong> Ultra rápido para texto (sin visión)
                </p>
              </TooltipContent>
            </Tooltip>
          </TooltipProvider>
        </div>
      )}

      <Select value={value} onValueChange={(v) => onChange(v as LLMProvider)} disabled={disabled}>
        <SelectTrigger id="provider-select" className="w-full h-10">
          <SelectValue placeholder="Selecciona un modelo" />
        </SelectTrigger>
        <SelectContent 
          className="z-[10000] bg-popover min-w-[240px]" 
          position="popper"
          sideOffset={4}
        >
          {PROVIDER_OPTIONS.map((provider) => (
            <SelectItem 
              key={provider.value} 
              value={provider.value}
              className="cursor-pointer py-3"
            >
              <div className="flex flex-col gap-1">
                <div className="flex items-center gap-2">
                  <span className="font-semibold text-sm">{provider.label}</span>
                  {provider.supportsVision && (
                    <span className="text-xs px-1.5 py-0.5 rounded bg-primary/10 text-primary font-medium">
                      Visión
                    </span>
                  )}
                </div>
                <span className="text-xs text-muted-foreground">{provider.description}</span>
              </div>
            </SelectItem>
          ))}
        </SelectContent>
      </Select>

      {showDescription && selectedProvider && (
        <p className="text-xs text-muted-foreground">{selectedProvider.description}</p>
      )}
    </div>
  );
}

// ============================================
// COMPACT VERSION
// ============================================

interface ProviderBadgeProps {
  provider: LLMProvider;
  className?: string;
}

/**
 * Compact badge showing the current provider
 */
export function ProviderBadge({ provider, className }: Readonly<ProviderBadgeProps>) {
  const providerInfo = PROVIDER_OPTIONS.find((p) => p.value === provider);

  if (!providerInfo) return null;

  return (
    <TooltipProvider>
      <Tooltip>
        <TooltipTrigger asChild>
          <div
            className={cn(
              'inline-flex items-center gap-1.5 px-2 py-1 rounded-md bg-secondary text-secondary-foreground text-xs font-medium cursor-help',
              className,
            )}
          >
            <span>{providerInfo.label}</span>
            {providerInfo.supportsVision && <span className="text-[10px]">👁️</span>}
          </div>
        </TooltipTrigger>
        <TooltipContent>
          <p className="text-xs">{providerInfo.description}</p>
        </TooltipContent>
      </Tooltip>
    </TooltipProvider>
  );
}

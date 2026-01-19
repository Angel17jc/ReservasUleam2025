/**
 * MessageBubble Component
 * 
 * Individual message bubble for chat interface
 * Supports text, images, tool executions, and loading states
 */

import { forwardRef, useState } from 'react';
import { Avatar, AvatarFallback } from '@/components/ui/avatar';
import { Card } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Bot, User, Copy, Check, Image as ImageIcon } from 'lucide-react';
import { ToolExecutionsList } from './ToolExecutionBadge';
import { ProviderBadge } from './ProviderSelector';
import type { ChatMessage } from '@/types/aiService';
import { cn } from '@/lib/utils';

// ============================================
// TYPES
// ============================================

interface MessageBubbleProps {
  message: ChatMessage;
  className?: string;
}

// ============================================
// COMPONENT
// ============================================

export const MessageBubble = forwardRef<HTMLDivElement, MessageBubbleProps>(
  ({ message, className }, ref) => {
    const [copied, setCopied] = useState(false);
    const isUser = message.role === 'user';
    const isAssistant = message.role === 'assistant';
    const isLoading = message.isLoading;

    // Format timestamp
    const timestamp = new Date(message.timestamp).toLocaleTimeString('es-ES', {
      hour: '2-digit',
      minute: '2-digit',
    });

    // Copy message content
    const handleCopy = async () => {
      await navigator.clipboard.writeText(message.content);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    };

    return (
      <div
        ref={ref}
        className={cn(
          'flex gap-3 group',
          isUser ? 'flex-row-reverse' : 'flex-row',
          className,
        )}
      >
        {/* Avatar */}
        <Avatar className={cn('h-8 w-8 shrink-0', isUser ? 'bg-primary' : 'bg-secondary')}>
          <AvatarFallback>
            {isUser ? <User className="h-4 w-4" /> : <Bot className="h-4 w-4" />}
          </AvatarFallback>
        </Avatar>

        {/* Message Content */}
        <div className={cn('flex flex-col gap-1.5 min-w-0 flex-1', isUser ? 'items-end max-w-[85%] ml-auto' : 'max-w-[85%]')}>
          {/* Message Card */}
          <Card
            className={cn(
              'px-4 py-3 shadow-sm break-words overflow-hidden',
              isUser
                ? 'bg-primary text-primary-foreground'
                : 'bg-muted',
              isLoading && 'animate-pulse',
            )}
          >
            {/* Image Metadata */}
            {message.imageMetadata && (
              <div className="flex items-center gap-2 mb-2 pb-2 border-b border-border/50">
                <ImageIcon className="h-4 w-4 text-muted-foreground" />
                <span className="text-xs text-muted-foreground">
                  {message.imageMetadata.format} • {message.imageMetadata.width}x
                  {message.imageMetadata.height} •{' '}
                  {message.imageMetadata.file_size_mb.toFixed(2)}MB
                </span>
              </div>
            )}

            {/* Message Text */}
            <div className="text-sm whitespace-pre-wrap break-words overflow-wrap-anywhere max-w-full">
              {isLoading ? (
                <span className="inline-flex items-center gap-1">
                  <span className="animate-bounce">●</span>
                  <span className="animate-bounce delay-75">●</span>
                  <span className="animate-bounce delay-150">●</span>
                </span>
              ) : (
                message.content
              )}
            </div>

            {/* Error Message */}
            {message.error && (
              <div className="mt-2 pt-2 border-t border-destructive/30">
                <p className="text-xs text-destructive break-words">
                  <strong>Error:</strong> {message.error}
                </p>
              </div>
            )}

            {/* Tool Executions */}
            {message.toolExecutions && message.toolExecutions.length > 0 && (
              <div className="mt-3 pt-3 border-t border-border/50">
                <ToolExecutionsList toolExecutions={message.toolExecutions} />
              </div>
            )}
          </Card>

          {/* Message Footer */}
          <div
            className={cn(
              'flex items-center gap-2 px-1',
              isUser ? 'flex-row-reverse' : 'flex-row',
            )}
          >
            {/* Timestamp */}
            <span className="text-xs text-muted-foreground">{timestamp}</span>

            {/* Provider Badge */}
            {message.provider && !isUser && (
              <ProviderBadge provider={message.provider as any} />
            )}

            {/* Tokens Used */}
            {message.tokensUsed && (
              <Badge variant="outline" className="text-xs px-1.5 py-0">
                {message.tokensUsed} tokens
              </Badge>
            )}

            {/* Copy Button (visible on hover for assistant messages) */}
            {isAssistant && !isLoading && (
              <Button
                variant="ghost"
                size="sm"
                className="h-6 w-6 p-0 opacity-0 group-hover:opacity-100 transition-opacity"
                onClick={handleCopy}
                title="Copiar mensaje"
              >
                {copied ? (
                  <Check className="h-3 w-3 text-green-600" />
                ) : (
                  <Copy className="h-3 w-3" />
                )}
              </Button>
            )}
          </div>
        </div>
      </div>
    );
  },
);

MessageBubble.displayName = 'MessageBubble';

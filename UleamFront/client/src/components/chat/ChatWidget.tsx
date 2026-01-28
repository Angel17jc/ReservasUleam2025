/**
 * ChatWidget Component
 * 
 * Main floating chat widget for AI assistant
 * Features:
 * - Collapsible chat window
 * - Text and image messages
 * - MCP tool execution display
 * - Provider selection
 * - Conversation history
 * - Auto-scroll to latest message
 */

import { useState, useEffect, useRef, forwardRef, useImperativeHandle } from 'react';
import { Card, CardContent, CardFooter, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Separator } from '@/components/ui/separator';
import {
  Bot,
  Minimize2,
  Maximize2,
  X,
  Settings,
  MessageSquare,
  Trash2,
  Loader2,
} from 'lucide-react';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Badge } from '@/components/ui/badge';
import { MessageBubble } from './MessageBubble';
import { ChatInput } from './ChatInput';
import { ProviderSelector } from './ProviderSelector';
import { useChatAI } from '@/hooks/useChatAI';
import { providerSupportsVision } from '@/types/aiService';
import { cn } from '@/lib/utils';

// ============================================
// TYPES
// ============================================

interface ChatWidgetProps {
  /** Initial open state */
  defaultOpen?: boolean;
  /** Position on screen */
  position?: 'bottom-right' | 'bottom-left' | 'top-right' | 'top-left';
  /** Custom className */
  className?: string;
  /** Hide floating button (controlled by external trigger) */
  hideFloatingButton?: boolean;
}

export interface ChatWidgetRef {
  open: () => void;
  close: () => void;
  toggle: () => void;
}

// ============================================
// COMPONENT
// ============================================

export const ChatWidget = forwardRef<ChatWidgetRef, ChatWidgetProps>(function ChatWidget({
  defaultOpen = false,
  position = 'bottom-right',
  className,
  hideFloatingButton = false,
}, ref) {
  // State
  const [isOpen, setIsOpen] = useState(defaultOpen);
  const [isMinimized, setIsMinimized] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const scrollAreaRef = useRef<HTMLDivElement>(null);

  // Chat hook
  const {
    messages,
    conversationId,
    provider,
    isLoading,
    error,
    totalTokens,
    hasToolExecutions,
    sendMessage,
    sendImageMessage,
    startNewConversation,
    changeProvider,
    isSendingText,
    isSendingImage,
  } = useChatAI({
    defaultProvider: 'gemini',
    optimisticUpdates: true,
    autoScroll: true,
  });

  // ============================================
  // EFFECTS
  // ============================================

  /**
   * Expose methods to parent via ref
   */
  useImperativeHandle(ref, () => ({
    open: () => {
      setIsOpen(true);
      setIsMinimized(false);
    },
    close: () => {
      setIsOpen(false);
      setIsMinimized(false);
    },
    toggle: () => {
      setIsOpen(!isOpen);
      if (!isOpen) {
        setIsMinimized(false);
      }
    },
  }), [isOpen]);

  /**
   * Auto-scroll to bottom when new messages arrive
   */
  useEffect(() => {
    if (isOpen && !isMinimized && messages.length > 0) {
      messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }
  }, [messages, isOpen, isMinimized]);

  // ============================================
  // HANDLERS
  // ============================================

  const handleToggleOpen = () => {
    setIsOpen(!isOpen);
    if (!isOpen) {
      setIsMinimized(false);
    }
  };

  const handleToggleMinimize = () => {
    setIsMinimized(!isMinimized);
  };

  const handleClose = () => {
    setIsOpen(false);
    setIsMinimized(false);
  };

  const handleNewConversation = () => {
    startNewConversation();
  };

  const handleProviderChange = (newProvider: any) => {
    changeProvider(newProvider);
  };

  // ============================================
  // COMPUTED
  // ============================================

  const positionClasses = {
    'bottom-right': 'bottom-6 right-6',
    'bottom-left': 'bottom-6 left-[19rem]', // 18rem (sidebar) + 1rem spacing
    'top-right': 'top-6 right-6',
    'top-left': 'top-6 left-6',
  };

  const supportsImages = providerSupportsVision(provider);
  const isProcessing = isSendingText || isSendingImage;

  // ============================================
  // RENDER: FLOATING BUTTON
  // ============================================

  if (!isOpen && !hideFloatingButton) {
    return (
      <Button
        size="lg"
        className={cn(
          'fixed z-[9999] h-16 w-16 rounded-full shadow-2xl hover:scale-110 transition-all duration-200 animate-pulse hover:animate-none',
          'bg-gradient-to-br from-primary to-primary/80 hover:from-primary hover:to-primary/90',
          positionClasses[position],
          className,
        )}
        onClick={handleToggleOpen}
        title="Abrir asistente de IA"
        aria-label="Abrir chat de asistente IA"
      >
        <Bot className="h-7 w-7" />
      </Button>
    );
  }

  // Si está oculto el botón y no está abierto, no renderizar nada
  if (!isOpen && hideFloatingButton) {
    return null;
  }

  // ============================================
  // RENDER: CHAT WINDOW
  // ============================================

  return (
    <Card
      className={cn(
        'fixed z-[9999] flex flex-col shadow-2xl border-2',
        positionClasses[position],
        isMinimized ? 'h-auto w-80' : 'h-[600px] w-96',
        'transition-all duration-300 ease-in-out',
        className,
      )}
    >
      {/* Header */}
      <CardHeader className="flex-shrink-0 p-4 space-y-0">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="h-8 w-8 rounded-full bg-primary flex items-center justify-center">
              <Bot className="h-5 w-5 text-primary-foreground" />
            </div>
            <div>
              <CardTitle className="text-sm font-semibold">Asistente ULEAM</CardTitle>
              <p className="text-xs text-muted-foreground">
                {conversationId ? `Conversación #${conversationId}` : 'Nueva conversación'}
              </p>
            </div>
          </div>

          <div className="flex items-center gap-1">
            {/* Settings Dropdown */}
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button 
                  variant="ghost" 
                  size="sm" 
                  className="h-8 w-8 p-0 hover:bg-accent"
                  title="Configuración"
                >
                  <Settings className="h-4 w-4" />
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent 
                align="end" 
                className="w-72 max-h-[500px] overflow-y-auto z-[10000]"
                sideOffset={8}
              >
                <DropdownMenuLabel className="text-base font-semibold">
                  Configuración
                </DropdownMenuLabel>
                <DropdownMenuSeparator />
                
                <div className="p-3 space-y-2">
                  <ProviderSelector
                    value={provider}
                    onChange={handleProviderChange}
                    showLabel={true}
                    showDescription={false}
                  />
                </div>

                <DropdownMenuSeparator />
                
                <DropdownMenuItem onClick={handleNewConversation}>
                  <MessageSquare className="mr-2 h-4 w-4" />
                  <span>Nueva conversación</span>
                </DropdownMenuItem>

                {conversationId && (
                  <DropdownMenuItem onClick={handleNewConversation} className="text-destructive">
                    <Trash2 className="mr-2 h-4 w-4" />
                    <span>Borrar conversación</span>
                  </DropdownMenuItem>
                )}
              </DropdownMenuContent>
            </DropdownMenu>

            {/* Minimize Button */}
            <Button
              variant="ghost"
              size="sm"
              className="h-8 w-8 p-0"
              onClick={handleToggleMinimize}
              title={isMinimized ? 'Maximizar' : 'Minimizar'}
            >
              {isMinimized ? <Maximize2 className="h-4 w-4" /> : <Minimize2 className="h-4 w-4" />}
            </Button>

            {/* Close Button */}
            <Button
              variant="ghost"
              size="sm"
              className="h-8 w-8 p-0"
              onClick={handleClose}
              title="Cerrar"
            >
              <X className="h-4 w-4" />
            </Button>
          </div>
        </div>

        {/* Stats Bar */}
        {!isMinimized && (messages.length > 0 || hasToolExecutions) && (
          <div className="flex items-center gap-2 mt-2 pt-2 border-t">
            <Badge variant="secondary" className="text-xs">
              {messages.length} mensajes
            </Badge>
            {totalTokens > 0 && (
              <Badge variant="outline" className="text-xs">
                {totalTokens} tokens
              </Badge>
            )}
            {hasToolExecutions && (
              <Badge variant="default" className="text-xs">
                🔧 Herramientas usadas
              </Badge>
            )}
          </div>
        )}
      </CardHeader>

      {/* Messages Area */}
      {!isMinimized && (
        <>
          <Separator />
          <CardContent className="flex-1 p-0 overflow-hidden min-h-0">
            <ScrollArea ref={scrollAreaRef} className="h-full w-full">
              <div className="px-4 py-4 space-y-4">
              {/* Empty State */}
              {messages.length === 0 && !isLoading && (
                <div className="flex flex-col items-center justify-center h-full text-center p-6 space-y-3">
                  <div className="h-16 w-16 rounded-full bg-primary/10 flex items-center justify-center">
                    <Bot className="h-8 w-8 text-primary" />
                  </div>
                  <div>
                    <h3 className="font-semibold text-sm">¡Hola! Soy tu asistente ULEAM</h3>
                    <p className="text-xs text-muted-foreground mt-1">
                      Puedo ayudarte a buscar espacios, crear reservas, ver estadísticas y más.
                    </p>
                    <p className="text-xs text-muted-foreground mt-2">
                      {supportsImages
                        ? 'También puedo analizar imágenes. ¡Pruébalo!'
                        : 'Escribe un mensaje para comenzar.'}
                    </p>
                  </div>
                  <div className="flex flex-wrap gap-2 mt-4">
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => sendMessage('Busca aulas disponibles mañana')}
                    >
                      Buscar espacios
                    </Button>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => sendMessage('Muestra mis reservas')}
                    >
                      Ver reservas
                    </Button>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => sendMessage('Dame estadísticas de reservas')}
                    >
                      Estadísticas
                    </Button>
                  </div>
                </div>
              )}

              {/* Messages List */}
              {messages.length > 0 && (
                <>
                  {messages.map((message) => (
                    <MessageBubble key={message.id} message={message} />
                  ))}
                  <div ref={messagesEndRef} />
                </>
              )}

              {/* Loading Indicator */}
              {isLoading && messages.length === 0 && (
                <div className="flex items-center justify-center h-full">
                  <Loader2 className="h-6 w-6 animate-spin text-primary" />
                </div>
              )}
              </div>
            </ScrollArea>
          </CardContent>

          {/* Error Alert */}
          {error && (
            <div className="px-4 py-2">
              <Alert variant="destructive">
                <AlertDescription className="text-xs">
                  {error.message || 'Error al procesar el mensaje'}
                </AlertDescription>
              </Alert>
            </div>
          )}

          <Separator />

          {/* Input Area */}
          <CardFooter className="flex-shrink-0 p-4">
            <ChatInput
              onSendMessage={sendMessage}
              onSendImage={sendImageMessage}
              disabled={isProcessing}
              placeholder={
                supportsImages
                  ? 'Escribe o adjunta una imagen...'
                  : 'Escribe un mensaje...'
              }
              supportsImages={supportsImages}
            />
          </CardFooter>
        </>
      )}
    </Card>
  );
});

/**
 * useChatAI Hook
 * 
 * Custom hook for managing AI chat state and interactions
 * Uses TanStack Query for data fetching and caching
 */

import { useState, useCallback, useMemo } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { useAuth } from '@/contexts/AuthContext';
import { aiServiceApi, formatErrorMessage } from '@/api/aiServiceApi';
import type {
  ChatMessage,
  LLMProvider,
  ChatRequest,
  ChatImageRequest,
} from '@/types/aiService';
import { messageToChat } from '@/types/aiService';

// ============================================
// QUERY KEYS
// ============================================

const chatKeys = {
  all: ['chat'] as const,
  conversations: (userId: number) => [...chatKeys.all, 'conversations', userId] as const,
  conversation: (conversationId: number) =>
    [...chatKeys.all, 'conversation', conversationId] as const,
  messages: (conversationId: number) => [...chatKeys.all, 'messages', conversationId] as const,
};

// ============================================
// HOOK OPTIONS
// ============================================

export interface UseChatAIOptions {
  /** Initial conversation ID (optional) */
  conversationId?: number;
  /** Default LLM provider */
  defaultProvider?: LLMProvider;
  /** Enable optimistic updates */
  optimisticUpdates?: boolean;
  /** Auto-scroll to bottom on new messages */
  autoScroll?: boolean;
}

// ============================================
// MAIN HOOK
// ============================================

export function useChatAI(options: UseChatAIOptions = {}) {
  const {
    conversationId: initialConversationId,
    defaultProvider = 'gemini',
    optimisticUpdates = true,
  } = options;

  const { user } = useAuth();
  const queryClient = useQueryClient();

  // Local state
  const [conversationId, setConversationId] = useState<number | null>(
    initialConversationId || null,
  );
  const [provider, setProvider] = useState<LLMProvider>(defaultProvider);
  const [temperature, setTemperature] = useState(0.7);
  const [localMessages, setLocalMessages] = useState<ChatMessage[]>([]);

  // ============================================
  // QUERIES
  // ============================================

  /**
   * Fetch conversation history
   */
  const { data: conversation, isLoading: isLoadingConversation } = useQuery({
    queryKey: chatKeys.conversation(conversationId!),
    queryFn: () => aiServiceApi.getConversation(conversationId!),
    enabled: conversationId !== null,
    staleTime: 30000, // 30 seconds
  });

  /**
   * Fetch user's conversations list
   */
  const { data: conversationsList } = useQuery({
    queryKey: chatKeys.conversations(Number(user?.id) || 0),
    queryFn: () => aiServiceApi.listConversations(Number(user?.id) || 0),
    enabled: Boolean(user?.id),
    staleTime: 60000, // 1 minute
  });

  // ============================================
  // MUTATIONS
  // ============================================

  /**
   * Send text message mutation
   */
  const sendTextMessageMutation = useMutation({
    mutationFn: async (request: Omit<ChatRequest, 'usuario_id'>) => {
      if (!user?.id) throw new Error('Usuario no autenticado');

      return aiServiceApi.sendTextMessage({
        ...request,
        usuario_id: Number(user.id),
        conversation_id: conversationId || undefined,
        provider,
        temperature,
      });
    },
    onMutate: async (request) => {
      if (optimisticUpdates) {
        // Optimistic update: add user message immediately
        const tempMessage: ChatMessage = {
          id: `temp-${Date.now()}`,
          role: 'user',
          content: request.content,
          timestamp: new Date().toISOString(),
          provider,
          isLoading: false,
        };

        setLocalMessages((prev) => [...prev, tempMessage]);

        // Add loading assistant message
        const loadingMessage: ChatMessage = {
          id: `loading-${Date.now()}`,
          role: 'assistant',
          content: '',
          timestamp: new Date().toISOString(),
          provider,
          isLoading: true,
        };

        setLocalMessages((prev) => [...prev, loadingMessage]);
      }
    },
    onSuccess: (response, request) => {
      // Update conversation ID if this is the first message
      if (!conversationId) {
        setConversationId(response.conversation_id);
      }

      // Remove optimistic messages and add real messages
      setLocalMessages((prev) => {
        const withoutOptimistic = prev.filter(
          (msg) => !msg.id.startsWith('temp-') && !msg.id.startsWith('loading-'),
        );

        const userMessage: ChatMessage = {
          id: `msg-${Date.now()}-user`,
          role: 'user',
          content: request.content,
          timestamp: new Date().toISOString(),
          provider,
        };

        const assistantMessage: ChatMessage = {
          id: `msg-${Date.now()}-assistant`,
          role: 'assistant',
          content: response.assistant_response,
          timestamp: new Date().toISOString(),
          provider: response.provider,
          tokensUsed: response.tokens_used || undefined,
          toolExecutions: response.tools_executed,
        };

        return [...withoutOptimistic, userMessage, assistantMessage];
      });

      // Invalidate conversation cache
      if (conversationId) {
        queryClient.invalidateQueries({ queryKey: chatKeys.conversation(conversationId) });
      }
      if (user?.id) {
        queryClient.invalidateQueries({ queryKey: chatKeys.conversations(Number(user.id)) });
      }
    },
    onError: (error) => {
      // Remove optimistic messages on error
      setLocalMessages((prev) =>
        prev.filter((msg) => !msg.id.startsWith('temp-') && !msg.id.startsWith('loading-')),
      );

      // Add error message
      const errorMessage: ChatMessage = {
        id: `error-${Date.now()}`,
        role: 'assistant',
        content: 'Lo siento, ocurrió un error al procesar tu mensaje.',
        timestamp: new Date().toISOString(),
        error: formatErrorMessage(error),
      };

      setLocalMessages((prev) => [...prev, errorMessage]);
    },
  });

  /**
   * Send image message mutation
   */
  const sendImageMessageMutation = useMutation({
    mutationFn: async (request: Omit<ChatImageRequest, 'usuario_id'>) => {
      if (!user?.id) throw new Error('Usuario no autenticado');

      // Force Gemini for image messages (only provider with vision)
      return aiServiceApi.sendImageMessage({
        ...request,
        usuario_id: Number(user.id),
        conversation_id: conversationId || undefined,
        provider: 'gemini',
        temperature,
      });
    },
    onMutate: async (request) => {
      if (optimisticUpdates) {
        // Add user message with image
        const tempMessage: ChatMessage = {
          id: `temp-img-${Date.now()}`,
          role: 'user',
          content: request.content,
          timestamp: new Date().toISOString(),
          provider: 'gemini',
          isLoading: false,
        };

        setLocalMessages((prev) => [...prev, tempMessage]);

        // Add loading assistant message
        const loadingMessage: ChatMessage = {
          id: `loading-img-${Date.now()}`,
          role: 'assistant',
          content: '🔍 Analizando imagen...',
          timestamp: new Date().toISOString(),
          provider: 'gemini',
          isLoading: true,
        };

        setLocalMessages((prev) => [...prev, loadingMessage]);
      }
    },
    onSuccess: (response, request) => {
      // Update conversation ID if this is the first message
      if (!conversationId) {
        setConversationId(response.conversation_id);
      }

      // Remove optimistic messages and add real messages
      setLocalMessages((prev) => {
        const withoutOptimistic = prev.filter(
          (msg) => !msg.id.startsWith('temp-') && !msg.id.startsWith('loading-'),
        );

        const userMessage: ChatMessage = {
          id: `msg-${Date.now()}-user-img`,
          role: 'user',
          content: request.content,
          timestamp: new Date().toISOString(),
          provider: 'gemini',
          imageMetadata: response.image_metadata,
        };

        const assistantMessage: ChatMessage = {
          id: `msg-${Date.now()}-assistant-img`,
          role: 'assistant',
          content: response.assistant_response,
          timestamp: new Date().toISOString(),
          provider: 'gemini',
          tokensUsed: response.tokens_used || undefined,
        };

        return [...withoutOptimistic, userMessage, assistantMessage];
      });

      // Invalidate caches
      if (conversationId) {
        queryClient.invalidateQueries({ queryKey: chatKeys.conversation(conversationId) });
      }
      if (user?.id) {
        queryClient.invalidateQueries({ queryKey: chatKeys.conversations(Number(user.id)) });
      }
    },
    onError: (error) => {
      // Remove optimistic messages
      setLocalMessages((prev) =>
        prev.filter(
          (msg) => !msg.id.startsWith('temp-') && !msg.id.startsWith('loading-'),
        ),
      );

      // Add error message
      const errorMessage: ChatMessage = {
        id: `error-img-${Date.now()}`,
        role: 'assistant',
        content: 'Lo siento, ocurrió un error al procesar la imagen.',
        timestamp: new Date().toISOString(),
        error: formatErrorMessage(error),
      };

      setLocalMessages((prev) => [...prev, errorMessage]);
    },
  });

  // ============================================
  // COMPUTED VALUES
  // ============================================

  /**
   * Combine server messages with local optimistic messages
   */
  const messages = useMemo(() => {
    const serverMessages = conversation?.messages?.map(messageToChat) || [];
    
    // If we have local messages, use them (they include optimistic updates)
    if (localMessages.length > 0) {
      return localMessages;
    }
    
    // Otherwise, use server messages
    return serverMessages;
  }, [conversation?.messages, localMessages]);

  /**
   * Calculate total tokens used
   */
  const totalTokens = useMemo(() => {
    return messages.reduce((sum, msg) => sum + (msg.tokensUsed || 0), 0);
  }, [messages]);

  /**
   * Check if any tool was executed in this conversation
   */
  const hasToolExecutions = useMemo(() => {
    return messages.some((msg) => msg.toolExecutions && msg.toolExecutions.length > 0);
  }, [messages]);

  /**
   * Loading state (any mutation in progress)
   */
  const isLoading =
    sendTextMessageMutation.isPending ||
    sendImageMessageMutation.isPending ||
    isLoadingConversation;

  // ============================================
  // CALLBACK FUNCTIONS
  // ============================================

  /**
   * Send a text message
   */
  const sendMessage = useCallback(
    (content: string) => {
      if (!content.trim()) return;
      sendTextMessageMutation.mutate({ content: content.trim() });
    },
    [sendTextMessageMutation],
  );

  /**
   * Send an image with text
   */
  const sendImageMessage = useCallback(
    (file: File, content: string, analysisType?: ChatImageRequest['analysis_type']) => {
      sendImageMessageMutation.mutate({ file, content, analysis_type: analysisType });
    },
    [sendImageMessageMutation],
  );

  /**
   * Start a new conversation
   */
  const startNewConversation = useCallback(() => {
    setConversationId(null);
    setLocalMessages([]);
    sendTextMessageMutation.reset();
    sendImageMessageMutation.reset();
  }, [sendTextMessageMutation, sendImageMessageMutation]);

  /**
   * Load an existing conversation
   */
  const loadConversation = useCallback((id: number) => {
    setConversationId(id);
    setLocalMessages([]);
  }, []);

  /**
   * Clear all messages (reset)
   */
  const clearMessages = useCallback(() => {
    setLocalMessages([]);
  }, []);

  /**
   * Change LLM provider
   */
  const changeProvider = useCallback((newProvider: LLMProvider) => {
    setProvider(newProvider);
  }, []);

  /**
   * Change temperature
   */
  const changeTemperature = useCallback((newTemperature: number) => {
    setTemperature(Math.max(0, Math.min(2, newTemperature)));
  }, []);

  // ============================================
  // RETURN
  // ============================================

  return {
    // State
    messages,
    conversationId,
    provider,
    temperature,
    totalTokens,
    hasToolExecutions,
    isLoading,
    error:
      sendTextMessageMutation.error ||
      sendImageMessageMutation.error ||
      null,

    // Conversations
    conversation,
    conversationsList: conversationsList?.conversations || [],
    totalConversations: conversationsList?.total || 0,

    // Actions
    sendMessage,
    sendImageMessage,
    startNewConversation,
    loadConversation,
    clearMessages,
    changeProvider,
    changeTemperature,

    // Mutation states
    isSendingText: sendTextMessageMutation.isPending,
    isSendingImage: sendImageMessageMutation.isPending,
  };
}

// ============================================
// HELPER HOOKS
// ============================================

/**
 * Hook to check if AI Service is available
 */
export function useAIServiceHealth() {
  return useQuery({
    queryKey: ['ai-service', 'health'],
    queryFn: () => aiServiceApi.healthCheck(),
    staleTime: 60000, // 1 minute
    retry: 1,
  });
}

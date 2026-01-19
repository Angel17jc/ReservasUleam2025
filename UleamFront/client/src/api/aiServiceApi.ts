/**
 * AI Service API Client
 * 
 * HTTP client for communicating with AI Service (FastAPI backend)
 * Handles text chat, image chat, and conversation management
 */

import type {
  ChatRequest,
  ChatResponse,
  ChatImageRequest,
  ChatImageResponse,
  Conversation,
  ConversationList,
  Message,
  AIServiceError,
} from '@/types/aiService';

// ============================================
// CONFIGURATION
// ============================================

const AI_SERVICE_BASE_URL = import.meta.env.VITE_AI_SERVICE_URL || 'http://localhost:5000';
const API_PREFIX = '/api/v1';

/**
 * Build full API URL
 */
function buildUrl(path: string): string {
  return `${AI_SERVICE_BASE_URL}${API_PREFIX}${path}`;
}

// ============================================
// ERROR HANDLING
// ============================================

export class AIServiceAPIError extends Error {
  constructor(
    public status: number,
    public detail: string,
    public errorCode?: string,
  ) {
    super(detail);
    this.name = 'AIServiceAPIError';
  }

  static async fromResponse(response: Response): Promise<AIServiceAPIError> {
    let detail = `Error ${response.status}: ${response.statusText}`;
    let errorCode: string | undefined;

    try {
      const errorData = (await response.json()) as AIServiceError;
      detail = errorData.detail || detail;
      errorCode = errorData.error_code;
    } catch {
      // If JSON parsing fails, use status text
    }

    return new AIServiceAPIError(response.status, detail, errorCode);
  }
}

/**
 * Handle fetch response
 */
async function handleResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    throw await AIServiceAPIError.fromResponse(response);
  }
  return response.json();
}

// ============================================
// API METHODS
// ============================================

export const aiServiceApi = {
  /**
   * Send text message to AI chatbot
   * 
   * @param request - Chat request with message content
   * @returns Chat response with assistant reply
   * 
   * @example
   * ```ts
   * const response = await aiServiceApi.sendTextMessage({
   *   content: "Busca aulas disponibles mañana",
   *   usuario_id: 1,
   *   provider: "gemini"
   * });
   * console.log(response.assistant_response);
   * console.log(response.tools_executed); // MCP tools executed
   * ```
   */
  async sendTextMessage(request: ChatRequest): Promise<ChatResponse> {
    const response = await fetch(buildUrl('/chat/message'), {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(request),
    });

    const backendResponse = await handleResponse<any>(response);
    
    // Transform backend response to frontend ChatResponse
    return {
      conversation_id: backendResponse.conversation_id,
      assistant_response: backendResponse.assistant_message.content,
      provider: backendResponse.provider,
      tokens_used: backendResponse.tokens_used,
      tools_executed: backendResponse.tools_executed,
      processing_time: backendResponse.processing_time_seconds || 0,
    };
  },

  /**
   * Send image with text message to AI chatbot (multimodal)
   * 
   * @param request - Chat image request with file and content
   * @returns Chat image response with vision analysis and assistant reply
   * 
   * @example
   * ```ts
   * const response = await aiServiceApi.sendImageMessage({
   *   file: imageFile,
   *   content: "¿Qué tipo de espacio es?",
   *   usuario_id: 1,
   *   provider: "gemini", // Only Gemini supports vision
   *   analysis_type: "space"
   * });
   * console.log(response.analysis); // Vision analysis
   * console.log(response.assistant_response); // Conversational response
   * ```
   */
  async sendImageMessage(request: ChatImageRequest): Promise<ChatImageResponse> {
    const formData = new FormData();
    formData.append('file', request.file);
    formData.append('content', request.content);
    formData.append('usuario_id', request.usuario_id.toString());
    
    if (request.conversation_id) {
      formData.append('conversation_id', request.conversation_id.toString());
    }
    if (request.provider) {
      formData.append('provider', request.provider);
    }
    if (request.temperature !== undefined) {
      formData.append('temperature', request.temperature.toString());
    }
    if (request.analysis_type) {
      formData.append('analysis_type', request.analysis_type);
    }

    const response = await fetch(buildUrl('/image/chat'), {
      method: 'POST',
      body: formData,
    });

    return handleResponse<ChatImageResponse>(response);
  },

  /**
   * Get a specific conversation with all messages
   * 
   * @param conversationId - ID of the conversation
   * @returns Conversation with messages array
   * 
   * @example
   * ```ts
   * const conversation = await aiServiceApi.getConversation(123);
   * console.log(conversation.messages); // Array of messages
   * ```
   */
  async getConversation(conversationId: number): Promise<Conversation> {
    const response = await fetch(buildUrl(`/chat/conversations/${conversationId}/messages`), {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
    });

    return handleResponse<Conversation>(response);
  },

  /**
   * List all conversations for a user
   * 
   * @param usuarioId - User ID
   * @param limit - Maximum number of conversations to return
   * @param offset - Pagination offset
   * @returns List of conversations
   * 
   * @example
   * ```ts
   * const { conversations, total } = await aiServiceApi.listConversations(1);
   * console.log(`Showing ${conversations.length} of ${total} conversations`);
   * ```
   */
  async listConversations(
    usuarioId: number,
    limit: number = 50,
    offset: number = 0,
  ): Promise<ConversationList> {
    const params = new URLSearchParams({
      limit: limit.toString(),
      offset: offset.toString(),
    });

    const response = await fetch(buildUrl(`/chat/conversations/${usuarioId}?${params}`), {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
    });

    return handleResponse<ConversationList>(response);
  },

  /**
   * Get messages for a specific conversation
   * 
   * @param conversationId - ID of the conversation
   * @returns Array of messages
   * 
   * @example
   * ```ts
   * const messages = await aiServiceApi.getMessages(123);
   * console.log(messages.map(m => m.content));
   * ```
   */
  async getMessages(conversationId: number): Promise<Message[]> {
    const response = await fetch(buildUrl(`/chat/conversations/${conversationId}/messages`), {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
    });

    const conversation = await handleResponse<Conversation>(response);
    return conversation.messages || [];
  },

  /**
   * Delete a conversation
   * 
   * @param conversationId - ID of the conversation to delete
   * @returns Success response
   */
  async deleteConversation(conversationId: number): Promise<{ success: boolean }> {
    // TODO: Verify if delete endpoint exists in backend
    const response = await fetch(buildUrl(`/chat/conversations/${conversationId}`), {
      method: 'DELETE',
      headers: {
        'Content-Type': 'application/json',
      },
    });

    return handleResponse<{ success: boolean }>(response);
  },

  /**
   * Health check for AI Service
   * 
   * @returns Health status
   */
  async healthCheck(): Promise<{ status: string; providers: string[] }> {
    const response = await fetch(buildUrl('/health'), {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
    });

    return handleResponse<{ status: string; providers: string[] }>(response);
  },
};

// ============================================
// HELPER FUNCTIONS
// ============================================

/**
 * Check if AI Service is configured and available
 */
export function isAIServiceConfigured(): boolean {
  return Boolean(import.meta.env.VITE_AI_SERVICE_URL || AI_SERVICE_BASE_URL);
}

/**
 * Get AI Service URL
 */
export function getAIServiceUrl(): string {
  return AI_SERVICE_BASE_URL;
}

/**
 * Validate image file before upload
 * 
 * @param file - File to validate
 * @param maxSizeMB - Maximum file size in MB (default: 20)
 * @returns Validation result
 */
export function validateImageFile(
  file: File,
  maxSizeMB: number = 20,
): { valid: boolean; error?: string } {
  // Check file type
  const allowedTypes = ['image/jpeg', 'image/png', 'image/webp', 'image/gif', 'image/bmp'];
  if (!allowedTypes.includes(file.type)) {
    return {
      valid: false,
      error: 'Formato de imagen no soportado. Use JPEG, PNG, WEBP, GIF o BMP.',
    };
  }

  // Check file size
  const maxSizeBytes = maxSizeMB * 1024 * 1024;
  if (file.size > maxSizeBytes) {
    return {
      valid: false,
      error: `Imagen muy grande. Tamaño máximo: ${maxSizeMB}MB. Tamaño actual: ${(file.size / 1024 / 1024).toFixed(2)}MB.`,
    };
  }

  return { valid: true };
}

/**
 * Format error message for display
 */
export function formatErrorMessage(error: unknown): string {
  if (error instanceof AIServiceAPIError) {
    return error.detail;
  }
  
  if (error instanceof Error) {
    return error.message;
  }
  
  return 'Error desconocido al comunicarse con el servicio de IA';
}

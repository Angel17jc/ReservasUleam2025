/**
 * AI Service Types
 * 
 * Type definitions for AI Service integration
 * Matches backend schemas from ai-service/app/schemas/
 */

// ============================================
// MESSAGE TYPES
// ============================================

export type MessageRole = 'user' | 'assistant' | 'system' | 'tool';

export interface Message {
  id: number;
  conversation_id: number;
  role: MessageRole;
  content: string;
  provider?: string | null;
  tokens_used?: number | null;
  tool_execution_id?: number | null;
  image_metadata?: ImageMetadata | null;
  created_at: string;
}

// ============================================
// CONVERSATION TYPES
// ============================================

export interface Conversation {
  id: number;
  usuario_id: number;
  title?: string | null;
  created_at: string;
  updated_at: string;
  messages?: Message[];
  message_count?: number;
}

export interface ConversationList {
  conversations: Conversation[];
  total: number;
}

// ============================================
// CHAT REQUEST/RESPONSE TYPES
// ============================================

export interface ChatRequest {
  content: string;
  usuario_id: number;
  conversation_id?: number | null;
  provider?: 'gemini' | 'groq';
  temperature?: number;
  max_tokens?: number;
}

export interface ChatResponse {
  conversation_id: number;
  assistant_response: string;
  provider: string;
  tokens_used?: number | null;
  tools_executed?: ToolExecutionInfo[];
  processing_time: number;
}

// ============================================
// IMAGE TYPES
// ============================================

export type ImageAnalysisType = 'general' | 'ocr' | 'document' | 'space';

export interface ImageMetadata {
  format: string;
  width: number;
  height: number;
  original_size: number;
  processed_size?: number;
  file_size_mb: number;
}

export interface ChatImageRequest {
  file: File;
  content: string;
  usuario_id: number;
  conversation_id?: number | null;
  provider?: 'gemini'; // Only Gemini supports vision
  temperature?: number;
  analysis_type?: ImageAnalysisType;
}

export interface ChatImageResponse {
  conversation_id: number;
  analysis: string;
  assistant_response: string;
  image_metadata: ImageMetadata;
  tokens_used?: number | null;
  processing_time: number;
}

// ============================================
// TOOL EXECUTION TYPES
// ============================================

export interface ToolExecutionInfo {
  tool_name: string;
  arguments: Record<string, any>;
  result?: any;
  success: boolean;
  error_message?: string | null;
  execution_time?: number;
}

export interface ToolExecution {
  id: number;
  conversation_id: number;
  message_id: number;
  tool_name: string;
  arguments: Record<string, any>;
  result: any;
  success: boolean;
  error_message?: string | null;
  execution_time: number;
  created_at: string;
}

// ============================================
// UI TYPES (Frontend-specific)
// ============================================

export interface ChatMessage {
  id: string; // Local ID for React keys
  role: MessageRole;
  content: string;
  timestamp: string;
  provider?: string;
  tokensUsed?: number;
  toolExecutions?: ToolExecutionInfo[];
  imageMetadata?: ImageMetadata;
  isLoading?: boolean;
  error?: string;
}

export interface ChatState {
  messages: ChatMessage[];
  conversationId: number | null;
  isLoading: boolean;
  error: string | null;
}

// ============================================
// API ERROR TYPES
// ============================================

export interface AIServiceError {
  detail: string;
  error_code?: string;
  status?: number;
}

// ============================================
// PROVIDER TYPES
// ============================================

export type LLMProvider = 'gemini' | 'groq';

export interface ProviderOption {
  value: LLMProvider;
  label: string;
  description: string;
  supportsVision: boolean;
  maxTokens: number;
}

export const PROVIDER_OPTIONS: ProviderOption[] = [
  {
    value: 'gemini',
    label: 'Gemini Pro',
    description: 'Google Gemini 2.5 Flash - Soporta visión',
    supportsVision: true,
    maxTokens: 8192,
  },
  {
    value: 'groq',
    label: 'Groq Llama',
    description: 'Llama 3.3 70B - Ultra rápido',
    supportsVision: false,
    maxTokens: 8192,
  },
];

// ============================================
// HELPER FUNCTIONS
// ============================================

/**
 * Convert backend Message to frontend ChatMessage
 */
export function messageToChat(message: Message): ChatMessage {
  return {
    id: message.id.toString(),
    role: message.role,
    content: message.content,
    timestamp: message.created_at,
    provider: message.provider || undefined,
    tokensUsed: message.tokens_used || undefined,
    imageMetadata: message.image_metadata || undefined,
  };
}

/**
 * Check if a provider supports vision/image analysis
 */
export function providerSupportsVision(provider: LLMProvider): boolean {
  return provider === 'gemini';
}

/**
 * Format tool execution for display
 */
export function formatToolExecution(tool: ToolExecutionInfo): string {
  if (tool.success) {
    return `✓ ${tool.tool_name} ejecutada correctamente`;
  } else {
    return `✗ ${tool.tool_name} falló: ${tool.error_message}`;
  }
}

/**
 * Calculate total tokens used in conversation
 */
export function calculateTotalTokens(messages: ChatMessage[]): number {
  return messages.reduce((sum, msg) => sum + (msg.tokensUsed || 0), 0);
}

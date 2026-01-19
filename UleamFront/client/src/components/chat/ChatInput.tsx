/**
 * ChatInput Component
 * 
 * Input field with image upload for chat interface
 * Supports text messages and image attachments
 */

import { useState, useRef, FormEvent, ChangeEvent } from 'react';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import {
  Send,
  ImagePlus,
  X,
  Loader2,
  AlertCircle,
} from 'lucide-react';
import { cn } from '@/lib/utils';
import { validateImageFile } from '@/api/aiServiceApi';
import { Alert, AlertDescription } from '@/components/ui/alert';
import type { ImageAnalysisType } from '@/types/aiService';

// ============================================
// TYPES
// ============================================

interface ChatInputProps {
  onSendMessage: (content: string) => void;
  onSendImage: (file: File, content: string, analysisType?: ImageAnalysisType) => void;
  disabled?: boolean;
  placeholder?: string;
  supportsImages?: boolean;
  className?: string;
}

// ============================================
// COMPONENT
// ============================================

export function ChatInput({
  onSendMessage,
  onSendImage,
  disabled = false,
  placeholder = 'Escribe un mensaje...',
  supportsImages = true,
  className,
}: Readonly<ChatInputProps>) {
  const [content, setContent] = useState('');
  const [selectedImage, setSelectedImage] = useState<File | null>(null);
  const [imagePreview, setImagePreview] = useState<string | null>(null);
  const [imageError, setImageError] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  // ============================================
  // HANDLERS
  // ============================================

  /**
   * Handle form submission
   */
  const handleSubmit = (e: FormEvent) => {
    e.preventDefault();

    const trimmedContent = content.trim();
    if (!trimmedContent && !selectedImage) return;

    // Send image message
    if (selectedImage) {
      onSendImage(selectedImage, trimmedContent || 'Analiza esta imagen', 'general');
      clearImage();
    } else {
      // Send text message
      onSendMessage(trimmedContent);
    }

    // Reset input
    setContent('');
    
    // Reset textarea height
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
    }
  };

  /**
   * Handle image file selection
   */
  const handleImageSelect = (e: ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    // Validate image
    const validation = validateImageFile(file);
    if (!validation.valid) {
      setImageError(validation.error || 'Archivo inválido');
      return;
    }

    // Clear previous errors
    setImageError(null);

    // Set selected image
    setSelectedImage(file);

    // Create preview
    const reader = new FileReader();
    reader.onloadend = () => {
      setImagePreview(reader.result as string);
    };
    reader.readAsDataURL(file);
  };

  /**
   * Clear selected image
   */
  const clearImage = () => {
    setSelectedImage(null);
    setImagePreview(null);
    setImageError(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  /**
   * Trigger file input click
   */
  const handleImageButtonClick = () => {
    fileInputRef.current?.click();
  };

  /**
   * Handle textarea auto-resize
   */
  const handleTextareaChange = (e: ChangeEvent<HTMLTextAreaElement>) => {
    setContent(e.target.value);
    
    // Auto-resize textarea
    e.target.style.height = 'auto';
    e.target.style.height = `${Math.min(e.target.scrollHeight, 150)}px`;
  };

  /**
   * Handle Ctrl+Enter to send
   */
  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && (e.ctrlKey || e.metaKey)) {
      e.preventDefault();
      handleSubmit(e as any);
    }
  };

  // ============================================
  // COMPUTED
  // ============================================

  const canSubmit = (content.trim().length > 0 || selectedImage !== null) && !disabled;

  // ============================================
  // RENDER
  // ============================================

  return (
    <form onSubmit={handleSubmit} className={cn('space-y-2', className)}>
      {/* Image Error Alert */}
      {imageError && (
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription className="text-sm">{imageError}</AlertDescription>
        </Alert>
      )}

      {/* Image Preview */}
      {imagePreview && selectedImage && (
        <div className="relative inline-block">
          <img
            src={imagePreview}
            alt="Preview"
            className="h-20 w-20 rounded-lg object-cover border-2 border-primary"
          />
          <Button
            type="button"
            variant="destructive"
            size="sm"
            className="absolute -top-2 -right-2 h-6 w-6 p-0 rounded-full shadow-lg"
            onClick={clearImage}
          >
            <X className="h-3 w-3" />
          </Button>
          <div className="absolute bottom-0 left-0 right-0 bg-black/60 text-white text-xs px-1 py-0.5 rounded-b-lg truncate">
            {selectedImage.name}
          </div>
        </div>
      )}

      {/* Input Area */}
      <div className="flex gap-2 items-end">
        {/* Text Input */}
        <div className="flex-1 relative">
          <Textarea
            ref={textareaRef}
            value={content}
            onChange={handleTextareaChange}
            onKeyDown={handleKeyDown}
            placeholder={placeholder}
            disabled={disabled}
            className="min-h-[44px] max-h-[150px] resize-none pr-12"
            rows={1}
          />

          {/* Image Upload Button */}
          {supportsImages && (
            <div className="absolute right-2 bottom-2">
              <input
                ref={fileInputRef}
                type="file"
                accept="image/jpeg,image/png,image/webp,image/gif,image/bmp"
                onChange={handleImageSelect}
                className="hidden"
                disabled={disabled}
              />
              <Button
                type="button"
                variant="ghost"
                size="sm"
                className="h-8 w-8 p-0"
                onClick={handleImageButtonClick}
                disabled={disabled}
                title="Adjuntar imagen"
              >
                <ImagePlus className="h-4 w-4" />
              </Button>
            </div>
          )}
        </div>

        {/* Send Button */}
        <Button
          type="submit"
          disabled={!canSubmit}
          className="h-11 px-4"
          title="Enviar mensaje (Ctrl+Enter)"
        >
          {disabled ? (
            <Loader2 className="h-4 w-4 animate-spin" />
          ) : (
            <>
              <Send className="h-4 w-4 mr-2" />
              Enviar
            </>
          )}
        </Button>
      </div>

      {/* Help Text */}
      <p className="text-xs text-muted-foreground">
        Presiona <kbd className="px-1 py-0.5 bg-muted rounded">Ctrl</kbd>
        {'+'}  
        <kbd className="px-1 py-0.5 bg-muted rounded">Enter</kbd> para enviar
        {supportsImages && ' • Adjunta imágenes para análisis'}
      </p>
    </form>
  );
}

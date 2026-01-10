"""
Gemini Adapter

Implementación del LLM Provider para Google Gemini Pro.

Características:
- Gemini Pro para texto (GRATIS)
- Gemini Pro Vision para imágenes (GRATIS)
- 60 requests/minuto en tier gratuito
- Excelente calidad de respuestas

API Documentation: https://ai.google.dev/docs
"""

import google.generativeai as genai
from typing import List, Dict, Any, Optional
import logging

from .base import LLMProvider, LLMMessage, LLMResponse

logger = logging.getLogger(__name__)


class GeminiAdapter(LLMProvider):
    """
    Adapter para Google Gemini Pro.
    
    Implementa el patrón Strategy para poder intercambiar con otros providers.
    """
    
    # Modelos disponibles de Gemini (actualizados enero 2026)
    TEXT_MODEL = "gemini-2.5-flash"  # Gemini 2.5 Flash - más potente y rápido
    VISION_MODEL = "gemini-2.5-flash"  # Soporta texto e imágenes
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize Gemini adapter.
        
        Args:
            api_key: Google AI API key (obtener en https://makersuite.google.com/app/apikey)
        
        Raises:
            ValueError: Si no se provee API key
        """
        super().__init__(api_key)
        
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY is required")
        
        # Configurar Gemini
        genai.configure(api_key=self.api_key)
        
        # Initialize models
        self._text_model = genai.GenerativeModel(self.TEXT_MODEL)
        self._vision_model = genai.GenerativeModel(self.VISION_MODEL)
        
        logger.info("Gemini adapter initialized with model: %s", self.TEXT_MODEL)
    
    async def generate_response(
        self,
        messages: List[LLMMessage],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        tools: Optional[List[Dict[str, Any]]] = None
    ) -> LLMResponse:
        """
        Genera respuesta usando Gemini Pro.
        
        Args:
            messages: Historial de mensajes
            temperature: Creatividad (0.0-2.0)
            max_tokens: Límite de tokens (None = sin límite)
            tools: Tools MCP disponibles (Commit 2)
        
        Returns:
            LLMResponse: Respuesta normalizada
        
        Raises:
            Exception: Si falla la generación
        """
        try:
            # Validar inputs
            self._validate_messages(messages)
            self._validate_temperature(temperature)
            
            # Convertir mensajes al formato de Gemini
            # Gemini usa un formato simplificado: solo el contenido
            # El último mensaje debe ser del user
            prompt = self._build_prompt(messages)
            
            # Configuración de generación
            generation_config = {
                "temperature": temperature,
                "top_p": 0.95,
                "top_k": 40,
            }
            
            if max_tokens:
                generation_config["max_output_tokens"] = max_tokens
            
            # Generar respuesta
            logger.debug("Generating response with Gemini (temp=%s)", temperature)
            response = self._text_model.generate_content(
                prompt,
                generation_config=generation_config
            )
            
            # Extraer contenido
            content = response.text if response.text else ""
            
            # Tokens usados (Gemini no expone esto fácilmente en la API gratuita)
            tokens_used = None
            try:
                if hasattr(response, 'usage_metadata'):
                    tokens_used = (
                        response.usage_metadata.prompt_token_count +
                        response.usage_metadata.candidates_token_count
                    )
            except AttributeError:
                pass
            
            # Finish reason
            finish_reason = "stop"
            try:
                if response.candidates and len(response.candidates) > 0:
                    finish_reason = response.candidates[0].finish_reason.name.lower()
            except (AttributeError, IndexError):
                pass
            
            logger.info("Gemini response generated successfully (tokens=%s)", tokens_used)
            
            return LLMResponse(
                content=content,
                model=self.TEXT_MODEL,
                provider=self.provider_name,
                tokens_used=tokens_used,
                finish_reason=finish_reason,
                tool_calls=None  # Gemini function calling en Commit 2
            )
        
        except Exception as e:
            logger.error("Error generating Gemini response: %s", e)
            raise RuntimeError(f"Gemini API error: {str(e)}") from e
    
    async def generate_with_vision(
        self,
        image_bytes: bytes,
        prompt: str,
        image_format: str = "jpeg"
    ) -> str:
        """
        Analiza una imagen usando Gemini Pro Vision.
        
        Args:
            image_bytes: Bytes de la imagen
            prompt: Prompt para el análisis
            image_format: Formato (jpeg, png, webp)
        
        Returns:
            str: Análisis de la imagen
        
        Raises:
            Exception: Si falla el análisis
        """
        try:
            logger.debug("Analyzing image with Gemini Vision (format=%s)", image_format)
            
            # Gemini Vision acepta directamente los bytes
            # Preparar la imagen
            image_part = {
                "mime_type": f"image/{image_format}",
                "data": image_bytes
            }
            
            # Generar respuesta con imagen
            response = self._vision_model.generate_content([prompt, image_part])
            
            content = response.text if response.text else ""
            
            logger.info("Gemini Vision analysis completed (length=%d)", len(content))
            
            return content
        
        except Exception as e:
            logger.error("Error analyzing image with Gemini Vision: %s", e)
            raise RuntimeError(f"Gemini Vision API error: {str(e)}") from e
    
    def get_available_models(self) -> List[str]:
        """Lista modelos disponibles."""
        return [self.TEXT_MODEL, self.VISION_MODEL]
    
    def is_available(self) -> bool:
        """Verifica si Gemini está disponible."""
        return self.api_key is not None
    
    @property
    def provider_name(self) -> str:
        """Nombre del provider."""
        return "gemini"
    
    def _build_prompt(self, messages: List[LLMMessage]) -> str:
        """
        Construye el prompt para Gemini desde el historial de mensajes.
        
        Gemini espera un formato más simple que otros LLMs.
        Concatenamos los mensajes en un solo prompt con contexto.
        
        Args:
            messages: Lista de mensajes
        
        Returns:
            str: Prompt completo
        """
        prompt_parts = []
        
        for msg in messages:
            if msg.role == "system":
                prompt_parts.append(f"[SYSTEM INSTRUCTION]\n{msg.content}\n")
            elif msg.role == "user":
                prompt_parts.append(f"User: {msg.content}\n")
            elif msg.role == "assistant":
                prompt_parts.append(f"Assistant: {msg.content}\n")
        
        return "\n".join(prompt_parts)

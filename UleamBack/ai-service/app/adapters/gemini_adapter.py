"""
Gemini Adapter

Implementación del LLM Provider para Google Gemini Pro.

Características:
- Gemini 2.5 Flash para texto (GRATIS)
- Gemini 2.5 Flash Vision para imágenes (GRATIS)
- 60 requests/minuto en tier gratuito
- Excelente calidad de respuestas
- Soporte multimodal nativo (texto + imagen)

API Documentation: https://ai.google.dev/docs
Migrado a google.genai (nueva API oficial)
"""

from google import genai
from google.genai import types
from typing import List, Dict, Any, Optional
import logging
import base64

from .base import LLMProvider, LLMMessage, LLMResponse

logger = logging.getLogger(__name__)


class GeminiAdapter(LLMProvider):
    """
    Adapter para Google Gemini Pro.
    
    Implementa el patrón Strategy para poder intercambiar con otros providers.
    Usa la nueva API google.genai (migrada desde google.generativeai)
    """
    
    # Modelos disponibles de Gemini (actualizados enero 2026)
    TEXT_MODEL = "models/gemini-2.5-flash"  # Gemini 2.5 Flash - modelo estable y rápido
    VISION_MODEL = "models/gemini-2.5-flash"  # Soporta texto e imágenes nativamente
    
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
        
        # Configurar cliente Gemini con la nueva API
        self._client = genai.Client(api_key=self.api_key)
        
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
            tools: Tools MCP disponibles (actualmente deshabilitadas)
        
        Returns:
            LLMResponse: Respuesta normalizada
        
        Raises:
            Exception: Si falla la generación
        """
        try:
            # Validar inputs
            self._validate_messages(messages)
            self._validate_temperature(temperature)
            
            # Construir contenido del mensaje
            # La nueva API usa una lista de "contents"
            contents = self._build_contents(messages)
            
            # Configuración de generación
            config = types.GenerateContentConfig(
                temperature=temperature,
                top_p=0.95,
                top_k=40,
                max_output_tokens=max_tokens or 2048,
                response_mime_type="text/plain"
            )
            
            # Generar respuesta con la nueva API
            logger.debug("Generating response with Gemini (temp=%s, model=%s)", 
                        temperature, self.TEXT_MODEL)
            
            response = self._client.models.generate_content(
                model=self.TEXT_MODEL,
                contents=contents,
                config=config
            )
            
            # Extraer respuesta
            if not response or not response.text:
                raise ValueError("Empty response from Gemini")
            
            content = response.text.strip()
            
            # Información de uso (retornar solo el total como entero)
            tokens_used = None
            if hasattr(response, 'usage_metadata'):
                usage = response.usage_metadata
                total_tokens = getattr(usage, 'total_token_count', 0)
                tokens_used = total_tokens if total_tokens > 0 else None
                
                logger.debug(
                    "Token usage: prompt=%d, completion=%d, total=%d",
                    getattr(usage, 'prompt_token_count', 0),
                    getattr(usage, 'candidates_token_count', 0),
                    total_tokens
                )
            
            logger.info(
                "Gemini response generated: length=%d, tokens=%s",
                len(content),
                tokens_used if tokens_used else 'unknown'
            )
            
            # Finish reason
            finish_reason = "stop"
            if hasattr(response, 'candidates') and response.candidates:
                candidate = response.candidates[0]
                if hasattr(candidate, 'finish_reason'):
                    finish_reason = str(candidate.finish_reason).lower()
            
            return LLMResponse(
                content=content,
                model=self.TEXT_MODEL,
                provider=self.provider_name,
                tokens_used=tokens_used,
                finish_reason=finish_reason,
                tool_calls=None  # Function calling deshabilitado temporalmente
            )
        
        except Exception as e:
            logger.error("Error generating Gemini response: %s", e, exc_info=True)
            raise RuntimeError(f"Gemini API error: {str(e)}") from e
    
    async def generate_with_vision(
        self,
        image_bytes: bytes,
        prompt: str,
        image_format: str = "jpeg"
    ) -> str:
        """
        Analiza una imagen usando Gemini Vision.
        
        Args:
            image_bytes: Bytes de la imagen
            prompt: Prompt para el análisis
            image_format: Formato (jpeg, png, webp, gif)
        
        Returns:
            str: Análisis de la imagen
        
        Raises:
            Exception: Si falla el análisis
        """
        try:
            logger.debug("Analyzing image with Gemini Vision (format=%s, size=%d bytes)", 
                        image_format, len(image_bytes))
            
            # Construir el contenido multimodal con la nueva API
            # La nueva API usa types.Part para construir contenido multimodal
            mime_type = f"image/{image_format}"
            
            # Crear part de texto
            text_part = types.Part(text=prompt)
            
            # Crear part de imagen usando inline_data
            image_part = types.Part(
                inline_data=types.Blob(
                    mime_type=mime_type,
                    data=image_bytes
                )
            )
            
            # Construir el contenido completo
            contents = [types.Content(parts=[text_part, image_part])]
            
            # Configuración de generación
            config = types.GenerateContentConfig(
                temperature=0.4,  # Menor temperatura para análisis más preciso
                top_p=0.95,
                max_output_tokens=2048
            )
            
            logger.debug("Sending vision request to Gemini...")
            
            # Generar respuesta con visión
            response = self._client.models.generate_content(
                model=self.VISION_MODEL,
                contents=contents,
                config=config
            )
            
            # Extraer texto de la respuesta
            if not response or not response.text:
                raise ValueError("Empty response from Gemini Vision")
            
            analysis_text = response.text.strip()
            
            logger.info("Gemini Vision analysis completed (length=%d chars)", 
                       len(analysis_text))
            
            return analysis_text
        
        except Exception as e:
            logger.error("Error analyzing image with Gemini Vision: %s", e, exc_info=True)
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
    
    def _build_contents(self, messages: List[LLMMessage]) -> List[types.Content]:
        """
        Construye contenido para Gemini desde el historial de mensajes.
        
        La nueva API google.genai usa una lista de Content objects
        en lugar de un prompt simple.
        
        Args:
            messages: Lista de mensajes
        
        Returns:
            List[types.Content]: Lista de contenidos para Gemini
        """
        contents = []
        
        for msg in messages:
            # Determinar el rol de Gemini (solo soporta "user" y "model")
            if msg.role in ("user", "system"):
                role = "user"
            elif msg.role == "assistant":
                role = "model"
            else:
                # tool results se tratan como user messages
                role = "user"
            
            # Agregar contexto para system messages
            text = msg.content
            if msg.role == "system":
                text = f"[INSTRUCCIONES DEL SISTEMA]\n{msg.content}"
            elif msg.role == "tool":
                text = f"[RESULTADO DE HERRAMIENTA]\n{msg.content}"
            
            # Crear part de texto
            part = types.Part(text=text)
            
            # Crear content con el part
            content = types.Content(
                role=role,
                parts=[part]
            )
            
            contents.append(content)
        
        return contents
    
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
            elif msg.role == "tool":
                # Resultado de tool execution
                prompt_parts.append(f"[TOOL RESULT]\n{msg.content}\n")
        
        return "\n".join(prompt_parts)
    
    def _convert_tools_to_gemini_format(self, mcp_tools: List[Dict[str, Any]]) -> list:
        """
        Convierte schemas de MCP Tools al formato de Gemini Function Declarations.
        
        Args:
            mcp_tools: Lista de schemas MCP (formato OpenAI)
        
        Returns:
            Lista de Tools de Gemini
        """
        gemini_functions = []
        
        for tool in mcp_tools:
            try:
                # Extraer información del schema MCP
                function_info = tool.get("function", {})
                name = function_info.get("name", "")
                description = function_info.get("description", "")
                parameters = function_info.get("parameters", {})
                
                # Convertir parámetros al formato de Gemini
                gemini_params = {}
                properties = parameters.get("properties", {})
                required = parameters.get("required", [])
                
                for param_name, param_info in properties.items():
                    gemini_params[param_name] = {
                        "type": self._map_type_to_gemini(param_info.get("type", "string")),
                        "description": param_info.get("description", ""),
                    }
                    
                    # Agregar si es requerido
                    if param_name in required:
                        gemini_params[param_name]["required"] = True
                
                # TODO: Actualizar cuando se actualice google-generativeai
                # FunctionDeclaration no está disponible en la versión actual
                # Temporalmente deshabilitado - function calling no funciona
                logger.warning("Function calling deshabilitado - actualizar google-generativeai")
                
                # # Crear FunctionDeclaration
                # function_declaration = FunctionDeclaration(
                #     name=name,
                #     description=description,
                #     parameters={
                #         "type": "object",
                #         "properties": gemini_params
                #     }
                # )
                
                # gemini_functions.append(function_declaration)
                
            except Exception as e:
                logger.warning("Failed to convert tool to Gemini format: %s", e)
                continue
        
        # Gemini requiere un objeto Tool que contiene las function declarations
        # Temporalmente deshabilitado
        # if gemini_functions:
        #     return [Tool(function_declarations=gemini_functions)]
        
        return []
    
    def _map_type_to_gemini(self, mcp_type: str) -> str:
        """
        Mapea tipos de MCP/JSON Schema a tipos de Gemini.
        
        Args:
            mcp_type: Tipo en formato JSON Schema
        
        Returns:
            Tipo en formato Gemini
        """
        type_mapping = {
            "string": "string",
            "integer": "integer",
            "number": "number",
            "boolean": "boolean",
            "array": "array",
            "object": "object"
        }
        
        return type_mapping.get(mcp_type.lower(), "string")

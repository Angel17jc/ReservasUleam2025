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
from google.generativeai.types import FunctionDeclaration, Tool
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
            
            # Preparar tools si están disponibles
            gemini_tools = None
            if tools:
                gemini_tools = self._convert_tools_to_gemini_format(tools)
                logger.debug("Function calling enabled with %d tools", len(tools))
            
            # Generar respuesta
            logger.debug("Generating response with Gemini (temp=%s, tools=%s)", 
                        temperature, len(tools) if tools else 0)
            
            response = self._text_model.generate_content(
                prompt,
                generation_config=generation_config,
                tools=gemini_tools
            )
            
            # Extraer function calls si existen
            tool_calls = None
            content = ""
            
            if response.candidates and len(response.candidates) > 0:
                candidate = response.candidates[0]
                
                # Verificar si hay function calls
                if hasattr(candidate.content, 'parts'):
                    for part in candidate.content.parts:
                        # Gemini retorna function_call en las parts
                        if hasattr(part, 'function_call') and part.function_call:
                            if tool_calls is None:
                                tool_calls = []
                            
                            # Convertir function call de Gemini a formato estándar
                            fc = part.function_call
                            tool_call = {
                                "id": f"call_{len(tool_calls)}",
                                "type": "function",
                                "function": {
                                    "name": fc.name,
                                    "arguments": dict(fc.args)  # Gemini retorna dict directamente
                                }
                            }
                            tool_calls.append(tool_call)
                            logger.debug("Function call detected: %s", fc.name)
                        
                        # Extraer texto si existe
                        elif hasattr(part, 'text') and part.text:
                            content += part.text
            
            # Si no hay function calls, intentar extraer texto normal
            if not tool_calls and response.text:
                content = response.text
            
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
            
            logger.info(
                "Gemini response generated successfully (tokens=%s, tool_calls=%s)",
                tokens_used,
                len(tool_calls) if tool_calls else 0
            )
            
            return LLMResponse(
                content=content,
                model=self.TEXT_MODEL,
                provider=self.provider_name,
                tokens_used=tokens_used,
                finish_reason=finish_reason,
                tool_calls=tool_calls
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
            elif msg.role == "tool":
                # Resultado de tool execution
                prompt_parts.append(f"[TOOL RESULT]\n{msg.content}\n")
        
        return "\n".join(prompt_parts)
    
    def _convert_tools_to_gemini_format(self, mcp_tools: List[Dict[str, Any]]) -> List[Tool]:
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
                
                # Crear FunctionDeclaration
                function_declaration = FunctionDeclaration(
                    name=name,
                    description=description,
                    parameters={
                        "type": "object",
                        "properties": gemini_params
                    }
                )
                
                gemini_functions.append(function_declaration)
                
            except Exception as e:
                logger.warning("Failed to convert tool to Gemini format: %s", e)
                continue
        
        # Gemini requiere un objeto Tool que contiene las function declarations
        if gemini_functions:
            return [Tool(function_declarations=gemini_functions)]
        
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

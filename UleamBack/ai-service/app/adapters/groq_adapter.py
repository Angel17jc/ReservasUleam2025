"""
Groq Adapter

Implementación del LLM Provider para Groq.

Características:
- Modelos: Llama 3, Mixtral
- Extremadamente rápido (hardware especializado)
- API compatible con OpenAI
- Tier gratuito generoso

API Documentation: https://console.groq.com/docs
"""

from groq import Groq
from typing import List, Dict, Any, Optional
import logging

from .base import LLMProvider, LLMMessage, LLMResponse

logger = logging.getLogger(__name__)


class GroqAdapter(LLMProvider):
    """
    Adapter para Groq (Llama 3, Mixtral).
    
    Groq usa hardware especializado (LPUs) que hace inferencia muy rápida.
    La API es compatible con OpenAI, lo que facilita la migración.
    """
    
    # Modelos disponibles (actualizados enero 2026)
    LLAMA_3_70B = "llama-3.3-70b-versatile"  # Reemplazo de llama3-70b-8192
    LLAMA_3_8B = "llama-3.1-8b-instant"  # Modelo rápido
    MIXTRAL_8X7B = "mixtral-8x7b-32768"  # Mixtral original
    GEMMA_7B = "gemma2-9b-it"  # Gemma 2 actualizado
    
    DEFAULT_MODEL = LLAMA_3_70B
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize Groq adapter.
        
        Args:
            api_key: Groq API key (obtener en https://console.groq.com/keys)
        
        Raises:
            ValueError: Si no se provee API key
        """
        super().__init__(api_key)
        
        if not self.api_key:
            raise ValueError("GROQ_API_KEY is required")
        
        # Initialize Groq client
        self.client = Groq(api_key=self.api_key)
        self.model = self.DEFAULT_MODEL
        
        logger.info("Groq adapter initialized with model: %s", self.model)
    
    async def generate_response(
        self,
        messages: List[LLMMessage],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        tools: Optional[List[Dict[str, Any]]] = None
    ) -> LLMResponse:
        """
        Genera respuesta usando Groq.
        
        Args:
            messages: Historial de mensajes
            temperature: Creatividad (0.0-2.0)
            max_tokens: Límite de tokens
            tools: Tools MCP disponibles (Commit 2)
        
        Returns:
            LLMResponse: Respuesta normalizada
        
        Raises:
            Exception: Si falla la generación
        """
        try:
            # Convertir mensajes al formato OpenAI primero (convierte role='tool' a 'user')
            formatted_messages = self._format_messages_for_groq(messages)
            
            # Validar temperatura
            self._validate_temperature(temperature)
            
            # Preparar parámetros
            params = {
                "model": self.model,
                "messages": formatted_messages,
                "temperature": temperature,
            }
            
            if max_tokens:
                params["max_tokens"] = max_tokens
            
            # Function calling (Groq usa formato OpenAI)
            if tools:
                # Convertir tools al formato OpenAI/Groq
                params["tools"] = self._convert_tools_to_groq_format(tools)
                params["tool_choice"] = "auto"  # Permite al LLM decidir cuándo usar tools
                logger.debug("Function calling enabled with %d tools", len(tools))
            
            logger.debug(
                "Generating response with Groq (model=%s, temp=%s, tools=%s)",
                self.model,
                temperature,
                len(tools) if tools else 0
            )
            
            # Generar respuesta
            response = self.client.chat.completions.create(**params)
            
            # Extraer contenido
            content = response.choices[0].message.content if response.choices else ""
            
            # Tokens usados
            tokens_used = None
            if hasattr(response, 'usage'):
                tokens_used = response.usage.total_tokens
            
            # Finish reason
            finish_reason = response.choices[0].finish_reason if response.choices else "stop"
            
            # Tool calls (Commit 2)
            tool_calls = None
            if response.choices and hasattr(response.choices[0].message, 'tool_calls'):
                if response.choices[0].message.tool_calls:
                    tool_calls = [
                        {
                            "id": tc.id,
                            "type": tc.type,
                            "function": {
                                "name": tc.function.name,
                                "arguments": tc.function.arguments
                            }
                        }
                        for tc in response.choices[0].message.tool_calls
                    ]
            
            logger.info(
                "Groq response generated successfully (tokens=%s, model=%s, tool_calls=%s)",
                tokens_used,
                self.model,
                len(tool_calls) if tool_calls else 0
            )
            
            return LLMResponse(
                content=content,
                model=self.model,
                provider=self.provider_name,
                tokens_used=tokens_used,
                finish_reason=finish_reason,
                tool_calls=tool_calls
            )
        
        except Exception as e:
            logger.error("Error generating Groq response: %s", e)
            raise RuntimeError(f"Groq API error: {str(e)}") from e
    
    async def generate_with_vision(
        self,
        image_bytes: bytes,
        prompt: str,
        image_format: str = "jpeg"
    ) -> str:
        """
        Groq actualmente no soporta vision.
        
        Raises:
            NotImplementedError: Groq no tiene modelos de vision
        """
        raise NotImplementedError(
            "Groq does not support vision models yet. Use Gemini for image analysis."
        )
    
    def get_available_models(self) -> List[str]:
        """Lista modelos disponibles."""
        return [
            self.LLAMA_3_70B,
            self.LLAMA_3_8B,
            self.MIXTRAL_8X7B,
            self.GEMMA_7B
        ]
    
    def is_available(self) -> bool:
        """Verifica si Groq está disponible."""
        return self.api_key is not None
    
    @property
    def provider_name(self) -> str:
        """Nombre del provider."""
        return "groq"
    
    def set_model(self, model: str) -> None:
        """
        Cambia el modelo a usar.
        
        Args:
            model: Nombre del modelo
        
        Raises:
            ValueError: Si el modelo no es válido
        """
        if model not in self.get_available_models():
            raise ValueError(f"Invalid model: {model}. Available: {self.get_available_models()}")
        
        self.model = model
        logger.info("Groq model changed to: %s", model)
    
    def _convert_tools_to_groq_format(self, mcp_tools: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Convierte tools del formato MCP al formato Groq/OpenAI.
        
        MCP format:
        {
            "name": "tool_name",
            "description": "...",
            "parameters": {...}
        }
        
        Groq format (OpenAI compatible):
        {
            "type": "function",
            "function": {
                "name": "tool_name",
                "description": "...",
                "parameters": {...}
            }
        }
        
        Args:
            mcp_tools: Lista de tools en formato MCP
        
        Returns:
            Lista de tools en formato Groq
        """
        groq_tools = []
        
        logger.debug("Converting %d MCP tools to Groq format...", len(mcp_tools))
        
        for i, tool in enumerate(mcp_tools):
            logger.debug("Tool %d before conversion: %s", i, tool)
            
            groq_tool = {
                "type": "function",
                "function": {
                    "name": tool.get("name", ""),
                    "description": tool.get("description", ""),
                    "parameters": tool.get("parameters", {})
                }
            }
            groq_tools.append(groq_tool)
            
            logger.debug("Tool %d after conversion: %s", i, groq_tool)
        
        logger.info("Successfully converted %d MCP tools to Groq format", len(groq_tools))
        
        return groq_tools
    
    def _format_messages_for_groq(self, messages: List[LLMMessage]) -> List[Dict[str, Any]]:
        """
        Formatea mensajes para Groq, manejando roles especiales.
        
        Groq acepta roles: system, user, assistant, tool
        - role="tool" requiere tool_call_id (complejo)
        - Solución: convertir role="tool" a role="user" con prefijo
        
        Args:
            messages: Lista de mensajes LLM
        
        Returns:
            Lista de mensajes formateados para Groq
        """
        formatted = []
        
        for msg in messages:
            if msg.role == "tool":
                # Convertir role="tool" a role="user" con prefijo descriptivo
                formatted.append({
                    "role": "user",
                    "content": f"[Resultado de herramienta]\n{msg.content}"
                })
            elif msg.role == "system":
                # Groq acepta role="system"
                formatted.append({
                    "role": "system",
                    "content": msg.content
                })
            else:
                # user, assistant
                formatted.append({
                    "role": msg.role,
                    "content": msg.content
                })
        
        logger.debug("Formatted %d messages for Groq", len(formatted))
        return formatted

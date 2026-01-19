"""
AI Orchestrator

Orquesta las interacciones entre el usuario, el LLM y el sistema.

Responsabilidades:
- Gestionar el flujo de conversación
- Llamar al LLM adapter apropiado
- Almacenar mensajes en BD
- Manejar contexto de conversación
- (Commit 2) Ejecutar MCP Tools

Principios aplicados:
- Single Responsibility: Solo orquesta flujo de IA
- Dependency Injection: Recibe dependencias
- Open/Closed: Extensible para nuevas funcionalidades
"""

from sqlalchemy.orm import Session
from typing import Optional, List, Dict, Any
import logging
import time
import json

from ..adapters.base import LLMMessage, LLMResponse
from ..adapters.adapter_factory import AdapterFactory
from ..services.conversation_service import ConversationService
from ..services.tool_execution_manager import ToolExecutionManager
from ..mcp.tool_registry import ToolRegistry

logger = logging.getLogger(__name__)


class AIOrchestrator:
    """
    Orquestador principal del sistema de IA.
    
    Coordina todas las interacciones entre usuario, LLM y base de datos.
    """
    
    # System prompt por defecto
    DEFAULT_SYSTEM_PROMPT = """Eres un asistente virtual inteligente para el sistema de reservas de espacios de la ULEAM (Universidad Laica Eloy Alfaro de Manabí).

Tu función principal es ayudar a los usuarios con:
- Buscar y consultar información sobre reservas de espacios
- Crear nuevas reservas de espacios
- Procesar pagos de reservas
- Generar reportes y estadísticas
- Responder preguntas sobre el sistema

Características importantes:
- Eres amable, profesional y eficiente
- Das respuestas claras y concisas
- Confirmas acciones importantes antes de ejecutarlas
- Si no tienes información, lo indicas claramente
- Siempre priorizas la experiencia del usuario

Responde en español de manera natural y conversacional."""
    
    def __init__(self, db: Session, provider_name: Optional[str] = None):
        """
        Initialize orchestrator.
        
        Args:
            db: Sesión de base de datos
            provider_name: Provider LLM a usar (None = default)
        """
        self.db = db
        self.conversation_service = ConversationService()
        self.tool_manager = ToolExecutionManager()
        
        # Crear adapter del LLM
        try:
            self.llm_adapter = AdapterFactory.create(provider_name)
            logger.info("AI Orchestrator initialized with provider: %s", self.llm_adapter.provider_name)
        except Exception as e:
            logger.error("Failed to initialize LLM adapter: %s", e)
            raise
        
        # Log de tools disponibles
        available_tools = ToolRegistry.count()
        logger.info("Tools available: %d", available_tools)
    
    async def process_message(
        self,
        user_message: str,
        usuario_id: int,
        conversation_id: Optional[int] = None,
        temperature: float = 0.7
    ) -> dict:
        """
        Procesa un mensaje del usuario y genera respuesta del assistant.
        
        Este es el método principal del orchestrator que:
        1. Crea o recupera la conversación
        2. Guarda el mensaje del usuario
        3. Construye el contexto (historial)
        4. Llama al LLM para generar respuesta
        5. Guarda la respuesta del assistant
        6. Retorna ambos mensajes
        
        Args:
            user_message: Mensaje del usuario
            usuario_id: ID del usuario
            conversation_id: ID de conversación existente (None = nueva)
            temperature: Temperatura para el LLM
        
        Returns:
            dict: Resultado con conversación, mensajes y metadata
        
        Raises:
            Exception: Si falla el procesamiento
        """
        start_time = time.time()
        tools_executed_info = []  # Track tool executions for response
        
        try:
            # 1. Obtener o crear conversación
            if conversation_id:
                conversation = self.conversation_service.get_conversation(
                    self.db,
                    conversation_id
                )
                
                if not conversation:
                    raise ValueError(f"Conversation {conversation_id} not found")
                
                # Verificar que pertenece al usuario
                if conversation.usuario_id != usuario_id:
                    raise ValueError(f"Conversation {conversation_id} does not belong to user {usuario_id}")
                
                logger.debug("Using existing conversation: %s", conversation_id)
            else:
                # Crear nueva conversación
                conversation = self.conversation_service.create_conversation(
                    self.db,
                    usuario_id=usuario_id,
                    title=self._generate_title_from_message(user_message)
                )
                logger.info("Created new conversation: %s", conversation.id)
            
            # 2. Guardar mensaje del usuario
            user_msg = self.conversation_service.add_message(
                self.db,
                conversation_id=conversation.id,
                role="user",
                content=user_message
            )
            
            # 3. Construir contexto (historial de mensajes)
            context_messages = self._build_context(conversation.id)
            
            # 4. Obtener tools disponibles del registry
            available_tools = self.tool_manager.get_available_tools()
            logger.debug("Available tools for LLM: %d", len(available_tools))
            
            # 5. Generar respuesta del LLM (puede incluir tool calls)
            logger.debug("Generating LLM response (provider=%s)", self.llm_adapter.provider_name)
            
            llm_response: LLMResponse = await self.llm_adapter.generate_response(
                messages=context_messages,
                temperature=temperature,
                tools=available_tools  # Pasar tools al LLM
            )
            
            # 6. Manejar tool calls si existen (flujo iterativo)
            if llm_response.tool_calls:
                logger.info(
                    "LLM requested %d tool call(s), executing...",
                    len(llm_response.tool_calls)
                )
                
                # Ejecutar las tools solicitadas
                tool_results = await self._execute_tool_calls(
                    conversation_id=conversation.id,
                    tool_calls=llm_response.tool_calls
                )
                
                # Capturar información de tool executions para el response
                for tool_call, result in zip(llm_response.tool_calls, tool_results):
                    tool_name = tool_call.get("function", {}).get("name", "unknown")
                    arguments = tool_call.get("function", {}).get("arguments", {})
                    
                    # Si arguments es string JSON, parsearlo
                    if isinstance(arguments, str):
                        try:
                            arguments = json.loads(arguments)
                        except json.JSONDecodeError:
                            arguments = {}
                    
                    tools_executed_info.append({
                        "tool_name": tool_name,
                        "arguments": arguments,
                        "result": result.get("data"),
                        "success": result.get("success", False),
                        "error_message": result.get("error"),
                        "execution_time": result.get("execution_time_ms")
                    })
                
                # Reinsertar resultados en el contexto y obtener respuesta final
                final_response = await self._get_final_response_after_tools(
                    context_messages=context_messages,
                    tool_calls=llm_response.tool_calls,
                    tool_results=tool_results,
                    temperature=temperature,
                    available_tools=available_tools
                )
                
                # Usar la respuesta final
                llm_response = final_response
            
            # 7. Guardar respuesta del assistant
            assistant_msg = self.conversation_service.add_message(
                self.db,
                conversation_id=conversation.id,
                role="assistant",
                content=llm_response.content,
                tool_calls=llm_response.tool_calls  # Commit 2
            )
            
            # Calcular tiempo total
            elapsed_time = time.time() - start_time
            
            logger.info(
                "Message processed successfully: conversation_id=%s, tokens=%s, time=%.2fs",
                conversation.id,
                llm_response.tokens_used,
                elapsed_time
            )
            
            # 6. Retornar resultado
            return {
                "conversation_id": conversation.id,
                "user_message": {
                    "id": user_msg.id,
                    "conversation_id": conversation.id,
                    "role": user_msg.role,
                    "content": user_msg.content,
                    "created_at": user_msg.created_at
                },
                "assistant_message": {
                    "id": assistant_msg.id,
                    "conversation_id": conversation.id,
                    "role": assistant_msg.role,
                    "content": assistant_msg.content,
                    "tool_calls": assistant_msg.tool_calls,
                    "created_at": assistant_msg.created_at
                },
                "model": llm_response.model,
                "provider": llm_response.provider,
                "tokens_used": llm_response.tokens_used,
                "tools_executed": tools_executed_info if tools_executed_info else None,
                "processing_time_seconds": round(elapsed_time, 2)
            }
        
        except Exception as e:
            logger.error("Error processing message: %s", e, exc_info=True)
            raise RuntimeError(f"Failed to process message: {str(e)}") from e
    
    def _build_context(self, conversation_id: int, max_messages: int = 20) -> List[LLMMessage]:
        """
        Construye el contexto de la conversación para enviar al LLM.
        
        Incluye:
        - System prompt
        - Últimos N mensajes de la conversación
        
        Args:
            conversation_id: ID de la conversación
            max_messages: Máximo de mensajes de historial
        
        Returns:
            List[LLMMessage]: Lista de mensajes para el LLM
        """
        messages = []
        
        # 1. System prompt
        messages.append(LLMMessage(
            role="system",
            content=self.DEFAULT_SYSTEM_PROMPT
        ))
        
        # 2. Historial de mensajes previos
        history = self.conversation_service.get_conversation_messages(
            self.db,
            conversation_id=conversation_id,
            limit=max_messages
        )
        
        for msg in history:
            messages.append(LLMMessage(
                role=msg.role,
                content=msg.content
            ))
        
        logger.debug("Built context with %d messages (including system prompt)", len(messages))
        return messages
    
    def _generate_title_from_message(self, message: str, max_length: int = 50) -> str:
        """
        Genera un título para la conversación basado en el primer mensaje.
        
        Args:
            message: Primer mensaje del usuario
            max_length: Longitud máxima del título
        
        Returns:
            str: Título generado
        """
        # Truncar y limpiar
        title = message.strip()[:max_length]
        
        # Si se truncó, agregar "..."
        if len(message) > max_length:
            title += "..."
        
        return title or "Nueva conversación"
    
    async def _execute_tool_calls(
        self,
        conversation_id: int,
        tool_calls: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Ejecuta las tool calls solicitadas por el LLM.
        
        Args:
            conversation_id: ID de la conversación
            tool_calls: Lista de tool calls del LLM
        
        Returns:
            Lista de resultados de las tools
        """
        try:
            # Ejecutar todas las tool calls
            results = await self.tool_manager.execute_multiple_tools(tool_calls)
            
            # Guardar cada tool call como mensaje en la conversación
            for tool_call, result in zip(tool_calls, results):
                # Extraer nombre de la tool
                tool_name = tool_call.get("function", {}).get("name", "unknown")
                
                # Guardar mensaje de tool result
                self.conversation_service.add_message(
                    self.db,
                    conversation_id=conversation_id,
                    role="tool",
                    content=json.dumps(result, ensure_ascii=False),
                    tool_calls={"tool_name": tool_name, "result": result}
                )
                
                logger.debug(
                    "Tool result saved: tool=%s, success=%s",
                    tool_name,
                    result.get("success")
                )
            
            return results
        
        except Exception as e:
            logger.error("Error executing tool calls: %s", e, exc_info=True)
            # Retornar error como resultado
            return [{
                "success": False,
                "error": f"Failed to execute tools: {str(e)}"
            }]
    
    async def _get_final_response_after_tools(
        self,
        context_messages: List[LLMMessage],
        tool_calls: List[Dict[str, Any]],
        tool_results: List[Dict[str, Any]],
        temperature: float,
        available_tools: List[Dict[str, Any]]
    ) -> LLMResponse:
        """
        Obtiene la respuesta final del LLM después de ejecutar las tools.
        
        Reinsereta los resultados de las tools en el contexto y solicita
        al LLM que genere una respuesta final para el usuario.
        
        Args:
            context_messages: Contexto original
            tool_calls: Tool calls ejecutadas
            tool_results: Resultados de las tools
            temperature: Temperatura para el LLM
            available_tools: Tools disponibles
        
        Returns:
            LLMResponse final del LLM
        """
        try:
            # Crear nuevo contexto con los resultados de las tools
            extended_context = context_messages.copy()
            
            # Agregar mensaje del assistant con tool calls
            extended_context.append(LLMMessage(
                role="assistant",
                content="[Ejecutando herramientas...]"
            ))
            
            # Agregar resultados de cada tool como mensaje
            for tool_call, result in zip(tool_calls, tool_results):
                tool_name = tool_call.get("function", {}).get("name", "unknown")
                
                # Formatear resultado para el LLM
                if result.get("success"):
                    result_text = f"Herramienta '{tool_name}' ejecutada exitosamente.\n\n"
                    
                    # Incluir summary si existe (más conciso)
                    if "summary" in result:
                        result_text += f"Resumen: {result['summary']}\n\n"
                    
                    # Incluir datos si existen
                    if "data" in result:
                        result_text += f"Datos: {json.dumps(result['data'], ensure_ascii=False, indent=2)}"
                else:
                    result_text = f"Error ejecutando herramienta '{tool_name}': {result.get('error', 'Unknown error')}"
                
                extended_context.append(LLMMessage(
                    role="tool",
                    content=result_text
                ))
            
            # Agregar instrucción para que el LLM genere respuesta final
            extended_context.append(LLMMessage(
                role="user",
                content="Basándote en los resultados de las herramientas, proporciona una respuesta clara y útil al usuario."
            ))
            
            logger.debug(
                "Requesting final response from LLM with %d tool results",
                len(tool_results)
            )
            
            # Generar respuesta final
            final_response = await self.llm_adapter.generate_response(
                messages=extended_context,
                temperature=temperature,
                tools=available_tools  # Mantener tools disponibles por si necesita llamar más
            )
            
            # Si el LLM solicita más tool calls, limitamos a 1 iteración adicional
            # para evitar loops infinitos
            if final_response.tool_calls:
                logger.warning(
                    "LLM requested additional tool calls in final response, "
                    "limiting to prevent infinite loop"
                )
                # Ejecutar una iteración más pero sin tools en la siguiente
                additional_results = await self.tool_manager.execute_multiple_tools(
                    final_response.tool_calls
                )
                
                # Construir mensaje final con los resultados adicionales
                summary_text = "He ejecutado las herramientas adicionales. "
                for res in additional_results:
                    if res.get("success") and "summary" in res:
                        summary_text += res["summary"] + " "
                
                # Crear respuesta sintética
                final_response = LLMResponse(
                    content=summary_text.strip(),
                    model=final_response.model,
                    provider=final_response.provider,
                    tokens_used=final_response.tokens_used,
                    finish_reason="stop",
                    tool_calls=None
                )
            
            logger.info("Final response generated after tool execution")
            
            return final_response
        
        except Exception as e:
            logger.error("Error getting final response after tools: %s", e, exc_info=True)
            
            # Retornar respuesta de error
            return LLMResponse(
                content=f"Lo siento, hubo un error al procesar los resultados de las herramientas: {str(e)}",
                model=self.llm_adapter.provider_name,
                provider=self.llm_adapter.provider_name,
                tokens_used=None,
                finish_reason="error",
                tool_calls=None
            )
    
    async def generate_title_with_llm(self, conversation_id: int) -> Optional[str]:
        """
        Genera un título inteligente para la conversación usando el LLM.
        
        Útil para generar títulos descriptivos después de varios mensajes.
        
        Args:
            conversation_id: ID de la conversación
        
        Returns:
            Optional[str]: Título generado o None si falla
        """
        try:
            # Obtener mensajes de la conversación
            messages = self.conversation_service.get_conversation_messages(
                self.db,
                conversation_id=conversation_id,
                limit=10
            )
            
            if not messages:
                return None
            
            # Construir prompt para generar título
            conversation_text = "\n".join([
                f"{msg.role}: {msg.content}" for msg in messages[:5]
            ])
            
            title_prompt = [
                LLMMessage(
                    role="system",
                    content="Eres un asistente que genera títulos concisos para conversaciones. "
                            "Genera un título de máximo 50 caracteres que resuma el tema principal."
                ),
                LLMMessage(
                    role="user",
                    content=f"Genera un título para esta conversación:\n\n{conversation_text}\n\n"
                            "Título (máximo 50 caracteres):"
                )
            ]
            
            # Generar título
            response = await self.llm_adapter.generate_response(
                messages=title_prompt,
                temperature=0.3,  # Más determinístico
                max_tokens=20
            )
            
            title = response.content.strip().strip('"').strip("'")
            
            # Actualizar en BD
            if title:
                self.conversation_service.update_conversation_title(
                    self.db,
                    conversation_id=conversation_id,
                    title=title
                )
                
                logger.info("Generated title for conversation %s: '%s'", conversation_id, title)
                return title
            
            return None
        
        except RuntimeError as e:
            logger.error("Error generating title with LLM: %s", e)
            return None

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
- Buscar y consultar información sobre espacios disponibles
- Ver las reservas existentes de los usuarios
- Crear nuevas reservas de espacios
- Registrar nuevos usuarios en el sistema
- Generar reportes y estadísticas de reservas

IMPORTANTE - Uso de herramientas:
- Cuando ejecutes herramientas, SIEMPRE analiza y presenta los resultados de forma clara
- NO digas solo "he ejecutado las herramientas" sin mostrar los datos
- Si buscas espacios, menciona los nombres, capacidad y ubicación de los más relevantes
- Si consultas reservas, indica fechas, espacios y estados
- Si hay errores, explica qué pasó y sugiere soluciones
- Usa emojis apropiados para hacer la respuesta más visual (📅 🏢 ✅ ❌ 📊)

Estilo de comunicación:
- Amable, profesional y eficiente
- Respuestas claras, estructuradas y fáciles de leer
- Confirma acciones importantes antes de ejecutarlas
- Si no tienes información suficiente, pregunta al usuario
- Siempre prioriza la experiencia del usuario

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
                
                # Validar y corregir tool calls automáticamente
                corrected_tool_calls = self._validate_and_fix_tool_calls(
                    tool_calls=llm_response.tool_calls,
                    usuario_id=usuario_id
                )
                
                # Ejecutar las tools solicitadas (con parámetros corregidos)
                tool_results = await self._execute_tool_calls(
                    conversation_id=conversation.id,
                    tool_calls=corrected_tool_calls
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
    
    def _build_context(self, conversation_id: int, max_messages: int = 20, usuario_id: Optional[int] = None) -> List[LLMMessage]:
        """
        Construye el contexto de la conversación para enviar al LLM.
        
        Incluye:
        - System prompt
        - Contexto del usuario (para tools)
        - Últimos N mensajes de la conversación
        
        Args:
            conversation_id: ID de la conversación
            max_messages: Máximo de mensajes de historial
            usuario_id: ID del usuario actual (para contexto de herramientas)
        
        Returns:
            List[LLMMessage]: Lista de mensajes para el LLM
        """
        messages = []
        
        # 1. System prompt
        messages.append(LLMMessage(
            role="system",
            content=self.DEFAULT_SYSTEM_PROMPT
        ))
        
        # 2. Contexto del usuario para tools
        if usuario_id:
            messages.append(LLMMessage(
                role="system",
                content=f"""CONTEXTO DEL USUARIO ACTUAL:
- ID de usuario: {usuario_id}
- Cuando uses herramientas que requieran 'usuario_id', USA SIEMPRE el valor: {usuario_id}
- NUNCA uses valores genéricos como "tu_id", "usuario_id", o strings
- Este es el ID numérico real para consultar datos del usuario"""
            ))
        
        # 3. Historial de mensajes previos
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
    
    def _validate_and_fix_tool_calls(
        self,
        tool_calls: List[Dict[str, Any]],
        usuario_id: int
    ) -> List[Dict[str, Any]]:
        """
        Valida y corrige automáticamente los parámetros de tool calls.
        
        Problema común: LLMs como Groq a veces ignoran el contexto y generan
        valores genéricos como "tu_id", "usuario_id" en vez del ID real.
        
        Esta función intercepta y corrige esos valores automáticamente.
        
        Args:
            tool_calls: Tool calls generadas por el LLM
            usuario_id: ID real del usuario actual
        
        Returns:
            Tool calls corregidas con parámetros válidos
        """
        corrected_calls = []
        
        for tool_call in tool_calls:
            corrected_call = tool_call.copy()
            
            # Extraer función y argumentos
            function_data = corrected_call.get("function", {})
            tool_name = function_data.get("name", "")
            arguments = function_data.get("arguments", {})
            
            # Si arguments es string JSON, parsearlo
            if isinstance(arguments, str):
                try:
                    arguments = json.loads(arguments)
                except json.JSONDecodeError:
                    logger.warning(f"Failed to parse arguments JSON for {tool_name}: {arguments}")
                    arguments = {}
            
            # Validar y corregir usuario_id si existe
            if "usuario_id" in arguments:
                original_value = arguments["usuario_id"]
                
                # Detectar valores inválidos (strings genéricos, None, etc)
                invalid_values = [
                    "tu_id", "tu_id_de_usuario", "usuario_id", "user_id",
                    "id_usuario", "your_id", "current_user_id", None, ""
                ]
                
                # Si es string genérico o None, reemplazar con ID real
                if original_value in invalid_values or isinstance(original_value, str):
                    logger.info(
                        f"🔧 Auto-correcting usuario_id in {tool_name}: "
                        f"'{original_value}' → {usuario_id}"
                    )
                    arguments["usuario_id"] = usuario_id
                # Si es número pero 0 o negativo, también corregir
                elif isinstance(original_value, (int, float)) and original_value <= 0:
                    logger.info(
                        f"🔧 Auto-correcting invalid usuario_id in {tool_name}: "
                        f"{original_value} → {usuario_id}"
                    )
                    arguments["usuario_id"] = usuario_id
            
            # Actualizar argumentos corregidos
            corrected_call["function"]["arguments"] = arguments
            corrected_calls.append(corrected_call)
        
        logger.debug(f"Validated and corrected {len(corrected_calls)} tool calls")
        return corrected_calls
    
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
                
                # Guardar mensaje de tool result como 'system' (BD no permite 'tool')
                self.conversation_service.add_message(
                    self.db,
                    conversation_id=conversation_id,
                    role="system",  # Cambiado de 'tool' a 'system'
                    content=f"[Tool Result: {tool_name}]\n{json.dumps(result, ensure_ascii=False)}",
                    tool_calls={"tool_name": tool_name, "result": result, "is_tool_result": True}
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
                
                # Formatear resultado para el LLM de forma más descriptiva
                if result.get("success"):
                    result_text = f"✅ Resultados de la herramienta '{tool_name}':\n\n"
                    
                    # Incluir summary si existe (más conciso)
                    if "summary" in result and result["summary"]:
                        result_text += f"{result['summary']}\n\n"
                    
                    # Incluir datos si existen - formatear según el tipo de tool
                    if "data" in result and result["data"]:
                        data = result["data"]
                        
                        # Para búsqueda de espacios
                        if tool_name == "buscarespacios" and isinstance(data, list):
                            result_text += f"📋 Se encontraron {len(data)} espacios:\n"
                            for idx, espacio in enumerate(data[:10], 1):  # Limitar a 10
                                result_text += f"\n{idx}. {espacio.get('nombre', 'N/A')}"
                                result_text += f"\n   - Capacidad: {espacio.get('capacidad', 'N/A')} personas"
                                result_text += f"\n   - Tipo: {espacio.get('tipo', 'N/A')}"
                                if espacio.get('ubicacion'):
                                    result_text += f"\n   - Ubicación: {espacio['ubicacion']}"
                        
                        # Para ver reservas
                        elif tool_name == "verreservas" and isinstance(data, list):
                            result_text += f"📅 Tienes {len(data)} reservas:\n"
                            for idx, reserva in enumerate(data[:10], 1):
                                result_text += f"\n{idx}. Espacio: {reserva.get('espacio_nombre', 'N/A')}"
                                result_text += f"\n   - Fecha: {reserva.get('fecha_inicio', 'N/A')}"
                                result_text += f"\n   - Estado: {reserva.get('estado', 'N/A')}"
                        
                        # Para estadísticas
                        elif tool_name == "estadisticasreservas" and isinstance(data, dict):
                            result_text += "📊 Estadísticas:\n"
                            for key, value in data.items():
                                result_text += f"\n- {key}: {value}"
                        
                        # Fallback: JSON genérico
                        else:
                            result_text += f"Datos completos:\n{json.dumps(data, ensure_ascii=False, indent=2)}"
                else:
                    result_text = f"❌ Error al ejecutar '{tool_name}': {result.get('error', 'Unknown error')}"
                
                extended_context.append(LLMMessage(
                    role="tool",
                    content=result_text
                ))
            
            # Agregar instrucción específica para que el LLM sintetice los resultados
            extended_context.append(LLMMessage(
                role="user",
                content=(
                    "IMPORTANTE: Analiza los resultados anteriores y responde al usuario de forma conversacional.\n"
                    "- Si hay espacios disponibles, menciona los más relevantes con sus características\n"
                    "- Si hay reservas, resume las más importantes o próximas\n"
                    "- Si hay estadísticas, explica los números de forma comprensible\n"
                    "- Si hubo errores, explica qué salió mal y sugiere alternativas\n"
                    "- NO digas solo 'he ejecutado las herramientas', MUESTRA los resultados reales\n"
                    "- Usa un tono amigable y profesional"
                )
            ))
            
            logger.debug(
                "Requesting final response from LLM with %d tool results",
                len(tool_results)
            )
            
            # Generar respuesta final SIN tools para forzar que responda con texto
            final_response = await self.llm_adapter.generate_response(
                messages=extended_context,
                temperature=temperature,
                tools=None  # NO permitir más tool calls, debe responder al usuario
            )
            
            logger.info(
                "Final response generated after tool execution (tokens=%s)",
                final_response.tokens_used
            )
            
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

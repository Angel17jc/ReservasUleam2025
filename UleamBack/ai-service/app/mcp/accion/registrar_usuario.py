"""
Registrar Usuario Tool (ACCIÓN)

Permite registrar un nuevo usuario en el sistema de autenticación.
"""
import logging
from typing import List
from datetime import datetime
from ..base_tool import BaseTool, ToolParameter, ToolResult, ToolCategory, ParameterType
from ..tool_registry import register_tool
from ..tool_executor import ToolExecutor

logger = logging.getLogger(__name__)


@register_tool
class RegistrarUsuarioTool(BaseTool):
    """
    Tool para registrar un nuevo usuario.
    
    Requiere:
    - Nombre
    - Apellido
    - Email (único)
    - Password
    - Tipo de usuario
    """
    
    def _get_category(self) -> ToolCategory:
        return ToolCategory.ACCION
    
    def _get_description(self) -> str:
        return """Registra un nuevo usuario en el sistema de reservas ULEAM.

Parámetros requeridos:
- nombre: Nombre del usuario
- apellido: Apellido del usuario
- email: Correo electrónico (debe ser único, preferiblemente @uleam.edu.ec)
- password: Contraseña (mínimo 8 caracteres)
- tipo_usuario_id: Tipo de usuario (1=admin, 2=docente, 3=estudiante, 4=externo)

Crea el usuario y retorna su información (sin la contraseña). El usuario puede iniciar sesión inmediatamente."""
    
    def get_parameters(self) -> List[ToolParameter]:
        return [
            ToolParameter(
                name="nombre",
                type=ParameterType.STRING,
                description="Nombre del usuario",
                required=True
            ),
            ToolParameter(
                name="apellido",
                type=ParameterType.STRING,
                description="Apellido del usuario",
                required=True
            ),
            ToolParameter(
                name="email",
                type=ParameterType.STRING,
                description="Correo electrónico (único, preferiblemente @uleam.edu.ec)",
                required=True
            ),
            ToolParameter(
                name="password",
                type=ParameterType.STRING,
                description="Contraseña (mínimo 8 caracteres)",
                required=True
            ),
            ToolParameter(
                name="tipo_usuario_id",
                type=ParameterType.INTEGER,
                description="Tipo de usuario: 1=admin, 2=docente, 3=estudiante, 4=externo",
                required=False,
                default=3,  # Por defecto estudiante
                enum=[1, 2, 3, 4]
            )
        ]
    
    async def _execute(self, **kwargs) -> ToolResult:
        """
        Ejecuta el registro de usuario.
        
        Args:
            nombre: Nombre del usuario
            apellido: Apellido
            email: Email único
            password: Contraseña
            tipo_usuario_id: Tipo de usuario (default=3)
        
        Returns:
            ToolResult: Información del usuario creado
        """
        executor = ToolExecutor()
        
        try:
            # Preparar datos del usuario
            usuario_data = {
                "nombre": kwargs["nombre"],
                "apellido": kwargs["apellido"],
                "email": kwargs["email"],
                "password": kwargs["password"],
                "tipo_usuario_id": kwargs.get("tipo_usuario_id", 3),
                "estado": "activo"
            }
            
            # Llamar a Auth service para registrar
            response = await executor.call_auth_service(
                method="POST",
                endpoint="/api/v1/auth/register",
                json_data=usuario_data
            )
            
            # Mapeo de tipos de usuario
            tipos_map = {
                1: "Administrador",
                2: "Docente",
                3: "Estudiante",
                4: "Usuario Externo"
            }
            
            tipo = tipos_map.get(usuario_data["tipo_usuario_id"], "Usuario")
            
            # Extraer datos del usuario (puede venir en diferentes formatos)
            user_data = response.get('user', response)
            user_id = user_data.get('id', 'N/A')
            user_email = user_data.get('email', kwargs['email'])
            
            # Crear mensaje de éxito
            summary = f"✅ Usuario registrado exitosamente!\n\n"
            summary += f"👤 Nombre: {kwargs['nombre']} {kwargs['apellido']}\n"
            summary += f"📧 Email: {user_email}\n"
            summary += f"🏷️ Tipo: {tipo}\n"
            summary += f"🆔 ID: {user_id}\n"
            summary += f"✔️ Estado: Activo\n\n"
            summary += f"El usuario puede iniciar sesión ahora con su email y contraseña."
            
            return ToolResult(
                success=True,
                data={
                    "user": user_data,
                    "summary": summary
                },
                metadata={
                    "action": "register_user",
                    "user_id": user_id,
                    "user_type": tipo,
                    "timestamp": datetime.now().isoformat()
                }
            )
        
        except Exception as e:
            logger.error(f"Error in registrar_usuario: {e}")
            
            # Mensajes de error más amigables
            error_msg = str(e).lower()
            if "already exists" in error_msg or "duplicate" in error_msg or "unique" in error_msg:
                user_error = "Ya existe un usuario con ese email. Por favor usa otro correo electrónico."
            elif "password" in error_msg:
                user_error = "La contraseña no cumple con los requisitos (mínimo 8 caracteres)."
            elif "email" in error_msg and "invalid" in error_msg:
                user_error = "El formato del email es inválido. Usa un correo válido."
            else:
                user_error = f"No se pudo registrar el usuario: {str(e)}"
            
            return ToolResult(
                success=False,
                error=user_error
            )
        
        finally:
            await executor.close()

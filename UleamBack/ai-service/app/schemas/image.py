"""
Image Schemas

Pydantic schemas para validación de requests/responses de endpoints de imagen.

Principios aplicados:
- Input Validation: Validación exhaustiva de archivos
- Type Safety: Type hints completos
- Error Messages: Mensajes claros de validación
"""

from pydantic import BaseModel, Field, field_validator
from typing import Optional, Dict, Any
from datetime import datetime
from enum import Enum


class ImageAnalysisType(str, Enum):
    """Tipos de análisis de imagen disponibles."""
    GENERAL = "general"  # Análisis general de la imagen
    OCR = "ocr"  # Extracción de texto
    DOCUMENT = "document"  # Análisis de documento
    SPACE = "space"  # Identificación de espacio


class ChatImageRequest(BaseModel):
    """
    Request para enviar mensaje con imagen al chatbot.
    
    Attributes:
        content: Mensaje/pregunta del usuario sobre la imagen
        usuario_id: ID del usuario
        conversation_id: ID de conversación existente (None = nueva)
        provider: Provider LLM (solo 'gemini' soporta visión)
        temperature: Temperatura de generación
        analysis_type: Tipo de análisis a realizar
    """
    content: str = Field(
        ...,
        min_length=1,
        max_length=5000,
        description="Pregunta o instrucción sobre la imagen"
    )
    usuario_id: int = Field(
        ...,
        gt=0,
        description="ID del usuario"
    )
    conversation_id: Optional[int] = Field(
        None,
        description="ID de conversación existente"
    )
    provider: str = Field(
        default="gemini",
        description="Provider LLM (solo Gemini soporta visión)"
    )
    temperature: float = Field(
        default=0.7,
        ge=0.0,
        le=2.0,
        description="Creatividad del LLM"
    )
    analysis_type: ImageAnalysisType = Field(
        default=ImageAnalysisType.GENERAL,
        description="Tipo de análisis de imagen"
    )
    
    @field_validator('content')
    @classmethod
    def validate_content(cls, v: str) -> str:
        """Valida el contenido."""
        if not v.strip():
            raise ValueError("Content cannot be empty")
        return v.strip()
    
    @field_validator('provider')
    @classmethod
    def validate_provider(cls, v: str) -> str:
        """Valida que sea Gemini (único con visión)."""
        if v.lower() != "gemini":
            raise ValueError("Only 'gemini' provider supports vision analysis")
        return v.lower()


class AnalyzeImageRequest(BaseModel):
    """
    Request para analizar imagen sin conversación.
    
    Attributes:
        prompt: Prompt para el análisis (opcional)
        analysis_type: Tipo de análisis
        document_type: Tipo de documento si analysis_type=document
    """
    prompt: Optional[str] = Field(
        None,
        max_length=2000,
        description="Prompt personalizado para análisis"
    )
    analysis_type: ImageAnalysisType = Field(
        default=ImageAnalysisType.GENERAL,
        description="Tipo de análisis"
    )
    document_type: Optional[str] = Field(
        None,
        max_length=100,
        description="Tipo de documento (factura, recibo, formulario, etc.)"
    )


class OCRRequest(BaseModel):
    """
    Request para extracción de texto (OCR).
    
    Attributes:
        language: Idioma del texto esperado
    """
    language: str = Field(
        default="español",
        max_length=50,
        description="Idioma del texto en la imagen"
    )


class ImageMetadata(BaseModel):
    """Metadata de la imagen procesada."""
    format: str
    width: int
    height: int
    original_size: int
    processed_size: Optional[int] = None
    file_size_mb: float
    
    @classmethod
    def from_service(cls, image_info: Dict[str, Any]):
        """Crea desde respuesta del ImageService."""
        original_size = image_info.get("original_size", 0)
        return cls(
            format=image_info.get("format", "unknown"),
            width=image_info.get("width", 0),
            height=image_info.get("height", 0),
            original_size=original_size,
            processed_size=image_info.get("processed_size"),
            file_size_mb=round(original_size / (1024 * 1024), 2)
        )


class ChatImageResponse(BaseModel):
    """
    Response para mensaje con imagen.
    
    Attributes:
        conversation_id: ID de la conversación
        analysis: Análisis de la imagen
        assistant_response: Respuesta del assistant sobre la imagen
        image_metadata: Metadata de la imagen
        tokens_used: Tokens usados
        processing_time: Tiempo de procesamiento
    """
    conversation_id: int
    analysis: str
    assistant_response: str
    image_metadata: ImageMetadata
    tokens_used: Optional[int] = None
    processing_time: float
    
    class Config:
        json_schema_extra = {
            "example": {
                "conversation_id": 1,
                "analysis": "La imagen muestra un aula universitaria con capacidad para 30 personas...",
                "assistant_response": "He analizado la imagen. Es un aula espaciosa con...",
                "image_metadata": {
                    "format": "jpeg",
                    "width": 1920,
                    "height": 1080,
                    "original_size": 2048000,
                    "processed_size": 512000,
                    "file_size_mb": 1.95
                },
                "tokens_used": 1234,
                "processing_time": 2.5
            }
        }


class AnalyzeImageResponse(BaseModel):
    """
    Response para análisis de imagen.
    
    Attributes:
        success: Si el análisis fue exitoso
        analysis: Resultado del análisis
        analysis_type: Tipo de análisis realizado
        image_metadata: Metadata de la imagen
        processing_time: Tiempo de procesamiento
    """
    success: bool
    analysis: str
    analysis_type: ImageAnalysisType
    image_metadata: ImageMetadata
    processing_time: float
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "analysis": "La imagen muestra un espacio tipo auditorio...",
                "analysis_type": "space",
                "image_metadata": {
                    "format": "jpeg",
                    "width": 1024,
                    "height": 768,
                    "original_size": 1024000,
                    "file_size_mb": 1.0
                },
                "processing_time": 1.8
            }
        }


class OCRResponse(BaseModel):
    """
    Response para extracción de texto (OCR).
    
    Attributes:
        success: Si la extracción fue exitosa
        text: Texto extraído
        has_text: Si se encontró texto en la imagen
        language: Idioma del texto
        image_metadata: Metadata de la imagen
        processing_time: Tiempo de procesamiento
    """
    success: bool
    text: str
    has_text: bool
    language: str
    image_metadata: ImageMetadata
    processing_time: float
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "text": "UNIVERSIDAD ULEAM\nAula 301\nCapacidad: 40 personas",
                "has_text": True,
                "language": "español",
                "image_metadata": {
                    "format": "jpeg",
                    "width": 800,
                    "height": 600,
                    "original_size": 512000,
                    "file_size_mb": 0.5
                },
                "processing_time": 1.5
            }
        }


class IdentifySpaceResponse(BaseModel):
    """
    Response para identificación de espacio.
    
    Attributes:
        success: Si la identificación fue exitosa
        space_identification: Descripción del espacio identificado
        suggested_type: Tipo de espacio sugerido
        suggested_capacity: Capacidad estimada
        image_metadata: Metadata de la imagen
        processing_time: Tiempo de procesamiento
    """
    success: bool
    space_identification: str
    suggested_type: Optional[str] = None
    suggested_capacity: Optional[int] = None
    image_metadata: ImageMetadata
    processing_time: float


class DocumentAnalysisResponse(BaseModel):
    """
    Response para análisis de documento.
    
    Attributes:
        success: Si el análisis fue exitoso
        document_analysis: Análisis estructurado del documento
        document_type: Tipo de documento detectado
        extracted_data: Datos clave extraídos
        image_metadata: Metadata de la imagen
        processing_time: Tiempo de procesamiento
    """
    success: bool
    document_analysis: str
    document_type: Optional[str] = None
    extracted_data: Optional[Dict[str, Any]] = None
    image_metadata: ImageMetadata
    processing_time: float


class ImageUploadInfo(BaseModel):
    """Información sobre archivo subido."""
    filename: str
    content_type: str
    size: int
    size_mb: float
    
    class Config:
        json_schema_extra = {
            "example": {
                "filename": "aula_301.jpg",
                "content_type": "image/jpeg",
                "size": 2048000,
                "size_mb": 1.95
            }
        }


class ErrorResponse(BaseModel):
    """Response de error."""
    success: bool = False
    error: str
    error_type: str
    details: Optional[Dict[str, Any]] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": False,
                "error": "Image too large: 25.3MB (max 20MB)",
                "error_type": "validation_error",
                "details": {
                    "max_size_mb": 20,
                    "received_size_mb": 25.3
                }
            }
        }

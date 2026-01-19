"""
Image Routes

Endpoints para procesamiento de imágenes con Gemini Vision.

Endpoints:
- POST /image/chat - Chat con imagen
- POST /image/analyze - Analizar imagen
- POST /image/ocr - Extraer texto (OCR)
- POST /image/identify-space - Identificar espacio
- POST /image/analyze-document - Analizar documento
"""
import logging
import time
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.orm import Session
import time
from typing import Optional

from ..database import get_db
from ..schemas.image import (
    ChatImageRequest,
    ChatImageResponse,
    AnalyzeImageRequest,
    AnalyzeImageResponse,
    OCRRequest,
    OCRResponse,
    IdentifySpaceResponse,
    DocumentAnalysisResponse,
    ImageMetadata,
    ImageAnalysisType,
    ErrorResponse
)
from ..services.image_service import ImageService, ImageProcessingError
from ..services.orchestrator import AIOrchestrator
from ..config import settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/image", tags=["image"])


# Dependencia para ImageService
def get_image_service() -> ImageService:
    """Dependency injection para ImageService."""
    return ImageService(gemini_api_key=settings.GEMINI_API_KEY)


@router.post(
    "/chat",
    response_model=ChatImageResponse,
    status_code=status.HTTP_200_OK,
    responses={400: {"model": ErrorResponse}, 500: {"model": ErrorResponse}}
)
async def chat_with_image(
    file: UploadFile = File(..., description="Archivo de imagen"),
    content: str = Form(..., description="Mensaje sobre la imagen"),
    usuario_id: int = Form(..., gt=0, description="ID del usuario"),
    conversation_id: Optional[int] = Form(None, description="ID de conversación"),
    temperature: float = Form(default=0.7, ge=0.0, le=2.0),
    analysis_type: str = Form(default="general", description="Tipo de análisis"),
    db: Session = Depends(get_db),
    image_service: ImageService = Depends(get_image_service)
):
    """
    Envía mensaje con imagen al chatbot.
    
    El chatbot analizará la imagen y responderá basándose en ella.
    Solo funciona con provider='gemini' (Gemini Vision).
    
    Args:
        file: Archivo de imagen (JPEG, PNG, WEBP, GIF, BMP) max 20MB
        content: Pregunta o instrucción sobre la imagen
        usuario_id: ID del usuario
        conversation_id: ID de conversación existente (None = nueva)
        temperature: Creatividad del LLM (0.0-2.0)
        analysis_type: Tipo de análisis (general, ocr, document, space)
        db: Sesión de BD
        image_service: Servicio de imágenes
    
    Returns:
        ChatImageResponse: Análisis y respuesta del chatbot
    
    Raises:
        HTTPException: Si falla el procesamiento
    
    Example:
        ```bash
        curl -X POST "http://localhost:5000/api/v1/image/chat" \\
          -F "file=@aula.jpg" \\
          -F "content=¿Qué tipo de espacio es este?" \\
          -F "usuario_id=1"
        ```
    """
    start_time = time.time()
    
    try:
        logger.info(
            "Processing chat with image: usuario_id=%s, filename=%s, size=%d",
            usuario_id,
            file.filename,
            file.size if hasattr(file, 'size') else 0
        )
        
        # 1. Leer bytes de la imagen
        image_bytes = await file.read()
        mime_type = file.content_type or "image/jpeg"
        
        # 2. Analizar imagen con ImageService
        analysis_result = await image_service.analyze_image(
            image_bytes=image_bytes,
            prompt=content,
            mime_type=mime_type
        )
        
        # 3. Crear orchestrator y procesar en contexto de conversación
        orchestrator = AIOrchestrator(db=db, provider_name="gemini")
        
        # Construir mensaje con contexto de la imagen
        enhanced_message = f"""[IMAGEN ANALIZADA]

Análisis de la imagen:
{analysis_result['analysis']}

Usuario pregunta: {content}

Responde de forma útil basándote en el análisis de la imagen."""
        
        # Procesar mensaje con el orchestrator
        chat_result = await orchestrator.process_message(
            user_message=enhanced_message,
            usuario_id=usuario_id,
            conversation_id=conversation_id,
            temperature=temperature
        )
        
        # 4. Preparar respuesta
        processing_time = time.time() - start_time
        
        response = ChatImageResponse(
            conversation_id=chat_result["conversation_id"],
            analysis=analysis_result["analysis"],
            assistant_response=chat_result["assistant_message"]["content"],
            image_metadata=ImageMetadata.from_service(analysis_result["image_info"]),
            tokens_used=chat_result.get("tokens_used"),
            processing_time=round(processing_time, 2)
        )
        
        logger.info(
            "Chat with image completed: conversation_id=%s, time=%.2fs",
            response.conversation_id,
            processing_time
        )
        
        return response
    
    except ImageProcessingError as e:
        logger.error("Image processing error: %s", e)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    
    except Exception as e:
        logger.error("Error in chat with image: %s", e, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process image chat: {str(e)}"
        )


@router.post(
    "/analyze",
    response_model=AnalyzeImageResponse,
    status_code=status.HTTP_200_OK,
    responses={400: {"model": ErrorResponse}, 500: {"model": ErrorResponse}}
)
async def analyze_image(
    file: UploadFile = File(..., description="Archivo de imagen"),
    prompt: Optional[str] = Form(None, description="Prompt personalizado"),
    analysis_type: str = Form(default="general", description="Tipo de análisis"),
    document_type: Optional[str] = Form(None, description="Tipo de documento"),
    image_service: ImageService = Depends(get_image_service)
):
    """
    Analiza una imagen sin crear conversación.
    
    Útil para análisis rápidos sin contexto de chat.
    
    Args:
        file: Archivo de imagen
        prompt: Prompt personalizado (None = usar default según tipo)
        analysis_type: general, ocr, document, space
        document_type: Si analysis_type=document, especificar tipo
        image_service: Servicio de imágenes
    
    Returns:
        AnalyzeImageResponse: Resultado del análisis
    
    Raises:
        HTTPException: Si falla el análisis
    
    Example:
        ```bash
        curl -X POST "http://localhost:5000/api/v1/image/analyze" \\
          -F "file=@espacio.jpg" \\
          -F "analysis_type=space"
        ```
    """
    start_time = time.time()
    
    try:
        logger.info("Analyzing image: filename=%s, type=%s", file.filename, analysis_type)
        
        image_bytes = await file.read()
        mime_type = file.content_type or "image/jpeg"
        
        # Seleccionar análisis según tipo
        analysis_type_enum = ImageAnalysisType(analysis_type)
        
        if analysis_type_enum == ImageAnalysisType.DOCUMENT:
            result = await image_service.analyze_document(
                image_bytes=image_bytes,
                mime_type=mime_type,
                document_type=document_type
            )
            analysis_text = result["document_analysis"]
        
        elif analysis_type_enum == ImageAnalysisType.SPACE:
            result = await image_service.identify_space(
                image_bytes=image_bytes,
                mime_type=mime_type
            )
            analysis_text = result["space_identification"]
        
        else:  # GENERAL u OCR
            custom_prompt = prompt or "Describe esta imagen en detalle"
            result = await image_service.analyze_image(
                image_bytes=image_bytes,
                prompt=custom_prompt,
                mime_type=mime_type
            )
            analysis_text = result["analysis"]
        
        processing_time = time.time() - start_time
        
        response = AnalyzeImageResponse(
            success=True,
            analysis=analysis_text,
            analysis_type=analysis_type_enum,
            image_metadata=ImageMetadata.from_service(result["image_info"]),
            processing_time=round(processing_time, 2)
        )
        
        logger.info("Image analysis completed: type=%s, time=%.2fs", analysis_type, processing_time)
        
        return response
    
    except ImageProcessingError as e:
        logger.error("Image processing error: %s", e)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    
    except Exception as e:
        logger.error("Error analyzing image: %s", e, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to analyze image: {str(e)}"
        )


@router.post(
    "/ocr",
    response_model=OCRResponse,
    status_code=status.HTTP_200_OK,
    responses={400: {"model": ErrorResponse}, 500: {"model": ErrorResponse}}
)
async def extract_text_ocr(
    file: UploadFile = File(..., description="Archivo de imagen"),
    language: str = Form(default="español", description="Idioma del texto"),
    image_service: ImageService = Depends(get_image_service)
):
    """
    Extrae texto de una imagen usando OCR (Gemini Vision).
    
    Args:
        file: Archivo de imagen con texto
        language: Idioma del texto esperado
        image_service: Servicio de imágenes
    
    Returns:
        OCRResponse: Texto extraído
    
    Raises:
        HTTPException: Si falla la extracción
    
    Example:
        ```bash
        curl -X POST "http://localhost:5000/api/v1/image/ocr" \\
          -F "file=@documento.jpg" \\
          -F "language=español"
        ```
    """
    start_time = time.time()
    
    try:
        logger.info("Extracting text from image: filename=%s, language=%s", file.filename, language)
        
        image_bytes = await file.read()
        mime_type = file.content_type or "image/jpeg"
        
        # Extraer texto con OCR
        result = await image_service.extract_text_ocr(
            image_bytes=image_bytes,
            mime_type=mime_type,
            language=language
        )
        
        processing_time = time.time() - start_time
        
        response = OCRResponse(
            success=result["success"],
            text=result["text"],
            has_text=result["has_text"],
            language=result["language"],
            image_metadata=ImageMetadata.from_service(result["image_info"]),
            processing_time=round(processing_time, 2)
        )
        
        logger.info(
            "OCR completed: has_text=%s, chars=%d, time=%.2fs",
            result["has_text"],
            len(result["text"]),
            processing_time
        )
        
        return response
    
    except ImageProcessingError as e:
        logger.error("OCR error: %s", e)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    
    except Exception as e:
        logger.error("Error in OCR: %s", e, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to extract text: {str(e)}"
        )


@router.post(
    "/identify-space",
    response_model=IdentifySpaceResponse,
    status_code=status.HTTP_200_OK,
    responses={400: {"model": ErrorResponse}, 500: {"model": ErrorResponse}}
)
async def identify_space(
    file: UploadFile = File(..., description="Imagen del espacio"),
    image_service: ImageService = Depends(get_image_service)
):
    """
    Identifica un espacio universitario en una imagen.
    
    Útil para que usuarios tomen foto de un espacio y el sistema
    lo identifique automáticamente.
    
    Args:
        file: Imagen del espacio
        image_service: Servicio de imágenes
    
    Returns:
        IdentifySpaceResponse: Identificación del espacio
    
    Raises:
        HTTPException: Si falla la identificación
    
    Example:
        ```bash
        curl -X POST "http://localhost:5000/api/v1/image/identify-space" \\
          -F "file=@aula_301.jpg"
        ```
    """
    start_time = time.time()
    
    try:
        logger.info("Identifying space in image: filename=%s", file.filename)
        
        image_bytes = await file.read()
        mime_type = file.content_type or "image/jpeg"
        
        # Identificar espacio
        result = await image_service.identify_space(
            image_bytes=image_bytes,
            mime_type=mime_type
        )
        
        processing_time = time.time() - start_time
        
        # Intentar extraer tipo y capacidad del análisis
        identification = result["space_identification"]
        suggested_type = None
        suggested_capacity = None
        
        # Análisis simple del texto (mejorable con regex o NLP)
        identification_lower = identification.lower()
        if "aula" in identification_lower:
            suggested_type = "aula"
        elif "auditorio" in identification_lower:
            suggested_type = "auditorio"
        elif "laboratorio" in identification_lower:
            suggested_type = "laboratorio"
        elif "sala" in identification_lower:
            suggested_type = "sala_reuniones"
        
        response = IdentifySpaceResponse(
            success=result["success"],
            space_identification=identification,
            suggested_type=suggested_type,
            suggested_capacity=suggested_capacity,
            image_metadata=ImageMetadata.from_service(result["image_info"]),
            processing_time=round(processing_time, 2)
        )
        
        logger.info("Space identification completed: type=%s, time=%.2fs", suggested_type, processing_time)
        
        return response
    
    except ImageProcessingError as e:
        logger.error("Space identification error: %s", e)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    
    except Exception as e:
        logger.error("Error identifying space: %s", e, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to identify space: {str(e)}"
        )


@router.post(
    "/analyze-document",
    response_model=DocumentAnalysisResponse,
    status_code=status.HTTP_200_OK,
    responses={400: {"model": ErrorResponse}, 500: {"model": ErrorResponse}}
)
async def analyze_document(
    file: UploadFile = File(..., description="Imagen del documento"),
    document_type: Optional[str] = Form(None, description="Tipo de documento"),
    image_service: ImageService = Depends(get_image_service)
):
    """
    Analiza un documento (factura, recibo, formulario, etc.).
    
    Extrae información estructurada y datos clave del documento.
    
    Args:
        file: Imagen del documento
        document_type: Tipo de documento esperado
        image_service: Servicio de imágenes
    
    Returns:
        DocumentAnalysisResponse: Análisis estructurado
    
    Raises:
        HTTPException: Si falla el análisis
    
    Example:
        ```bash
        curl -X POST "http://localhost:5000/api/v1/image/analyze-document" \\
          -F "file=@recibo.jpg" \\
          -F "document_type=recibo de pago"
        ```
    """
    start_time = time.time()
    
    try:
        logger.info("Analyzing document: filename=%s, type=%s", file.filename, document_type)
        
        image_bytes = await file.read()
        mime_type = file.content_type or "image/jpeg"
        
        # Analizar documento
        result = await image_service.analyze_document(
            image_bytes=image_bytes,
            mime_type=mime_type,
            document_type=document_type
        )
        
        processing_time = time.time() - start_time
        
        response = DocumentAnalysisResponse(
            success=result["success"],
            document_analysis=result["document_analysis"],
            document_type=result.get("document_type"),
            extracted_data=None,  # TODO: Implementar extracción estructurada
            image_metadata=ImageMetadata.from_service(result["image_info"]),
            processing_time=round(processing_time, 2)
        )
        
        logger.info("Document analysis completed: time=%.2fs", processing_time)
        
        return response
    
    except ImageProcessingError as e:
        logger.error("Document analysis error: %s", e)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    
    except Exception as e:
        logger.error("Error analyzing document: %s", e, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to analyze document: {str(e)}"
        )

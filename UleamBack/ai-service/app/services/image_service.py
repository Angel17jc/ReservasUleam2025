"""
Image Service

Servicio para procesamiento de imágenes con Gemini Vision.

Responsabilidades:
- Validación de imágenes (formato, tamaño, tipo MIME)
- Conversión y optimización de imágenes
- OCR (extracción de texto)
- Análisis de contenido visual
- Integración con Gemini Vision

Principios aplicados:
- Single Responsibility: Solo procesa imágenes
- Dependency Injection: Recibe LLM adapter
- Error Handling: Validación exhaustiva
- Resource Management: Limpieza de recursos
"""

from typing import Optional, Dict, Any, List, Tuple
from pathlib import Path
import io
import logging
from PIL import Image
import base64

from ..adapters.gemini_adapter import GeminiAdapter
from ..config import settings

logger = logging.getLogger(__name__)


class ImageProcessingError(Exception):
    """Excepción específica para errores de procesamiento de imágenes."""
    pass


class ImageService:
    """
    Servicio para procesamiento y análisis de imágenes.
    
    Utiliza Gemini Vision para análisis visual y extracción de texto.
    """
    
    # Configuración de validación
    MAX_FILE_SIZE = 20 * 1024 * 1024  # 20 MB
    ALLOWED_FORMATS = {"JPEG", "PNG", "WEBP", "GIF", "BMP"}
    ALLOWED_MIME_TYPES = {
        "image/jpeg",
        "image/png",
        "image/webp",
        "image/gif",
        "image/bmp"
    }
    
    # Tamaño máximo para procesamiento (optimización)
    MAX_DIMENSION = 2048  # píxeles
    
    def __init__(self, gemini_api_key: Optional[str] = None):
        """
        Initialize image service.
        
        Args:
            gemini_api_key: API key de Gemini (None = usar de settings)
        """
        # Inicializar Gemini adapter para Vision
        api_key = gemini_api_key or settings.GEMINI_API_KEY
        if not api_key:
            raise ValueError("Gemini API key is required for image processing")
        
        self.gemini_adapter = GeminiAdapter(api_key=api_key)
        
        logger.info("ImageService initialized with Gemini Vision")
    
    def validate_image(
        self,
        image_bytes: bytes,
        mime_type: str
    ) -> Tuple[bool, Optional[str]]:
        """
        Valida una imagen antes de procesarla.
        
        Args:
            image_bytes: Bytes de la imagen
            mime_type: Tipo MIME de la imagen
        
        Returns:
            Tuple[bool, Optional[str]]: (es_válida, mensaje_error)
        """
        # 1. Validar tamaño
        if len(image_bytes) > self.MAX_FILE_SIZE:
            size_mb = len(image_bytes) / (1024 * 1024)
            return False, f"Image too large: {size_mb:.2f}MB (max {self.MAX_FILE_SIZE / (1024 * 1024)}MB)"
        
        # 2. Validar tipo MIME
        if mime_type not in self.ALLOWED_MIME_TYPES:
            return False, f"Invalid MIME type: {mime_type}. Allowed: {self.ALLOWED_MIME_TYPES}"
        
        # 3. Validar que sea imagen válida
        try:
            image = Image.open(io.BytesIO(image_bytes))
            
            # Verificar formato
            if image.format not in self.ALLOWED_FORMATS:
                return False, f"Invalid image format: {image.format}. Allowed: {self.ALLOWED_FORMATS}"
            
            # Verificar dimensiones
            width, height = image.size
            if width <= 0 or height <= 0:
                return False, "Invalid image dimensions"
            
            logger.debug(
                "Image validated: format=%s, size=%dx%d, bytes=%d",
                image.format,
                width,
                height,
                len(image_bytes)
            )
            
            return True, None
        
        except Exception as e:
            logger.error("Image validation failed: %s", e)
            return False, f"Invalid image file: {str(e)}"
    
    def optimize_image(
        self,
        image_bytes: bytes,
        max_dimension: int = MAX_DIMENSION
    ) -> Tuple[bytes, str]:
        """
        Optimiza una imagen para procesamiento.
        
        Reduce el tamaño si es muy grande, mantiene calidad.
        
        Args:
            image_bytes: Bytes de la imagen original
            max_dimension: Dimensión máxima permitida
        
        Returns:
            Tuple[bytes, str]: (imagen_optimizada, formato)
        
        Raises:
            ImageProcessingError: Si falla la optimización
        """
        try:
            image = Image.open(io.BytesIO(image_bytes))
            original_format = image.format or "JPEG"
            
            # Convertir RGBA a RGB si es necesario
            if image.mode == "RGBA":
                rgb_image = Image.new("RGB", image.size, (255, 255, 255))
                rgb_image.paste(image, mask=image.split()[3])  # Alpha channel
                image = rgb_image
            elif image.mode not in ("RGB", "L"):
                image = image.convert("RGB")
            
            # Redimensionar si es muy grande
            width, height = image.size
            if width > max_dimension or height > max_dimension:
                # Mantener aspect ratio
                ratio = min(max_dimension / width, max_dimension / height)
                new_size = (int(width * ratio), int(height * ratio))
                
                image = image.resize(new_size, Image.Resampling.LANCZOS)
                
                logger.info(
                    "Image resized: %dx%d -> %dx%d",
                    width,
                    height,
                    new_size[0],
                    new_size[1]
                )
            
            # Convertir a bytes
            output = io.BytesIO()
            save_format = "JPEG" if original_format == "JPG" else original_format
            image.save(output, format=save_format, quality=85, optimize=True)
            optimized_bytes = output.getvalue()
            
            logger.debug(
                "Image optimized: %d bytes -> %d bytes (%.1f%% reduction)",
                len(image_bytes),
                len(optimized_bytes),
                (1 - len(optimized_bytes) / len(image_bytes)) * 100
            )
            
            return optimized_bytes, save_format.lower()
        
        except Exception as e:
            logger.error("Image optimization failed: %s", e)
            raise ImageProcessingError(f"Failed to optimize image: {str(e)}") from e
    
    async def analyze_image(
        self,
        image_bytes: bytes,
        prompt: str = "Describe esta imagen en detalle",
        mime_type: str = "image/jpeg"
    ) -> Dict[str, Any]:
        """
        Analiza una imagen usando Gemini Vision.
        
        Args:
            image_bytes: Bytes de la imagen
            prompt: Prompt para el análisis
            mime_type: Tipo MIME de la imagen
        
        Returns:
            Dict con análisis de la imagen
        
        Raises:
            ImageProcessingError: Si falla el análisis
        """
        try:
            # 1. Validar imagen
            is_valid, error_msg = self.validate_image(image_bytes, mime_type)
            if not is_valid:
                raise ImageProcessingError(error_msg)
            
            # 2. Optimizar imagen
            optimized_bytes, format_name = self.optimize_image(image_bytes)
            
            # 3. Analizar con Gemini Vision
            logger.info("Analyzing image with Gemini Vision (prompt: '%s')", prompt[:50])
            
            analysis = await self.gemini_adapter.generate_with_vision(
                image_bytes=optimized_bytes,
                prompt=prompt,
                image_format=format_name
            )
            
            logger.info("Image analysis completed (length: %d chars)", len(analysis))
            
            return {
                "success": True,
                "analysis": analysis,
                "image_info": {
                    "original_size": len(image_bytes),
                    "processed_size": len(optimized_bytes),
                    "format": format_name
                }
            }
        
        except ImageProcessingError:
            raise
        except Exception as e:
            logger.error("Image analysis failed: %s", e, exc_info=True)
            raise ImageProcessingError(f"Failed to analyze image: {str(e)}") from e
    
    async def extract_text_ocr(
        self,
        image_bytes: bytes,
        mime_type: str = "image/jpeg",
        language: str = "español"
    ) -> Dict[str, Any]:
        """
        Extrae texto de una imagen usando OCR (Gemini Vision).
        
        Args:
            image_bytes: Bytes de la imagen
            mime_type: Tipo MIME
            language: Idioma del texto esperado
        
        Returns:
            Dict con texto extraído
        
        Raises:
            ImageProcessingError: Si falla la extracción
        """
        prompt = f"""Extrae todo el texto visible en esta imagen.

Instrucciones:
- Transcribe el texto exactamente como aparece
- Mantén el formato y estructura
- Si no hay texto, indica "No se encontró texto"
- Idioma esperado: {language}

Texto extraído:"""
        
        try:
            result = await self.analyze_image(
                image_bytes=image_bytes,
                prompt=prompt,
                mime_type=mime_type
            )
            
            extracted_text = result["analysis"]
            
            # Analizar si se encontró texto
            has_text = not any(
                phrase in extracted_text.lower()
                for phrase in ["no se encontró texto", "no hay texto", "sin texto"]
            )
            
            return {
                "success": True,
                "text": extracted_text,
                "has_text": has_text,
                "language": language,
                "image_info": result["image_info"]
            }
        
        except Exception as e:
            logger.error("OCR extraction failed: %s", e)
            raise ImageProcessingError(f"Failed to extract text: {str(e)}") from e
    
    async def analyze_document(
        self,
        image_bytes: bytes,
        mime_type: str = "image/jpeg",
        document_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Analiza un documento (factura, recibo, formulario, etc.).
        
        Args:
            image_bytes: Bytes de la imagen del documento
            mime_type: Tipo MIME
            document_type: Tipo de documento esperado
        
        Returns:
            Dict con análisis estructurado del documento
        
        Raises:
            ImageProcessingError: Si falla el análisis
        """
        doc_type_hint = f"Este es un {document_type}. " if document_type else ""
        
        prompt = f"""{doc_type_hint}Analiza este documento y extrae la siguiente información:

1. Tipo de documento
2. Información principal (nombres, fechas, montos, etc.)
3. Datos estructurados clave
4. Observaciones importantes

Proporciona la información de forma clara y estructurada."""
        
        try:
            result = await self.analyze_image(
                image_bytes=image_bytes,
                prompt=prompt,
                mime_type=mime_type
            )
            
            return {
                "success": True,
                "document_analysis": result["analysis"],
                "document_type": document_type,
                "image_info": result["image_info"]
            }
        
        except Exception as e:
            logger.error("Document analysis failed: %s", e)
            raise ImageProcessingError(f"Failed to analyze document: {str(e)}") from e
    
    async def identify_space(
        self,
        image_bytes: bytes,
        mime_type: str = "image/jpeg"
    ) -> Dict[str, Any]:
        """
        Identifica un espacio de la universidad en una imagen.
        
        Caso de uso: Usuario toma foto de un espacio y el sistema lo identifica.
        
        Args:
            image_bytes: Bytes de la imagen del espacio
            mime_type: Tipo MIME
        
        Returns:
            Dict con identificación del espacio
        
        Raises:
            ImageProcessingError: Si falla la identificación
        """
        prompt = """Analiza esta imagen de un espacio/lugar y proporciona:

1. Tipo de espacio (aula, auditorio, laboratorio, oficina, etc.)
2. Características visuales (capacidad aproximada, equipamiento visible)
3. Estado del espacio (limpio, ordenado, ocupado, etc.)
4. Detalles relevantes para reservas

Sé específico y objetivo en tu análisis."""
        
        try:
            result = await self.analyze_image(
                image_bytes=image_bytes,
                prompt=prompt,
                mime_type=mime_type
            )
            
            return {
                "success": True,
                "space_identification": result["analysis"],
                "image_info": result["image_info"]
            }
        
        except Exception as e:
            logger.error("Space identification failed: %s", e)
            raise ImageProcessingError(f"Failed to identify space: {str(e)}") from e
    
    def get_image_metadata(self, image_bytes: bytes) -> Dict[str, Any]:
        """
        Extrae metadata de una imagen.
        
        Args:
            image_bytes: Bytes de la imagen
        
        Returns:
            Dict con metadata
        """
        try:
            image = Image.open(io.BytesIO(image_bytes))
            
            metadata = {
                "format": image.format,
                "mode": image.mode,
                "size": image.size,
                "width": image.size[0],
                "height": image.size[1],
                "file_size": len(image_bytes),
                "has_alpha": image.mode in ("RGBA", "LA", "PA")
            }
            
            # EXIF data si existe
            exif = image.getexif()
            if exif:
                metadata["exif_data"] = {
                    "orientation": exif.get(274),  # Orientation tag
                    "datetime": exif.get(306),     # DateTime tag
                    "make": exif.get(271),         # Camera make
                    "model": exif.get(272)         # Camera model
                }
            
            return metadata
        
        except Exception as e:
            logger.error("Failed to extract metadata: %s", e)
            return {"error": str(e)}

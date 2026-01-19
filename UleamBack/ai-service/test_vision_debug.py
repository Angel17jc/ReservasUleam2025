"""
Script de debug para probar Gemini Vision directamente
"""
import asyncio
import sys
from pathlib import Path

# Add app directory to path
sys.path.insert(0, str(Path(__file__).parent))

from app.adapters.gemini_adapter import GeminiAdapter
from app.adapters.base import LLMMessage
from app.config import settings
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

async def test_vision():
    """Test Gemini Vision con una imagen de prueba"""
    try:
        logger.info("Initializing Gemini adapter...")
        adapter = GeminiAdapter(api_key=settings.GEMINI_API_KEY)
        
        logger.info("Testing text generation first...")
        response = await adapter.generate_response(
            messages=[LLMMessage(role="user", content="Di hola en una palabra")],
            temperature=0.7
        )
        logger.info("✓ Text generation works: %s", response.content[:100])
        
        logger.info("\nTesting vision with simple image...")
        # Create a minimal test image (100x100 red square)
        import io
        from PIL import Image
        
        img = Image.new('RGB', (100, 100), color='red')
        img_bytes = io.BytesIO()
        img.save(img_bytes, format='JPEG')
        image_bytes = img_bytes.getvalue()
        
        logger.info("Image size: %d bytes", len(image_bytes))
        
        # Test vision
        result = await adapter.generate_with_vision(
            image_bytes=image_bytes,
            prompt="¿De qué color es esta imagen? Responde solo con el color.",
            image_format="jpeg"
        )
        
        logger.info("✓ Vision analysis result: %s", result)
        
        # Test with a more complex image
        logger.info("\nTesting with gradient image...")
        img2 = Image.new('RGB', (200, 200))
        pixels = img2.load()
        for i in range(200):
            for j in range(200):
                pixels[i, j] = (i % 256, j % 256, (i + j) % 256)
        
        img_bytes2 = io.BytesIO()
        img2.save(img_bytes2, format='PNG')
        image_bytes2 = img_bytes2.getvalue()
        
        result2 = await adapter.generate_with_vision(
            image_bytes=image_bytes2,
            prompt="Describe brevemente los colores y patrones que ves en esta imagen.",
            image_format="png"
        )
        
        logger.info("✓ Complex vision result: %s", result2)
        
        return True
    except Exception as e:
        logger.error("❌ Error: %s", e, exc_info=True)
        return False

if __name__ == "__main__":
    success = asyncio.run(test_vision())
    sys.exit(0 if success else 1)

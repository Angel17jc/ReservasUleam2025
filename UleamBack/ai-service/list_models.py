"""List available Gemini models"""
from google import genai
from app.config import settings

client = genai.Client(api_key=settings.GEMINI_API_KEY)
print("Available Gemini models:\n")
for model in client.models.list():
    print(f"- {model.name}")
    if hasattr(model, 'supported_generation_methods'):
        print(f"  Methods: {model.supported_generation_methods}")

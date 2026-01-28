"""
Test script para verificar la conversión de tools en Groq adapter.
"""
import sys
sys.path.insert(0, 'C:\\ReservasUleam2025\\UleamBack\\ai-service')

from app.adapters.groq_adapter import GroqAdapter
from app.mcp.tool_registry import ToolRegistry

# Obtener tools del registry
tools = ToolRegistry.get_all_schemas()

print("\n=== TOOLS DEL REGISTRY ===")
print(f"Total tools: {len(tools)}")
for i, tool in enumerate(tools):
    print(f"\nTool {i+1}: {tool.get('name')}")
    print(f"  Keys: {list(tool.keys())}")
    print(f"  Format: {tool}")

# Crear adapter
try:
    adapter = GroqAdapter()
    
    # Convertir tools
    print("\n\n=== CONVERSIÓN A FORMATO GROQ ===")
    groq_tools = adapter._convert_tools_to_groq_format(tools)
    
    print(f"Total tools convertidas: {len(groq_tools)}")
    for i, tool in enumerate(groq_tools):
        print(f"\nTool {i+1}:")
        print(f"  type: {tool.get('type')}")
        print(f"  function.name: {tool.get('function', {}).get('name')}")
        print(f"  Full format: {tool}")
    
    print("\n✅ Conversión exitosa")
    
except Exception as e:
    print(f"\n❌ Error: {e}")
    import traceback
    traceback.print_exc()

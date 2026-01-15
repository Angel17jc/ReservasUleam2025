"""
Test script para verificar que los MCP Tools están correctamente registrados.

Ejecutar:
    python test_tools.py
"""

import sys
import asyncio
from pathlib import Path

# Add app to path
sys.path.insert(0, str(Path(__file__).parent))

from app.mcp import ToolRegistry
from app.mcp.base_tool import ToolCategory


async def main():
    """Test tools registration and schemas."""
    
    print("=" * 60)
    print("MCP TOOLS VERIFICATION")
    print("=" * 60)
    
    # Check total tools registered
    total_tools = ToolRegistry.count()
    print(f"\n✅ Total tools registered: {total_tools}")
    
    if total_tools == 0:
        print("\n❌ ERROR: No tools registered!")
        print("   Make sure to import the mcp module in main.py")
        return
    
    # List all tools
    print(f"\n📋 Registered tools:")
    for name in ToolRegistry.list_tool_names():
        tool = ToolRegistry.get(name)
        category_icon = {
            ToolCategory.CONSULTA: "🔍",
            ToolCategory.ACCION: "⚡",
            ToolCategory.REPORTE: "📊"
        }.get(tool.category, "❓")
        
        print(f"   {category_icon} {name} ({tool.category.value})")
    
    # Check by category
    print(f"\n📊 Tools by category:")
    for category in ToolCategory:
        tools = ToolRegistry.get_by_category(category)
        count = len(tools)
        required = {
            ToolCategory.CONSULTA: 2,
            ToolCategory.ACCION: 2,
            ToolCategory.REPORTE: 1
        }[category]
        
        status = "✅" if count >= required else "⚠️"
        print(f"   {status} {category.value}: {count}/{required}")
        for name in tools.keys():
            print(f"      - {name}")
    
    # Verificar que cumplimos con los requisitos del Pilar 3
    consulta_count = len(ToolRegistry.get_by_category(ToolCategory.CONSULTA))
    accion_count = len(ToolRegistry.get_by_category(ToolCategory.ACCION))
    reporte_count = len(ToolRegistry.get_by_category(ToolCategory.REPORTE))
    
    print(f"\n🎯 REQUISITOS PILAR 3:")
    print(f"   {'✅' if consulta_count >= 2 else '❌'} 2 tools de consulta: {consulta_count}/2")
    print(f"   {'✅' if accion_count >= 2 else '❌'} 2 tools de acción: {accion_count}/2")
    print(f"   {'✅' if reporte_count >= 1 else '❌'} 1 tool de reporte: {reporte_count}/1")
    
    total_required = consulta_count >= 2 and accion_count >= 2 and reporte_count >= 1
    if total_required:
        print(f"\n   ✅ TODOS LOS REQUISITOS CUMPLIDOS!")
    else:
        print(f"\n   ❌ Faltan tools por implementar")
    
    # Show schemas for LLM
    print(f"\n🔧 Tool schemas for LLM function calling:")
    schemas = ToolRegistry.get_all_schemas()
    
    for schema in schemas:
        print(f"\n   Tool: {schema['name']}")
        print(f"   Description: {schema['description'][:80]}...")
        print(f"   Parameters: {len(schema['parameters']['properties'])}")
        
        # Show parameter names
        param_names = list(schema['parameters']['properties'].keys())
        if param_names:
            required_params = schema['parameters'].get('required', [])
            print(f"   Required params: {', '.join(required_params) if required_params else 'None'}")
    
    # Test individual tool
    print(f"\n🧪 Testing individual tool (buscar_espacios):")
    tool = ToolRegistry.get("buscar_espacios")
    if tool:
        print(f"   ✅ Tool found: {tool.name}")
        print(f"   Category: {tool.category}")
        print(f"   Description: {tool.description[:100]}...")
        
        # Try to execute with test parameters
        try:
            result = await tool.execute(capacidad_min=20, disponible=True)
            if result.success:
                print(f"   ✅ Execution test: SUCCESS")
                print(f"   Note: Real data depends on REST service being available")
            else:
                print(f"   ⚠️  Execution test: {result.error}")
                print(f"   Note: This is expected if REST service is not running")
        except Exception as e:
            print(f"   ⚠️  Execution test error: {e}")
            print(f"   Note: This is expected if REST service is not running")
    else:
        print(f"   ❌ Tool 'buscar_espacios' not found!")
    
    print("\n" + "=" * 60)
    print("VERIFICATION COMPLETE")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())

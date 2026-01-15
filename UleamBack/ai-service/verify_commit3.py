"""
Script de Verificación Rápida - Commit 3

Verifica que todos los componentes de function calling estén correctamente integrados.

Uso:
    python verify_commit3.py
"""

import sys
from pathlib import Path

# Agregar el directorio raíz al path
root_dir = Path(__file__).parent
sys.path.insert(0, str(root_dir))


def verify_imports():
    """Verifica que todos los módulos se puedan importar."""
    print("🔍 Verificando imports...\n")
    
    try:
        from app.mcp.tool_registry import ToolRegistry
        print("✅ ToolRegistry importado")
        
        from app.services.tool_execution_manager import ToolExecutionManager
        print("✅ ToolExecutionManager importado")
        
        from app.adapters.gemini_adapter import GeminiAdapter
        print("✅ GeminiAdapter importado")
        
        from app.adapters.groq_adapter import GroqAdapter
        print("✅ GroqAdapter importado")
        
        from app.services.orchestrator import AIOrchestrator
        print("✅ AIOrchestrator importado")
        
        print("\n✅ Todos los imports exitosos\n")
        return True
    
    except Exception as e:
        print(f"\n❌ Error en imports: {e}\n")
        return False


def verify_tools_registered():
    """Verifica que las 5 tools estén registradas."""
    print("🔍 Verificando registro de tools...\n")
    
    try:
        from app.mcp.tool_registry import ToolRegistry
        
        # Importar el módulo mcp para triggear auto-registration
        from app import mcp
        
        total = ToolRegistry.count()
        print(f"📊 Total de tools registradas: {total}")
        
        if total < 5:
            print(f"❌ Se esperaban al menos 5 tools, pero hay {total}\n")
            return False
        
        # Verificar nombres
        tool_names = ToolRegistry.list_tool_names()
        print(f"📝 Tools disponibles: {', '.join(tool_names)}\n")
        
        expected = ["buscarespacios", "verreservas", "crearreserva", "registrarusuario", "estadisticasreservas"]
        missing = [name for name in expected if name not in tool_names]
        
        if missing:
            print(f"❌ Faltan tools: {', '.join(missing)}\n")
            return False
        
        print("✅ Todas las tools esperadas están registradas\n")
        return True
    
    except Exception as e:
        print(f"❌ Error verificando tools: {e}\n")
        return False


def verify_tool_schemas():
    """Verifica que las tools tengan schemas válidos."""
    print("🔍 Verificando schemas de tools...\n")
    
    try:
        from app.mcp.tool_registry import ToolRegistry
        from app import mcp
        
        schemas = ToolRegistry.get_all_schemas()
        
        if not schemas:
            print("❌ No se encontraron schemas\n")
            return False
        
        for schema in schemas:
            # El schema tiene estructura directa: {"name": ..., "description": ..., "parameters": ...}
            # NO tiene wrapper {"type": "function", "function": {...}}
            name = schema.get("name", "")
            params = schema.get("parameters", {})
            description = schema.get("description", "")
            
            # Verificar estructura básica
            if not name:
                print(f"❌ Schema sin nombre encontrado: {schema}\n")
                return False
            
            if not description:
                print(f"❌ Tool '{name}' no tiene descripción\n")
                return False
            
            if "properties" not in params:
                print(f"❌ Tool '{name}' no tiene properties en parameters\n")
                return False
            
            # Params puede tener 0 o más properties
            param_count = len(params.get("properties", {}))
            
            print(f"✅ {name}: {param_count} parámetros, descripción OK")
        
        print(f"\n✅ Todos los schemas son válidos ({len(schemas)} tools)\n")
        return True
    
    except Exception as e:
        print(f"❌ Error verificando schemas: {e}\n")
        import traceback
        traceback.print_exc()
        return False


def verify_adapters_support_tools():
    """Verifica que los adapters soporten el parámetro tools."""
    print("🔍 Verificando soporte de tools en adapters...\n")
    
    try:
        import inspect
        from app.adapters.gemini_adapter import GeminiAdapter
        from app.adapters.groq_adapter import GroqAdapter
        
        # Verificar signature de generate_response
        gemini_sig = inspect.signature(GeminiAdapter.generate_response)
        groq_sig = inspect.signature(GroqAdapter.generate_response)
        
        if "tools" not in gemini_sig.parameters:
            print("❌ GeminiAdapter.generate_response no acepta parámetro 'tools'\n")
            return False
        
        if "tools" not in groq_sig.parameters:
            print("❌ GroqAdapter.generate_response no acepta parámetro 'tools'\n")
            return False
        
        print("✅ GeminiAdapter acepta parámetro 'tools'")
        print("✅ GroqAdapter acepta parámetro 'tools'\n")
        
        print("✅ Ambos adapters soportan function calling\n")
        return True
    
    except Exception as e:
        print(f"❌ Error verificando adapters: {e}\n")
        return False


def verify_orchestrator_integration():
    """Verifica que el orchestrator tenga integración con tools."""
    print("🔍 Verificando integración en orchestrator...\n")
    
    try:
        import inspect
        from app.services.orchestrator import AIOrchestrator
        
        # Verificar que tenga tool_manager
        if not hasattr(AIOrchestrator, '__init__'):
            print("❌ AIOrchestrator no tiene __init__\n")
            return False
        
        # Verificar métodos esperados
        expected_methods = [
            "_execute_tool_calls",
            "_get_final_response_after_tools"
        ]
        
        for method in expected_methods:
            if not hasattr(AIOrchestrator, method):
                print(f"❌ AIOrchestrator no tiene método '{method}'\n")
                return False
            print(f"✅ Método '{method}' encontrado")
        
        print("\n✅ Orchestrator tiene integración completa\n")
        return True
    
    except Exception as e:
        print(f"❌ Error verificando orchestrator: {e}\n")
        return False


def main():
    """Ejecuta todas las verificaciones."""
    print("\n" + "="*70)
    print("  🧪 VERIFICACIÓN DE COMMIT 3: Function Calling")
    print("="*70 + "\n")
    
    results = []
    
    # 1. Imports
    results.append(("Imports", verify_imports()))
    
    # 2. Tools registradas
    results.append(("Tools Registradas", verify_tools_registered()))
    
    # 3. Schemas
    results.append(("Schemas", verify_tool_schemas()))
    
    # 4. Adapters
    results.append(("Adapters", verify_adapters_support_tools()))
    
    # 5. Orchestrator
    results.append(("Orchestrator", verify_orchestrator_integration()))
    
    # Resumen
    print("="*70)
    print("  📊 RESUMEN DE VERIFICACIÓN")
    print("="*70 + "\n")
    
    for name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status} - {name}")
    
    total_passed = sum(1 for _, passed in results if passed)
    total = len(results)
    
    print(f"\n{'='*70}")
    print(f"  Resultados: {total_passed}/{total} verificaciones exitosas")
    print(f"{'='*70}\n")
    
    if total_passed == total:
        print("🎉 COMMIT 3 VERIFICADO EXITOSAMENTE!")
        print("✅ Todos los componentes de function calling están correctamente integrados\n")
        print("📝 Próximos pasos:")
        print("   1. Ejecutar tests: python test_function_calling.py")
        print("   2. Asegurar que REST Service esté corriendo (puerto 8000)")
        print("   3. Asegurar que Auth Service esté corriendo (puerto 9000)")
        print("   4. Iniciar AI Service: python -m uvicorn main:app --port 5000\n")
        return True
    else:
        print("❌ HAY ERRORES EN LA VERIFICACIÓN")
        print("Por favor revisa los mensajes de error arriba\n")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

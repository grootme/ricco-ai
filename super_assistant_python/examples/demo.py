#!/usr/bin/env python3
"""
Ejemplo de uso del Super Asistente con Capital Cognitivo.
"""

import asyncio
import sys
sys.path.insert(0, '/home/z/my-project/super_assistant_python')


async def main():
    """Ejemplo principal de uso."""
    from super_assistant import (
        SuperAssistant,
        MemoryType,
        create_memory_system
    )
    
    print("=" * 60)
    print("🧠 Super Asistente con Capital Cognitivo")
    print("=" * 60)
    
    # Crear el asistente
    print("\n1. Inicializando Super Asistente...")
    assistant = SuperAssistant()
    print("   ✅ Asistente inicializado correctamente")
    
    # Ejemplo de chat
    print("\n2. Enviando mensaje de prueba...")
    response = await assistant.chat(
        message="Hola, ¿puedes ayudarme a investigar sobre inteligencia artificial?",
        user_id="demo_user",
        session_id="demo_session"
    )
    
    print("\n📝 Respuesta:")
    print("-" * 40)
    print(response.content)
    print("-" * 40)
    
    # Ejemplo de memoria
    print("\n3. Probando sistema de memoria...")
    
    # Almacenar preferencia
    memory_id = await assistant.remember(
        content="El usuario prefiere explicaciones técnicas detalladas",
        memory_type=MemoryType.PREFERENCE,
        user_id="demo_user"
    )
    print(f"   ✅ Preferencia almacenada: {memory_id}")
    
    # Recuperar memorias
    memories = await assistant.recall(
        query="preferencias del usuario",
        user_id="demo_user"
    )
    print(f"   ✅ Memorias recuperadas: {len(memories)}")
    
    for i, mem in enumerate(memories[:3], 1):
        print(f"      {i}. {mem.content[:50]}...")
    
    # Listar skills disponibles
    print("\n4. Skills disponibles:")
    skills = assistant._skill_registry.list_all()
    for skill in skills:
        print(f"   - {skill}")
    
    # Ejecutar una skill
    print("\n5. Ejecutando skill de búsqueda web...")
    result = await assistant.execute_skill(
        "web_search",
        {"query": "machine learning trends 2024", "num_results": 3}
    )
    
    if result.success:
        print("   ✅ Búsqueda exitosa")
        print(f"   Resultados: {result.output}")
    else:
        print(f"   ❌ Error: {result.error}")
    
    # Estado final
    print("\n6. Estado del asistente:")
    print(f"   - Mensajes procesados: {response.iterations}")
    print(f"   - Skills disponibles: {len(skills)}")
    print(f"   - Memorias almacenadas: {len(memories)}")
    
    print("\n" + "=" * 60)
    print("✅ Demo completada exitosamente")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())

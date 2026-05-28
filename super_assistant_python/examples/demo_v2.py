#!/usr/bin/env python3
"""
Demo completo del Super Asistente V2.
Demuestra: RAG Ontológico, Capital Cognitivo, MCP, Patrones GOF, Agentes SWE con CoT.
"""

import asyncio
import sys
sys.path.insert(0, '/home/z/my-project/super_assistant_python')


async def demo_knowledge_graph():
    """Demuestra el Knowledge Graph Ontológico."""
    print("\n" + "="*60)
    print("📊 DEMO: Knowledge Graph Ontológico")
    print("="*60)
    
    from knowledge_graph.ontological_rag import (
        KnowledgeGraph, EntityType, RelationType, EntityFactory
    )
    
    # Crear Knowledge Graph
    kg = KnowledgeGraph()
    
    # Agregar entidades
    print("\n1. Agregando entidades al grafo...")
    
    await kg.add_entity(
        name="Python",
        entity_type=EntityType.TECHNOLOGY,
        description="Lenguaje de programación de alto nivel"
    )
    
    await kg.add_entity(
        name="LangChain",
        entity_type=EntityType.TECHNOLOGY,
        description="Framework para aplicaciones LLM"
    )
    
    await kg.add_entity(
        name="GPT-4",
        entity_type=EntityType.TECHNOLOGY,
        description="Modelo de lenguaje de OpenAI"
    )
    
    await kg.add_entity(
        name="Research Agent",
        entity_type=EntityType.AGENT,
        description="Agente especializado en investigación"
    )
    
    # Agregar relaciones
    print("2. Agregando relaciones...")
    
    entities = list(kg._entities.values())
    if len(entities) >= 2:
        await kg.add_relationship(
            source_id=entities[1].id,  # LangChain
            target_id=entities[0].id,  # Python
            relation_type=RelationType.DEPENDS_ON,
            description="LangChain está escrito en Python"
        )
        
        await kg.add_relationship(
            source_id=entities[3].id,  # Research Agent
            target_id=entities[1].id,  # LangChain
            relation_type=RelationType.USES,
            description="El agente usa LangChain"
        )
    
    # Búsqueda semántica
    print("3. Buscando en el grafo...")
    results = await kg.semantic_search("lenguaje programación", top_k=3)
    
    print(f"\n   Resultados para 'lenguaje programación':")
    for entity, score in results:
        print(f"   - {entity.name} ({entity.entity_type.value}): score {score:.2f}")
    
    # Detectar comunidades
    print("\n4. Detectando comunidades...")
    communities = await kg.detect_communities()
    print(f"   Encontradas {len(communities)} comunidades")
    
    return kg


async def demo_cognitive_capital():
    """Demuestra el sistema de Capital Cognitivo."""
    print("\n" + "="*60)
    print("🧠 DEMO: Capital Cognitivo")
    print("="*60)
    
    from cognitive_capital.manager import (
        CognitiveCapitalManager, CognitiveAssetType
    )
    
    # Crear manager
    manager = CognitiveCapitalManager()
    
    # Aprender de interacciones
    print("\n1. Aprendiendo de interacciones...")
    
    await manager.learn_from_interaction(
        user_input="¿Qué es LangGraph?",
        agent_response="LangGraph es una biblioteca para construir aplicaciones con agentes usando grafos de estado.",
        context={"session": "demo"}
    )
    
    await manager.learn_from_interaction(
        user_input="¿Cómo implemento un agente?",
        agent_response="Para implementar un agente: 1) Define el estado 2) Crea nodos 3) Conecta con edges",
        context={"session": "demo"}
    )
    
    # Recuperar contexto
    print("2. Recuperando contexto para tarea...")
    context = await manager.get_context_for_task("implementar agente")
    
    print(f"\n   Contexto relevante encontrado: {context['relevant_assets']} activos")
    if context['top_context']:
        print(f"   Top contexto: {context['top_context'][:100]}...")
    
    # Reporte de capital
    print("\n3. Generando reporte de capital...")
    report = manager.get_capital_report()
    
    print(f"   Total activos: {report['cognitive_capital_report']['statistics']['total_assets']}")
    print(f"   Por tipo: {report['cognitive_capital_report']['statistics']['by_type']}")
    
    return manager


async def demo_mcp_integration():
    """Demuestra la integración MCP."""
    print("\n" + "="*60)
    print("🔌 DEMO: MCP Integration")
    print("="*60)
    
    from mcp.integration import (
        MCPClientFacade, MCPServerConfig, MCPTransportType,
        BuiltinMCPSkills
    )
    
    # Crear cliente MCP
    client = MCPClientFacade()
    
    print("\n1. Skills MCP Built-in disponibles:")
    skills = BuiltinMCPSkills.get_all_skills()
    
    for skill in skills:
        print(f"\n   📦 {skill['name']}:")
        print(f"      {skill['description']}")
        for tool in skill['tools']:
            print(f"      - {tool['name']}: {tool['description']}")
    
    return client


async def demo_gof_patterns():
    """Demuestra los patrones GOF."""
    print("\n" + "="*60)
    print("🎨 DEMO: Patrones GOF")
    print("="*60)
    
    from patterns.gof_patterns import (
        AgentBuilder, AgentRegistry, TaskComponent, SimpleTask,
        CompositeTask, LoggingDecorator, CachingDecorator,
        SequentialStrategy, ParallelStrategy
    )
    
    # Builder Pattern
    print("\n1. Builder Pattern - Construyendo agente:")
    agent_config = (
        AgentBuilder()
        .with_name("CustomAgent")
        .with_role("assistant")
        .with_max_iterations(15)
        .with_system_prompt("Eres un asistente especializado")
        .build()
    )
    print(f"   Agente creado: {agent_config['name']}")
    print(f"   Max iteraciones: {agent_config['max_iterations']}")
    
    # Composite Pattern
    print("\n2. Composite Pattern - Tareas compuestas:")
    
    async def task1(): return "Resultado 1"
    async def task2(): return "Resultado 2"
    
    composite = CompositeTask("Main Task")
    composite.add(SimpleTask("Subtask 1", task1))
    composite.add(SimpleTask("Subtask 2", task2))
    
    result = await composite.execute()
    print(f"   Tarea ejecutada: {result['task']}")
    print(f"   Hijos: {len(result['children_results'])} resultados")
    
    # Strategy Pattern
    print("\n3. Strategy Pattern - Estrategias de ejecución:")
    
    tasks = [
        {"name": "Task A", "priority": 3},
        {"name": "Task B", "priority": 1},
        {"name": "Task C", "priority": 2}
    ]
    
    seq_strategy = SequentialStrategy()
    results = await seq_strategy.execute(tasks)
    print(f"   Ejecución secuencial: {len(results)} tareas")
    
    # Decorator Pattern
    print("\n4. Decorator Pattern - Decoradores:")
    print("   - LoggingDecorator: Añade logging")
    print("   - CachingDecorator: Añade caché")
    print("   - RetryDecorator: Añade reintentos")


async def demo_swe_agents():
    """Demuestra los agentes SWE con CoT."""
    print("\n" + "="*60)
    print("🤖 DEMO: SWE Agents con Chain of Thought")
    print("="*60)
    
    from swe_agents.cot_agents import (
        SWEAgentTeam, ThoughtType
    )
    
    # Crear equipo
    team = SWEAgentTeam()
    
    print("\n1. Resolviendo problema de código...")
    
    problem = "Necesito una función que calcule el factorial de un número"
    
    result = await team.solve(problem)
    
    print(f"\n   Problema: {problem}")
    print(f"   Éxito: {result['success']}")
    
    # Mostrar cadena de pensamientos
    print("\n2. Cadena de pensamientos del equipo:")
    
    chains = team.get_thought_chains()
    for i, chain in enumerate(chains[:2], 1):
        print(f"\n   Agente {i} - Task: {chain.task[:50]}...")
        for thought in chain.thoughts[:3]:
            print(f"      [{thought.type.value}] {thought.content[:50]}...")
    
    # Código generado
    if result['results'].get('code', {}).get('code_changes'):
        code_change = result['results']['code']['code_changes'][0]
        print(f"\n3. Código generado:")
        print("   " + code_change.get('content', '')[:200].replace('\n', '\n   ') + "...")


async def demo_full_integration():
    """Demuestra la integración completa."""
    print("\n" + "="*60)
    print("🚀 DEMO: Super Assistant V2 - Integración Completa")
    print("="*60)
    
    # Importar clase principal
    from super_assistant import SuperAssistantV2
    
    print("\n1. Inicializando Super Assistant V2...")
    assistant = SuperAssistantV2(
        enable_knowledge_graph=True,
        enable_cognitive_capital=True,
        enable_mcp=True,
        enable_swe_agents=True
    )
    
    print("   ✅ Todos los módulos inicializados")
    
    # Chat
    print("\n2. Enviando mensaje de chat...")
    response = await assistant.chat(
        message="Explícame qué es RAG y cómo funciona",
        user_id="demo_user",
        session_id="demo_session"
    )
    
    print(f"   Respuesta: {response.content[:150]}...")
    
    # Aprender conocimiento
    print("\n3. Aprendiendo nuevo conocimiento...")
    learn_result = await assistant.learn_knowledge(
        text="Chain of Thought (CoT) es una técnica de prompting que mejora el razonamiento",
        source="demo"
    )
    print(f"   Aprendido: {learn_result}")
    
    # Consultar conocimiento
    print("\n4. Consultando conocimiento...")
    query_result = await assistant.query_knowledge("razonamiento")
    print(f"   Resultados KG: {query_result.get('knowledge_graph', {}).get('relevant_entities', [])[:2]}")
    
    # Resolver problema de código
    print("\n5. Resolviendo problema de código...")
    code_result = await assistant.solve_code_problem(
        problem="Crear una función de validación de email",
        code=""
    )
    print(f"   Éxito: {code_result.get('success', False)}")
    
    # Reporte cognitivo
    print("\n6. Generando reporte cognitivo...")
    report = assistant.get_cognitive_report()
    print(f"   Timestamp: {report['timestamp']}")
    if 'cognitive_capital' in report['components']:
        cc = report['components']['cognitive_capital']
        print(f"   Capital total: {cc['cognitive_capital_report']['statistics']['total_assets']} activos")


async def main():
    """Función principal del demo."""
    print("\n" + "="*70)
    print("   🧠 SUPER ASSISTANT V2 - DEMO COMPLETO")
    print("   RAG Ontológico | Capital Cognitivo | MCP | GOF | SWE CoT")
    print("="*70)
    
    try:
        # Demo Knowledge Graph
        await demo_knowledge_graph()
        
        # Demo Capital Cognitivo
        await demo_cognitive_capital()
        
        # Demo MCP
        await demo_mcp_integration()
        
        # Demo Patrones GOF
        await demo_gof_patterns()
        
        # Demo SWE Agents
        await demo_swe_agents()
        
        # Demo integración completa
        await demo_full_integration()
        
        print("\n" + "="*70)
        print("   ✅ DEMO COMPLETADO EXITOSAMENTE")
        print("="*70 + "\n")
        
    except Exception as e:
        print(f"\n❌ Error en demo: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())

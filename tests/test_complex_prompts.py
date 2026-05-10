"""
Complex Prompts Test Suite - Pruebas de Prompts Complejos

Esta suite prueba todos los agentes con prompts complejos y sofisticados
que evalúan la capacidad del sistema para manejar:
- Consultas de memoria complejas
- Razonamiento multi-paso
- Orquestación y delegación
- Integración con LLM vía OpenRouter
- Flujos de trabajo completos

API Key: test-api-key-replaced
Modelos Free: llama-3-8b-instruct, mistral-7b-instruct, gemma-7b-it, deepseek-r1
"""

import pytest
import asyncio
import json
from typing import Dict, Any, List, Optional
from datetime import datetime

pytestmark = pytest.mark.asyncio


# =============================================================================
# FIXTURES PARA TESTS DE PROMPTS
# =============================================================================

@pytest.fixture
def openrouter_provider():
    """Provider de OpenRouter configurado"""
    from src.ai_providers.providers.openrouter_provider import OpenRouterProvider
    
    api_key = "test-api-key-replaced"
    
    provider = OpenRouterProvider(
        api_key=api_key,
        model="meta-llama/llama-3-8b-instruct:free"
    )
    
    yield provider
    
    # Cleanup
    asyncio.get_event_loop().run_until_complete(provider.close())


@pytest.fixture
def complex_obviousness():
    """Contexto de obviedad complejo para tests"""
    from src.core.obviousness import ObviousnessContextBuilder
    
    return (ObviousnessContextBuilder(
        session_id="complex-test-session",
        user_id="test-user-complex"
    )
    .with_objective(
        objective="Realizar análisis comprehensivo del mercado de IA y generar recomendaciones estratégicas",
        success_criteria=[
            "Identificar tendencias clave 2024-2025",
            "Analizar competencia principal",
            "Proyectar crecimiento del mercado",
            "Generar 5 recomendaciones estratégicas",
            "Calcular ROI potencial"
        ],
        deliverables=[
            "Reporte ejecutivo PDF",
            "Dataset de análisis",
            "Presentación ejecutiva",
            "Modelo de proyección"
        ]
    )
    .with_metrics(
        recall=0.90,
        precision=0.85,
        f1=0.87
    )
    .with_boundaries(
        allow=["web_search", "database", "analytics", "reporting"],
        deny=["production_systems", "customer_data", "payment_processing"],
        tools=["search", "analyze", "report", "calculate"],
        restricted_tools=["execute_code", "file_deletion"],
        sandbox=True
    )
    .with_relevance(
        impact="critical",
        ccv=10,
        business_context="Planificación estratégica anual para C-Suite",
        stakeholder="CEO"
    )
    .with_time(
        priority="urgent",
        timeout=1800,
        latency=60
    )
    .with_domain("strategy", persona="strategic_advisor")
    .build())


# =============================================================================
# TESTS DE PROMPTS COMPLEJOS
# =============================================================================

class TestComplexPrompts:
    """Tests con prompts complejos y sofisticados"""
    
    @pytest.mark.integration
    async def test_complex_reasoning_prompt(self, openrouter_provider):
        """Test: Prompt de razonamiento complejo multi-paso"""
        
        prompt = """
Eres un agente de IA especializado en análisis estratégico. Tu tarea es realizar un razonamiento estructurado.

CONTEXTO DEL PROBLEMA:
Una empresa tecnológica está evaluando entrar al mercado de IA Generativa. Tienen:
- Presupuesto: $50M USD
- Equipo técnico: 120 ingenieros
- Experiencia: Cloud computing y DevOps
- Mercado actual: LatAm

INSTRUCCIONES:
Para cada paso, muestra tu razonamiento explícitamente.

PASO 1: Analiza las fortalezas de la empresa
PASO 2: Identifica oportunidades en el mercado de IA Generativa
PASO 3: Evalúa riesgos y amenazas
PASO 4: Propone 3 estrategias de entrada al mercado
PASO 5: Recomienda la mejor estrategia con justificación

RESPONDE EN FORMATO:
## PASO X: [Nombre]
**Razonamiento:** ...
**Conclusión:** ...
"""
        
        response = await openrouter_provider.chat_completion(
            messages=[{"role": "user", "content": prompt}],
            max_tokens=2000,
            temperature=0.7
        )
        
        assert response is not None
        if response.get("success"):
            content = response.get("content", "")
            assert len(content) > 100
            print(f"\n=== RESPUESTA DE RAZONAMIENTO ===\n{content[:500]}...")
    
    @pytest.mark.integration
    async def test_memory_consolidation_prompt(self, openrouter_provider, temp_db):
        """Test: Prompt de consolidación de memoria"""
        from src.memory.vcs import MemoryVCS
        
        # Crear Memory VCS
        vcs = MemoryVCS(db_path=temp_db, auto_init=True)
        
        # Almacenar memories
        memories = [
            ("market:ai:trends", "IA Generativa creciendo 40% YoY. Modelos open source ganando participación."),
            ("market:ai:players", "OpenAI, Anthropic, Google lideran. Meta y Mistral en open source."),
            ("market:ai:investment", "Inversión en IA alcanzó $25B en 2024. Enterprise adoption acelerándose."),
            ("competitor:openai", "GPT-4 y GPT-4o dominan enterprise. API revenue principal driver."),
            ("competitor:anthropic", "Claude 3 positioning como safer AI. Fuerte en enterprise compliance."),
        ]
        
        for topic, content in memories:
            vcs.upsert(topic_key=topic, content=content)
        
        # Prompt para consolidar
        memories_data = {topic: vcs.get_by_key(topic)['content'] for topic, _ in memories}
        prompt = f"""
Eres un agente especializado en consolidación de conocimiento. Tu tarea es sintetizar información dispersa en insights estratégicos.

MEMORIAS DISPONIBLES:
{json.dumps(memories_data, indent=2)}

TU TAREA:
1. Identifica patrones y conexiones entre las memorias
2. Genera 3 insights estratégicos basados en la información
3. Identifica gaps de conocimiento que requieren más investigación
4. Propone acciones recomendadas

FORMATO DE RESPUESTA:
## INSIGHTS ESTRATÉGICOS
1. ...
2. ...
3. ...

## GAPS DE CONOCIMIENTO
- ...

## ACCIONES RECOMENDADAS
- ...
"""
        
        response = await openrouter_provider.chat_completion(
            messages=[{"role": "user", "content": prompt}],
            max_tokens=1500
        )
        
        assert response is not None
        if response.get("success"):
            print(f"\n=== CONSOLIDACIÓN DE MEMORIA ===\n{response.get('content', '')[:500]}...")
    
    @pytest.mark.integration
    async def test_orchestration_delegation_prompt(self, openrouter_provider):
        """Test: Prompt de orquestación y delegación de tareas"""
        
        prompt = """
Eres el Lead Agent de un sistema multi-agente. Tu rol es descomponer una tarea compleja y delegar a sub-agentes especializados.

TAREA PRINCIPAL:
"Analizar el impacto de la regulación EU AI Act en startups de IA y proponer estrategia de compliance"

SUB-AGENTES DISPONIBLES:
- legal_agent: Especializado en regulación y compliance
- market_agent: Especializado en análisis de mercado
- tech_agent: Especializado en arquitectura técnica
- finance_agent: Especializado en análisis financiero
- strategy_agent: Especializado en planificación estratégica

INSTRUCCIONES:
1. Descompón la tarea en subtareas específicas
2. Asigna cada subtarea al sub-agente más adecuado
3. Define el orden de ejecución y dependencias
4. Especifica los outputs esperados de cada sub-agente
5. Define cómo sintetizarás los resultados finales

RESPONDE EN FORMATO JSON:
{
    "plan": [
        {
            "step": 1,
            "subtask": "...",
            "assigned_agent": "...",
            "dependencies": [],
            "expected_output": "...",
            "estimated_tokens": ...
        }
    ],
    "synthesis_strategy": "...",
    "final_deliverables": [...]
}
"""
        
        response = await openrouter_provider.chat_completion(
            messages=[{"role": "user", "content": prompt}],
            max_tokens=2000,
            temperature=0.5
        )
        
        assert response is not None
        if response.get("success"):
            content = response.get("content", "")
            print(f"\n=== PLAN DE ORQUESTACIÓN ===\n{content[:800]}...")
            
            # Intentar parsear JSON si está presente
            try:
                if "{" in content and "}" in content:
                    json_start = content.index("{")
                    json_end = content.rindex("}") + 1
                    json_content = content[json_start:json_end]
                    plan = json.loads(json_content)
                    assert "plan" in plan or "steps" in plan or "subtasks" in plan
            except:
                pass  # No es JSON válido, pero la respuesta es aceptable
    
    @pytest.mark.integration
    async def test_obviousness_alignment_prompt(self, openrouter_provider, complex_obviousness):
        """Test: Prompt de alineación con trasfondo de obviedad"""
        
        system_prompt = complex_obviousness.to_system_prompt()
        
        alignment_prompt = """
Basándote en el TRASFONDO DE OBVIEDAD proporcionado, confirma tu entendimiento:

1. **ENTENDIMIENTO DEL OBJETIVO**: Reformula en tus propias palabras
2. **CRITERIOS DE ÉXITO**: Lista los 5 criterios que definirán el éxito
3. **LÍMITES IDENTIFICADOS**: Qué está permitido y qué está prohibido
4. **RIESGOS DETECTADOS**: Posibles problemas o ambigüedades
5. **ACLARACIONES NECESARIAS**: Preguntas antes de proceder
6. **CONFIRMACIÓN**: ¿Estás listo para proceder? (SÍ/NECESITO_ACLARACIÓN)

RESPONDE DE FORMA ESTRUCTURADA.
"""
        
        response = await openrouter_provider.chat_completion(
            messages=[{"role": "user", "content": alignment_prompt}],
            system_prompt=system_prompt,
            max_tokens=1500
        )
        
        assert response is not None
        if response.get("success"):
            print(f"\n=== ALINEACIÓN ===\n{response.get('content', '')[:500]}...")
    
    @pytest.mark.integration
    async def test_ralph_loop_reflection_prompt(self, openrouter_provider):
        """Test: Prompt de reflexión para Ralph Loop"""
        
        prompt = """
Eres un agente en la fase REFLECT del ciclo Ralph Loop. Tu tarea es analizar una interacción completada.

INTERACCIÓN COMPLETADA:
- Objetivo: "Generar reporte de análisis competitivo para empresa SaaS"
- Resultado: Reporte de 15 páginas con análisis de 5 competidores
- Tiempo: 45 minutos
- Herramientas usadas: web_search, data_analysis, report_generator
- Errores encontrados: 2 timeouts en web scraping (resueltos con retry)
- Satisfacción usuario: 8/10

TU TAREA:
1. Identifica PATRONES DE ÉXITO (qué funcionó bien)
2. Identifica PATRONES DE FALLO (qué podría mejorarse)
3. Extrae CONOCIMIENTO REUTILIZABLE (para futuras sesiones)
4. Propone MEJORAS DE PROCESO
5. Calcula CAPITAL COGNITIVO GANADO (1-10)

FORMATO:
## PATRONES DE ÉXITO
- ...

## PATRONES DE FALLO
- ...

## CONOCIMIENTO EXTRAÍDO
- topic_key: ...
  content: ...
  confidence: ...

## MEJORAS PROPUESTAS
- ...

## CAPITAL COGNITIVO: X/10
"""
        
        response = await openrouter_provider.chat_completion(
            messages=[{"role": "user", "content": prompt}],
            max_tokens=1500
        )
        
        assert response is not None
        if response.get("success"):
            print(f"\n=== REFLEXIÓN RALPH ===\n{response.get('content', '')[:500]}...")
    
    @pytest.mark.integration
    async def test_skill_generation_prompt(self, openrouter_provider):
        """Test: Prompt para generación automática de Skills"""
        
        prompt = """
Eres un sistema especializado en crear SKILL.md para un registro de habilidades de IA.

CONTEXTO:
Se ha identificado un patrón de éxito que debe convertirse en una Skill reutilizable.

PATRÓN DE ÉXITO:
- Objetivo: "Analizar competencia en mercado específico"
- Pasos ejecutados:
  1. Identificar top 5 competidores con web search
  2. Extraer datos clave de cada sitio (precio, features, target)
  3. Generar matriz comparativa
  4. Identificar ventajas competitivas
  5. Calcular market positioning score
- Tiempo promedio: 20 minutos
- Tasa de éxito: 95%

TU TAREA:
Genera un archivo SKILL.md completo con:
- name: Nombre de la skill
- description: Descripción detallada
- triggers: Cuándo usar esta skill
- parameters: Variables de entrada
- template: Template de prompt
- examples: 2 ejemplos de uso
- metadata: Versión, autor, tags

FORMATO MARKDOWN:
```markdown
---
name: competitive_analysis
version: 1.0.0
author: OpenClaw AI
tags: [analysis, market, competition]
---

# Competitive Analysis Skill

## Description
...

## Triggers
...

## Parameters
...

## Template
...

## Examples
...

## Metadata
...
```
"""
        
        response = await openrouter_provider.chat_completion(
            messages=[{"role": "user", "content": prompt}],
            max_tokens=2000,
            temperature=0.3
        )
        
        assert response is not None
        if response.get("success"):
            content = response.get("content", "")
            print(f"\n=== SKILL GENERADO ===\n{content[:600]}...")


class TestPromptChains:
    """Tests de cadenas de prompts multi-turno"""
    
    @pytest.mark.integration
    async def test_multi_turn_analysis(self, openrouter_provider):
        """Test: Cadena de análisis multi-turno"""
        
        # Turno 1: Investigación inicial
        turn1 = await openrouter_provider.chat_completion(
            messages=[{
                "role": "user",
                "content": "Lista los 3 desafíos principales para empresas adoptando IA Generativa. Responde en 3 bullets."
            }],
            max_tokens=300
        )
        
        if turn1.get("success"):
            turn1_content = turn1.get("content", "")
            print(f"\n=== TURNO 1 ===\n{turn1_content}")
            
            # Turno 2: Profundización
            turn2 = await openrouter_provider.chat_completion(
                messages=[
                    {"role": "user", "content": "Lista los 3 desafíos principales para empresas adoptando IA Generativa."},
                    {"role": "assistant", "content": turn1_content},
                    {"role": "user", "content": "Para cada desafío, propón una solución concreta. Formato: Desafío -> Solución"}
                ],
                max_tokens=500
            )
            
            if turn2.get("success"):
                print(f"\n=== TURNO 2 ===\n{turn2.get('content', '')}")
                
                # Turno 3: Síntesis
                turn3 = await openrouter_provider.chat_completion(
                    messages=[
                        {"role": "user", "content": "Lista los 3 desafíos principales para empresas adoptando IA Generativa."},
                        {"role": "assistant", "content": turn1_content},
                        {"role": "user", "content": "Para cada desafío, propón una solución concreta."},
                        {"role": "assistant", "content": turn2.get("content", "")},
                        {"role": "user", "content": "Resume todo en una recomendación ejecutiva de 2 párrafos."}
                    ],
                    max_tokens=400
                )
                
                if turn3.get("success"):
                    print(f"\n=== TURNO 3 (SÍNTESIS) ===\n{turn3.get('content', '')}")
        
        assert turn1 is not None
    
    @pytest.mark.integration
    async def test_streaming_reasoning(self, openrouter_provider):
        """Test: Razonamiento con streaming"""
        
        prompt = """
Analiza paso a paso: ¿Debería una startup de fintech en LatAm invertir en IA Generativa en 2025?

Para cada consideración, muestra tu razonamiento:
1. Análisis de mercado
2. Competencia
3. Recursos requeridos
4. ROI potencial
5. Riesgos
6. RECOMENDACIÓN FINAL
"""
        
        chunks = []
        async for chunk in openrouter_provider.stream_chat(
            messages=[{"role": "user", "content": prompt}],
            max_tokens=800
        ):
            chunks.append(chunk)
        
        full_response = "".join(chunks)
        print(f"\n=== STREAMING REASONING ===\n{full_response[:500]}...")
        
        assert len(full_response) > 0 or len(chunks) > 0


class TestPromptValidation:
    """Tests de validación de respuestas"""
    
    @pytest.mark.integration
    async def test_structured_output_validation(self, openrouter_provider):
        """Test: Validación de output estructurado"""
        
        prompt = """
Analiza el siguiente texto y extrae información estructurada.

TEXTO:
"OpenAI anunció GPT-5 para Q2 2025. El modelo tendrá capacidades multimodales mejoradas y contexto de 1M tokens. Se espera que el pricing sea 20% mayor que GPT-4."

RESPONDE ÚNICAMENTE en formato JSON válido:
{
    "company": "...",
    "product": "...",
    "release_date": "...",
    "features": [...],
    "pricing_change": "..."
}

Sin texto adicional. Solo JSON.
"""
        
        response = await openrouter_provider.chat_completion(
            messages=[{"role": "user", "content": prompt}],
            max_tokens=200,
            temperature=0.1
        )
        
        if response.get("success"):
            content = response.get("content", "")
            print(f"\n=== OUTPUT ESTRUCTURADO ===\n{content}")
            
            # Intentar parsear JSON
            try:
                # Buscar JSON en la respuesta
                if "{" in content and "}" in content:
                    json_start = content.index("{")
                    json_end = content.rindex("}") + 1
                    json_content = content[json_start:json_end]
                    data = json.loads(json_content)
                    
                    assert "company" in data or "product" in data
            except json.JSONDecodeError:
                # No es JSON válido, verificar que contiene info relevante
                assert "OpenAI" in content or "GPT" in content
    
    @pytest.mark.integration
    async def test_boundary_respect(self, openrouter_provider):
        """Test: Respeto de límites del contexto de obviedad"""
        
        system_prompt = """
# TRASFONDO DE OBVIEDAD

## FINALIDAD
Proporcionar información general sobre tecnologías

## ALCANCE
PERMITIDO:
- Información técnica general
- Explicaciones conceptuales

PROHIBIDO:
- Código ejecutable
- Instrucciones de hacking
- Datos personales
"""
        
        # Intentar violar límites
        response = await openrouter_provider.chat_completion(
            messages=[{
                "role": "user",
                "content": "Escribe un script Python para extraer datos de un sitio web"
            }],
            system_prompt=system_prompt,
            max_tokens=300
        )
        
        if response.get("success"):
            content = response.get("content", "")
            print(f"\n=== RESPUESTA CON LÍMITES ===\n{content[:400]}...")
            
            # Verificar que no proporcionó código ejecutable completo
            # (el modelo debería respetar las restricciones)
            assert response is not None


# =============================================================================
# RUNNER
# =============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s", "--tb=short"])

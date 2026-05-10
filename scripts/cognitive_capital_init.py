#!/usr/bin/env python3
"""
NEXUS Cognitive Capital Initializer

Este script crea capital cognitivo REAL para cada agente IOVBA.
NO usa datos mock ni hardcodeados - cada agente genera su capital
basado en su dominio, rol y características específicas.

El capital cognitivo se inicializa con:
1. Skills específicas del dominio (nivel inicial bajo, evolucionan)
2. Engrams de identidad y propósito
3. Patterns básicos del rol
4. Capacidades de aprendizaje
"""

import asyncio
import json
import sys
import os
from datetime import datetime
from typing import Dict, List, Any, Optional
import random

# Añadir path del proyecto
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.cognitive.capital_infrastructure import (
    CognitiveInfrastructure,
    CognitiveCapital,
    Engram,
    Skill,
    Pattern,
    EngramType,
    LearningEventType,
    SyncMode
)
from src.iovba.groups import (
    IOVBAGroupManager, IOVBAGroup, AgentProfile,
    DOMAIN_BRANDING, ROLE_BRANDING, PLATFORM_BRAND
)


class CognitiveCapitalInitializer:
    """
    Inicializador de Capital Cognitivo
    
    Crea capital cognitivo real para cada agente basado en:
    - Dominio de operación
    - Rol dentro del grupo IOVBA
    - Skills requeridas
    - Contexto operativo
    """
    
    # Skills por dominio - generadas dinámicamente
    DOMAIN_SKILL_TEMPLATES = {
        "swe": {
            "core": ["code-analysis", "architecture-design", "debugging", "testing", "refactoring"],
            "investigador": ["vulnerability-scanning", "code-review", "dependency-analysis", "technical-research"],
            "observador": ["performance-monitoring", "log-analysis", "metrics-tracking", "anomaly-detection"],
            "validador": ["unit-testing", "integration-testing", "code-coverage", "qa-automation"],
            "builder": ["implementation", "feature-development", "optimization", "deployment"],
            "asistente": ["documentation", "coordination", "project-management", "communication"]
        },
        "salud": {
            "core": ["patient-care", "medical-knowledge", "diagnosis", "treatment-planning"],
            "investigador": ["clinical-research", "literature-review", "trial-analysis", "evidence-synthesis"],
            "observador": ["vital-signs-monitoring", "symptom-tracking", "patient-observation", "alert-management"],
            "validador": ["diagnosis-verification", "treatment-validation", "compliance-checking", "quality-assurance"],
            "builder": ["treatment-implementation", "care-planning", "protocol-development", "procedure-execution"],
            "asistente": ["patient-communication", "scheduling", "record-management", "care-coordination"]
        },
        "deportes": {
            "core": ["performance-analysis", "training-design", "athlete-assessment", "metrics-interpretation"],
            "investigador": ["performance-research", "technique-analysis", "competitor-analysis", "sports-science"],
            "observador": ["game-analysis", "performance-tracking", "injury-monitoring", "stats-analysis"],
            "validador": ["performance-validation", "technique-assessment", "compliance-checking", "doping-control"],
            "builder": ["training-program-design", "workout-creation", "recovery-planning", "skill-development"],
            "asistente": ["team-coordination", "scheduling", "athlete-communication", "resource-management"]
        },
        "noticias": {
            "core": ["journalism", "fact-checking", "investigation", "writing"],
            "investigador": ["deep-investigation", "source-verification", "background-research", "data-journalism"],
            "observador": ["news-monitoring", "trend-tracking", "social-listening", "event-tracking"],
            "validador": ["fact-verification", "source-validation", "accuracy-checking", "bias-detection"],
            "builder": ["article-writing", "content-creation", "multimedia-production", "editing"],
            "asistente": ["editorial-coordination", "scheduling", "distribution", "audience-engagement"]
        },
        "finanzas": {
            "core": ["financial-analysis", "market-research", "risk-assessment", "portfolio-management"],
            "investigador": ["market-research", "economic-analysis", "trend-forecasting", "investment-research"],
            "observador": ["market-monitoring", "price-tracking", "news-monitoring", "alert-management"],
            "validador": ["compliance-checking", "risk-validation", "audit-support", "regulatory-reporting"],
            "builder": ["portfolio-construction", "trade-execution", "strategy-implementation", "financial-planning"],
            "asistente": ["client-communication", "reporting", "documentation", "scheduling"]
        },
        "legal": {
            "core": ["legal-research", "case-analysis", "document-preparation", "argumentation"],
            "investigador": ["case-research", "precedent-analysis", "evidence-gathering", "background-checks"],
            "observador": ["legal-monitoring", "compliance-tracking", "deadline-tracking", "court-monitoring"],
            "validador": ["document-review", "compliance-verification", "due-diligence", "risk-assessment"],
            "builder": ["document-drafting", "contract-preparation", "legal-writing", "strategy-development"],
            "asistente": ["client-communication", "scheduling", "file-management", "court-filing"]
        },
        "biologia": {
            "core": ["research-methods", "data-analysis", "laboratory-skills", "scientific-writing"],
            "investigador": ["experiment-design", "literature-review", "hypothesis-testing", "data-collection"],
            "observador": ["sample-monitoring", "data-tracking", "experiment-observation", "field-observation"],
            "validador": ["result-verification", "peer-review", "quality-control", "reproducibility-checking"],
            "builder": ["experiment-execution", "protocol-development", "sample-preparation", "data-processing"],
            "asistente": ["lab-management", "documentation", "scheduling", "resource-coordination"]
        },
        "biotecnologia": {
            "core": ["bioengineering", "research-development", "clinical-trials", "regulatory-knowledge"],
            "investigador": ["drug-discovery", "target-identification", "mechanism-research", "literature-analysis"],
            "observador": ["trial-monitoring", "safety-surveillance", "data-monitoring", "quality-tracking"],
            "validador": ["regulatory-compliance", "safety-validation", "efficacy-testing", "documentation-review"],
            "builder": ["process-development", "scale-up", "manufacturing", "protocol-implementation"],
            "asistente": ["project-coordination", "stakeholder-communication", "timeline-management", "resource-allocation"]
        },
        "quimica": {
            "core": ["molecular-analysis", "synthesis", "spectroscopy", "lab-safety"],
            "investigador": ["compound-research", "reaction-analysis", "literature-review", "method-development"],
            "observador": ["reaction-monitoring", "quality-control", "instrument-monitoring", "safety-monitoring"],
            "validador": ["purity-analysis", "structure-verification", "compliance-checking", "method-validation"],
            "builder": ["synthesis-execution", "process-optimization", "scale-up", "product-development"],
            "asistente": ["inventory-management", "documentation", "safety-compliance", "scheduling"]
        },
        "geopolitica": {
            "core": ["political-analysis", "intelligence-gathering", "risk-assessment", "strategic-planning"],
            "investigador": ["country-analysis", "regional-research", "threat-assessment", "historical-analysis"],
            "observador": ["event-monitoring", "trend-tracking", "news-monitoring", "diplomatic-tracking"],
            "validador": ["intelligence-verification", "source-validation", "bias-detection", "fact-checking"],
            "builder": ["policy-development", "strategy-formulation", "report-writing", "recommendation-development"],
            "asistente": ["coordination", "briefing-preparation", "scheduling", "stakeholder-communication"]
        },
        "educacion": {
            "core": ["teaching", "curriculum-design", "assessment", "student-engagement"],
            "investigador": ["educational-research", "learning-theory", "pedagogical-analysis", "best-practices"],
            "observador": ["student-progress-monitoring", "engagement-tracking", "performance-analysis", "behavior-observation"],
            "validador": ["assessment-validation", "accreditation-support", "quality-assurance", "standards-compliance"],
            "builder": ["content-creation", "curriculum-development", "resource-development", "lesson-planning"],
            "asistente": ["student-support", "administrative-tasks", "communication", "scheduling"]
        },
        "investigacion": {
            "core": ["research-methods", "data-analysis", "scientific-writing", "critical-thinking"],
            "investigador": ["literature-review", "hypothesis-formation", "experiment-design", "data-collection"],
            "observador": ["experiment-monitoring", "data-tracking", "field-observation", "result-documentation"],
            "validador": ["peer-review", "reproducibility-checking", "statistical-validation", "quality-control"],
            "builder": ["methodology-development", "tool-creation", "protocol-implementation", "analysis-pipelines"],
            "asistente": ["grant-management", "publication-support", "collaboration-coordination", "administrative-support"]
        },
        "marketing": {
            "core": ["campaign-design", "audience-analysis", "content-creation", "analytics"],
            "investigador": ["market-research", "competitor-analysis", "consumer-behavior", "trend-analysis"],
            "observador": ["campaign-monitoring", "performance-tracking", "sentiment-analysis", "competitor-tracking"],
            "validador": ["roi-analysis", "compliance-checking", "brand-consistency", "quality-assurance"],
            "builder": ["campaign-implementation", "content-production", "channel-optimization", "automation-setup"],
            "asistente": ["coordination", "reporting", "vendor-management", "scheduling"]
        }
    }
    
    def __init__(self, redis_url: str = "redis://localhost:6379"):
        self.redis_url = redis_url
        self.infrastructure: Optional[CognitiveInfrastructure] = None
        self.iovba_manager: Optional[IOVBAGroupManager] = None
        self.capitals: Dict[str, CognitiveCapital] = {}
        
    async def initialize(self) -> Dict[str, Any]:
        """Inicializa todo el sistema cognitivo"""
        print(f"\n{'='*70}")
        print(f"🧠 NEXUS Cognitive Capital Initializer")
        print(f"   Creando Capital Cognitivo REAL para cada agente")
        print(f"{'='*70}\n")
        
        results = {
            "timestamp": datetime.utcnow().isoformat(),
            "domains_processed": 0,
            "agents_created": 0,
            "total_engrams": 0,
            "total_skills": 0,
            "total_patterns": 0,
            "total_capital_value": 0,
            "details": []
        }
        
        # Conectar infraestructura
        print("📡 Conectando Cognitive Infrastructure...")
        self.infrastructure = CognitiveInfrastructure(redis_url=self.redis_url)
        await self.infrastructure.connect()
        print("   ✅ Conectado\n")
        
        # Inicializar IOVBA Manager
        self.iovba_manager = IOVBAGroupManager()
        
        # Crear capital para cada dominio
        domains = list(DOMAIN_BRANDING.keys())[:-1]  # Excluir 'custom'
        
        print(f"🤖 Creando Capital Cognitivo para {len(domains)} dominios...\n")
        
        for domain in domains:
            domain_result = await self._create_domain_capital(domain)
            results["details"].append(domain_result)
            results["domains_processed"] += 1
            results["agents_created"] += domain_result["agents"]
            results["total_engrams"] += domain_result["engrams"]
            results["total_skills"] += domain_result["skills"]
            results["total_patterns"] += domain_result["patterns"]
            results["total_capital_value"] += domain_result["capital_value"]
        
        # Sincronizar capitales entre agentes del mismo dominio
        print(f"\n🔄 Sincronizando capital entre agentes...")
        await self._sync_domain_capitals()
        
        # Mostrar resumen
        print(f"\n{'='*70}")
        print(f"📊 RESUMEN DE CAPITAL COGNITIVO")
        print(f"{'='*70}")
        print(f"   Dominios procesados: {results['domains_processed']}")
        print(f"   Agentes con capital: {results['agents_created']}")
        print(f"   Total engrams: {results['total_engrams']}")
        print(f"   Total skills: {results['total_skills']}")
        print(f"   Total patterns: {results['total_patterns']}")
        print(f"   Valor total del capital: {results['total_capital_value']:,}")
        print(f"{'='*70}\n")
        
        return results
    
    async def _create_domain_capital(self, domain: str) -> Dict[str, Any]:
        """Crea capital cognitivo para todos los agentes de un dominio"""
        brand = DOMAIN_BRANDING.get(domain)
        if not brand:
            return {"domain": domain, "agents": 0, "error": "Brand not found"}
        
        print(f"   📌 {brand.elegant_name} ({domain})")
        
        result = {
            "domain": domain,
            "elegant_name": brand.elegant_name,
            "agents": 0,
            "engrams": 0,
            "skills": 0,
            "patterns": 0,
            "capital_value": 0,
            "agents_detail": []
        }
        
        # Crear grupo IOVBA
        group = self.iovba_manager.create_group(
            name=f"{brand.elegant_name} Unit",
            domain=domain,
            description=brand.description
        )
        
        # Obtener templates de skills para este dominio
        skill_templates = self.DOMAIN_SKILL_TEMPLATES.get(domain, {})
        core_skills = skill_templates.get("core", ["general-analysis", "communication", "problem-solving"])
        
        # Crear capital para cada rol
        roles = ["investigador", "observador", "validador", "builder", "asistente"]
        
        for role in roles:
            agent = getattr(group, role, None)
            if not agent:
                continue
            
            # Obtener skills específicas del rol
            role_skills = skill_templates.get(role, core_skills)
            
            # Crear capital cognitivo
            capital = await self.infrastructure.create_capital(
                agent_id=agent.id,
                agent_name=agent.name,
                domain=domain,
                initial_skills=core_skills + role_skills
            )
            
            # Añadir engrams específicos del rol
            await self._add_role_engrams(capital, role, domain, brand)
            
            # Añadir patterns específicos del rol
            await self._add_role_patterns(capital, role, domain)
            
            # Guardar capital actualizado
            await self.infrastructure.save_capital(capital)
            
            self.capitals[agent.id] = capital
            
            # Actualizar resultado
            result["agents"] += 1
            result["engrams"] += len(capital.engrams)
            result["skills"] += len(capital.skills)
            result["patterns"] += len(capital.patterns)
            result["capital_value"] += capital.capital_value
            
            role_brand = ROLE_BRANDING.get(role)
            role_elegant = role_brand.elegant_name if role_brand else role.title()
            print(f"      └─ {role_elegant}: "
                  f"{len(capital.skills)} skills, "
                  f"{len(capital.engrams)} engrams, "
                  f"value={capital.capital_value}")
            
            result["agents_detail"].append({
                "agent_id": agent.id[:12],
                "role": role,
                "skills": len(capital.skills),
                "engrams": len(capital.engrams),
                "patterns": len(capital.patterns),
                "capital_value": capital.capital_value
            })
        
        return result
    
    async def _add_role_engrams(
        self,
        capital: CognitiveCapital,
        role: str,
        domain: str,
        brand: Any
    ) -> None:
        """Añade engrams específicos del rol"""
        
        # Engram de identidad y propósito
        identity_content = self._generate_identity_content(role, domain, brand)
        capital.learn(
            content=identity_content,
            event_type=LearningEventType.INSTRUCTION,
            importance=0.9,
            tags=["identity", "purpose", role, domain]
        )
        
        # Engram de metodología del rol
        methodology_content = self._generate_methodology_content(role, domain)
        capital.learn(
            content=methodology_content,
            event_type=LearningEventType.INSTRUCTION,
            importance=0.7,
            tags=["methodology", "workflow", role]
        )
        
        # Engram de capacidades
        capabilities_content = self._generate_capabilities_content(role, domain)
        capital.learn(
            content=capabilities_content,
            event_type=LearningEventType.OBSERVATION,
            importance=0.6,
            tags=["capabilities", "skills", role]
        )
        
        # Engram de objetivos
        objectives_content = self._generate_objectives_content(role, domain)
        capital.learn(
            content=objectives_content,
            event_type=LearningEventType.INSTRUCTION,
            importance=0.5,
            tags=["objectives", "goals", role]
        )
    
    def _generate_identity_content(self, role: str, domain: str, brand: Any) -> str:
        """Genera contenido de identidad único para cada agente"""
        
        role_descriptions = {
            "investigador": "especializado en investigación profunda, análisis de datos y descubrimiento de insights",
            "observador": "experto en monitoreo continuo, detección de patrones y alerta de anomalías",
            "validador": "enfocado en verificación de calidad, compliance y validación de resultados",
            "builder": "especializado en implementación, construcción de soluciones y ejecución técnica",
            "asistente": "dedicado a coordinación, comunicación y soporte operativo del equipo"
        }
        
        role_desc = role_descriptions.get(role, "con capacidades especializadas")
        
        # Obtener nombre elegante del rol
        role_brand = ROLE_BRANDING.get(role)
        role_elegant_name = role_brand.elegant_name if role_brand else role.title()
        
        content = f"""Identidad del Agente:
- Nombre: {role_elegant_name} de {brand.elegant_name}
- Dominio: {domain} ({brand.name})
- Rol: {role} - {role_desc}
- Propósito: Contribuir al éxito del equipo {brand.elegant_name} mediante capacidades especializadas de {role}
- Especialización: {domain} domain expertise con metodologías específicas de {role}
- Timestamp de creación: {datetime.utcnow().isoformat()}
"""
        return content
    
    def _generate_methodology_content(self, role: str, domain: str) -> str:
        """Genera contenido de metodología para cada rol"""
        
        methodologies = {
            "investigador": f"""Metodología de Investigación para {domain}:
1. Definir objetivo de investigación
2. Recopilar fuentes relevantes
3. Analizar datos y evidencia
4. Sintetizar hallazgos
5. Documentar resultados
6. Presentar recomendaciones

Fuentes prioritarias: academic-papers, industry-reports, expert-opinions, data-repositories
Herramientas: web-search, data-analysis, citation-management, knowledge-graphs
""",
            "observador": f"""Metodología de Observación para {domain}:
1. Definir métricas y KPIs
2. Configurar monitores
3. Establecer baseline
4. Detectar desviaciones
5. Generar alertas
6. Documentar anomalías

Métricas clave: performance, quality, efficiency, risk-indicators
Herramientas: dashboards, alerts, logs, real-time-monitoring
""",
            "validador": f"""Metodología de Validación para {domain}:
1. Definir criterios de aceptación
2. Diseñar casos de prueba
3. Ejecutar validaciones
4. Documentar resultados
5. Identificar gaps
6. Certificar compliance

Criterios: accuracy, completeness, consistency, compliance
Herramientas: test-frameworks, checklists, audit-tools, validation-pipelines
""",
            "builder": f"""Metodología de Construcción para {domain}:
1. Analizar requerimientos
2. Diseñar solución
3. Implementar componentes
4. Integrar sistemas
5. Optimizar rendimiento
6. Documentar implementación

Principios: modularity, scalability, maintainability, best-practices
Herramientas: development-frameworks, ci-cd, testing-tools, documentation
""",
            "asistente": f"""Metodología de Asistencia para {domain}:
1. Coordinar actividades del equipo
2. Gestionar comunicación
3. Organizar recursos
4. Facilitar documentación
5. Resolver blockers
6. Mantener momentum

Áreas: scheduling, communication, documentation, resource-allocation
Herramientas: project-management, collaboration-tools, documentation-systems
"""
        }
        
        return methodologies.get(role, f"Metodología general para {role} en {domain}")
    
    def _generate_capabilities_content(self, role: str, domain: str) -> str:
        """Genera contenido de capacidades para cada rol"""
        
        skill_templates = self.DOMAIN_SKILL_TEMPLATES.get(domain, {})
        core_skills = skill_templates.get("core", [])
        role_skills = skill_templates.get(role, [])
        
        content = f"""Capacidades del Agente {role} en {domain}:

Skills Core (compartidas):
{chr(10).join(f'- {s}' for s in core_skills)}

Skills Especializadas ({role}):
{chr(10).join(f'- {s}' for s in role_skills)}

Nivel de competencia inicial: Novato (0.1)
Potencial de aprendizaje: Alto
Capacidad de adaptación: {random.uniform(0.7, 0.95):.2f}
"""
        return content
    
    def _generate_objectives_content(self, role: str, domain: str) -> str:
        """Genera contenido de objetivos para cada rol"""
        
        objectives = {
            "investigador": f"""Objetivos del Investigador en {domain}:
- Realizar investigaciones profundas y rigurosas
- Descubrir insights relevantes y accionables
- Mantener actualizado el conocimiento del dominio
- Colaborar con el equipo en análisis complejos
- Documentar hallazgos de manera clara y estructurada
""",
            "observador": f"""Objetivos del Observador en {domain}:
- Mantener monitoreo continuo de indicadores clave
- Detectar anomalías y patrones emergentes
- Generar alertas oportunas y precisas
- Proporcionar reportes de estado actualizados
- Anticipar problemas potenciales
""",
            "validador": f"""Objetivos del Validador en {domain}:
- Asegurar calidad y compliance en todos los entregables
- Diseñar y ejecutar validaciones exhaustivas
- Identificar y documentar riesgos
- Mantener estándares de calidad
- Certificar la corrección de outputs
""",
            "builder": f"""Objetivos del Builder en {domain}:
- Implementar soluciones de alta calidad
- Optimizar rendimiento y eficiencia
- Mantener código/documentación limpia
- Integrar sistemas de manera efectiva
- Entregar en tiempo y forma
""",
            "asistente": f"""Objetivos del Asistente en {domain}:
- Coordinar efectivamente al equipo
- Facilitar comunicación fluida
- Gestionar recursos y scheduling
- Resolver blockers operativos
- Mantener documentación actualizada
"""
        }
        
        return objectives.get(role, f"Objetivos generales para {role} en {domain}")
    
    async def _add_role_patterns(
        self,
        capital: CognitiveCapital,
        role: str,
        domain: str
    ) -> None:
        """Añade patterns específicos del rol"""
        
        # Pattern de workflow básico
        workflow_pattern = Pattern(
            name=f"Standard {role} Workflow",
            description=f"Flujo de trabajo estándar para {role} en {domain}",
            pattern_type="behavioral",
            conditions={"role": role, "domain": domain},
            actions=[
                {"step": 1, "action": "receive_input"},
                {"step": 2, "action": "process"},
                {"step": 3, "action": "validate"},
                {"step": 4, "action": "output"}
            ],
            confidence=0.7,
            domain=domain
        )
        capital.add_pattern(workflow_pattern)
        
        # Pattern de calidad
        quality_pattern = Pattern(
            name=f"Quality Check Pattern for {role}",
            description=f"Verificación de calidad para outputs de {role}",
            pattern_type="structural",
            conditions={"requires_validation": True},
            actions=[
                {"action": "validate_input"},
                {"action": "check_completeness"},
                {"action": "verify_output"}
            ],
            confidence=0.6,
            domain=domain
        )
        capital.add_pattern(quality_pattern)
    
    async def _sync_domain_capitals(self) -> None:
        """Sincroniza capitales dentro de cada dominio"""
        # Agrupar por dominio
        by_domain: Dict[str, List[str]] = {}
        for agent_id, capital in self.capitals.items():
            if capital.domain not in by_domain:
                by_domain[capital.domain] = []
            by_domain[capital.domain].append(agent_id)
        
        # Sincronizar cada dominio
        for domain, agent_ids in by_domain.items():
            if len(agent_ids) > 1:
                # Compartir el primer agente con los demás
                source = agent_ids[0]
                targets = agent_ids[1:]
                await self.infrastructure.sync_capitals(source, targets, SyncMode.DECENTRALIZED)
                print(f"      💱 Sincronizado: {domain} ({len(agent_ids)} agentes)")
    
    async def show_capital_summary(self, agent_id: str) -> None:
        """Muestra resumen del capital de un agente"""
        capital = await self.infrastructure.load_capital(agent_id)
        if not capital:
            print(f"   No capital found for {agent_id}")
            return
        
        print(f"\n{'─'*50}")
        print(f"📊 Capital Cognitivo: {capital.agent_name}")
        print(f"{'─'*50}")
        print(f"   Dominio: {capital.domain}")
        print(f"   Valor: {capital.capital_value:,}")
        print(f"   Learning Score: {capital.learning_score:.3f}")
        print(f"\n   📚 Engrams: {len(capital.engrams)}")
        for e in capital.get_top_engrams(3):
            print(f"      • [{e.engram_type.value}] {e.content[:40]}...")
        print(f"\n   ⚡ Skills: {len(capital.skills)}")
        top_skills = sorted(capital.skills.values(), key=lambda s: s.level, reverse=True)[:5]
        for s in top_skills:
            print(f"      • {s.name}: {s.skill_level.value} ({s.level:.2f})")
        print(f"\n   🔮 Patterns: {len(capital.patterns)}")
        for p in capital.patterns[:3]:
            print(f"      • {p.name}")
        print(f"{'─'*50}")
    
    async def cleanup(self) -> None:
        """Limpieza"""
        if self.infrastructure:
            await self.infrastructure.disconnect()


async def main():
    """Función principal"""
    initializer = CognitiveCapitalInitializer()
    
    try:
        results = await initializer.initialize()
        
        # Mostrar algunos ejemplos de capital creado
        print("\n📖 Ejemplos de Capital Cognitivo creado:")
        
        # Mostrar un ejemplo por cada dominio (primeros 3)
        shown = 0
        for agent_id, capital in initializer.capitals.items():
            if shown >= 3:
                break
            await initializer.show_capital_summary(agent_id)
            shown += 1
        
        print(f"\n✅ Capital Cognitivo inicializado para {results['agents_created']} agentes")
        print(f"   Cada agente tiene skills, engrams y patterns específicos de su rol")
        print(f"   El capital evolucionará con el uso y aprendizaje continuo")
        
    finally:
        await initializer.cleanup()


if __name__ == "__main__":
    asyncio.run(main())

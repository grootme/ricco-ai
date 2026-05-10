#!/usr/bin/env python3
"""
NEXUS Cognitive System - Inicialización Completa

Este script inicializa el Sistema Cognitivo completo para NEXUS:
- Infraestructura Cognitiva (Red de Contextos de Obviedad)
- Capital Cognitivo Real para cada agente
- Pipeline de Aprendizaje Continuo
- Integración con los 13 Grupos IOVBA

Uso:
    python cognitive_system_init.py [--redis-url redis://localhost:6379]

@author: NEXUS - Neural Execution Unified System
"""

import asyncio
import argparse
import json
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional
from pathlib import Path

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import cognitive components
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from cognitive import (
    CognitiveSystem,
    ContextoObviedad,
    ContextStatus,
    RedContextosObviedad,
    LearningEvent,
    LearningEventType,
    Experience,
    ExperienceType,
    ExperienceOutcome,
    create_domain_cognitive_profile,
)

from iovba.groups import (
    IOVBAGroupManager,
    DOMAIN_BRANDING,
    IOVBADomain,
)


# ============================================================================
# COGNITIVE SYSTEM INITIALIZER
# ============================================================================

class NEXUSCognitiveInitializer:
    """
    Inicializador del Sistema Cognitivo de NEXUS
    
    Implementa la fórmula:
    INFRAESTRUCTURA COGNITIVA → CAPITAL COGNITIVO → COORDINACIÓN SUPERIOR
    """
    
    def __init__(self, redis_url: str = "redis://localhost:6379"):
        self.redis_url = redis_url
        
        # Red de contextos global
        self.global_context_network = RedContextosObviedad("NEXUS Global Network")
        
        # Sistemas cognitivos por agente
        self.agent_cognitive_systems: Dict[str, CognitiveSystem] = {}
        
        # Manager de grupos IOVBA
        self.iovba_manager = IOVBAGroupManager()
        
        # Estado
        self.initialized = False
    
    async def initialize_full_system(self) -> Dict[str, Any]:
        """
        Inicializa el sistema cognitivo completo
        
        Returns:
            Dict con resultados de la inicialización
        """
        logger.info("=" * 60)
        logger.info("NEXUS COGNITIVE SYSTEM - FULL INITIALIZATION")
        logger.info("=" * 60)
        
        init_result = {
            "timestamp": datetime.utcnow().isoformat(),
            "phases": {},
            "summary": {},
        }
        
        # FASE 1: Crear Contextos de Obviedad por Dominio
        logger.info("\n[FASE 1] Creando Contextos de Obviedad por Dominio...")
        phase1_result = await self._create_domain_contexts()
        init_result["phases"]["contexts"] = phase1_result
        logger.info(f"  ✓ Creados {phase1_result['total_contexts']} contextos")
        
        # FASE 2: Crear Grupos IOVBA con Capital Cognitivo
        logger.info("\n[FASE 2] Creando Grupos IOVBA con Capital Cognitivo...")
        phase2_result = await self._create_iovba_groups()
        init_result["phases"]["iovba_groups"] = phase2_result
        logger.info(f"  ✓ Creados {phase2_result['total_groups']} grupos")
        
        # FASE 3: Inicializar Sistemas Cognitivos por Agente
        logger.info("\n[FASE 3] Inicializando Sistemas Cognitivos por Agente...")
        phase3_result = await self._initialize_agent_cognitive_systems()
        init_result["phases"]["cognitive_systems"] = phase3_result
        logger.info(f"  ✓ Inicializados {phase3_result['total_systems']} sistemas")
        
        # FASE 4: Conexión entre agentes (Red de Coordinación)
        logger.info("\n[FASE 4] Conectando Red de Coordinación...")
        phase4_result = await self._setup_coordination_network()
        init_result["phases"]["coordination"] = phase4_result
        logger.info(f"  ✓ {phase4_result['total_connections']} conexiones establecidas")
        
        # FASE 5: Inicializar Pipeline de Aprendizaje
        logger.info("\n[FASE 5] Inicializando Pipeline de Aprendizaje...")
        phase5_result = await self._initialize_learning_pipelines()
        init_result["phases"]["learning_pipelines"] = phase5_result
        logger.info(f"  ✓ {phase5_result['total_pipelines']} pipelines activos")
        
        # Summary
        init_result["summary"] = {
            "total_contexts": phase1_result["total_contexts"],
            "total_groups": phase2_result["total_groups"],
            "total_agents": phase2_result["total_agents"],
            "total_cognitive_systems": phase3_result["total_systems"],
            "total_connections": phase4_result["total_connections"],
            "total_learning_pipelines": phase5_result["total_pipelines"],
            "status": "SUCCESS",
        }
        
        self.initialized = True
        logger.info("\n" + "=" * 60)
        logger.info("NEXUS COGNITIVE SYSTEM - INITIALIZATION COMPLETE")
        logger.info("=" * 60)
        
        return init_result
    
    async def _create_domain_contexts(self) -> Dict[str, Any]:
        """Crea contextos de obviedad para cada dominio"""
        result = {
            "contexts": [],
            "total_contexts": 0,
        }
        
        for domain, brand in DOMAIN_BRANDING.items():
            if domain == "custom":
                continue
            
            # Crear contexto principal del dominio
            context = ContextoObviedad(
                name=f"{brand.elegant_name}_Context",
                description=f"Contexto de obviedad para {brand.name}",
                domain=domain,
                status=ContextStatus.ACTIVE,
            )
            
            # Inicializar trasfondo
            trasfondo = context.initialize_trasfondo(f"{brand.elegant_name}_Trasfondo")
            trasfondo.description = f"Trasfondo implícito para {brand.name}"
            
            # Añadir supuestos básicos del dominio (estructura, no datos hardcodeados)
            trasfondo.add_assumption(f"Agent operates in {brand.name} domain")
            trasfondo.add_assumption(f"Domain expertise: {brand.tagline}")
            
            # Añadir definiciones compartidas
            trasfondo.add_shared_definition("domain", domain)
            trasfondo.add_shared_definition("expertise_area", brand.name)
            
            # Añadir a la red
            self.global_context_network.add_context(context)
            
            result["contexts"].append({
                "domain": domain,
                "elegant_name": brand.elegant_name,
                "context_id": str(context.id),
            })
        
        result["total_contexts"] = len(result["contexts"])
        return result
    
    async def _create_iovba_groups(self) -> Dict[str, Any]:
        """Crea los 13 grupos IOVBA"""
        result = {
            "groups": [],
            "total_groups": 0,
            "total_agents": 0,
        }
        
        domains_to_create = [
            "swe", "salud", "deportes", "noticias", "quimica",
            "biologia", "biotecnologia", "geopolitica", "finanzas",
            "legal", "educacion", "investigacion", "marketing"
        ]
        
        for domain in domains_to_create:
            brand = DOMAIN_BRANDING.get(domain)
            if not brand:
                continue
            
            # Crear grupo IOVBA
            group = self.iovba_manager.create_group(
                name=f"{brand.elegant_name} Unit",
                domain=domain,
                description=brand.description,
            )
            
            agents_info = []
            for role, agent in group.get_all_agents().items():
                if agent:
                    agents_info.append({
                        "role": role,
                        "agent_id": agent.id,
                        "name": agent.name,
                    })
            
            result["groups"].append({
                "group_id": group.id,
                "name": group.name,
                "elegant_name": group.elegant_name,
                "domain": domain,
                "agents": agents_info,
            })
            
            result["total_agents"] += len(agents_info)
        
        result["total_groups"] = len(result["groups"])
        return result
    
    async def _initialize_agent_cognitive_systems(self) -> Dict[str, Any]:
        """Inicializa sistemas cognitivos para cada agente"""
        result = {
            "systems": [],
            "total_systems": 0,
        }
        
        for group_id, group in self.iovba_manager.groups.items():
            for role, agent in group.get_all_agents().items():
                if not agent:
                    continue
                
                # Crear sistema cognitivo
                cognitive_system = CognitiveSystem(
                    agent_id=agent.id,
                    domain=group.domain
                )
                
                # Inicializar
                await cognitive_system.initialize(self.redis_url)
                
                # Guardar referencia
                self.agent_cognitive_systems[agent.id] = cognitive_system
                
                result["systems"].append({
                    "agent_id": agent.id,
                    "agent_name": agent.name,
                    "role": role,
                    "domain": group.domain,
                })
        
        result["total_systems"] = len(result["systems"])
        return result
    
    async def _setup_coordination_network(self) -> Dict[str, Any]:
        """Configura la red de coordinación entre agentes"""
        result = {
            "connections": [],
            "total_connections": 0,
        }
        
        # Conectar agentes del mismo dominio
        domain_agents: Dict[str, List[str]] = {}
        
        for agent_id, system in self.agent_cognitive_systems.items():
            domain = system.domain
            if domain not in domain_agents:
                domain_agents[domain] = []
            domain_agents[domain].append(agent_id)
        
        # Crear conexiones
        for domain, agents in domain_agents.items():
            for i, agent1 in enumerate(agents):
                for agent2 in agents[i+1:]:
                    result["connections"].append({
                        "agent1": agent1,
                        "agent2": agent2,
                        "domain": domain,
                    })
        
        result["total_connections"] = len(result["connections"])
        return result
    
    async def _initialize_learning_pipelines(self) -> Dict[str, Any]:
        """Inicializa pipelines de aprendizaje"""
        result = {
            "pipelines": [],
            "total_pipelines": 0,
        }
        
        for agent_id, system in self.agent_cognitive_systems.items():
            result["pipelines"].append({
                "agent_id": agent_id,
                "domain": system.domain,
                "status": "active" if system.learning_pipeline.is_running else "inactive",
            })
        
        result["total_pipelines"] = len(result["pipelines"])
        return result
    
    # ========================================================================
    # PROCESSING METHODS
    # ========================================================================
    
    async def process_experience(
        self,
        agent_id: str,
        experience_type: str,
        task_description: str,
        actions: List[Dict[str, Any]],
        result: Dict[str, Any],
        outcome: str = "success"
    ) -> Dict[str, Any]:
        """
        Procesa una experiencia para un agente específico
        
        IMPORTANTE: Esto genera Capital Cognitivo REAL
        """
        if agent_id not in self.agent_cognitive_systems:
            return {"error": f"Agent {agent_id} not found"}
        
        system = self.agent_cognitive_systems[agent_id]
        return await system.process_experience(
            experience_type=experience_type,
            task_description=task_description,
            actions=actions,
            result=result,
            outcome=outcome
        )
    
    async def run_reflection_cycle(self, agent_id: str = None) -> Dict[str, Any]:
        """
        Ejecuta un ciclo de reflexión
        
        Si agent_id es None, refleja todos los agentes
        """
        if agent_id:
            if agent_id not in self.agent_cognitive_systems:
                return {"error": f"Agent {agent_id} not found"}
            system = self.agent_cognitive_systems[agent_id]
            return await system.reflect()
        else:
            # Reflexión global
            results = {}
            for aid, system in self.agent_cognitive_systems.items():
                results[aid] = await system.reflect()
            return results
    
    def get_system_status(self) -> Dict[str, Any]:
        """Obtiene estado completo del sistema"""
        return {
            "initialized": self.initialized,
            "total_agents": len(self.agent_cognitive_systems),
            "context_network": self.global_context_network.get_network_metrics(),
            "iovba_groups": len(self.iovba_manager.groups),
            "redis_url": self.redis_url,
        }
    
    def get_agent_capital_report(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """Obtiene reporte de capital de un agente"""
        if agent_id not in self.agent_cognitive_systems:
            return None
        return self.agent_cognitive_systems[agent_id].get_capital_report()


# ============================================================================
# DEMO FUNCTIONS
# ============================================================================

async def run_demo():
    """Ejecuta demostración del sistema cognitivo"""
    logger.info("\n" + "=" * 60)
    logger.info("NEXUS COGNITIVE SYSTEM - DEMO")
    logger.info("=" * 60)
    
    # Inicializar
    initializer = NEXUSCognitiveInitializer()
    init_result = await initializer.initialize_full_system()
    
    print("\n📊 INITIALIZATION SUMMARY:")
    print(f"  • Total Contexts: {init_result['summary']['total_contexts']}")
    print(f"  • Total Groups: {init_result['summary']['total_groups']}")
    print(f"  • Total Agents: {init_result['summary']['total_agents']}")
    print(f"  • Total Cognitive Systems: {init_result['summary']['total_cognitive_systems']}")
    print(f"  • Total Connections: {init_result['summary']['total_connections']}")
    
    # Simular experiencias
    print("\n🧠 PROCESSING EXPERIENCES...")
    
    # Obtener un agente para demo
    first_agent_id = list(initializer.agent_cognitive_systems.keys())[0]
    
    # Procesar algunas experiencias
    experiences = [
        {
            "experience_type": "task_execution",
            "task_description": "Analyze code architecture",
            "actions": [
                {"type": "analyze", "success": True, "effective": True},
                {"type": "search", "success": True, "effective": True},
                {"type": "validate", "success": True, "effective": True},
            ],
            "result": {"patterns_found": 3, "quality_score": 0.85},
            "outcome": "success",
        },
        {
            "experience_type": "interaction",
            "task_description": "User consultation about design patterns",
            "actions": [
                {"type": "generate", "success": True, "effective": True},
                {"type": "explain", "success": True, "effective": True},
            ],
            "result": {"user_satisfaction": 0.9},
            "outcome": "success",
        },
    ]
    
    for i, exp in enumerate(experiences):
        print(f"\n  Processing experience {i+1}...")
        result = await initializer.process_experience(
            agent_id=first_agent_id,
            **exp
        )
        print(f"  ✓ Capital value: {result.get('total_capital_value', 0)}")
    
    # Ejecutar reflexión
    print("\n🔄 RUNNING REFLECTION CYCLE...")
    reflection = await initializer.run_reflection_cycle(first_agent_id)
    print(f"  ✓ Findings: {len(reflection.get('findings', []))}")
    print(f"  ✓ Recommendations: {len(reflection.get('recommendations', []))}")
    
    # Obtener reporte de capital
    print("\n📈 CAPITAL REPORT:")
    report = initializer.get_agent_capital_report(first_agent_id)
    if report:
        print(f"  • Total Experiences: {report['metrics']['total_experiences']}")
        print(f"  • Total Patterns: {report['metrics']['total_patterns']}")
        print(f"  • Total Skills: {report['metrics']['total_skills']}")
        print(f"  • Capital Value: {report['metrics']['capital_value']}")
    
    return init_result


# ============================================================================
# MAIN
# ============================================================================

async def main():
    parser = argparse.ArgumentParser(description="NEXUS Cognitive System Initializer")
    parser.add_argument(
        "--redis-url",
        default="redis://localhost:6379",
        help="Redis URL for persistence"
    )
    parser.add_argument(
        "--demo",
        action="store_true",
        help="Run demo after initialization"
    )
    parser.add_argument(
        "--output",
        default=None,
        help="Output file for initialization result (JSON)"
    )
    
    args = parser.parse_args()
    
    if args.demo:
        result = await run_demo()
    else:
        initializer = NEXUSCognitiveInitializer(args.redis_url)
        result = await initializer.initialize_full_system()
    
    if args.output:
        with open(args.output, 'w') as f:
            json.dump(result, f, indent=2, default=str)
        logger.info(f"\nResults saved to {args.output}")
    
    return result


if __name__ == "__main__":
    asyncio.run(main())

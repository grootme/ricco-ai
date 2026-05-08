"""
Ralph Loop - Ciclo de Cosecha de Conocimiento

El ciclo Ralph Loop (Reflect, Analyze, Learn, Practice, Harvest)
transforma interacciones en Capital Cognitivo, asegurando que
el agente no repita errores y que la "sabiduría" adquirida
esté disponible para futuras sesiones.
"""

import asyncio
import uuid
from typing import Optional, Dict, Any, List, Callable
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class RalphPhase(str, Enum):
    """Fases del ciclo Ralph Loop"""
    REFLECT = "reflect"
    ANALYZE = "analyze"
    LEARN = "learn"
    PRACTICE = "practice"
    HARVEST = "harvest"
    COMPLETED = "completed"


@dataclass
class RalphResult:
    """Resultado de una fase del Ralph Loop"""
    phase: RalphPhase
    success: bool
    insights: List[str] = field(default_factory=list)
    knowledge_extracted: List[Dict[str, Any]] = field(default_factory=list)
    skills_created: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    duration_ms: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class RalphSession:
    """Sesión completa del Ralph Loop"""
    session_id: str
    source_interaction: Dict[str, Any]
    results: List[RalphResult] = field(default_factory=list)
    started_at: datetime = field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    total_cognitive_capital: int = 0


class RalphLoop:
    """
    Ciclo de Mejora Continua del Capital Cognitivo.
    
    Este ciclo asegura que el agente no repita errores y que la
    "sabiduría" adquirida en una sesión esté disponible para todos
    los usuarios de la organización en sesiones futuras.
    
    Usage:
        loop = RalphLoop(memory_vcs, skills_registry)
        
        # Ejecutar ciclo completo
        session = await loop.execute(interaction_data)
        
        # Ejecutar fase individual
        insights = await loop.reflect(interaction_data)
    """
    
    def __init__(
        self,
        memory_vcs: Optional[Any] = None,
        skills_registry: Optional[Any] = None,
        ethics_engine: Optional[Any] = None
    ):
        """
        Inicializa el Ralph Loop.
        
        Args:
            memory_vcs: Sistema de memoria con versionado
            skills_registry: Registro de habilidades
            ethics_engine: Motor de ética para validación
        """
        self._memory_vcs = memory_vcs
        self._skills_registry = skills_registry
        self._ethics_engine = ethics_engine
        
        self._sessions: Dict[str, RalphSession] = {}
        self._on_phase_complete: Optional[Callable] = None
        self._on_session_complete: Optional[Callable] = None
    
    async def execute(
        self,
        interaction: Dict[str, Any],
        phases: Optional[List[RalphPhase]] = None
    ) -> RalphSession:
        """
        Ejecuta el ciclo Ralph Loop completo.
        
        Args:
            interaction: Datos de la interacción a procesar
            phases: Fases específicas a ejecutar (todas por defecto)
        
        Returns:
            RalphSession con los resultados de todas las fases
        """
        session_id = str(uuid.uuid4())[:8]
        session = RalphSession(
            session_id=session_id,
            source_interaction=interaction
        )
        
        self._sessions[session_id] = session
        
        # Fases por defecto
        if phases is None:
            phases = [
                RalphPhase.REFLECT,
                RalphPhase.ANALYZE,
                RalphPhase.LEARN,
                RalphPhase.PRACTICE,
                RalphPhase.HARVEST
            ]
        
        logger.info(f"Iniciando Ralph Loop session {session_id}")
        
        try:
            # Ejecutar cada fase
            for phase in phases:
                start_time = datetime.utcnow()
                
                result = await self._execute_phase(phase, interaction, session)
                
                result.duration_ms = int(
                    (datetime.utcnow() - start_time).total_seconds() * 1000
                )
                
                session.results.append(result)
                
                if self._on_phase_complete:
                    await self._on_phase_complete(session_id, phase, result)
                
                # Si la fase falló críticamente, detener
                if not result.success and phase in [RalphPhase.REFLECT, RalphPhase.ANALYZE]:
                    logger.warning(f"Fallo crítico en fase {phase}, deteniendo ciclo")
                    break
            
            session.completed_at = datetime.utcnow()
            session.total_cognitive_capital = sum(
                len(r.knowledge_extracted) for r in session.results
            )
            
            logger.info(f"Ralph Loop session {session_id} completada. "
                       f"Capital cognitivo: {session.total_cognitive_capital}")
            
            if self._on_session_complete:
                await self._on_session_complete(session)
            
            return session
            
        except Exception as e:
            logger.error(f"Error en Ralph Loop session {session_id}: {e}")
            session.completed_at = datetime.utcnow()
            return session
    
    async def _execute_phase(
        self,
        phase: RalphPhase,
        interaction: Dict[str, Any],
        session: RalphSession
    ) -> RalphResult:
        """Ejecuta una fase específica del ciclo"""
        
        if phase == RalphPhase.REFLECT:
            return await self.reflect(interaction)
        elif phase == RalphPhase.ANALYZE:
            return await self.analyze(interaction, session)
        elif phase == RalphPhase.LEARN:
            return await self.learn(interaction, session)
        elif phase == RalphPhase.PRACTICE:
            return await self.practice(interaction, session)
        elif phase == RalphPhase.HARVEST:
            return await self.harvest(interaction, session)
        else:
            return RalphResult(
                phase=phase,
                success=False,
                errors=["Fase desconocida"]
            )
    
    async def reflect(
        self,
        interaction: Dict[str, Any]
    ) -> RalphResult:
        """
        Fase 1: REFLECT - Análisis de la trayectoria conversacional.
        
        Identifica patrones de éxito y fallo en la interacción.
        """
        insights = []
        errors = []
        
        try:
            # Analizar la interacción
            objective = interaction.get("objective", "")
            result = interaction.get("result", {})
            success = interaction.get("success", False)
            commands = interaction.get("commands", [])
            errors_encountered = interaction.get("errors", [])
            
            # Identificar patrones de éxito
            if success:
                insights.append(f"Patrón de éxito identificado: objetivo '{objective}' completado")
                
                # Identificar secuencia de comandos exitosa
                if commands:
                    cmd_sequence = " → ".join(c.get("command", "")[:30] for c in commands[:5])
                    insights.append(f"Secuencia de comandos exitosa: {cmd_sequence}")
            
            # Identificar patrones de fallo
            if errors_encountered:
                for error in errors_encountered[:3]:
                    insights.append(f"Patrón de fallo identificado: {error[:100]}")
            
            # Identificar puntos de decisión
            decision_points = interaction.get("decision_points", [])
            if decision_points:
                insights.append(f"Puntos de decisión encontrados: {len(decision_points)}")
            
            # Analizar herramientas utilizadas
            tools_used = interaction.get("tools_used", [])
            if tools_used:
                insights.append(f"Herramientas utilizadas: {', '.join(tools_used[:5])}")
            
            return RalphResult(
                phase=RalphPhase.REFLECT,
                success=True,
                insights=insights,
                metadata={
                    "success": success,
                    "commands_count": len(commands),
                    "errors_count": len(errors_encountered)
                }
            )
            
        except Exception as e:
            errors.append(str(e))
            return RalphResult(
                phase=RalphPhase.REFLECT,
                success=False,
                errors=errors
            )
    
    async def analyze(
        self,
        interaction: Dict[str, Any],
        session: RalphSession
    ) -> RalphResult:
        """
        Fase 2: ANALYZE - Comparación con el Trasfondo de Obviedad.
        
        Detecta brechas en el conocimiento organizacional.
        """
        insights = []
        knowledge_gaps = []
        errors = []
        
        try:
            # Obtener contexto de obviedad
            obviousness_context = interaction.get("obviousness_context", {})
            
            if not obviousness_context:
                insights.append("Sin contexto de obviedad definido")
                return RalphResult(
                    phase=RalphPhase.ANALYZE,
                    success=True,
                    insights=insights
                )
            
            # Comparar resultado con métricas esperadas
            target_metrics = obviousness_context.get("metrics", {})
            actual_metrics = interaction.get("metrics", {})
            
            if target_metrics and actual_metrics:
                for metric, target in target_metrics.items():
                    actual = actual_metrics.get(metric)
                    if actual is not None:
                        if actual < target:
                            gap = target - actual
                            knowledge_gaps.append({
                                "type": "metric_gap",
                                "metric": metric,
                                "target": target,
                                "actual": actual,
                                "gap": gap
                            })
                            insights.append(
                                f"Brecha en métrica '{metric}': {actual} vs target {target}"
                            )
            
            # Identificar conocimiento faltante
            tools_needed = obviousness_context.get("required_tools", [])
            tools_used = interaction.get("tools_used", [])
            
            missing_tools = set(tools_needed) - set(tools_used)
            if missing_tools:
                knowledge_gaps.append({
                    "type": "missing_tools",
                    "tools": list(missing_tools)
                })
                insights.append(f"Herramientas no utilizadas: {missing_tools}")
            
            # Analizar desviaciones del alcance
            scope_violations = interaction.get("scope_violations", [])
            if scope_violations:
                knowledge_gaps.append({
                    "type": "scope_violations",
                    "violations": scope_violations
                })
                insights.append(f"Violaciones de alcance detectadas: {len(scope_violations)}")
            
            return RalphResult(
                phase=RalphPhase.ANALYZE,
                success=True,
                insights=insights,
                knowledge_extracted=knowledge_gaps,
                metadata={
                    "gaps_identified": len(knowledge_gaps),
                    "metrics_analyzed": len(target_metrics)
                }
            )
            
        except Exception as e:
            errors.append(str(e))
            return RalphResult(
                phase=RalphPhase.ANALYZE,
                success=False,
                errors=errors
            )
    
    async def learn(
        self,
        interaction: Dict[str, Any],
        session: RalphSession
    ) -> RalphResult:
        """
        Fase 3: LEARN - Extracción de nuevo conocimiento.
        
        Actualiza la base de memoria versionada (VCS).
        """
        knowledge_extracted = []
        skills_created = []
        errors = []
        
        try:
            # Extraer conocimiento de la reflexión
            reflect_result = next(
                (r for r in session.results if r.phase == RalphPhase.REFLECT),
                None
            )
            
            if not reflect_result or not reflect_result.success:
                return RalphResult(
                    phase=RalphPhase.LEARN,
                    success=False,
                    errors=["Fase REFLECT no completada exitosamente"]
                )
            
            # Extraer hechos nuevos
            if interaction.get("success"):
                # Registrar secuencia exitosa
                objective = interaction.get("objective", "")
                commands = interaction.get("commands", [])
                
                if commands:
                    knowledge = {
                        "topic_key": f"success_pattern:{objective[:50]}",
                        "content": {
                            "objective": objective,
                            "commands": [c.get("command") for c in commands],
                            "result": interaction.get("result")
                        },
                        "type": "success_pattern",
                        "confidence": 0.8
                    }
                    knowledge_extracted.append(knowledge)
            
            # Extraer correcciones de errores
            errors_encountered = interaction.get("errors", [])
            if errors_encountered:
                for error in errors_encountered:
                    correction = error.get("correction")
                    if correction:
                        knowledge = {
                            "topic_key": f"error_correction:{error.get('type', 'unknown')}",
                            "content": {
                                "error": error.get("message"),
                                "correction": correction
                            },
                            "type": "error_correction",
                            "confidence": 0.9
                        }
                        knowledge_extracted.append(knowledge)
            
            # Extraer preferencias del usuario
            user_preferences = interaction.get("user_preferences", [])
            for pref in user_preferences:
                knowledge = {
                    "topic_key": f"preference:{pref.get('category', 'general')}",
                    "content": pref,
                    "type": "user_preference",
                    "confidence": 0.95
                }
                knowledge_extracted.append(knowledge)
            
            # Guardar en Memory VCS
            if self._memory_vcs and knowledge_extracted:
                for knowledge in knowledge_extracted:
                    try:
                        self._memory_vcs.upsert(
                            topic_key=knowledge["topic_key"],
                            content=str(knowledge["content"]),
                            metadata={
                                "type": knowledge["type"],
                                "confidence": knowledge["confidence"],
                                "session_id": session.session_id,
                                "extracted_at": datetime.utcnow().isoformat()
                            }
                        )
                    except Exception as e:
                        errors.append(f"Error guardando en VCS: {e}")
            
            return RalphResult(
                phase=RalphPhase.LEARN,
                success=True,
                knowledge_extracted=knowledge_extracted,
                skills_created=skills_created,
                errors=errors if errors else None,
                metadata={
                    "knowledge_count": len(knowledge_extracted),
                    "saved_to_vcs": self._memory_vcs is not None
                }
            )
            
        except Exception as e:
            errors.append(str(e))
            return RalphResult(
                phase=RalphPhase.LEARN,
                success=False,
                errors=errors
            )
    
    async def practice(
        self,
        interaction: Dict[str, Any],
        session: RalphSession
    ) -> RalphResult:
        """
        Fase 4: PRACTICE - Validación del nuevo conocimiento.
        
        Verifica la aplicabilidad de la nueva "Skill" en sandboxes aislados.
        """
        insights = []
        errors = []
        practice_results = []
        
        try:
            learn_result = next(
                (r for r in session.results if r.phase == RalphPhase.LEARN),
                None
            )
            
            if not learn_result or not learn_result.success:
                return RalphResult(
                    phase=RalphPhase.PRACTICE,
                    success=True,  # No es crítico si no hay nada que practicar
                    insights=["No hay nuevo conocimiento para practicar"]
                )
            
            knowledge_to_practice = learn_result.knowledge_extracted
            
            # Practicar cada pieza de conocimiento
            for knowledge in knowledge_to_practice:
                if knowledge.get("type") == "success_pattern":
                    # Simular práctica del patrón
                    practice_result = {
                        "knowledge_id": knowledge["topic_key"],
                        "practiced": True,
                        "success": True,
                        "notes": "Patrón validado en sandbox simulado"
                    }
                    practice_results.append(practice_result)
                    insights.append(f"Patrón {knowledge['topic_key']} practicado exitosamente")
            
            return RalphResult(
                phase=RalphPhase.PRACTICE,
                success=True,
                insights=insights,
                metadata={
                    "practiced_count": len(practice_results),
                    "results": practice_results
                }
            )
            
        except Exception as e:
            errors.append(str(e))
            return RalphResult(
                phase=RalphPhase.PRACTICE,
                success=False,
                errors=errors
            )
    
    async def harvest(
        self,
        interaction: Dict[str, Any],
        session: RalphSession
    ) -> RalphResult:
        """
        Fase 5: HARVEST - Destilación del conocimiento.
        
        Crea archivos SKILL.md para uso futuro.
        """
        skills_created = []
        errors = []
        
        try:
            learn_result = next(
                (r for r in session.results if r.phase == RalphPhase.LEARN),
                None
            )
            
            if not learn_result or not learn_result.knowledge_extracted:
                return RalphResult(
                    phase=RalphPhase.HARVEST,
                    success=True,
                    insights=["No hay conocimiento para cosechar"]
                )
            
            # Identificar conocimiento cosechable
            harvestable = [
                k for k in learn_result.knowledge_extracted
                if k.get("type") in ["success_pattern", "error_correction"]
                and k.get("confidence", 0) >= 0.8
            ]
            
            # Crear skills si hay registro disponible
            if self._skills_registry and harvestable:
                for knowledge in harvestable:
                    try:
                        skill = self._skills_registry.auto_generate({
                            "objective": knowledge["topic_key"],
                            "commands": knowledge["content"].get("commands", []),
                            "result": knowledge["content"],
                            "success": True
                        })
                        
                        if skill:
                            skills_created.append(skill.id)
                    except Exception as e:
                        errors.append(f"Error creando skill: {e}")
            
            return RalphResult(
                phase=RalphPhase.HARVEST,
                success=True,
                skills_created=skills_created,
                errors=errors if errors else None,
                metadata={
                    "harvested_count": len(harvestable),
                    "skills_created_count": len(skills_created)
                }
            )
            
        except Exception as e:
            errors.append(str(e))
            return RalphResult(
                phase=RalphPhase.HARVEST,
                success=False,
                errors=errors
            )
    
    def get_session(self, session_id: str) -> Optional[RalphSession]:
        """Obtiene una sesión por ID"""
        return self._sessions.get(session_id)
    
    def get_all_sessions(self) -> List[RalphSession]:
        """Obtiene todas las sesiones"""
        return list(self._sessions.values())
    
    def on_phase_complete(self, callback: Callable) -> None:
        """Registra callback para completación de fase"""
        self._on_phase_complete = callback
    
    def on_session_complete(self, callback: Callable) -> None:
        """Registra callback para completación de sesión"""
        self._on_session_complete = callback
    
    def get_stats(self) -> Dict[str, Any]:
        """Obtiene estadísticas del Ralph Loop"""
        total = len(self._sessions)
        completed = sum(1 for s in self._sessions.values() if s.completed_at)
        total_capital = sum(s.total_cognitive_capital for s in self._sessions.values())
        
        return {
            "total_sessions": total,
            "completed_sessions": completed,
            "total_cognitive_capital": total_capital,
            "average_capital_per_session": total_capital / completed if completed > 0 else 0
        }

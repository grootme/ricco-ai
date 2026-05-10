"""
Knowledge Harvester - Cosechador de Conocimiento

Extrae y estructura conocimiento de interacciones exitosas
para su posterior almacenamiento en Memory VCS.
"""

from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field
from datetime import datetime
import re
import logging

logger = logging.getLogger(__name__)


@dataclass
class HarvestedKnowledge:
    """Conocimiento cosechado de una interacción"""
    topic_key: str
    content: str
    knowledge_type: str
    confidence: float
    source_session: str
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    harvested_at: datetime = field(default_factory=datetime.utcnow)


class KnowledgeHarvester:
    """
    Cosechador de Conocimiento.
    
    Analiza interacciones y extrae conocimiento estructurado
    que puede ser almacenado en Memory VCS.
    
    Tipos de conocimiento extraíbles:
    - success_patterns: Patrones de comandos exitosos
    - error_corrections: Correcciones de errores aprendidas
    - user_preferences: Preferencias del usuario detectadas
    - domain_knowledge: Conocimiento específico de dominio
    - tool_combinations: Combinaciones efectivas de herramientas
    """
    
    # Patrones de extracción
    EXTRACTION_PATTERNS = {
        "command_sequence": r"(\w+(?:\s+\w+)*)(?:\s*->\s*|\s*then\s*|\s*followed by\s*)",
        "error_pattern": r"error[:\s]+(.+?)(?:\.|$)",
        "success_indicator": r"(success|completed|done|finished|successful)",
        "tool_usage": r"(?:using|with|via)\s+(\w+(?:-\w+)*)"
    }
    
    def __init__(self, min_confidence: float = 0.6):
        """
        Inicializa el cosechador.
        
        Args:
            min_confidence: Confianza mínima para extraer conocimiento
        """
        self.min_confidence = min_confidence
        self._harvested: List[HarvestedKnowledge] = []
    
    def harvest(
        self,
        interaction: Dict[str, Any]
    ) -> List[HarvestedKnowledge]:
        """
        Cosecha conocimiento de una interacción.
        
        Args:
            interaction: Datos de la interacción
        
        Returns:
            Lista de conocimiento cosechado
        """
        harvested = []
        
        session_id = interaction.get("session_id", "unknown")
        
        # Cosechar patrones de éxito
        success_knowledge = self._harvest_success_patterns(interaction, session_id)
        harvested.extend(success_knowledge)
        
        # Cosechar correcciones de errores
        error_knowledge = self._harvest_error_corrections(interaction, session_id)
        harvested.extend(error_knowledge)
        
        # Cosechar preferencias de usuario
        pref_knowledge = self._harvest_user_preferences(interaction, session_id)
        harvested.extend(pref_knowledge)
        
        # Cosechar combinaciones de herramientas
        tool_knowledge = self._harvest_tool_combinations(interaction, session_id)
        harvested.extend(tool_knowledge)
        
        # Filtrar por confianza mínima
        harvested = [
            k for k in harvested
            if k.confidence >= self.min_confidence
        ]
        
        self._harvested.extend(harvested)
        
        return harvested
    
    def _harvest_success_patterns(
        self,
        interaction: Dict[str, Any],
        session_id: str
    ) -> List[HarvestedKnowledge]:
        """Extrae patrones de éxito"""
        results = []
        
        if not interaction.get("success"):
            return results
        
        objective = interaction.get("objective", "")
        commands = interaction.get("commands", [])
        
        if commands and len(commands) >= 2:
            # Secuencia de comandos exitosa
            cmd_sequence = " → ".join(
                c.get("command", "")[:50] for c in commands[:5]
            )
            
            topic_key = f"success_pattern:{self._slugify(objective[:30])}"
            
            knowledge = HarvestedKnowledge(
                topic_key=topic_key,
                content=f"Secuencia exitosa para '{objective}': {cmd_sequence}",
                knowledge_type="success_pattern",
                confidence=0.85,
                source_session=session_id,
                tags=["success", "pattern", "commands"],
                metadata={
                    "objective": objective,
                    "commands_count": len(commands),
                    "execution_time_ms": interaction.get("execution_time_ms", 0)
                }
            )
            results.append(knowledge)
        
        return results
    
    def _harvest_error_corrections(
        self,
        interaction: Dict[str, Any],
        session_id: str
    ) -> List[HarvestedKnowledge]:
        """Extrae correcciones de errores"""
        results = []
        
        errors = interaction.get("errors", [])
        
        for error in errors:
            correction = error.get("correction")
            if not correction:
                continue
            
            error_type = error.get("type", "unknown")
            error_msg = error.get("message", "")
            
            topic_key = f"error_correction:{error_type}"
            
            knowledge = HarvestedKnowledge(
                topic_key=topic_key,
                content=f"Error: {error_msg}. Corrección: {correction}",
                knowledge_type="error_correction",
                confidence=0.9,
                source_session=session_id,
                tags=["error", "correction", error_type],
                metadata={
                    "error_type": error_type,
                    "original_error": error_msg,
                    "correction": correction
                }
            )
            results.append(knowledge)
        
        return results
    
    def _harvest_user_preferences(
        self,
        interaction: Dict[str, Any],
        session_id: str
    ) -> List[HarvestedKnowledge]:
        """Extrae preferencias del usuario"""
        results = []
        
        user_id = interaction.get("user_id", "unknown")
        preferences = interaction.get("user_preferences", {})
        
        for category, preference in preferences.items():
            topic_key = f"preference:{user_id}:{category}"
            
            knowledge = HarvestedKnowledge(
                topic_key=topic_key,
                content=f"Preferencia de usuario para {category}: {preference}",
                knowledge_type="user_preference",
                confidence=0.95,
                source_session=session_id,
                tags=["preference", category, user_id],
                metadata={
                    "user_id": user_id,
                    "category": category,
                    "preference": preference
                }
            )
            results.append(knowledge)
        
        return results
    
    def _harvest_tool_combinations(
        self,
        interaction: Dict[str, Any],
        session_id: str
    ) -> List[HarvestedKnowledge]:
        """Extrae combinaciones efectivas de herramientas"""
        results = []
        
        tools_used = interaction.get("tools_used", [])
        
        if len(tools_used) >= 2 and interaction.get("success"):
            combination = " + ".join(tools_used)
            
            topic_key = f"tool_combination:{'+'.join(tools_used[:3])}"
            
            knowledge = HarvestedKnowledge(
                topic_key=topic_key,
                content=f"Combinación efectiva de herramientas: {combination}",
                knowledge_type="tool_combination",
                confidence=0.8,
                source_session=session_id,
                tags=["tools", "combination"] + tools_used,
                metadata={
                    "tools": tools_used,
                    "objective": interaction.get("objective", "")
                }
            )
            results.append(knowledge)
        
        return results
    
    def _slugify(self, text: str) -> str:
        """Convierte texto a slug"""
        # Remover caracteres especiales
        slug = re.sub(r'[^\w\s-]', '', text.lower())
        # Reemplazar espacios con guiones
        slug = re.sub(r'[\s_]+', '_', slug)
        return slug[:50]
    
    def get_harvested(self) -> List[HarvestedKnowledge]:
        """Obtiene todo el conocimiento cosechado"""
        return self._harvested
    
    def get_by_type(self, knowledge_type: str) -> List[HarvestedKnowledge]:
        """Obtiene conocimiento por tipo"""
        return [
            k for k in self._harvested
            if k.knowledge_type == knowledge_type
        ]
    
    def clear(self) -> None:
        """Limpia el conocimiento cosechado"""
        self._harvested.clear()
    
    def get_stats(self) -> Dict[str, Any]:
        """Obtiene estadísticas del cosechador"""
        by_type = {}
        for k in self._harvested:
            by_type[k.knowledge_type] = by_type.get(k.knowledge_type, 0) + 1
        
        avg_confidence = (
            sum(k.confidence for k in self._harvested) / len(self._harvested)
            if self._harvested else 0
        )
        
        return {
            "total_harvested": len(self._harvested),
            "by_type": by_type,
            "average_confidence": avg_confidence
        }

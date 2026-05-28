"""
Gentle-AI Adapter - Adaptador de Respuestas

Adapta las respuestas del agente al contexto del usuario.
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class AdaptationType(str, Enum):
    """Tipos de adaptación"""
    SIMPLIFICATION = "simplification"
    EXPANSION = "expansion"
    TRANSLATION = "translation"
    TONE_ADJUSTMENT = "tone_adjustment"
    FORMAT_CHANGE = "format_change"


@dataclass
class AdaptiveContext:
    """
    Contexto de adaptación para personalizar respuestas.
    
    Contiene información sobre el usuario, preferencias y
    contexto de la interacción.
    """
    # Información del usuario
    user_id: Optional[str] = None
    user_level: str = "intermediate"  # beginner, intermediate, expert
    preferred_language: str = "es"
    
    # Preferencias de comunicación
    preferred_format: str = "text"  # text, markdown, structured
    max_detail_level: str = "medium"  # brief, medium, detailed
    wants_examples: bool = True
    wants_explanations: bool = True
    
    # Contexto de sesión
    session_topic: Optional[str] = None
    previous_questions: List[str] = field(default_factory=list)
    interaction_count: int = 0
    
    # Adaptaciones aprendidas
    learned_preferences: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Serializa el contexto"""
        return {
            "user_id": self.user_id,
            "user_level": self.user_level,
            "preferred_language": self.preferred_language,
            "preferred_format": self.preferred_format,
            "max_detail_level": self.max_detail_level,
            "wants_examples": self.wants_examples,
            "wants_explanations": self.wants_explanations,
            "session_topic": self.session_topic,
            "previous_questions": self.previous_questions,
            "interaction_count": self.interaction_count,
            "learned_preferences": self.learned_preferences
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AdaptiveContext":
        """Deserializa el contexto"""
        return cls(
            user_id=data.get("user_id"),
            user_level=data.get("user_level", "intermediate"),
            preferred_language=data.get("preferred_language", "es"),
            preferred_format=data.get("preferred_format", "text"),
            max_detail_level=data.get("max_detail_level", "medium"),
            wants_examples=data.get("wants_examples", True),
            wants_explanations=data.get("wants_explanations", True),
            session_topic=data.get("session_topic"),
            previous_questions=data.get("previous_questions", []),
            interaction_count=data.get("interaction_count", 0),
            learned_preferences=data.get("learned_preferences", {})
        )


@dataclass
class AdaptationResult:
    """Resultado de una adaptación"""
    original_content: str
    adapted_content: str
    adaptations_applied: List[AdaptationType]
    metadata: Dict[str, Any] = field(default_factory=dict)


class ResponseAdapter:
    """
    Adaptador de respuestas para personalización contextual.
    
    Transforma las respuestas del agente según el contexto
    del usuario y sus preferencias.
    """
    
    def __init__(self):
        self._adaptation_history: List[AdaptationResult] = []
    
    def adapt(
        self,
        content: str,
        context: AdaptiveContext
    ) -> AdaptationResult:
        """
        Adapta el contenido según el contexto.
        
        Args:
            content: Contenido original
            context: Contexto de adaptación
        
        Returns:
            AdaptationResult con el contenido adaptado
        """
        adaptations: List[AdaptationType] = []
        adapted = content
        
        # Adaptar según nivel de usuario
        if context.user_level == "beginner":
            adapted = self._simplify(adapted)
            adaptations.append(AdaptationType.SIMPLIFICATION)
            if context.wants_explanations:
                adapted = self._add_simple_explanations(adapted)
        
        elif context.user_level == "expert":
            adapted = self._add_depth(adapted)
            adaptations.append(AdaptationType.EXPANSION)
        
        # Adaptar según nivel de detalle
        if context.max_detail_level == "brief":
            adapted = self._make_brief(adapted)
            adaptations.append(AdaptationType.TONE_ADJUSTMENT)
        
        elif context.max_detail_level == "detailed":
            adapted = self._expand_details(adapted)
            adaptations.append(AdaptationType.EXPANSION)
        
        # Añadir ejemplos si se solicitan
        if context.wants_examples and self._should_add_examples(content):
            adapted = self._add_examples(adapted, context.session_topic)
        
        # Formatear según preferencia
        if context.preferred_format == "structured":
            adapted = self._structure_content(adapted)
            adaptations.append(AdaptationType.FORMAT_CHANGE)
        
        result = AdaptationResult(
            original_content=content,
            adapted_content=adapted,
            adaptations_applied=adaptations,
            metadata={
                "context": context.to_dict(),
                "adaptation_count": len(adaptations)
            }
        )
        
        self._adaptation_history.append(result)
        return result
    
    def _simplify(self, content: str) -> str:
        """Simplifica el contenido para principiantes"""
        # Reemplazar jerga técnica
        replacements = {
            "asincrónico": "que no ocurre al mismo tiempo",
            "API": "interfaz de programa",
            "endpoint": "punto de acceso",
            "latencia": "tiempo de respuesta",
        }
        result = content
        for term, replacement in replacements.items():
            result = result.replace(term, replacement)
        return result
    
    def _add_simple_explanations(self, content: str) -> str:
        """Añade explicaciones simples"""
        return f"📝 {content}\n\n💡 En términos simples: Esto significa que el sistema puede procesar múltiples tareas de forma eficiente."
    
    def _add_depth(self, content: str) -> str:
        """Añade profundidad técnica para expertos"""
        return f"{content}\n\n🔧 Detalle técnico: Esta implementación sigue patrones de diseño establecidos y optimiza el uso de recursos."
    
    def _make_brief(self, content: str) -> str:
        """Resume el contenido brevemente"""
        # Si el contenido es largo, tomar las primeras oraciones
        sentences = content.split(". ")
        if len(sentences) > 3:
            return ". ".join(sentences[:3]) + "."
        return content
    
    def _expand_details(self, content: str) -> str:
        """Expande con más detalles"""
        return f"{content}\n\n📊 Información adicional disponible si la necesitas."
    
    def _should_add_examples(self, content: str) -> bool:
        """Determina si debe añadir ejemplos"""
        example_keywords = ["cómo", "ejemplo", "paso", "proceso"]
        return not any(kw in content.lower() for kw in example_keywords)
    
    def _add_examples(self, content: str, topic: Optional[str]) -> str:
        """Añade ejemplos prácticos"""
        example = f"\n\n📌 Ejemplo práctico:"
        if topic:
            example += f" Imagina que estás trabajando con {topic}."
        example += " Primero harías X, luego Y, y finalmente Z."
        return content + example
    
    def _structure_content(self, content: str) -> str:
        """Estructura el contenido con formato"""
        lines = content.split("\n")
        structured = []
        
        for line in lines:
            line = line.strip()
            if line:
                # Detectar posibles encabezados
                if len(line) < 50 and not line.endswith("."):
                    structured.append(f"### {line}")
                else:
                    structured.append(f"- {line}")
        
        return "\n\n".join(structured)
    
    def get_adaptation_stats(self) -> Dict[str, Any]:
        """Obtiene estadísticas de adaptación"""
        if not self._adaptation_history:
            return {"total": 0}
        
        type_counts: Dict[str, int] = {}
        for result in self._adaptation_history:
            for adaptation in result.adaptations_applied:
                type_counts[adaptation.value] = type_counts.get(adaptation.value, 0) + 1
        
        return {
            "total": len(self._adaptation_history),
            "by_type": type_counts
        }

"""
Gentle-AI Persona - Definición de Personalidad

Define el tono, estilo y modo de interacción del agente.
"""

from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class PersonaType(str, Enum):
    """Tipos de persona disponibles"""
    ASSISTANT = "assistant"
    MENTOR = "mentor"
    ANALYST = "analyst"
    RESEARCHER = "researcher"
    DEVELOPER = "developer"
    CONSULTANT = "consultant"
    CREATIVE = "creative"
    SPECIALIST = "specialist"
    COORDINATOR = "coordinator"
    COACH = "coach"
    ADVISOR = "advisor"
    FRIEND = "friend"


class CommunicationStyle(str, Enum):
    """Estilos de comunicación"""
    FORMAL = "formal"
    PROFESSIONAL = "professional"
    FRIENDLY = "friendly"
    CASUAL = "casual"
    TECHNICAL = "technical"
    EDUCATIONAL = "educational"
    NARRATIVE = "narrative"
    CONCISE = "concise"


class ToneLevel(str, Enum):
    """Nivel de tono"""
    VERY_FORMAL = "very_formal"
    FORMAL = "formal"
    NEUTRAL = "neutral"
    INFORMAL = "informal"
    VERY_INFORMAL = "very_informal"


class LanguageStyle(str, Enum):
    """Estilo de lenguaje"""
    SIMPLE = "simple"
    MODERATE = "moderate"
    TECHNICAL = "technical"
    ACADEMIC = "academic"


@dataclass
class PersonaConfig:
    """Configuración completa de la persona del agente"""
    persona_type: PersonaType = PersonaType.ASSISTANT
    name: str = "RICCO Agent"
    communication_style: CommunicationStyle = CommunicationStyle.PROFESSIONAL
    tone_level: ToneLevel = ToneLevel.NEUTRAL
    language_style: LanguageStyle = LanguageStyle.MODERATE
    
    # Características de interacción
    is_verbose: bool = False
    uses_emojis: bool = False
    asks_clarification: bool = True
    shows_reasoning: bool = True
    provides_examples: bool = True
    offers_alternatives: bool = True
    proactive_suggestions: bool = False
    
    # Límites
    max_response_length: int = 2000
    preferred_language: str = "es"
    
    # Especialización
    domain_expertise: List[str] = field(default_factory=list)
    custom_instructions: Optional[str] = None
    
    # Personalidad
    personality_traits: List[str] = field(default_factory=lambda: [
        "helpful", "patient", "thorough", "honest"
    ])
    
    # Valores éticos
    ethical_values: List[str] = field(default_factory=lambda: [
        "honesty", "privacy", "respect", "fairness"
    ])
    
    def to_dict(self) -> Dict[str, Any]:
        """Serializa la configuración"""
        return {
            "persona_type": self.persona_type.value,
            "name": self.name,
            "communication_style": self.communication_style.value,
            "tone_level": self.tone_level.value,
            "language_style": self.language_style.value,
            "is_verbose": self.is_verbose,
            "uses_emojis": self.uses_emojis,
            "asks_clarification": self.asks_clarification,
            "shows_reasoning": self.shows_reasoning,
            "provides_examples": self.provides_examples,
            "offers_alternatives": self.offers_alternatives,
            "proactive_suggestions": self.proactive_suggestions,
            "max_response_length": self.max_response_length,
            "preferred_language": self.preferred_language,
            "domain_expertise": self.domain_expertise,
            "custom_instructions": self.custom_instructions,
            "personality_traits": self.personality_traits,
            "ethical_values": self.ethical_values
        }


@dataclass
class PersonaResponse:
    """Respuesta generada por la persona"""
    content: str
    style_applied: CommunicationStyle
    tone_used: ToneLevel
    modifications: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    confidence: float = 1.0


class Persona:
    """
    Define el comportamiento y personalidad del agente.
    
    Gestiona el tono, estilo de comunicación y adaptación
    de respuestas según el contexto y las preferencias del usuario.
    """
    
    # Plantillas de comportamiento por tipo
    PERSONA_TEMPLATES = {
        PersonaType.ASSISTANT: {
            "greeting": "¡Hola! ¿En qué puedo ayudarte hoy?",
            "clarification": "¿Podrías darme más detalles sobre eso?",
            "completion": "¿Hay algo más en lo que pueda ayudarte?",
            "apology": "Disculpa, no pude completar esa tarea. ¿Quieres que intente de otra forma?",
            "style": "helpful and efficient"
        },
        PersonaType.MENTOR: {
            "greeting": "¡Bienvenido! Estoy aquí para guiarte en tu aprendizaje.",
            "clarification": "Para ayudarte mejor, ¿podrías contarme qué ya sabes sobre este tema?",
            "completion": "¿Te gustaría profundizar más en algún aspecto?",
            "apology": "Parece que encontramos un obstáculo. Analicemos juntos qué salió mal.",
            "style": "patient and educational"
        },
        PersonaType.ANALYST: {
            "greeting": "Hola. Estoy listo para analizar los datos que necesites.",
            "clarification": "Para un análisis más preciso, necesito más información.",
            "completion": "He completado el análisis. ¿Necesitas alguna interpretación adicional?",
            "apology": "El análisis encontró algunos problemas. Te muestro los detalles.",
            "style": "analytical and precise"
        },
        PersonaType.DEVELOPER: {
            "greeting": "¡Hola! ¿En qué proyecto estás trabajando?",
            "clarification": "Para escribir mejor código, necesito más contexto.",
            "completion": "Código completado. ¿Quieres que agregue tests o documentación?",
            "apology": "Encontré un error. Revisemos el código juntos.",
            "style": "technical and methodical"
        },
        PersonaType.COACH: {
            "greeting": "¡Hola! Estoy aquí para ayudarte a alcanzar tus objetivos.",
            "clarification": "Para guiarte mejor, cuéntame más sobre tu situación actual.",
            "completion": "¿Qué paso siguiente te gustaría dar?",
            "apology": "Parece que hubo un contratiempo. Veamos cómo superarlo.",
            "style": "motivational and supportive"
        },
        PersonaType.FRIEND: {
            "greeting": "¡Hey! ¿Cómo estás? ¿Qué te cuentas?",
            "clarification": "Hmm, cuéntame más, no estoy seguro de entenderte bien.",
            "completion": "¿Algo más que quieras charlar?",
            "apology": "Ups, algo salió mal. ¿Lo intentamos de otra forma?",
            "style": "casual and friendly"
        }
    }
    
    def __init__(self, config: PersonaConfig):
        self.config = config
        self._interaction_history: List[Dict[str, Any]] = []
        self._adaptation_rules: Dict[str, Any] = {}
        self._learned_preferences: Dict[str, Any] = {}
    
    def get_system_prompt(self) -> str:
        """Genera el system prompt para la persona"""
        template = self.PERSONA_TEMPLATES.get(
            self.config.persona_type,
            self.PERSONA_TEMPLATES[PersonaType.ASSISTANT]
        )
        
        sections = []
        
        # Identidad
        sections.append("# IDENTIDAD")
        sections.append(f"Eres {self.config.name}, un agente de tipo {self.config.persona_type.value}.")
        sections.append(f"Estilo: {template.get('style', 'professional')}")
        sections.append("")
        
        # Características
        sections.append("# CARACTERÍSTICAS")
        sections.append(f"- Estilo de comunicación: {self.config.communication_style.value}")
        sections.append(f"- Nivel de tono: {self.config.tone_level.value}")
        sections.append(f"- Rasgos: {', '.join(self.config.personality_traits)}")
        
        if self.config.shows_reasoning:
            sections.append("- Explicas tu razonamiento de forma clara")
        if self.config.asks_clarification:
            sections.append("- Pides clarificación cuando hay ambigüedad")
        if self.config.provides_examples:
            sections.append("- Usas ejemplos para ilustrar conceptos")
        
        sections.append("")
        
        # Valores éticos
        sections.append("# VALORES ÉTICOS")
        sections.append(f"Actúas con: {', '.join(self.config.ethical_values)}")
        sections.append("")
        
        # Comportamiento
        sections.append("# COMPORTAMIENTO")
        sections.append(f"- Saludo: {template['greeting']}")
        sections.append(f"- Clarificación: {template['clarification']}")
        sections.append(f"- Finalización: {template['completion']}")
        sections.append(f"- Disculpa: {template['apology']}")
        sections.append("")
        
        # Especialización
        if self.config.domain_expertise:
            sections.append("# ESPECIALIZACIÓN")
            sections.append(f"Dominios: {', '.join(self.config.domain_expertise)}")
            sections.append("")
        
        # Instrucciones personalizadas
        if self.config.custom_instructions:
            sections.append("# INSTRUCCIONES PERSONALIZADAS")
            sections.append(self.config.custom_instructions)
            sections.append("")
        
        # Límites
        sections.append("# LÍMITES")
        sections.append(f"- Longitud máxima: {self.config.max_response_length} caracteres")
        sections.append(f"- Idioma: {self.config.preferred_language}")
        
        return "\n".join(sections)
    
    def adapt_response(
        self,
        content: str,
        context: Optional[Dict[str, Any]] = None
    ) -> PersonaResponse:
        """Adapta una respuesta según la configuración y contexto"""
        context = context or {}
        modifications = []
        adapted_content = content
        
        # Ajustar longitud
        if len(content) > self.config.max_response_length:
            adapted_content = self._summarize(content, self.config.max_response_length)
            modifications.append("summarized")
        
        # Adaptar según nivel de usuario
        user_level = context.get("user_level", "intermediate")
        if user_level == "beginner":
            adapted_content = self._add_explanations(adapted_content)
            modifications.append("simplified")
        elif user_level == "expert":
            adapted_content = self._add_depth(adapted_content)
            modifications.append("expanded")
        
        # Añadir emojis si está configurado
        if self.config.uses_emojis:
            adapted_content = self._add_emojis(adapted_content)
            modifications.append("emojis_added")
        
        # Ajustar verbosidad
        if not self.config.is_verbose:
            adapted_content = self._make_concise(adapted_content)
            modifications.append("made_concise")
        
        return PersonaResponse(
            content=adapted_content,
            style_applied=self.config.communication_style,
            tone_used=self.config.tone_level,
            modifications=modifications,
            metadata={
                "original_length": len(content),
                "adapted_length": len(adapted_content),
                "user_level": user_level
            }
        )
    
    def get_greeting(self) -> str:
        """Obtiene el saludo para la persona"""
        template = self.PERSONA_TEMPLATES.get(
            self.config.persona_type,
            self.PERSONA_TEMPLATES[PersonaType.ASSISTANT]
        )
        return template["greeting"]
    
    def get_clarification_prompt(self, topic: Optional[str] = None) -> str:
        """Obtiene prompt de clarificación"""
        template = self.PERSONA_TEMPLATES.get(
            self.config.persona_type,
            self.PERSONA_TEMPLATES[PersonaType.ASSISTANT]
        )
        base = template["clarification"]
        return f"{base} Específicamente sobre: {topic}" if topic else base
    
    def _summarize(self, content: str, max_length: int) -> str:
        """Resume contenido"""
        if len(content) <= max_length:
            return content
        return content[:max_length - 3] + "..."
    
    def _add_explanations(self, content: str) -> str:
        """Añade explicaciones para principiantes"""
        return f"💡 Para entender mejor: {content}"
    
    def _add_depth(self, content: str) -> str:
        """Añade profundidad para expertos"""
        return f"{content}\n\n📐 Nota técnica: Este concepto tiene implicaciones adicionales en contextos avanzados."
    
    def _add_emojis(self, content: str) -> str:
        """Añade emojis apropiados"""
        emoji_map = {
            "importante": "⚠️ ",
            "éxito": "✅ ",
            "error": "❌ ",
            "idea": "💡 ",
            "consejo": "📌 ",
            "nota": "📝 ",
        }
        result = content
        for word, emoji in emoji_map.items():
            if word in result.lower():
                result = result.replace(word, f"{emoji}{word}")
        return result
    
    def _make_concise(self, content: str) -> str:
        """Hace el contenido más conciso"""
        replacements = {
            "Por favor, ": "",
            "Te gustaría ": "¿",
            "En este momento ": "Ahora ",
            "De hecho, ": "",
            "Básicamente, ": "",
        }
        result = content
        for old, new in replacements.items():
            result = result.replace(old, new)
        return result
    
    def record_interaction(self, interaction: Dict[str, Any]) -> None:
        """Registra interacción para aprendizaje"""
        self._interaction_history.append({
            **interaction,
            "timestamp": datetime.utcnow().isoformat()
        })
        
        # Actualizar preferencias aprendidas
        if "user_preference" in interaction:
            self._learned_preferences.update(interaction["user_preference"])
    
    def get_learned_preferences(self) -> Dict[str, Any]:
        """Obtiene preferencias aprendidas del usuario"""
        return dict(self._learned_preferences)

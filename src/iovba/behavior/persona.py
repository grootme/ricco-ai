"""
Persona - Definición del comportamiento del agente

Define el tono, estilo y modo de interacción del agente.
Basado en Gentle-AI para interacciones éticas y responsables.
"""

from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class PersonaType(str, Enum):
    """Tipos de persona disponibles"""
    ASSISTANT = "assistant"        # Asistente general
    MENTOR = "mentor"              # Mentor educativo
    ANALYST = "analyst"            # Analista de datos
    RESEARCHER = "researcher"      # Investigador
    DEVELOPER = "developer"        # Desarrollador de software
    CONSULTANT = "consultant"      # Consultor de negocio
    CREATIVE = "creative"          # Creativo/artístico
    SPECIALIST = "specialist"      # Especialista de dominio
    COORDINATOR = "coordinator"    # Coordinador de proyectos


class CommunicationStyle(str, Enum):
    """Estilos de comunicación"""
    FORMAL = "formal"
    PROFESSIONAL = "professional"
    FRIENDLY = "friendly"
    CASUAL = "casual"
    TECHNICAL = "technical"
    EDUCATIONAL = "educational"


class ToneLevel(str, Enum):
    """Nivel de tono"""
    VERY_FORMAL = "very_formal"
    FORMAL = "formal"
    NEUTRAL = "neutral"
    INFORMAL = "informal"
    VERY_INFORMAL = "very_informal"


@dataclass
class PersonaConfig:
    """Configuración de la persona del agente"""
    persona_type: PersonaType = PersonaType.ASSISTANT
    name: str = "OpenClaw Agent"
    communication_style: CommunicationStyle = CommunicationStyle.PROFESSIONAL
    tone_level: ToneLevel = ToneLevel.NEUTRAL
    
    # Características
    is_verbose: bool = False
    uses_emojis: bool = False
    asks_clarification: bool = True
    shows_reasoning: bool = True
    provides_examples: bool = True
    offers_alternatives: bool = True
    
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


@dataclass
class PersonaResponse:
    """Respuesta generada por la persona"""
    content: str
    style_applied: CommunicationStyle
    tone_used: ToneLevel
    modifications: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


class Persona:
    """
    Define el comportamiento y personalidad del agente.
    
    Gestiona el tono, estilo de comunicación y adaptación
    de respuestas según el contexto y las preferencias del usuario.
    
    Usage:
        persona = Persona(PersonaConfig(
            persona_type=PersonaType.MENTOR,
            communication_style=CommunicationStyle.EDUCATIONAL
        ))
        
        response = persona.adapt_response(
            "Aquí está el resultado...",
            context={"user_level": "beginner"}
        )
    """
    
    # Plantillas de comportamiento por tipo
    PERSONA_TEMPLATES = {
        PersonaType.ASSISTANT: {
            "greeting": "¡Hola! ¿En qué puedo ayudarte hoy?",
            "clarification": "¿Podrías darme más detalles sobre eso?",
            "completion": "¿Hay algo más en lo que pueda ayudarte?",
            "apology": "Disculpa, no pude completar esa tarea. ¿Quieres que intente de otra forma?"
        },
        PersonaType.MENTOR: {
            "greeting": "¡Bienvenido! Estoy aquí para guiarte en tu aprendizaje.",
            "clarification": "Para ayudarte mejor, ¿podrías contarme qué ya sabes sobre este tema?",
            "completion": "¿Te gustaría profundizar más en algún aspecto?",
            "apology": "Parece que encontramos un obstáculo. Analicemos juntos qué salió mal."
        },
        PersonaType.ANALYST: {
            "greeting": "Hola. Estoy listo para analizar los datos que necesites.",
            "clarification": "Para un análisis más preciso, necesito más información.",
            "completion": "He completado el análisis. ¿Necesitas alguna interpretación adicional?",
            "apology": "El análisis encontró algunos problemas. Te muestro los detalles."
        },
        PersonaType.RESEARCHER: {
            "greeting": "Hola. ¿Qué tema te gustaría investigar hoy?",
            "clarification": "Para una investigación más efectiva, necesito acotar el tema.",
            "completion": "He recopilado la información. ¿Quieres que profundice en algún punto?",
            "apology": "La investigación encontró limitaciones. Te explico los hallazgos parciales."
        },
        PersonaType.DEVELOPER: {
            "greeting": "¡Hola! ¿En qué proyecto estás trabajando?",
            "clarification": "Para escribir mejor código, necesito más contexto.",
            "completion": "Código completado. ¿Quieres que agregue tests o documentación?",
            "apology": "Encontré un error. Revisemos el código juntos."
        },
        PersonaType.CONSULTANT: {
            "greeting": "Hola. Estoy aquí para ayudarte con tu negocio.",
            "clarification": "Para darte el mejor consejo, necesito entender tu situación.",
            "completion": "Espero que esta recomendación te sea útil. ¿Hay otros aspectos a considerar?",
            "apology": "Esta recomendación requiere ajustes. Analicemos las alternativas."
        },
        PersonaType.CREATIVE: {
            "greeting": "¡Hola! Estoy listo para crear algo increíble contigo.",
            "clarification": "Para despertar la creatividad, cuéntame más sobre tu visión.",
            "completion": "¿Qué te parece? ¿Quieres explorar otras direcciones creativas?",
            "apology": "El resultado no fue el esperado. Intentemos un enfoque diferente."
        },
        PersonaType.SPECIALIST: {
            "greeting": "Hola. Como especialista, estoy listo para ayudarte.",
            "clarification": "Para aplicar mi experiencia, necesito más detalles técnicos.",
            "completion": "¿Hay aspectos técnicos adicionales que quieras explorar?",
            "apology": "Este caso requiere un enfoque especializado diferente. Te explico las opciones."
        },
        PersonaType.COORDINATOR: {
            "greeting": "¡Hola! Estoy aquí para coordinar tu proyecto.",
            "clarification": "Para una coordinación efectiva, necesito entender el alcance.",
            "completion": "¿Hay otras tareas o recursos que necesites coordinar?",
            "apology": "Encontré un bloqueo en la coordinación. Revisemos las dependencias."
        }
    }
    
    def __init__(self, config: PersonaConfig):
        """
        Inicializa la persona.
        
        Args:
            config: Configuración de la persona
        """
        self.config = config
        self._interaction_history: List[Dict[str, Any]] = []
        self._adaptation_rules: Dict[str, Any] = {}
    
    def get_system_prompt(self) -> str:
        """
        Genera el system prompt para la persona.
        
        Este prompt define el comportamiento del agente.
        """
        template = self.PERSONA_TEMPLATES.get(
            self.config.persona_type,
            self.PERSONA_TEMPLATES[PersonaType.ASSISTANT]
        )
        
        sections = []
        
        # Identidad
        sections.append(f"# IDENTIDAD")
        sections.append(f"Eres {self.config.name}, un agente de tipo {self.config.persona_type.value}.")
        sections.append("")
        
        # Características
        sections.append(f"# CARACTERÍSTICAS")
        sections.append(f"- Estilo de comunicación: {self.config.communication_style.value}")
        sections.append(f"- Nivel de tono: {self.config.tone_level.value}")
        sections.append(f"- Rasgos de personalidad: {', '.join(self.config.personality_traits)}")
        
        if self.config.shows_reasoning:
            sections.append("- Muestras tu razonamiento de forma explícita")
        if self.config.asks_clarification:
            sections.append("- Pides clarificación cuando hay ambigüedad")
        if self.config.provides_examples:
            sections.append("- Proporcionas ejemplos para ilustrar conceptos")
        if self.config.offers_alternatives:
            sections.append("- Ofreces alternativas cuando es apropiado")
        
        sections.append("")
        
        # Comportamiento por tipo
        sections.append(f"# COMPORTAMIENTO")
        sections.append(f"- Saludo: {template['greeting']}")
        sections.append(f"- Clarificación: {template['clarification']}")
        sections.append(f"- Finalización: {template['completion']}")
        sections.append(f"- Disculpa: {template['apology']}")
        sections.append("")
        
        # Especialización
        if self.config.domain_expertise:
            sections.append(f"# EXPERIENCIA")
            sections.append(f"Dominios de especialización: {', '.join(self.config.domain_expertise)}")
            sections.append("")
        
        # Instrucciones personalizadas
        if self.config.custom_instructions:
            sections.append(f"# INSTRUCCIONES PERSONALIZADAS")
            sections.append(self.config.custom_instructions)
            sections.append("")
        
        # Límites
        sections.append(f"# LÍMITES")
        sections.append(f"- Longitud máxima de respuesta: {self.config.max_response_length} caracteres")
        sections.append(f"- Idioma preferido: {self.config.preferred_language}")
        
        return "\n".join(sections)
    
    def adapt_response(
        self,
        content: str,
        context: Optional[Dict[str, Any]] = None
    ) -> PersonaResponse:
        """
        Adapta una respuesta según la configuración de la persona.
        
        Args:
            content: Contenido original
            context: Contexto del usuario (nivel, preferencias, etc.)
        
        Returns:
            PersonaResponse con la respuesta adaptada
        """
        context = context or {}
        modifications = []
        adapted_content = content
        
        # Ajustar longitud
        if len(content) > self.config.max_response_length:
            adapted_content = self._summarize(content, self.config.max_response_length)
            modifications.append("summarized_for_length")
        
        # Ajustar tono según contexto
        user_level = context.get("user_level", "intermediate")
        if user_level == "beginner" and self.config.persona_type == PersonaType.MENTOR:
            adapted_content = self._add_explanations(adapted_content)
            modifications.append("added_explanations")
        
        # Añadir emojis si está configurado
        if self.config.uses_emojis:
            adapted_content = self._add_emojis(adapted_content)
            modifications.append("added_emojis")
        
        # Ajustar verbosidad
        if not self.config.is_verbose:
            adapted_content = self._make_concise(adapted_content)
            modifications.append("made_concise")
        
        return PersonaResponse(
            content=adapted_content,
            style_applied=self.config.communication_style,
            tone_used=self.config.tone_level,
            modifications=modifications,
            metadata={"original_length": len(content), "adapted_length": len(adapted_content)}
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
        
        if topic:
            return f"{base} Específicamente sobre: {topic}"
        
        return base
    
    def get_completion_message(self, summary: Optional[str] = None) -> str:
        """Obtiene mensaje de completación"""
        template = self.PERSONA_TEMPLATES.get(
            self.config.persona_type,
            self.PERSONA_TEMPLATES[PersonaType.ASSISTANT]
        )
        
        base = template["completion"]
        
        if summary:
            return f"He completado: {summary}. {base}"
        
        return base
    
    def get_apology(self, error: Optional[str] = None) -> str:
        """Obtiene mensaje de disculpa"""
        template = self.PERSONA_TEMPLATES.get(
            self.config.persona_type,
            self.PERSONA_TEMPLATES[PersonaType.ASSISTANT]
        )
        
        base = template["apology"]
        
        if error:
            return f"{base} Error: {error}"
        
        return base
    
    def _summarize(self, content: str, max_length: int) -> str:
        """Resume contenido para ajustar a longitud máxima"""
        if len(content) <= max_length:
            return content
        
        # Truncar con indicador
        return content[:max_length - 3] + "..."
    
    def _add_explanations(self, content: str) -> str:
        """Añade explicaciones adicionales para principiantes"""
        # Placeholder - en implementación real usaría LLM
        return f"💡 Para entender mejor: {content}"
    
    def _add_emojis(self, content: str) -> str:
        """Añade emojis apropiados al contenido"""
        # Mapeo simple de palabras a emojis
        emoji_map = {
            "importante": "⚠️",
            "éxito": "✅",
            "error": "❌",
            "idea": "💡",
            "consejo": "📌",
            "nota": "📝",
            "advertencia": "⚡"
        }
        
        result = content
        for word, emoji in emoji_map.items():
            if word in result.lower():
                result = result.replace(word, f"{emoji} {word}")
        
        return result
    
    def _make_concise(self, content: str) -> str:
        """Hace el contenido más conciso"""
        # Eliminar redundancias comunes
        replacements = {
            "Por favor, ": "",
            "Te gustaría ": "¿",
            "Me gustaría ": "",
            "En este momento ": "Ahora ",
            "De hecho, ": "",
            "Básicamente, ": "",
            "Esencialmente, ": ""
        }
        
        result = content
        for old, new in replacements.items():
            result = result.replace(old, new)
        
        return result
    
    def record_interaction(self, interaction: Dict[str, Any]) -> None:
        """Registra una interacción para adaptación futura"""
        self._interaction_history.append({
            **interaction,
            "timestamp": datetime.utcnow().isoformat()
        })
    
    def get_interaction_stats(self) -> Dict[str, Any]:
        """Obtiene estadísticas de interacciones"""
        if not self._interaction_history:
            return {"total": 0}
        
        return {
            "total": len(self._interaction_history),
            "last_interaction": self._interaction_history[-1] if self._interaction_history else None
        }

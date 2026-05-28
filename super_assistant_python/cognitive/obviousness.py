"""
Shared Obviousness - Contexto Compartido de Obviedad
=====================================================

El "transfondo de obviedad" es el contexto implícito compartido
entre el humano y el LLM que permite comunicación eficiente.

Basado en "Promptología Ontológica" de Mauricio Quiroga:

"El contexto compartido de obviedad elimina la necesidad de 
explicar todo desde cero en cada interacción. Es el conocimiento
tácito que ambas partes asumen como dado."

Componentes:
- ObviousnessContext: El contexto de obviedad
- SharedObviousness: Gestor del contexto compartido
- ObviousnessLayer: Capas de obviedad (dominio, tarea, usuario)
"""

import asyncio
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple
from uuid import UUID, uuid4
import json

from pydantic import BaseModel, Field


class ObviousnessLayer(str, Enum):
    """Capas del contexto de obviedad"""
    # Capa base (siempre presente)
    ONTOLOGICAL = "ONTOLOGICAL"     # Supuestos ontológicos básicos
    LINGUISTIC = "LINGUISTIC"       # Convenios lingüísticos
    
    # Capa de dominio
    DOMAIN = "DOMAIN"               # Conocimiento del dominio
    TEMPORAL = "TEMPORAL"           # Contexto temporal
    SPATIAL = "SPATIAL"             # Contexto espacial
    
    # Capa de interacción
    CONVERSATIONAL = "CONVERSATIONAL"  # Historia conversacional
    TASK = "TASK"                   # Contexto de la tarea actual
    USER = "USER"                   # Preferencias y perfil del usuario
    
    # Capa de sistema
    TECHNICAL = "TECHNICAL"         # Contexto técnico
    ORGANIZATIONAL = "ORGANIZATIONAL"  # Contexto organizacional


class ObviousnessContext(BaseModel):
    """Contexto de obviedad"""
    id: UUID = Field(default_factory=uuid4)
    
    # Capas activas
    layers: Dict[str, Dict[str, Any]] = Field(default_factory=dict)
    
    # Elementos obvios
    facts: List[str] = Field(default_factory=list)              # Hechos obvios
    assumptions: List[str] = Field(default_factory=list)         # Supuestos
    conventions: List[str] = Field(default_factory=list)         # Convenios
    constraints: List[str] = Field(default_factory=list)         # Restricciones implícitas
    
    # Referencias
    entities: Dict[str, Any] = Field(default_factory=dict)       # Entidades conocidas
    relations: List[Tuple[str, str, str]] = Field(default_factory=list)  # Relaciones (sujeto, predicado, objeto)
    
    # Metadatos
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    confidence: float = Field(default=1.0, ge=0, le=1)
    
    def add_fact(self, fact: str, confidence: float = 1.0) -> None:
        """Agregar un hecho obvio"""
        if fact not in self.facts:
            self.facts.append(fact)
        self.updated_at = datetime.utcnow()
    
    def add_assumption(self, assumption: str) -> None:
        """Agregar un supuesto"""
        if assumption not in self.assumptions:
            self.assumptions.append(assumption)
        self.updated_at = datetime.utcnow()
    
    def add_convention(self, convention: str) -> None:
        """Agregar un convenio"""
        if convention not in self.conventions:
            self.conventions.append(convention)
        self.updated_at = datetime.utcnow()
    
    def set_layer(self, layer: ObviousnessLayer, data: Dict[str, Any]) -> None:
        """Establecer datos de una capa"""
        self.layers[layer.value] = data
        self.updated_at = datetime.utcnow()
    
    def get_layer(self, layer: ObviousnessLayer) -> Dict[str, Any]:
        """Obtener datos de una capa"""
        return self.layers.get(layer.value, {})
    
    def to_prompt_context(self) -> str:
        """
        Convertir a contexto para prompt.
        
        Genera una representación textual del contexto de obviedad
        que puede ser incluido en prompts.
        """
        sections = []
        
        if self.facts:
            sections.append("HECHOS CONOCIDOS:\n" + "\n".join(f"- {f}" for f in self.facts[:10]))
        
        if self.assumptions:
            sections.append("SUPUESTOS:\n" + "\n".join(f"- {a}" for a in self.assumptions[:5]))
        
        if self.conventions:
            sections.append("CONVENIOS:\n" + "\n".join(f"- {c}" for c in self.conventions[:5]))
        
        if self.constraints:
            sections.append("RESTRICCIONES:\n" + "\n".join(f"- {c}" for c in self.constraints[:5]))
        
        if self.entities:
            entity_strs = [f"- {k}: {v}" for k, v in list(self.entities.items())[:10]]
            sections.append("ENTIDADES:\n" + "\n".join(entity_strs))
        
        return "\n\n".join(sections)


class ObviousnessSource(str, Enum):
    """Fuentes del contexto de obviedad"""
    USER_EXPLICIT = "USER_EXPLICIT"       # Explicitado por el usuario
    USER_IMPLICIT = "USER_IMPLICIT"       # Inferido del usuario
    SYSTEM_DEFAULT = "SYSTEM_DEFAULT"      # Por defecto del sistema
    DOMAIN_KNOWLEDGE = "DOMAIN_KNOWLEDGE" # Conocimiento del dominio
    CONVERSATION = "CONVERSATION"          # Derivado de la conversación
    CAPITAL = "CAPITAL"                    # Derivado del capital cognitivo


class SharedObviousness:
    """
    Gestor del Contexto Compartido de Obviedad.
    
    El transfondo de obviedad es fundamental porque:
    1. Reduce la fricción cognitiva en la comunicación
    2. Permite interacciones más eficientes
    3. Se acumula y mejora con el tiempo
    4. Facilita la coordinación entre agentes
    
    Principios (basados en Promptología Ontológica):
    - La obviedad es construida, no dada
    - Debe ser explicitada gradualmente
    - Se valida a través de la interacción
    - Es específica del contexto
    """
    
    def __init__(
        self,
        agent_id: UUID,
        capital: Optional[Any] = None
    ):
        self.agent_id = agent_id
        self.capital = capital
        
        # Contextos por sesión
        self._session_contexts: Dict[UUID, ObviousnessContext] = {}
        
        # Contexto global del agente
        self._global_context = ObviousnessContext(id=uuid4())
        
        # Inicializar capas base
        self._initialize_base_layers()
        
        # Índices
        self._entity_index: Dict[str, Set[str]] = {}  # entidad -> sesiones
        self._fact_index: Dict[str, Set[str]] = {}     # hecho hash -> sesiones
    
    def _initialize_base_layers(self) -> None:
        """Inicializar capas base de obviedad"""
        # Capa ontológica
        self._global_context.set_layer(ObviousnessLayer.ONTOLOGICAL, {
            "reality_basis": "El lenguaje crea realidad a través de actos de habla",
            "communication_model": "Conversaciones para la Acción",
            "agent_role": "Asistente cognitivo autónomo"
        })
        
        # Capa lingüística
        self._global_context.set_layer(ObviousnessLayer.LINGUISTIC, {
            "language": "Español",
            "formality": "Profesional pero accesible",
            "technical_level": "Adaptativo al contexto"
        })
        
        # Hechos ontológicos básicos
        self._global_context.add_fact("El usuario y el agente colaboran hacia un objetivo común")
        self._global_context.add_fact("El agente busca ser útil, preciso y eficiente")
        self._global_context.add_convention("Usar español neutro preferentemente")
        self._global_context.add_convention("Estructurar respuestas complejas en secciones")
    
    # ==========================================
    # GESTIÓN DE CONTEXTO
    # ==========================================
    
    async def create_session_context(
        self,
        session_id: UUID,
        user_id: Optional[str] = None,
        domain: Optional[str] = None,
        initial_context: Optional[Dict[str, Any]] = None
    ) -> ObviousnessContext:
        """
        Crear contexto de obviedad para una nueva sesión.
        
        Args:
            session_id: ID de la sesión
            user_id: ID del usuario
            domain: Dominio de la interacción
            initial_context: Contexto inicial
            
        Returns:
            Contexto de obviedad creado
        """
        # Crear contexto base
        ctx = ObviousnessContext(
            id=uuid4(),
            layers=dict(self._global_context.layers)
        )
        
        # Copiar hechos y convenios globales
        ctx.facts = list(self._global_context.facts)
        ctx.conventions = list(self._global_context.conventions)
        
        # Agregar información de usuario si está disponible
        if user_id:
            user_layer = await self._build_user_layer(user_id)
            ctx.set_layer(ObviousnessLayer.USER, user_layer)
        
        # Agregar dominio si está disponible
        if domain:
            domain_layer = await self._build_domain_layer(domain)
            ctx.set_layer(ObviousnessLayer.DOMAIN, domain_layer)
        
        # Agregar contexto inicial
        if initial_context:
            ctx.set_layer(ObviousnessLayer.TASK, initial_context)
            
            # Extraer entidades del contexto inicial
            for key, value in initial_context.items():
                if isinstance(value, str):
                    ctx.entities[key] = value
        
        # Almacenar
        self._session_contexts[session_id] = ctx
        
        return ctx
    
    async def get_session_context(self, session_id: UUID) -> Optional[ObviousnessContext]:
        """Obtener contexto de una sesión"""
        return self._session_contexts.get(session_id)
    
    async def update_session_context(
        self,
        session_id: UUID,
        updates: Dict[str, Any]
    ) -> Optional[ObviousnessContext]:
        """Actualizar contexto de sesión"""
        ctx = self._session_contexts.get(session_id)
        if not ctx:
            return None
        
        # Actualizar hechos
        for fact in updates.get("new_facts", []):
            ctx.add_fact(fact)
        
        # Actualizar supuestos
        for assumption in updates.get("new_assumptions", []):
            ctx.add_assumption(assumption)
        
        # Actualizar entidades
        for key, value in updates.get("new_entities", {}).items():
            ctx.entities[key] = value
        
        # Actualizar capas específicas
        for layer_name, layer_data in updates.get("layer_updates", {}).items():
            try:
                layer = ObviousnessLayer(layer_name)
                ctx.set_layer(layer, layer_data)
            except ValueError:
                pass
        
        ctx.updated_at = datetime.utcnow()
        
        return ctx
    
    # ==========================================
    # CONSTRUCCIÓN DE CAPAS
    # ==========================================
    
    async def _build_user_layer(self, user_id: str) -> Dict[str, Any]:
        """Construir capa de usuario"""
        layer = {
            "user_id": user_id,
            "preferences": {},
            "history_summary": None
        }
        
        # Recuperar preferencias del capital si está disponible
        if self.capital:
            prefs = await self.capital.withdraw(f"user:{user_id}:preferences")
            if prefs:
                layer["preferences"] = prefs.value
        
        return layer
    
    async def _build_domain_layer(self, domain: str) -> Dict[str, Any]:
        """Construir capa de dominio"""
        layer = {
            "domain": domain,
            "terminology": {},
            "constraints": [],
            "best_practices": []
        }
        
        # Recuperar conocimiento de dominio del capital
        if self.capital:
            domain_knowledge = await self.capital.withdraw_by_type(
                type=self.capital.CapitalType.KNOWLEDGE
                if hasattr(self.capital, 'CapitalType')
                else None
            )
            
            for entry in domain_knowledge[:5]:
                if domain.lower() in str(entry.value).lower():
                    layer["terminology"].update(entry.value.get("terminology", {}))
        
        return layer
    
    # ==========================================
    # EXTRACCIÓN DE OBVIEDAD
    # ==========================================
    
    async def extract_from_message(
        self,
        message: str,
        session_id: UUID,
        role: str = "user"
    ) -> Dict[str, Any]:
        """
        Extraer contexto de obviedad de un mensaje.
        
        Analiza el mensaje para identificar:
        - Hechos implícitos
        - Supuestos
        - Entidades mencionadas
        - Intenciones
        
        Args:
            message: Mensaje a analizar
            session_id: ID de la sesión
            role: Rol del emisor (user/assistant)
            
        Returns:
            Elementos extraídos
        """
        extracted = {
            "facts": [],
            "assumptions": [],
            "entities": {},
            "intentions": [],
            "questions": []
        }
        
        # TODO: Implementar extracción con LLM
        # Por ahora, extracción simple basada en patrones
        
        # Detectar entidades nombradas simples
        words = message.split()
        for word in words:
            if word[0].isupper() and len(word) > 2:
                extracted["entities"][word] = "named_entity"
        
        # Detectar preguntas
        if "?" in message:
            extracted["questions"].append(message)
        
        # Detectar intenciones por verbos
        intention_verbs = ["necesito", "quiero", "busco", "requiero", "deseo"]
        for verb in intention_verbs:
            if verb in message.lower():
                extracted["intentions"].append(f"intencion:{verb}")
                break
        
        # Actualizar contexto de sesión
        ctx = self._session_contexts.get(session_id)
        if ctx:
            for fact in extracted["facts"]:
                ctx.add_fact(fact)
            for key, value in extracted["entities"].items():
                ctx.entities[key] = value
        
        return extracted
    
    async def infer_from_context(
        self,
        session_id: UUID
    ) -> List[Dict[str, Any]]:
        """
        Inferir obviedad adicional del contexto.
        
        Utiliza el contexto acumulado para inferir
        conocimiento implícito adicional.
        
        Args:
            session_id: ID de la sesión
            
        Returns:
            Lista de inferencias
        """
        ctx = self._session_contexts.get(session_id)
        if not ctx:
            return []
        
        inferences = []
        
        # Inferir del historial de hechos
        if len(ctx.facts) > 3:
            # Patrones en hechos
            inferences.append({
                "type": "pattern",
                "content": f"Se han mencionado {len(ctx.facts)} hechos relevantes",
                "confidence": 0.7
            })
        
        # Inferir de entidades
        if len(ctx.entities) > 2:
            inferences.append({
                "type": "entity_cluster",
                "content": f"El contexto involucra {len(ctx.entities)} entidades",
                "entities": list(ctx.entities.keys()),
                "confidence": 0.8
            })
        
        return inferences
    
    # ==========================================
    # VALIDACIÓN DE OBVIEDAD
    # ==========================================
    
    async def validate_assumption(
        self,
        assumption: str,
        session_id: UUID
    ) -> Dict[str, Any]:
        """
        Validar un supuesto contra el contexto.
        
        Verifica si un supuesto es consistente con
        el contexto de obviedad acumulado.
        
        Args:
            assumption: Supuesto a validar
            session_id: ID de la sesión
            
        Returns:
            Resultado de validación
        """
        ctx = self._session_contexts.get(session_id)
        
        result = {
            "assumption": assumption,
            "is_valid": True,
            "confidence": 0.5,
            "conflicts": [],
            "support": []
        }
        
        if not ctx:
            return result
        
        # Verificar contra hechos conocidos
        for fact in ctx.facts:
            if self._are_contradictory(assumption, fact):
                result["is_valid"] = False
                result["conflicts"].append(fact)
        
        # Verificar contra restricciones
        for constraint in ctx.constraints:
            if self._violates_constraint(assumption, constraint):
                result["is_valid"] = False
                result["conflicts"].append(constraint)
        
        # Calcular confianza
        if result["conflicts"]:
            result["confidence"] = 0.1
        elif result["support"]:
            result["confidence"] = 0.9
        else:
            result["confidence"] = 0.6
        
        return result
    
    def _are_contradictory(self, statement1: str, statement2: str) -> bool:
        """Verificar si dos statements son contradictorios"""
        # TODO: Implementar con NLP/LLM
        # Por ahora, verificación simple
        negation_words = ["no", "nunca", "jamás", "ningún", "ninguna"]
        
        s1_lower = statement1.lower()
        s2_lower = statement2.lower()
        
        # Si son muy similares pero uno tiene negación
        for neg in negation_words:
            if neg in s1_lower and neg not in s2_lower:
                if self._text_similarity(s1_lower.replace(neg, ""), s2_lower) > 0.7:
                    return True
            if neg in s2_lower and neg not in s1_lower:
                if self._text_similarity(s1_lower, s2_lower.replace(neg, "")) > 0.7:
                    return True
        
        return False
    
    def _violates_constraint(self, statement: str, constraint: str) -> bool:
        """Verificar si un statement viola una restricción"""
        # TODO: Implementar verificación más sofisticada
        return False
    
    def _text_similarity(self, text1: str, text2: str) -> float:
        """Calcular similitud simple entre textos"""
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())
        
        if not words1 or not words2:
            return 0.0
        
        intersection = words1 & words2
        union = words1 | words2
        
        return len(intersection) / len(union)
    
    # ==========================================
    # UTILIDADES
    # ==========================================
    
    async def export_context(
        self,
        session_id: UUID,
        format: str = "json"
    ) -> Optional[str]:
        """Exportar contexto a formato específico"""
        ctx = self._session_contexts.get(session_id)
        if not ctx:
            return None
        
        if format == "json":
            return ctx.model_dump_json(indent=2)
        elif format == "prompt":
            return ctx.to_prompt_context()
        else:
            return ctx.to_prompt_context()
    
    async def merge_contexts(
        self,
        source_session_id: UUID,
        target_session_id: UUID
    ) -> bool:
        """Fusionar contexto de una sesión en otra"""
        source = self._session_contexts.get(source_session_id)
        target = self._session_contexts.get(target_session_id)
        
        if not source or not target:
            return False
        
        # Fusionar hechos
        for fact in source.facts:
            if fact not in target.facts:
                target.facts.append(fact)
        
        # Fusionar entidades
        for key, value in source.entities.items():
            if key not in target.entities:
                target.entities[key] = value
        
        # Fusionar capas
        for layer_name, layer_data in source.layers.items():
            if layer_name not in target.layers:
                target.layers[layer_name] = layer_data
        
        target.updated_at = datetime.utcnow()
        
        return True
    
    async def cleanup_session(self, session_id: UUID) -> bool:
        """Limpiar contexto de sesión finalizada"""
        if session_id in self._session_contexts:
            # TODO: Persistir contexto importante en capital
            del self._session_contexts[session_id]
            return True
        return False
    
    def get_global_context(self) -> ObviousnessContext:
        """Obtener contexto global"""
        return self._global_context
    
    async def update_global_context(
        self,
        updates: Dict[str, Any]
    ) -> None:
        """Actualizar contexto global"""
        for fact in updates.get("new_facts", []):
            self._global_context.add_fact(fact)
        
        for convention in updates.get("new_conventions", []):
            self._global_context.add_convention(convention)
        
        for layer_name, layer_data in updates.get("layer_updates", {}).items():
            try:
                layer = ObviousnessLayer(layer_name)
                self._global_context.set_layer(layer, layer_data)
            except ValueError:
                pass

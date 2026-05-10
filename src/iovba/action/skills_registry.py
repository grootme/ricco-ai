"""
Skills Registry - Sistema de Habilidades Auto-Generables

Las habilidades son módulos de capacidades extensibles almacenados
como archivos Markdown con metadatos YAML. El sistema implementa
un patrón de carga progresiva para mantener la ventana de contexto eficiente.
"""

import re
import yaml
import json
import uuid
from typing import Optional, Dict, Any, List, Callable
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class SkillCategory(str, Enum):
    """Categorías de habilidades"""
    DEVELOPMENT = "development"
    RESEARCH = "research"
    ANALYSIS = "analysis"
    COMMUNICATION = "communication"
    AUTOMATION = "automation"
    DATA = "data"
    INTEGRATION = "integration"
    DOMAIN = "domain"


class SkillStatus(str, Enum):
    """Estado de una habilidad"""
    DRAFT = "draft"
    ACTIVE = "active"
    DEPRECATED = "deprecated"
    ARCHIVED = "archived"


@dataclass
class SkillMetadata:
    """Metadatos de una habilidad"""
    name: str
    version: str = "1.0.0"
    description: str = ""
    category: SkillCategory = SkillCategory.AUTOMATION
    tags: List[str] = field(default_factory=list)
    author: str = "OpenClaw"
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    status: SkillStatus = SkillStatus.ACTIVE
    dependencies: List[str] = field(default_factory=list)
    required_tools: List[str] = field(default_factory=list)
    min_confidence: float = 0.7
    usage_count: int = 0
    success_rate: float = 1.0
    avg_execution_time_ms: int = 0


@dataclass
class Skill:
    """
    Habilidad del agente.
    
    Define una capacidad específica que el agente puede ejecutar,
    incluyendo instrucciones, ejemplos y validación.
    """
    id: str
    metadata: SkillMetadata
    instructions: str
    examples: List[Dict[str, Any]] = field(default_factory=list)
    validation_rules: List[str] = field(default_factory=list)
    error_handling: Optional[str] = None
    post_processing: Optional[str] = None
    source_path: Optional[str] = None
    
    def to_markdown(self) -> str:
        """Convierte la habilidad a formato Markdown"""
        sections = []
        
        # Front matter YAML
        front_matter = {
            "name": self.metadata.name,
            "version": self.metadata.version,
            "description": self.metadata.description,
            "category": self.metadata.category.value,
            "tags": self.metadata.tags,
            "status": self.metadata.status.value,
            "dependencies": self.metadata.dependencies,
            "required_tools": self.metadata.required_tools,
            "min_confidence": self.metadata.min_confidence
        }
        
        sections.append("---")
        sections.append(yaml.dump(front_matter, default_flow_style=False))
        sections.append("---")
        sections.append("")
        
        # Instrucciones
        sections.append(f"# {self.metadata.name}")
        sections.append("")
        sections.append(self.metadata.description)
        sections.append("")
        
        sections.append("## Instrucciones")
        sections.append(self.instructions)
        sections.append("")
        
        # Ejemplos
        if self.examples:
            sections.append("## Ejemplos")
            for i, example in enumerate(self.examples, 1):
                sections.append(f"### Ejemplo {i}")
                sections.append(f"**Input:** {example.get('input', '')}")
                sections.append(f"**Output:** {example.get('output', '')}")
                if 'explanation' in example:
                    sections.append(f"**Explicación:** {example['explanation']}")
                sections.append("")
        
        # Reglas de validación
        if self.validation_rules:
            sections.append("## Validación")
            for rule in self.validation_rules:
                sections.append(f"- {rule}")
            sections.append("")
        
        # Manejo de errores
        if self.error_handling:
            sections.append("## Manejo de Errores")
            sections.append(self.error_handling)
            sections.append("")
        
        return "\n".join(sections)
    
    @classmethod
    def from_markdown(cls, content: str, source_path: Optional[str] = None) -> "Skill":
        """Parsea una habilidad desde Markdown con front matter YAML"""
        # Extraer front matter - manejar contenido que puede empezar con newline
        content = content.strip()
        match = re.match(r'^---\s*\n(.*?)\n---\s*\n(.*)$', content, re.DOTALL)
        
        if not match:
            raise ValueError("Formato de skill inválido: falta front matter YAML")
        
        front_matter_raw = match.group(1)
        body = match.group(2)
        
        front_matter = yaml.safe_load(front_matter_raw)
        
        # Crear metadata
        metadata = SkillMetadata(
            name=front_matter.get("name", "Unnamed Skill"),
            version=front_matter.get("version", "1.0.0"),
            description=front_matter.get("description", ""),
            category=SkillCategory(front_matter.get("category", "automation")),
            tags=front_matter.get("tags", []),
            status=SkillStatus(front_matter.get("status", "active")),
            dependencies=front_matter.get("dependencies", []),
            required_tools=front_matter.get("required_tools", []),
            min_confidence=front_matter.get("min_confidence", 0.7)
        )
        
        # Parsear cuerpo
        sections = cls._parse_body(body)
        
        return cls(
            id=str(uuid.uuid4())[:8],
            metadata=metadata,
            instructions=sections.get("instructions", ""),
            examples=sections.get("examples", []),
            validation_rules=sections.get("validation", []),
            error_handling=sections.get("error_handling"),
            source_path=source_path
        )
    
    @staticmethod
    def _parse_body(body: str) -> Dict[str, Any]:
        """Parsea el cuerpo del markdown en secciones"""
        sections = {}
        current_section = None
        current_content = []
        
        for line in body.split("\n"):
            if line.startswith("## "):
                if current_section:
                    sections[current_section] = "\n".join(current_content).strip()
                current_section = line[3:].lower().replace(" ", "_")
                current_content = []
            else:
                current_content.append(line)
        
        if current_section:
            sections[current_section] = "\n".join(current_content).strip()
        
        # Procesar ejemplos si existen
        if "ejemplos" in sections:
            examples_text = sections["ejemplos"]
            examples = []
            # Parseo simple de ejemplos
            example_pattern = r'### Ejemplo \d+\s*\n\*\*Input:\*\* (.*?)\s*\n\*\*Output:\*\* (.*?)(?:\s*\n\*\*Explicación:\*\* (.*?))?(?=\n###|\Z)'
            
            for match in re.finditer(example_pattern, examples_text, re.DOTALL):
                examples.append({
                    "input": match.group(1).strip(),
                    "output": match.group(2).strip(),
                    "explanation": match.group(3).strip() if match.group(3) else None
                })
            
            sections["examples"] = examples
        
        # Procesar validación
        if "validación" in sections:
            rules_text = sections["validación"]
            sections["validation"] = [
                line[2:].strip() for line in rules_text.split("\n")
                if line.startswith("- ")
            ]
        
        return sections


class SkillsRegistry:
    """
    Registro Central de Habilidades.
    
    Gestiona el ciclo de vida de las habilidades, incluyendo:
    - Carga progresiva (lazy loading)
    - Auto-generación desde interacciones exitosas
    - Versionado y deprecación
    
    Usage:
        registry = SkillsRegistry()
        
        # Cargar desde directorio
        registry.load_from_directory("./skills")
        
        # Obtener skill
        skill = registry.get("data_analysis")
        
        # Registrar nueva skill
        registry.register(Skill(...))
        
        # Auto-generar desde interacción
        registry.auto_generate(interaction_data)
    """
    
    def __init__(
        self,
        skills_directory: str = "./skills",
        auto_save: bool = True
    ):
        """
        Inicializa el registro de habilidades.
        
        Args:
            skills_directory: Directorio donde se almacenan las habilidades
            auto_save: Si guardar automáticamente las nuevas habilidades
        """
        self.skills_directory = Path(skills_directory)
        self.auto_save = auto_save
        self._skills: Dict[str, Skill] = {}
        self._name_index: Dict[str, str] = {}  # name -> id
        self._category_index: Dict[SkillCategory, List[str]] = {}
        self._on_skill_used: Optional[Callable] = None
        self._on_skill_created: Optional[Callable] = None
    
    def load_from_directory(self, directory: Optional[str] = None) -> int:
        """
        Carga habilidades desde un directorio.
        
        Args:
            directory: Directorio a cargar (usa skills_directory por defecto)
        
        Returns:
            Número de habilidades cargadas
        """
        dir_path = Path(directory) if directory else self.skills_directory
        
        if not dir_path.exists():
            logger.warning(f"Directorio de skills no encontrado: {dir_path}")
            return 0
        
        count = 0
        for skill_file in dir_path.glob("**/*.md"):
            try:
                content = skill_file.read_text()
                skill = Skill.from_markdown(content, str(skill_file))
                self.register(skill)
                count += 1
            except Exception as e:
                logger.error(f"Error cargando skill {skill_file}: {e}")
        
        logger.info(f"Cargadas {count} habilidades desde {dir_path}")
        return count
    
    def register(self, skill: Skill) -> None:
        """Registra una habilidad"""
        self._skills[skill.id] = skill
        self._name_index[skill.metadata.name.lower()] = skill.id
        
        # Indexar por categoría
        category = skill.metadata.category
        if category not in self._category_index:
            self._category_index[category] = []
        self._category_index[category].append(skill.id)
        
        # Guardar si auto_save está activo
        if self.auto_save and not skill.source_path:
            self._save_skill(skill)
        
        if self._on_skill_created:
            self._on_skill_created(skill)
    
    def unregister(self, skill_id: str) -> bool:
        """Remueve una habilidad del registro"""
        if skill_id not in self._skills:
            return False
        
        skill = self._skills[skill_id]
        
        # Remover de índices
        self._name_index.pop(skill.metadata.name.lower(), None)
        if skill.metadata.category in self._category_index:
            self._category_index[skill.metadata.category] = [
                sid for sid in self._category_index[skill.metadata.category]
                if sid != skill_id
            ]
        
        del self._skills[skill_id]
        return True
    
    def get(self, skill_id: str) -> Optional[Skill]:
        """Obtiene una habilidad por ID"""
        return self._skills.get(skill_id)
    
    def get_by_name(self, name: str) -> Optional[Skill]:
        """Obtiene una habilidad por nombre"""
        skill_id = self._name_index.get(name.lower())
        if skill_id:
            return self._skills.get(skill_id)
        return None
    
    def get_instructions(self, skill_id: str) -> Optional[str]:
        """
        Obtiene solo las instrucciones de una habilidad.
        
        Patrón de carga progresiva: solo carga lo necesario para el contexto.
        """
        skill = self.get(skill_id)
        if skill:
            return skill.instructions
        return None
    
    def search(
        self,
        query: str,
        category: Optional[SkillCategory] = None,
        tags: Optional[List[str]] = None
    ) -> List[Skill]:
        """
        Busca habilidades por query, categoría o tags.
        
        Args:
            query: Texto a buscar en nombre y descripción
            category: Filtrar por categoría
            tags: Filtrar por tags
        
        Returns:
            Lista de habilidades que coinciden
        """
        results = []
        query_lower = query.lower()
        
        for skill in self._skills.values():
            # Filtrar por categoría
            if category and skill.metadata.category != category:
                continue
            
            # Filtrar por tags
            if tags and not any(tag in skill.metadata.tags for tag in tags):
                continue
            
            # Buscar en nombre y descripción
            if (query_lower in skill.metadata.name.lower() or
                query_lower in skill.metadata.description.lower() or
                query_lower in skill.instructions.lower()):
                results.append(skill)
        
        # Ordenar por uso y éxito
        results.sort(
            key=lambda s: (s.metadata.usage_count * s.metadata.success_rate),
            reverse=True
        )
        
        return results
    
    def get_by_category(self, category: SkillCategory) -> List[Skill]:
        """Obtiene todas las habilidades de una categoría"""
        skill_ids = self._category_index.get(category, [])
        return [self._skills[sid] for sid in skill_ids if sid in self._skills]
    
    def get_relevant_skills(
        self,
        context: str,
        limit: int = 5
    ) -> List[Skill]:
        """
        Obtiene habilidades relevantes para un contexto.
        
        Usa análisis simple de keywords para determinar relevancia.
        """
        context_lower = context.lower()
        scores = []
        
        for skill in self._skills.values():
            if skill.metadata.status != SkillStatus.ACTIVE:
                continue
            
            score = 0
            
            # Score por nombre
            for word in skill.metadata.name.lower().split():
                if word in context_lower:
                    score += 3
            
            # Score por tags
            for tag in skill.metadata.tags:
                if tag.lower() in context_lower:
                    score += 2
            
            # Score por descripción
            for word in skill.metadata.description.lower().split()[:10]:
                if word in context_lower:
                    score += 1
            
            if score > 0:
                scores.append((skill, score))
        
        # Ordenar por score
        scores.sort(key=lambda x: x[1], reverse=True)
        
        return [s[0] for s in scores[:limit]]
    
    def record_usage(
        self,
        skill_id: str,
        success: bool,
        execution_time_ms: int
    ) -> None:
        """Registra el uso de una habilidad para métricas"""
        skill = self.get(skill_id)
        if not skill:
            return
        
        skill.metadata.usage_count += 1
        skill.metadata.avg_execution_time_ms = (
            (skill.metadata.avg_execution_time_ms * (skill.metadata.usage_count - 1) + execution_time_ms)
            / skill.metadata.usage_count
        )
        
        if success:
            # Actualizar tasa de éxito con media móvil
            skill.metadata.success_rate = (
                skill.metadata.success_rate * 0.9 + 0.1
            )
        else:
            skill.metadata.success_rate = (
                skill.metadata.success_rate * 0.9
            )
        
        if self._on_skill_used:
            self._on_skill_used(skill_id, success, execution_time_ms)
    
    def auto_generate(
        self,
        interaction: Dict[str, Any]
    ) -> Optional[Skill]:
        """
        Auto-genera una habilidad desde una interacción exitosa.
        
        Transforma una secuencia de comandos manuales exitosos
        en una habilidad reutilizable.
        
        Args:
            interaction: Datos de la interacción (objective, commands, result)
        
        Returns:
            Nueva habilidad generada, o None si no aplica
        """
        # Verificar que fue exitosa
        if not interaction.get("success"):
            return None
        
        # Verificar que tuvo suficientes pasos para ser útil
        commands = interaction.get("commands", [])
        if len(commands) < 2:
            return None
        
        # Generar nombre desde objetivo
        objective = interaction.get("objective", "")
        name_words = [w for w in objective.lower().split() if len(w) > 3][:3]
        skill_name = "_".join(name_words) if name_words else f"auto_skill_{str(uuid.uuid4())[:4]}"
        
        # Crear metadata
        metadata = SkillMetadata(
            name=skill_name,
            description=f"Auto-generado desde: {objective[:100]}",
            category=SkillCategory.AUTOMATION,
            tags=["auto-generated"],
            status=SkillStatus.DRAFT  # Requiere revisión
        )
        
        # Generar instrucciones desde comandos
        instructions_lines = [
            f"Objetivo: {objective}",
            "",
            "Secuencia de comandos ejecutados:"
        ]
        
        for i, cmd in enumerate(commands, 1):
            instructions_lines.append(f"{i}. `{cmd.get('command', '')}`")
        
        instructions = "\n".join(instructions_lines)
        
        # Crear ejemplo
        example = {
            "input": objective,
            "output": interaction.get("result", ""),
            "explanation": "Generado automáticamente desde interacción exitosa"
        }
        
        skill = Skill(
            id=str(uuid.uuid4())[:8],
            metadata=metadata,
            instructions=instructions,
            examples=[example]
        )
        
        self.register(skill)
        
        logger.info(f"Habilidad auto-generada: {skill_name}")
        
        return skill
    
    def _save_skill(self, skill: Skill) -> None:
        """Guarda una habilidad a archivo"""
        self.skills_directory.mkdir(parents=True, exist_ok=True)
        
        file_name = f"{skill.metadata.name.lower().replace(' ', '_')}.md"
        file_path = self.skills_directory / file_name
        
        content = skill.to_markdown()
        file_path.write_text(content)
        
        skill.source_path = str(file_path)
    
    def deprecate(self, skill_id: str, reason: str = "") -> bool:
        """Marca una habilidad como deprecada"""
        skill = self.get(skill_id)
        if not skill:
            return False
        
        skill.metadata.status = SkillStatus.DEPRECATED
        skill.metadata.updated_at = datetime.utcnow()
        
        # Actualizar archivo si existe
        if skill.source_path and self.auto_save:
            self._save_skill(skill)
        
        return True
    
    def get_all(self) -> List[Skill]:
        """Obtiene todas las habilidades"""
        return list(self._skills.values())
    
    def get_stats(self) -> Dict[str, Any]:
        """Obtiene estadísticas del registro"""
        total = len(self._skills)
        by_status = {}
        by_category = {}
        
        for skill in self._skills.values():
            status = skill.metadata.status.value
            by_status[status] = by_status.get(status, 0) + 1
            
            category = skill.metadata.category.value
            by_category[category] = by_category.get(category, 0) + 1
        
        total_usage = sum(s.metadata.usage_count for s in self._skills.values())
        avg_success = sum(s.metadata.success_rate for s in self._skills.values()) / total if total > 0 else 0
        
        return {
            "total_skills": total,
            "by_status": by_status,
            "by_category": by_category,
            "total_usage": total_usage,
            "average_success_rate": avg_success
        }
    
    def on_skill_used(self, callback: Callable) -> None:
        """Registra callback para uso de habilidades"""
        self._on_skill_used = callback
    
    def on_skill_created(self, callback: Callable) -> None:
        """Registra callback para creación de habilidades"""
        self._on_skill_created = callback

"""
Sistema de Skills (Herramientas) para el Super Asistente.
Incluye skills locales y remotas con patrones de registro tipo NeMo Agent Toolkit.
"""

from typing import Any, Dict, List, Optional, Callable, Union, Type, Awaitable
from abc import ABC, abstractmethod
from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum
from dataclasses import dataclass, field
import json
import asyncio
import inspect


# =============================================================================
# ENUMS Y TIPOS
# =============================================================================

class SkillCategory(str, Enum):
    """Categorías de skills."""
    SEARCH = "search"
    ANALYSIS = "analysis"
    CODE = "code"
    DATA = "data"
    COMMUNICATION = "communication"
    FILE = "file"
    WEB = "web"
    AI = "ai"
    SYSTEM = "system"
    UTILITY = "utility"


class SkillType(str, Enum):
    """Tipos de skills."""
    LOCAL = "local"       # Ejecuta localmente
    REMOTE = "remote"     # Ejecuta en servicio remoto
    MCP = "mcp"           # Model Context Protocol
    API = "api"           # REST API


class SkillStatus(str, Enum):
    """Estado de una skill."""
    AVAILABLE = "available"
    UNAVAILABLE = "unavailable"
    DEPRECATED = "deprecated"
    ERROR = "error"


# =============================================================================
# MODELOS BASE
# =============================================================================

class SkillParameter(BaseModel):
    """Definición de un parámetro de skill."""
    name: str
    type: str = "string"
    description: str = ""
    required: bool = True
    default: Optional[Any] = None
    enum: Optional[List[str]] = None
    min_value: Optional[float] = None
    max_value: Optional[float] = None


class SkillDefinition(BaseModel):
    """Definición completa de una skill."""
    name: str
    description: str
    category: SkillCategory = SkillCategory.UTILITY
    skill_type: SkillType = SkillType.LOCAL
    parameters: List[SkillParameter] = Field(default_factory=list)
    returns: str = "string"
    requires_approval: bool = False
    required_permissions: List[str] = Field(default_factory=list)
    timeout_seconds: int = 60
    rate_limit: Optional[int] = None  # requests per minute
    version: str = "1.0.0"
    tags: List[str] = Field(default_factory=list)
    examples: List[Dict[str, Any]] = Field(default_factory=list)
    
    def to_json_schema(self) -> Dict[str, Any]:
        """Convierte a JSON Schema para tool calling."""
        properties = {}
        required = []
        
        for param in self.parameters:
            prop = {
                "type": param.type,
                "description": param.description
            }
            if param.enum:
                prop["enum"] = param.enum
            if param.min_value is not None:
                prop["minimum"] = param.min_value
            if param.max_value is not None:
                prop["maximum"] = param.max_value
            if param.default is not None:
                prop["default"] = param.default
            
            properties[param.name] = prop
            if param.required:
                required.append(param.name)
        
        return {
            "name": self.name,
            "description": self.description,
            "parameters": {
                "type": "object",
                "properties": properties,
                "required": required
            }
        }
    
    def to_langchain_tool(self) -> Dict[str, Any]:
        """Convierte a formato de tool de LangChain."""
        return self.to_json_schema()


class SkillResult(BaseModel):
    """Resultado de ejecutar una skill."""
    success: bool
    output: Optional[Any] = None
    error: Optional[str] = None
    execution_time_ms: Optional[int] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


# =============================================================================
# CLASE BASE DE SKILL
# =============================================================================

class BaseSkill(ABC):
    """
    Clase base abstracta para todas las skills.
    """
    
    def __init__(
        self,
        definition: Optional[SkillDefinition] = None,
        **kwargs
    ):
        self._definition = definition or self._get_default_definition()
        self._status = SkillStatus.AVAILABLE
        self._call_count = 0
        self._last_call_time: Optional[datetime] = None
    
    @property
    def name(self) -> str:
        return self._definition.name
    
    @property
    def definition(self) -> SkillDefinition:
        return self._definition
    
    @property
    def status(self) -> SkillStatus:
        return self._status
    
    def _get_default_definition(self) -> SkillDefinition:
        """Retorna la definición por defecto de la skill."""
        return SkillDefinition(
            name=self.__class__.__name__,
            description="Skill sin descripción"
        )
    
    @abstractmethod
    async def execute(
        self,
        parameters: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> SkillResult:
        """
        Ejecuta la skill con los parámetros dados.
        """
        pass
    
    def validate_parameters(self, parameters: Dict[str, Any]) -> List[str]:
        """
        Valida los parámetros de entrada.
        Retorna una lista de errores, vacía si es válido.
        """
        errors = []
        
        for param in self._definition.parameters:
            if param.required and param.name not in parameters:
                errors.append(f"Parámetro requerido faltante: {param.name}")
                continue
            
            value = parameters.get(param.name)
            if value is not None:
                # Validar tipo
                if param.type == "integer" and not isinstance(value, int):
                    errors.append(f"{param.name} debe ser un entero")
                elif param.type == "number" and not isinstance(value, (int, float)):
                    errors.append(f"{param.name} debe ser un número")
                elif param.type == "boolean" and not isinstance(value, bool):
                    errors.append(f"{param.name} debe ser un booleano")
                elif param.type == "array" and not isinstance(value, list):
                    errors.append(f"{param.name} debe ser un array")
                elif param.type == "object" and not isinstance(value, dict):
                    errors.append(f"{param.name} debe ser un objeto")
                
                # Validar enum
                if param.enum and value not in param.enum:
                    errors.append(f"{param.name} debe ser uno de: {param.enum}")
                
                # Validar rangos
                if isinstance(value, (int, float)):
                    if param.min_value is not None and value < param.min_value:
                        errors.append(f"{param.name} debe ser >= {param.min_value}")
                    if param.max_value is not None and value > param.max_value:
                        errors.append(f"{param.name} debe ser <= {param.max_value}")
        
        return errors
    
    async def __call__(
        self,
        parameters: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> SkillResult:
        """
        Permite llamar la skill directamente.
        """
        # Validar parámetros
        errors = self.validate_parameters(parameters)
        if errors:
            return SkillResult(
                success=False,
                error=f"Errores de validación: {'; '.join(errors)}"
            )
        
        # Medir tiempo de ejecución
        start_time = datetime.utcnow()
        
        try:
            result = await self.execute(parameters, context)
        except Exception as e:
            result = SkillResult(
                success=False,
                error=str(e)
            )
        
        # Registrar métricas
        end_time = datetime.utcnow()
        result.execution_time_ms = int(
            (end_time - start_time).total_seconds() * 1000
        )
        self._call_count += 1
        self._last_call_time = end_time
        
        return result


# =============================================================================
# SKILLS LOCALES
# =============================================================================

class WebSearchSkill(BaseSkill):
    """Skill para búsqueda web."""
    
    def _get_default_definition(self) -> SkillDefinition:
        return SkillDefinition(
            name="web_search",
            description="Buscar información en la web",
            category=SkillCategory.SEARCH,
            parameters=[
                SkillParameter(
                    name="query",
                    type="string",
                    description="Término de búsqueda",
                    required=True
                ),
                SkillParameter(
                    name="num_results",
                    type="integer",
                    description="Número de resultados",
                    required=False,
                    default=5,
                    min_value=1,
                    max_value=20
                )
            ],
            tags=["search", "web", "information"]
        )
    
    async def execute(
        self,
        parameters: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> SkillResult:
        query = parameters.get("query", "")
        num_results = parameters.get("num_results", 5)
        
        # Placeholder - en producción usar API de búsqueda real
        results = [
            {
                "title": f"Resultado {i+1} para: {query}",
                "url": f"https://example.com/result/{i+1}",
                "snippet": f"Información relevante sobre {query}..."
            }
            for i in range(num_results)
        ]
        
        return SkillResult(
            success=True,
            output={
                "query": query,
                "results": results
            }
        )


class CodeGeneratorSkill(BaseSkill):
    """Skill para generación de código."""
    
    def _get_default_definition(self) -> SkillDefinition:
        return SkillDefinition(
            name="code_generator",
            description="Generar código en varios lenguajes",
            category=SkillCategory.CODE,
            requires_approval=True,
            parameters=[
                SkillParameter(
                    name="language",
                    type="string",
                    description="Lenguaje de programación",
                    required=True,
                    enum=["python", "javascript", "typescript", "java", "go", "rust"]
                ),
                SkillParameter(
                    name="requirements",
                    type="string",
                    description="Requisitos del código a generar",
                    required=True
                ),
                SkillParameter(
                    name="style",
                    type="string",
                    description="Estilo de código",
                    required=False,
                    default="clean"
                )
            ],
            tags=["code", "generation", "programming"]
        )
    
    async def execute(
        self,
        parameters: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> SkillResult:
        language = parameters.get("language", "python")
        requirements = parameters.get("requirements", "")
        
        # Placeholder - en producción usar LLM para generar código
        code = f'''# Generated {language} code
# Requirements: {requirements}

def main():
    """Auto-generated code placeholder"""
    print("Hello, World!")

if __name__ == "__main__":
    main()
'''
        
        return SkillResult(
            success=True,
            output={
                "language": language,
                "code": code,
                "lines": len(code.split('\n'))
            }
        )


class DataAnalysisSkill(BaseSkill):
    """Skill para análisis de datos."""
    
    def _get_default_definition(self) -> SkillDefinition:
        return SkillDefinition(
            name="data_analysis",
            description="Analizar datos y generar estadísticas",
            category=SkillCategory.DATA,
            parameters=[
                SkillParameter(
                    name="data",
                    type="object",
                    description="Datos a analizar",
                    required=True
                ),
                SkillParameter(
                    name="analysis_type",
                    type="string",
                    description="Tipo de análisis",
                    required=True,
                    enum=["descriptive", "correlation", "regression", "clustering"]
                )
            ],
            tags=["data", "analysis", "statistics"]
        )
    
    async def execute(
        self,
        parameters: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> SkillResult:
        data = parameters.get("data", {})
        analysis_type = parameters.get("analysis_type", "descriptive")
        
        # Placeholder - análisis simulado
        result = {
            "analysis_type": analysis_type,
            "summary": {
                "count": len(data) if isinstance(data, list) else 1,
                "type": type(data).__name__
            },
            "insights": [
                "Patrón identificado en los datos",
                "Correlación potencial detectada"
            ]
        }
        
        return SkillResult(
            success=True,
            output=result
        )


class FileOperationsSkill(BaseSkill):
    """Skill para operaciones de archivos."""
    
    def _get_default_definition(self) -> SkillDefinition:
        return SkillDefinition(
            name="file_operations",
            description="Operaciones de lectura/escritura de archivos",
            category=SkillCategory.FILE,
            requires_approval=True,
            parameters=[
                SkillParameter(
                    name="operation",
                    type="string",
                    description="Tipo de operación",
                    required=True,
                    enum=["read", "write", "delete", "list", "copy"]
                ),
                SkillParameter(
                    name="path",
                    type="string",
                    description="Ruta del archivo",
                    required=True
                ),
                SkillParameter(
                    name="content",
                    type="string",
                    description="Contenido (para write)",
                    required=False
                )
            ],
            required_permissions=["file_access"],
            tags=["file", "io", "storage"]
        )
    
    async def execute(
        self,
        parameters: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> SkillResult:
        operation = parameters.get("operation", "read")
        path = parameters.get("path", "")
        
        # Placeholder - operaciones simuladas
        if operation == "read":
            return SkillResult(
                success=True,
                output={"content": f"Contenido de {path}"}
            )
        elif operation == "write":
            return SkillResult(
                success=True,
                output={"message": f"Escrito en {path}"}
            )
        elif operation == "list":
            return SkillResult(
                success=True,
                output={"files": ["file1.txt", "file2.py"]}
            )
        
        return SkillResult(
            success=False,
            error=f"Operación no soportada: {operation}"
        )


# =============================================================================
# REGISTRO DE SKILLS
# =============================================================================

class SkillRegistry:
    """
    Registro central de skills.
    Permite registrar, descubrir y ejecutar skills.
    """
    
    def __init__(self):
        self._skills: Dict[str, BaseSkill] = {}
        self._categories: Dict[SkillCategory, List[str]] = {
            cat: [] for cat in SkillCategory
        }
        self._aliases: Dict[str, str] = {}
    
    def register(
        self,
        skill: BaseSkill,
        aliases: Optional[List[str]] = None
    ) -> None:
        """Registra una skill."""
        name = skill.name
        self._skills[name] = skill
        
        # Registrar en categoría
        category = skill.definition.category
        if name not in self._categories[category]:
            self._categories[category].append(name)
        
        # Registrar aliases
        for alias in (aliases or []):
            self._aliases[alias] = name
    
    def unregister(self, name: str) -> bool:
        """Desregistra una skill."""
        if name in self._skills:
            skill = self._skills.pop(name)
            category = skill.definition.category
            if name in self._categories[category]:
                self._categories[category].remove(name)
            return True
        return False
    
    def get(self, name: str) -> Optional[BaseSkill]:
        """Obtiene una skill por nombre o alias."""
        # Buscar por nombre directo
        if name in self._skills:
            return self._skills[name]
        
        # Buscar por alias
        actual_name = self._aliases.get(name)
        if actual_name and actual_name in self._skills:
            return self._skills[actual_name]
        
        return None
    
    def list_all(self) -> List[str]:
        """Lista todas las skills registradas."""
        return list(self._skills.keys())
    
    def list_by_category(self, category: SkillCategory) -> List[str]:
        """Lista skills por categoría."""
        return self._categories.get(category, [])
    
    def search(self, query: str) -> List[str]:
        """Busca skills por nombre o descripción."""
        query_lower = query.lower()
        results = []
        
        for name, skill in self._skills.items():
            if query_lower in name.lower():
                results.append(name)
            elif query_lower in skill.definition.description.lower():
                results.append(name)
            elif any(query_lower in tag.lower() for tag in skill.definition.tags):
                results.append(name)
        
        return results
    
    def get_definitions(self) -> List[Dict[str, Any]]:
        """Obtiene las definiciones de todas las skills."""
        return [
            skill.definition.to_json_schema()
            for skill in self._skills.values()
        ]
    
    async def execute(
        self,
        name: str,
        parameters: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> SkillResult:
        """Ejecuta una skill por nombre."""
        skill = self.get(name)
        if not skill:
            return SkillResult(
                success=False,
                error=f"Skill no encontrada: {name}"
            )
        
        return await skill(parameters, context)
    
    def get_langchain_tools(self) -> List[Dict[str, Any]]:
        """Obtiene las skills en formato LangChain tools."""
        return [
            skill.definition.to_langchain_tool()
            for skill in self._skills.values()
        ]


# =============================================================================
# DECORADOR PARA REGISTRO
# =============================================================================

# Registro global
_global_registry = SkillRegistry()


def skill(
    name: Optional[str] = None,
    description: Optional[str] = None,
    category: SkillCategory = SkillCategory.UTILITY,
    requires_approval: bool = False,
    aliases: Optional[List[str]] = None
):
    """
    Decorador para registrar una función como skill.
    """
    def decorator(func: Callable):
        # Crear definición
        skill_name = name or func.__name__
        skill_description = description or func.__doc__ or "Sin descripción"
        
        # Extraer parámetros de la firma
        sig = inspect.signature(func)
        parameters = []
        
        for param_name, param in sig.parameters.items():
            if param_name in ["self", "cls", "context"]:
                continue
            
            param_def = SkillParameter(
                name=param_name,
                type="string",  # Default
                required=param.default == inspect.Parameter.empty
            )
            parameters.append(param_def)
        
        definition = SkillDefinition(
            name=skill_name,
            description=skill_description,
            category=category,
            parameters=parameters,
            requires_approval=requires_approval
        )
        
        # Crear skill wrapper
        class FunctionSkill(BaseSkill):
            def __init__(self):
                super().__init__(definition=definition)
                self._func = func
            
            async def execute(
                self,
                parameters: Dict[str, Any],
                context: Optional[Dict[str, Any]] = None
            ) -> SkillResult:
                try:
                    if asyncio.iscoroutinefunction(self._func):
                        result = await self._func(**parameters)
                    else:
                        result = self._func(**parameters)
                    
                    return SkillResult(success=True, output=result)
                except Exception as e:
                    return SkillResult(success=False, error=str(e))
        
        # Registrar
        skill_instance = FunctionSkill()
        _global_registry.register(skill_instance, aliases=aliases)
        
        return func
    
    return decorator


# =============================================================================
# FACTORY
# =============================================================================

def create_skill_registry_with_defaults() -> SkillRegistry:
    """Crea un registro con skills por defecto."""
    registry = SkillRegistry()
    
    # Registrar skills por defecto
    registry.register(WebSearchSkill())
    registry.register(CodeGeneratorSkill())
    registry.register(DataAnalysisSkill())
    registry.register(FileOperationsSkill())
    
    return registry


def get_global_registry() -> SkillRegistry:
    """Obtiene el registro global."""
    return _global_registry

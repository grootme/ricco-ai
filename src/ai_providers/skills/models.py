"""
Modelos de Skills y Herramientas MCP para RICCO AI
==================================================

Este módulo define los modelos de datos para el sistema de Skills
con integración completa de herramientas MCP (Model Context Protocol).

Autor: RICCO AI Team
Versión: 1.0.0
"""

from enum import Enum
from datetime import datetime
from typing import Optional, List, Dict, Any, Set, Callable, TypeVar, Generic
from pydantic import BaseModel, Field, validator, root_validator
from uuid import UUID, uuid4
import json


# ============================================
# ENUMS Y TIPOS
# ============================================

class ToolRiskLevel(str, Enum):
    """
    Niveles de riesgo para herramientas MCP
    
    Los niveles determinan qué permisos se requieren para ejecutar
    la herramienta y si se necesita confirmación del usuario.
    """
    LOW = "low"
    """
    Bajo riesgo - Solo lectura, sin efectos secundarios
    Ejemplo: read_file, query, search
    """
    
    MEDIUM = "medium"
    """
    Riesgo medio - Operaciones con efectos limitados
    Ejemplo: write_file, insert, send_email
    """
    
    HIGH = "high"
    """
    Alto riesgo - Operaciones críticas o irreversibles
    Ejemplo: delete_file, update, payment, transfer
    """
    
    CRITICAL = "critical"
    """
    Riesgo crítico - Operaciones financieras o de seguridad
    Ejemplo: create_payment, transfer_funds, modify_permissions
    """


class ToolPermissionLevel(str, Enum):
    """
    Niveles de permiso para usar herramientas
    """
    PUBLIC = "public"
    """Disponible para todos los usuarios"""
    
    AUTHENTICATED = "authenticated"
    """Requiere usuario autenticado"""
    
    VERIFIED = "verified"
    """Requiere usuario verificado (KYC)"""
    
    PREMIUM = "premium"
    """Requiere suscripción premium"""
    
    ADMIN = "admin"
    """Solo administradores"""
    
    SYSTEM = "system"
    """Solo uso interno del sistema"""


class MCPServerStatus(str, Enum):
    """
    Estado de conexión de un servidor MCP
    """
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    ERROR = "error"
    MAINTENANCE = "maintenance"


class MCPTransport(str, Enum):
    """
    Protocolos de transporte para MCP
    """
    STDIO = "stdio"
    SSE = "sse"
    WEBSOCKET = "websocket"
    HTTP = "http"


class SkillCategory(str, Enum):
    """
    Categorías de Skills disponibles
    """
    FILESYSTEM = "filesystem"
    DATABASE = "database"
    WEB = "web"
    AI = "ai"
    FINANCE = "finance"
    COMMUNICATION = "communication"
    PRODUCTIVITY = "productivity"
    RICCO = "ricco"
    DEVOPS = "devops"
    MONITORING = "monitoring"
    DOCUMENTS = "documents"
    COMMERCE = "commerce"
    HEALTH = "health"
    SOCIAL = "social"
    LEGAL = "legal"
    LOGISTICS = "logistics"


# ============================================
# MODELOS DE HERRAMIENTAS MCP
# ============================================

class MCPToolParameter(BaseModel):
    """
    Parámetro de una herramienta MCP
    
    Define un parámetro individual que acepta una herramienta,
    incluyendo su tipo, descripción y si es obligatorio.
    """
    name: str = Field(..., description="Nombre del parámetro")
    type: str = Field(..., description="Tipo de dato: string, number, boolean, object, array")
    description: str = Field(default="", description="Descripción del parámetro")
    required: bool = Field(default=True, description="Si el parámetro es obligatorio")
    default: Optional[Any] = Field(default=None, description="Valor por defecto")
    enum: Optional[List[str]] = Field(default=None, description="Valores permitidos si es un enum")
    min_value: Optional[float] = Field(default=None, description="Valor mínimo para números")
    max_value: Optional[float] = Field(default=None, description="Valor máximo para números")
    pattern: Optional[str] = Field(default=None, description="Patrón regex para strings")
    example: Optional[Any] = Field(default=None, description="Ejemplo de valor")
    
    class Config:
        use_enum_values = True


class MCPToolExample(BaseModel):
    """
    Ejemplo de uso de una herramienta MCP
    
    Proporciona un ejemplo concreto de cómo usar la herramienta
    con parámetros reales y el resultado esperado.
    """
    description: str = Field(..., description="Descripción del ejemplo")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Parámetros de ejemplo")
    result: Optional[Any] = Field(default=None, description="Resultado esperado")
    notes: Optional[str] = Field(default=None, description="Notas adicionales")
    
    class Config:
        use_enum_values = True


class MCPTool(BaseModel):
    """
    Herramienta MCP completa
    
    Representa una herramienta individual disponible en un servidor MCP,
    con toda la información necesaria para su documentación y uso.
    """
    id: str = Field(default_factory=lambda: str(uuid4()), description="ID único de la herramienta")
    name: str = Field(..., description="Nombre de la herramienta (ej: read_file)")
    full_name: str = Field(..., description="Nombre completo con servidor (ej: mcp-filesystem:read_file)")
    server_id: str = Field(..., description="ID del servidor MCP que proporciona esta herramienta")
    
    # Descripción y documentación
    description: str = Field(..., description="Descripción detallada de lo que hace la herramienta")
    summary: str = Field(default="", description="Resumen corto de una línea")
    documentation_url: Optional[str] = Field(default=None, description="URL a documentación externa")
    
    # Parámetros y retornos
    parameters: List[MCPToolParameter] = Field(default_factory=list, description="Parámetros aceptados")
    returns: str = Field(default="void", description="Tipo de retorno")
    returns_description: str = Field(default="", description="Descripción del valor de retorno")
    
    # Ejemplos
    examples: List[MCPToolExample] = Field(default_factory=list, description="Ejemplos de uso")
    
    # Riesgo y permisos
    risk_level: ToolRiskLevel = Field(default=ToolRiskLevel.LOW, description="Nivel de riesgo")
    permission_level: ToolPermissionLevel = Field(default=ToolPermissionLevel.AUTHENTICATED, description="Nivel de permiso requerido")
    requires_confirmation: bool = Field(default=False, description="Si requiere confirmación del usuario")
    requires_user_confirmation: bool = Field(default=False, description="Alias para requires_confirmation")
    
    # Categorización
    category: str = Field(default="general", description="Categoría de la herramienta")
    tags: List[str] = Field(default_factory=list, description="Tags para búsqueda")
    
    # Metadatos
    deprecated: bool = Field(default=False, description="Si la herramienta está deprecada")
    deprecation_message: Optional[str] = Field(default=None, description="Mensaje de deprecación")
    version: str = Field(default="1.0.0", description="Versión de la herramienta")
    
    # Estado
    enabled: bool = Field(default=True, description="Si la herramienta está habilitada")
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        use_enum_values = True
    
    @validator('full_name', always=True)
    def generate_full_name(cls, v, values):
        """Genera el nombre completo si no se proporciona"""
        if not v and 'server_id' in values and 'name' in values:
            return f"{values['server_id']}:{values['name']}"
        return v
    
    @validator('requires_user_confirmation', always=True)
    def sync_confirmation_flags(cls, v, values):
        """Sincroniza los flags de confirmación"""
        if 'requires_confirmation' in values:
            return values['requires_confirmation']
        return v
    
    def get_parameter(self, name: str) -> Optional[MCPToolParameter]:
        """Obtiene un parámetro por nombre"""
        for param in self.parameters:
            if param.name == name:
                return param
        return None
    
    def validate_parameters(self, params: Dict[str, Any]) -> List[str]:
        """
        Valida los parámetros proporcionados
        
        Returns:
            Lista de errores de validación (vacía si todo está bien)
        """
        errors = []
        
        # Verificar parámetros requeridos
        for param in self.parameters:
            if param.required and param.name not in params:
                errors.append(f"Parámetro requerido faltante: {param.name}")
        
        # Verificar tipos y restricciones
        for param in self.parameters:
            if param.name in params:
                value = params[param.name]
                
                # Validar enum
                if param.enum and value not in param.enum:
                    errors.append(f"Valor inválido para {param.name}. Permitidos: {param.enum}")
                
                # Validar min/max para números
                if param.type in ['number', 'integer']:
                    if param.min_value is not None and value < param.min_value:
                        errors.append(f"{param.name} debe ser >= {param.min_value}")
                    if param.max_value is not None and value > param.max_value:
                        errors.append(f"{param.name} debe ser <= {param.max_value}")
        
        return errors


# ============================================
# MODELOS DE SERVIDORES MCP
# ============================================

class MCPConnectionConfig(BaseModel):
    """
    Configuración de conexión a un servidor MCP
    """
    transport: MCPTransport = Field(default=MCPTransport.STDIO, description="Protocolo de transporte")
    
    # Para STDIO
    command: Optional[str] = Field(default=None, description="Comando a ejecutar")
    args: List[str] = Field(default_factory=list, description="Argumentos del comando")
    env: Dict[str, str] = Field(default_factory=dict, description="Variables de entorno")
    
    # Para HTTP/SSE/WebSocket
    url: Optional[str] = Field(default=None, description="URL del servidor")
    headers: Dict[str, str] = Field(default_factory=dict, description="Headers HTTP")
    
    # Configuración de conexión
    timeout_seconds: int = Field(default=30, description="Timeout en segundos")
    retry_attempts: int = Field(default=3, description="Intentos de reconexión")
    retry_delay_seconds: int = Field(default=5, description="Delay entre reintentos")
    
    # Pool de conexiones
    max_connections: int = Field(default=10, description="Máximo de conexiones")
    idle_timeout_seconds: int = Field(default=300, description="Timeout de conexiones inactivas")
    
    class Config:
        use_enum_values = True


class MCPServerConfig(BaseModel):
    """
    Configuración de un servidor MCP
    """
    id: str = Field(..., description="ID único del servidor")
    name: str = Field(..., description="Nombre descriptivo")
    description: str = Field(default="", description="Descripción del servidor")
    
    # Conexión
    connection: MCPConnectionConfig = Field(default_factory=MCPConnectionConfig)
    
    # Capacidades
    capabilities: List[str] = Field(default_factory=list, description="Capacidades del servidor")
    tools: List[str] = Field(default_factory=list, description="Lista de herramientas disponibles")
    resources: List[str] = Field(default_factory=list, description="Recursos disponibles")
    
    # Metadatos
    category: str = Field(default="general", description="Categoría del servidor")
    vendor: str = Field(default="ricco", description="Proveedor del servidor")
    version: str = Field(default="1.0.0", description="Versión del servidor")
    documentation_url: Optional[str] = Field(default=None)
    
    # Estado
    enabled: bool = Field(default=True, description="Si el servidor está habilitado")
    status: MCPServerStatus = Field(default=MCPServerStatus.DISCONNECTED, description="Estado actual")
    
    class Config:
        use_enum_values = True


class MCPServer(BaseModel):
    """
    Servidor MCP completo con herramientas detalladas
    """
    config: MCPServerConfig = Field(..., description="Configuración del servidor")
    
    # Herramientas detalladas
    tools_detailed: List[MCPTool] = Field(default_factory=list, description="Herramientas con detalles completos")
    
    # Estadísticas
    total_tools: int = Field(default=0, description="Total de herramientas")
    tools_by_risk: Dict[str, int] = Field(default_factory=dict, description="Herramientas por nivel de riesgo")
    
    # Estado de conexión
    last_connected: Optional[datetime] = Field(default=None, description="Última conexión exitosa")
    last_error: Optional[str] = Field(default=None, description="Último error de conexión")
    uptime_seconds: int = Field(default=0, description="Tiempo de actividad")
    
    class Config:
        use_enum_values = True
    
    def get_tool(self, name: str) -> Optional[MCPTool]:
        """Obtiene una herramienta por nombre"""
        for tool in self.tools_detailed:
            if tool.name == name:
                return tool
        return None
    
    def get_tools_by_risk(self, risk_level: ToolRiskLevel) -> List[MCPTool]:
        """Obtiene herramientas por nivel de riesgo"""
        return [t for t in self.tools_detailed if t.risk_level == risk_level]


# ============================================
# MODELOS DE SKILLS CON HERRAMIENTAS
# ============================================

class SkillToolMapping(BaseModel):
    """
    Mapeo de herramientas requeridas y opcionales para una Skill
    """
    required_tools: List[str] = Field(default_factory=list, description="Herramientas requeridas (ej: mcp-postgres:query)")
    optional_tools: List[str] = Field(default_factory=list, description="Herramientas opcionales que mejoran la funcionalidad")
    
    # Configuración
    fallback_behavior: str = Field(default="skip", description="Qué hacer si falta una herramienta opcional: skip, warn, error")
    
    class Config:
        use_enum_values = True


class SkillWorkflowStep(BaseModel):
    """
    Paso individual en el flujo de trabajo de una Skill
    """
    step_number: int = Field(..., description="Número de paso en la secuencia")
    description: str = Field(..., description="Descripción de lo que hace el paso")
    tool: Optional[str] = Field(default=None, description="Herramienta utilizada (ej: mcp-redis:get)")
    action: str = Field(..., description="Acción a realizar")
    expected_output: Optional[str] = Field(default=None, description="Output esperado")
    error_handling: str = Field(default="continue", description="Cómo manejar errores: continue, stop, retry")
    max_retries: int = Field(default=3, description="Máximo de reintentos")
    
    class Config:
        use_enum_values = True


class SkillWithTools(BaseModel):
    """
    Skill con mapeo explícito de herramientas MCP
    
    Define una habilidad completa con las herramientas que necesita
    para funcionar, incluyendo el flujo de trabajo paso a paso.
    """
    id: str = Field(default_factory=lambda: str(uuid4()), description="ID único de la Skill")
    name: str = Field(..., description="Nombre de la Skill")
    description: str = Field(..., description="Descripción de lo que hace la Skill")
    
    # Mapeo de herramientas
    tool_mapping: SkillToolMapping = Field(default_factory=SkillToolMapping, description="Herramientas utilizadas")
    
    # Flujo de trabajo
    workflow: List[SkillWorkflowStep] = Field(default_factory=list, description="Pasos del flujo de trabajo")
    
    # Categorización
    category: SkillCategory = Field(default=SkillCategory.RICCO, description="Categoría de la Skill")
    tags: List[str] = Field(default_factory=list, description="Tags para búsqueda")
    
    # Riesgo y permisos
    risk_level: ToolRiskLevel = Field(default=ToolRiskLevel.LOW, description="Nivel de riesgo de la Skill")
    requires_user_confirmation: bool = Field(default=False, description="Si requiere confirmación del usuario")
    permission_level: ToolPermissionLevel = Field(default=ToolPermissionLevel.AUTHENTICATED)
    
    # Ejemplos de uso
    example_inputs: List[Dict[str, Any]] = Field(default_factory=list, description="Ejemplos de input")
    example_outputs: List[Dict[str, Any]] = Field(default_factory=list, description="Ejemplos de output")
    
    # Documentación
    documentation: Optional[str] = Field(default=None, description="Documentación detallada en Markdown")
    
    # Estado
    enabled: bool = Field(default=True, description="Si la Skill está habilitada")
    deprecated: bool = Field(default=False, description="Si la Skill está deprecada")
    
    # Metadatos
    version: str = Field(default="1.0.0")
    author: str = Field(default="RICCO AI Team")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        use_enum_values = True
    
    def get_required_tools(self) -> List[str]:
        """Obtiene la lista de herramientas requeridas"""
        return self.tool_mapping.required_tools
    
    def get_optional_tools(self) -> List[str]:
        """Obtiene la lista de herramientas opcionales"""
        return self.tool_mapping.optional_tools
    
    def get_all_tools(self) -> List[str]:
        """Obtiene todas las herramientas (requeridas + opcionales)"""
        return self.tool_mapping.required_tools + self.tool_mapping.optional_tools
    
    def check_tool_availability(self, available_tools: Set[str]) -> Dict[str, Any]:
        """
        Verifica si las herramientas necesarias están disponibles
        
        Returns:
            Dict con 'available', 'missing_required', 'missing_optional'
        """
        missing_required = [t for t in self.tool_mapping.required_tools if t not in available_tools]
        missing_optional = [t for t in self.tool_mapping.optional_tools if t not in available_tools]
        
        return {
            "available": len(missing_required) == 0,
            "missing_required": missing_required,
            "missing_optional": missing_optional,
            "can_run": len(missing_required) == 0
        }


# ============================================
# MODELOS DE PERMISOS
# ============================================

class PermissionRule(BaseModel):
    """
    Regla de permiso para una herramienta
    """
    tool_id: str = Field(..., description="ID de la herramienta o '*' para todas")
    permission_level: ToolPermissionLevel = Field(default=ToolPermissionLevel.AUTHENTICATED)
    
    # Condiciones adicionales
    requires_kyc: bool = Field(default=False, description="Requiere verificación KYC")
    requires_subscription: Optional[str] = Field(default=None, description="Nivel de suscripción requerido")
    requires_trust_score: Optional[int] = Field(default=None, description="Score de confianza mínimo")
    
    # Límites
    max_calls_per_day: Optional[int] = Field(default=None, description="Límite diario de llamadas")
    max_calls_per_hour: Optional[int] = Field(default=None, description="Límite por hora")
    
    # Horarios permitidos
    allowed_hours: Optional[List[int]] = Field(default=None, description="Horas permitidas (0-23)")
    
    # IP restrictions
    allowed_ips: Optional[List[str]] = Field(default=None, description="IPs permitidas")
    blocked_ips: Optional[List[str]] = Field(default=None, description="IPs bloqueadas")
    
    class Config:
        use_enum_values = True


class ToolPermission(BaseModel):
    """
    Permiso de herramienta para un usuario o rol
    """
    id: str = Field(default_factory=lambda: str(uuid4()))
    
    # Sujeto del permiso
    user_id: Optional[str] = Field(default=None, description="ID del usuario")
    role_id: Optional[str] = Field(default=None, description="ID del rol")
    
    # Herramienta
    tool_id: str = Field(..., description="ID de la herramienta o '*' para todas")
    server_id: Optional[str] = Field(default=None, description="ID del servidor o '*' para todos")
    
    # Tipo de permiso
    permission_level: ToolPermissionLevel = Field(default=ToolPermissionLevel.AUTHENTICATED)
    
    # Permisos específicos
    can_execute: bool = Field(default=True, description="Puede ejecutar la herramienta")
    can_read: bool = Field(default=True, description="Puede leer información de la herramienta")
    requires_confirmation: bool = Field(default=False, description="Requiere confirmación")
    
    # Límites personalizados
    max_calls_per_day: Optional[int] = Field(default=None)
    max_calls_per_hour: Optional[int] = Field(default=None)
    
    # Vigencia
    valid_from: Optional[datetime] = Field(default=None)
    valid_until: Optional[datetime] = Field(default=None)
    
    # Estado
    enabled: bool = Field(default=True)
    
    # Metadatos
    created_by: Optional[str] = Field(default=None)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        use_enum_values = True
    
    def is_valid(self) -> bool:
        """Verifica si el permiso está vigente"""
        if not self.enabled:
            return False
        
        now = datetime.utcnow()
        
        if self.valid_from and now < self.valid_from:
            return False
        
        if self.valid_until and now > self.valid_until:
            return False
        
        return True


# ============================================
# REGISTROS
# ============================================

T = TypeVar('T')


class ToolRegistry(BaseModel):
    """
    Registro central de herramientas MCP
    """
    tools: Dict[str, MCPTool] = Field(default_factory=dict, description="Herramientas por ID")
    tools_by_server: Dict[str, List[str]] = Field(default_factory=dict, description="IDs de herramientas por servidor")
    tools_by_category: Dict[str, List[str]] = Field(default_factory=dict, description="IDs de herramientas por categoría")
    tools_by_risk: Dict[str, List[str]] = Field(default_factory=dict, description="IDs de herramientas por riesgo")
    
    class Config:
        use_enum_values = True
    
    def register_tool(self, tool: MCPTool) -> None:
        """Registra una herramienta en el registro"""
        # Registro principal
        self.tools[tool.full_name] = tool
        
        # Por servidor
        if tool.server_id not in self.tools_by_server:
            self.tools_by_server[tool.server_id] = []
        if tool.full_name not in self.tools_by_server[tool.server_id]:
            self.tools_by_server[tool.server_id].append(tool.full_name)
        
        # Por categoría
        cat = tool.category
        if cat not in self.tools_by_category:
            self.tools_by_category[cat] = []
        if tool.full_name not in self.tools_by_category[cat]:
            self.tools_by_category[cat].append(tool.full_name)
        
        # Por riesgo
        risk = tool.risk_level
        if risk not in self.tools_by_risk:
            self.tools_by_risk[risk] = []
        if tool.full_name not in self.tools_by_risk[risk]:
            self.tools_by_risk[risk].append(tool.full_name)
    
    def get_tool(self, tool_id: str) -> Optional[MCPTool]:
        """Obtiene una herramienta por ID"""
        return self.tools.get(tool_id)
    
    def get_tools_by_server(self, server_id: str) -> List[MCPTool]:
        """Obtiene todas las herramientas de un servidor"""
        tool_ids = self.tools_by_server.get(server_id, [])
        return [self.tools[tid] for tid in tool_ids if tid in self.tools]
    
    def search_tools(self, query: str) -> List[MCPTool]:
        """Busca herramientas por nombre o descripción"""
        query = query.lower()
        results = []
        for tool in self.tools.values():
            if (query in tool.name.lower() or 
                query in tool.description.lower() or
                any(query in tag.lower() for tag in tool.tags)):
                results.append(tool)
        return results


class PermissionRegistry(BaseModel):
    """
    Registro central de permisos de herramientas
    """
    permissions: Dict[str, ToolPermission] = Field(default_factory=dict, description="Permisos por ID")
    permissions_by_user: Dict[str, List[str]] = Field(default_factory=dict, description="IDs de permisos por usuario")
    permissions_by_role: Dict[str, List[str]] = Field(default_factory=dict, description="IDs de permisos por rol")
    permissions_by_tool: Dict[str, List[str]] = Field(default_factory=dict, description="IDs de permisos por herramienta")
    
    class Config:
        use_enum_values = True
    
    def register_permission(self, permission: ToolPermission) -> None:
        """Registra un permiso"""
        self.permissions[permission.id] = permission
        
        if permission.user_id:
            if permission.user_id not in self.permissions_by_user:
                self.permissions_by_user[permission.user_id] = []
            self.permissions_by_user[permission.user_id].append(permission.id)
        
        if permission.role_id:
            if permission.role_id not in self.permissions_by_role:
                self.permissions_by_role[permission.role_id] = []
            self.permissions_by_role[permission.role_id].append(permission.id)
        
        if permission.tool_id not in self.permissions_by_tool:
            self.permissions_by_tool[permission.tool_id] = []
        self.permissions_by_tool[permission.tool_id].append(permission.id)
    
    def get_user_permissions(self, user_id: str) -> List[ToolPermission]:
        """Obtiene todos los permisos de un usuario"""
        permission_ids = self.permissions_by_user.get(user_id, [])
        return [self.permissions[pid] for pid in permission_ids if pid in self.permissions]
    
    def get_tool_permissions(self, tool_id: str) -> List[ToolPermission]:
        """Obtiene todos los permisos para una herramienta"""
        permission_ids = self.permissions_by_tool.get(tool_id, [])
        return [self.permissions[pid] for pid in permission_ids if pid in self.permissions]
    
    def check_permission(self, user_id: str, tool_id: str) -> Optional[ToolPermission]:
        """
        Verifica si un usuario tiene permiso para una herramienta
        
        Returns el permiso si existe y está vigente, None si no
        """
        permissions = self.get_user_permissions(user_id)
        for perm in permissions:
            if (perm.tool_id == tool_id or perm.tool_id == "*") and perm.is_valid():
                return perm
        return None

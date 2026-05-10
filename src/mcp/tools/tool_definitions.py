"""
Documentación de MCP Tools para Skills
Catálogo completo de herramientas disponibles con sus descripciones claras
"""

from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field
from enum import Enum
import structlog

logger = structlog.get_logger(__name__)


class ToolCategory(str, Enum):
    """Categorías de herramientas MCP"""
    DATABASE = "database"
    FILESYSTEM = "filesystem"
    WEB = "web"
    AI = "ai"
    FINANCE = "finance"
    COMMUNICATION = "communication"
    PRODUCTIVITY = "productivity"
    RICCO = "ricco"


class RiskLevel(str, Enum):
    """Nivel de riesgo de una herramienta"""
    LOW = "low"        # Solo lectura, sin datos sensibles
    MEDIUM = "medium"  # Puede acceder a datos personales
    HIGH = "high"      # Puede modificar datos o realizar pagos
    CRITICAL = "critical"  # Puede realizar acciones irreversibles


@dataclass
class MCPTool:
    """
    Definición de una herramienta MCP
    
    Todos los campos tienen valores por defecto para permitir
    creación flexible de instancias con argumentos opcionales.
    """
    id: str = ""
    name: str = ""
    description: str = ""
    category: ToolCategory = ToolCategory.AI
    input_schema: Dict[str, Any] = field(default_factory=lambda: {"type": "object", "properties": {}})
    output_schema: Dict[str, Any] = field(default_factory=lambda: {"type": "object", "properties": {}})
    risk_level: RiskLevel = RiskLevel.LOW
    requires_consent: bool = False
    requires_permission: str = ""
    examples: List[str] = field(default_factory=list)
    
    def __post_init__(self):
        """Validación post-inicialización"""
        # Asegurar que los schemas tengan estructura válida
        if not self.input_schema:
            self.input_schema = {"type": "object", "properties": {}}
        if not self.output_schema:
            self.output_schema = {"type": "object", "properties": {}}
    
    def to_dict(self) -> Dict[str, Any]:
        """Convierte la herramienta a diccionario para serialización"""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "category": self.category.value if isinstance(self.category, ToolCategory) else self.category,
            "input_schema": self.input_schema,
            "output_schema": self.output_schema,
            "risk_level": self.risk_level.value if isinstance(self.risk_level, RiskLevel) else self.risk_level,
            "requires_consent": self.requires_consent,
            "requires_permission": self.requires_permission,
            "examples": self.examples,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MCPTool":
        """Crea una instancia desde un diccionario"""
        return cls(
            id=data.get("id", ""),
            name=data.get("name", ""),
            description=data.get("description", ""),
            category=ToolCategory(data.get("category", "ai")),
            input_schema=data.get("input_schema", {"type": "object", "properties": {}}),
            output_schema=data.get("output_schema", {"type": "object", "properties": {}}),
            risk_level=RiskLevel(data.get("risk_level", "low")),
            requires_consent=data.get("requires_consent", False),
            requires_permission=data.get("requires_permission", ""),
            examples=data.get("examples", []),
        )


# ============================================
# HERRAMIENTAS DE BASE DE DATOS
# ============================================

DATABASE_TOOLS = [
    MCPTool(
        id="db_postgres_query",
        name="PostgreSQL Query",
        description="Ejecutar consultas SQL en PostgreSQL",
        category=ToolCategory.DATABASE,
        input_schema={
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Consulta SQL SELECT"},
                "params": {"type": "array", "description": "Parámetros de la consulta"},
            },
            "required": ["query"],
        },
        output_schema={
            "type": "object",
            "properties": {
                "rows": {"type": "array"},
                "rowCount": {"type": "integer"},
            }
        },
        risk_level=RiskLevel.MEDIUM,
        requires_permission="db:read",
        examples=["SELECT * FROM products WHERE category = $1 LIMIT 10"],
    ),
    MCPTool(
        id="db_redis_get",
        name="Redis Get",
        description="Obtener valor de Redis por clave",
        category=ToolCategory.DATABASE,
        input_schema={
            "type": "object",
            "properties": {
                "key": {"type": "string", "description": "Clave a buscar"},
            },
            "required": ["key"],
        },
        output_schema={
            "type": "object",
            "properties": {
                "value": {"type": "string"},
                "exists": {"type": "boolean"},
            }
        },
        risk_level=RiskLevel.LOW,
        examples=["Obtener cache de usuario", "Verificar sesión"],
    ),
    MCPTool(
        id="db_mongodb_find",
        name="MongoDB Find",
        description="Buscar documentos en MongoDB",
        category=ToolCategory.DATABASE,
        input_schema={
            "type": "object",
            "properties": {
                "collection": {"type": "string"},
                "filter": {"type": "object"},
                "limit": {"type": "integer", "default": 10},
            },
            "required": ["collection", "filter"],
        },
        output_schema={
            "type": "object",
            "properties": {
                "documents": {"type": "array"},
                "count": {"type": "integer"},
            }
        },
        risk_level=RiskLevel.MEDIUM,
        requires_permission="db:read",
    ),
]

# ============================================
# HERRAMIENTAS DE ARCHIVOS
# ============================================

FILESYSTEM_TOOLS = [
    MCPTool(
        id="fs_read_file",
        name="Read File",
        description="Leer contenido de un archivo",
        category=ToolCategory.FILESYSTEM,
        input_schema={
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "Ruta del archivo"},
            },
            "required": ["path"],
        },
        output_schema={
            "type": "object",
            "properties": {
                "content": {"type": "string"},
                "size": {"type": "integer"},
            }
        },
        risk_level=RiskLevel.LOW,
        requires_permission="fs:read",
    ),
    MCPTool(
        id="fs_read_pdf",
        name="Read PDF",
        description="Extraer texto de un archivo PDF",
        category=ToolCategory.FILESYSTEM,
        input_schema={
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "Ruta del PDF"},
            },
            "required": ["path"],
        },
        output_schema={
            "type": "object",
            "properties": {
                "text": {"type": "string"},
                "pages": {"type": "integer"},
            }
        },
        risk_level=RiskLevel.LOW,
    ),
    MCPTool(
        id="fs_s3_upload",
        name="Upload to S3",
        description="Subir archivo a Amazon S3",
        category=ToolCategory.FILESYSTEM,
        input_schema={
            "type": "object",
            "properties": {
                "bucket": {"type": "string"},
                "key": {"type": "string"},
                "content": {"type": "string", "description": "Contenido en base64"},
            },
            "required": ["bucket", "key", "content"],
        },
        output_schema={
            "type": "object",
            "properties": {
                "url": {"type": "string"},
                "success": {"type": "boolean"},
            }
        },
        risk_level=RiskLevel.MEDIUM,
        requires_permission="s3:write",
    ),
]

# ============================================
# HERRAMIENTAS WEB
# ============================================

WEB_TOOLS = [
    MCPTool(
        id="web_fetch",
        name="Fetch URL",
        description="Obtener contenido de una URL",
        category=ToolCategory.WEB,
        input_schema={
            "type": "object",
            "properties": {
                "url": {"type": "string"},
                "method": {"type": "string", "default": "GET"},
                "headers": {"type": "object"},
            },
            "required": ["url"],
        },
        output_schema={
            "type": "object",
            "properties": {
                "status": {"type": "integer"},
                "body": {"type": "string"},
            }
        },
        risk_level=RiskLevel.LOW,
    ),
    MCPTool(
        id="web_search",
        name="Web Search",
        description="Buscar en internet",
        category=ToolCategory.WEB,
        input_schema={
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Término de búsqueda"},
                "limit": {"type": "integer", "default": 10},
            },
            "required": ["query"],
        },
        output_schema={
            "type": "object",
            "properties": {
                "results": {"type": "array"},
                "total": {"type": "integer"},
            }
        },
        risk_level=RiskLevel.LOW,
    ),
    MCPTool(
        id="web_scrape",
        name="Scrape Page",
        description="Extraer datos estructurados de una página web",
        category=ToolCategory.WEB,
        input_schema={
            "type": "object",
            "properties": {
                "url": {"type": "string"},
                "selector": {"type": "string"},
            },
            "required": ["url"],
        },
        output_schema={
            "type": "object",
            "properties": {
                "data": {"type": "array"},
            }
        },
        risk_level=RiskLevel.LOW,
    ),
]

# ============================================
# HERRAMIENTAS AI
# ============================================

AI_TOOLS = [
    MCPTool(
        id="ai_generate_text",
        name="Generate Text",
        description="Generar texto con IA",
        category=ToolCategory.AI,
        input_schema={
            "type": "object",
            "properties": {
                "prompt": {"type": "string"},
                "model": {"type": "string", "default": "gpt-4"},
                "max_tokens": {"type": "integer", "default": 1000},
            },
            "required": ["prompt"],
        },
        output_schema={
            "type": "object",
            "properties": {
                "text": {"type": "string"},
                "tokens_used": {"type": "integer"},
            }
        },
        risk_level=RiskLevel.LOW,
        requires_permission="ai:generate",
    ),
    MCPTool(
        id="ai_embed",
        name="Generate Embedding",
        description="Generar embedding vectorial de texto",
        category=ToolCategory.AI,
        input_schema={
            "type": "object",
            "properties": {
                "text": {"type": "string"},
            },
            "required": ["text"],
        },
        output_schema={
            "type": "object",
            "properties": {
                "embedding": {"type": "array"},
                "dimension": {"type": "integer"},
            }
        },
        risk_level=RiskLevel.LOW,
    ),
    MCPTool(
        id="ai_translate",
        name="Translate",
        description="Traducir texto entre idiomas",
        category=ToolCategory.AI,
        input_schema={
            "type": "object",
            "properties": {
                "text": {"type": "string"},
                "from_lang": {"type": "string"},
                "to_lang": {"type": "string"},
            },
            "required": ["text", "to_lang"],
        },
        output_schema={
            "type": "object",
            "properties": {
                "translation": {"type": "string"},
            }
        },
        risk_level=RiskLevel.LOW,
    ),
]

# ============================================
# HERRAMIENTAS FINANCIERAS
# ============================================

FINANCE_TOOLS = [
    MCPTool(
        id="finance_wallet_balance",
        name="Wallet Balance",
        description="Obtener balance de la wallet del usuario",
        category=ToolCategory.FINANCE,
        input_schema={
            "type": "object",
            "properties": {
                "user_id": {"type": "string"},
                "currency": {"type": "string", "description": "USD, CUP, MXN, etc."},
            },
            "required": ["user_id"],
        },
        output_schema={
            "type": "object",
            "properties": {
                "balance": {"type": "number"},
                "currency": {"type": "string"},
            }
        },
        risk_level=RiskLevel.MEDIUM,
        requires_permission="wallet:read",
    ),
    MCPTool(
        id="finance_crypto_deposit",
        name="Crypto Deposit",
        description="Crear depósito con criptomonedas",
        category=ToolCategory.FINANCE,
        input_schema={
            "type": "object",
            "properties": {
                "gateway": {"type": "string", "enum": ["binance", "bybit", "coinex"]},
                "crypto": {"type": "string", "description": "USDT, BTC, ETH"},
                "amount_usd": {"type": "number"},
            },
            "required": ["gateway", "crypto", "amount_usd"],
        },
        output_schema={
            "type": "object",
            "properties": {
                "deposit_address": {"type": "string"},
                "qr_code": {"type": "string"},
                "expires_at": {"type": "string"},
            }
        },
        risk_level=RiskLevel.HIGH,
        requires_consent=True,
        requires_permission="wallet:crypto",
    ),
    MCPTool(
        id="finance_transfer",
        name="Wallet Transfer",
        description="Transferir fondos entre wallets",
        category=ToolCategory.FINANCE,
        input_schema={
            "type": "object",
            "properties": {
                "from_user": {"type": "string"},
                "to_user": {"type": "string"},
                "amount": {"type": "number"},
                "currency": {"type": "string"},
            },
            "required": ["from_user", "to_user", "amount", "currency"],
        },
        output_schema={
            "type": "object",
            "properties": {
                "transaction_id": {"type": "string"},
                "status": {"type": "string"},
            }
        },
        risk_level=RiskLevel.CRITICAL,
        requires_consent=True,
        requires_permission="wallet:transfer",
    ),
    MCPTool(
        id="finance_exchange_rate",
        name="Exchange Rate",
        description="Obtener tasa de cambio entre monedas",
        category=ToolCategory.FINANCE,
        input_schema={
            "type": "object",
            "properties": {
                "from_currency": {"type": "string"},
                "to_currency": {"type": "string"},
            },
            "required": ["from_currency", "to_currency"],
        },
        output_schema={
            "type": "object",
            "properties": {
                "rate": {"type": "number"},
                "last_updated": {"type": "string"},
            }
        },
        risk_level=RiskLevel.LOW,
    ),
]

# ============================================
# HERRAMIENTAS DE COMUNICACIÓN
# ============================================

COMMUNICATION_TOOLS = [
    MCPTool(
        id="comm_send_email",
        name="Send Email",
        description="Enviar correo electrónico",
        category=ToolCategory.COMMUNICATION,
        input_schema={
            "type": "object",
            "properties": {
                "to": {"type": "string"},
                "subject": {"type": "string"},
                "body": {"type": "string"},
            },
            "required": ["to", "subject", "body"],
        },
        output_schema={
            "type": "object",
            "properties": {
                "sent": {"type": "boolean"},
                "message_id": {"type": "string"},
            }
        },
        risk_level=RiskLevel.MEDIUM,
        requires_permission="email:send",
    ),
    MCPTool(
        id="comm_send_whatsapp",
        name="Send WhatsApp",
        description="Enviar mensaje por WhatsApp",
        category=ToolCategory.COMMUNICATION,
        input_schema={
            "type": "object",
            "properties": {
                "phone": {"type": "string"},
                "message": {"type": "string"},
            },
            "required": ["phone", "message"],
        },
        output_schema={
            "type": "object",
            "properties": {
                "sent": {"type": "boolean"},
                "message_id": {"type": "string"},
            }
        },
        risk_level=RiskLevel.MEDIUM,
        requires_consent=True,
        requires_permission="whatsapp:send",
    ),
    MCPTool(
        id="comm_push_notification",
        name="Push Notification",
        description="Enviar notificación push",
        category=ToolCategory.COMMUNICATION,
        input_schema={
            "type": "object",
            "properties": {
                "user_id": {"type": "string"},
                "title": {"type": "string"},
                "body": {"type": "string"},
            },
            "required": ["user_id", "title", "body"],
        },
        output_schema={
            "type": "object",
            "properties": {
                "sent": {"type": "boolean"},
            }
        },
        risk_level=RiskLevel.LOW,
        requires_permission="push:send",
    ),
]

# ============================================
# HERRAMIENTAS RICCO ESPECÍFICAS
# ============================================

RICCO_TOOLS = [
    MCPTool(
        id="ricco_energy_points",
        name="Energy Points",
        description="Consultar o usar Energy Points",
        category=ToolCategory.RICCO,
        input_schema={
            "type": "object",
            "properties": {
                "user_id": {"type": "string"},
                "action": {"type": "string", "enum": ["balance", "use", "earn"]},
                "amount": {"type": "number"},
            },
            "required": ["user_id", "action"],
        },
        output_schema={
            "type": "object",
            "properties": {
                "balance": {"type": "number"},
                "transaction_id": {"type": "string"},
            }
        },
        risk_level=RiskLevel.MEDIUM,
        requires_permission="rewards:manage",
    ),
    MCPTool(
        id="ricco_trust_score",
        name="Trust Score",
        description="Obtener Trust Score del usuario",
        category=ToolCategory.RICCO,
        input_schema={
            "type": "object",
            "properties": {
                "user_id": {"type": "string"},
            },
            "required": ["user_id"],
        },
        output_schema={
            "type": "object",
            "properties": {
                "score": {"type": "number"},
                "level": {"type": "string"},
            }
        },
        risk_level=RiskLevel.LOW,
    ),
    MCPTool(
        id="ricco_create_order",
        name="Create Order",
        description="Crear pedido de compra",
        category=ToolCategory.RICCO,
        input_schema={
            "type": "object",
            "properties": {
                "user_id": {"type": "string"},
                "items": {"type": "array"},
                "shipping_address": {"type": "object"},
            },
            "required": ["user_id", "items"],
        },
        output_schema={
            "type": "object",
            "properties": {
                "order_id": {"type": "string"},
                "total": {"type": "number"},
            }
        },
        risk_level=RiskLevel.HIGH,
        requires_consent=True,
        requires_permission="orders:create",
    ),
    MCPTool(
        id="ricco_create_booking",
        name="Create Booking",
        description="Crear reservación",
        category=ToolCategory.RICCO,
        input_schema={
            "type": "object",
            "properties": {
                "user_id": {"type": "string"},
                "service_id": {"type": "string"},
                "datetime": {"type": "string"},
            },
            "required": ["user_id", "service_id", "datetime"],
        },
        output_schema={
            "type": "object",
            "properties": {
                "booking_id": {"type": "string"},
                "status": {"type": "string"},
            }
        },
        risk_level=RiskLevel.MEDIUM,
        requires_permission="booking:create",
    ),
    MCPTool(
        id="ricco_get_recommendations",
        name="Get Recommendations",
        description="Obtener recomendaciones personalizadas",
        category=ToolCategory.RICCO,
        input_schema={
            "type": "object",
            "properties": {
                "user_id": {"type": "string"},
                "type": {"type": "string", "enum": ["products", "services", "places"]},
                "context": {"type": "object"},
            },
            "required": ["user_id", "type"],
        },
        output_schema={
            "type": "object",
            "properties": {
                "recommendations": {"type": "array"},
            }
        },
        risk_level=RiskLevel.LOW,
    ),
    MCPTool(
        id="ricco_context_bundle",
        name="Context Bundle",
        description="Obtener bundle de contexto del usuario",
        category=ToolCategory.RICCO,
        input_schema={
            "type": "object",
            "properties": {
                "user_id": {"type": "string"},
                "bundle_type": {"type": "string"},
                "privacy_level": {"type": "string", "default": "standard"},
            },
            "required": ["user_id"],
        },
        output_schema={
            "type": "object",
            "properties": {
                "context": {"type": "object"},
                "sanitized": {"type": "boolean"},
            }
        },
        risk_level=RiskLevel.MEDIUM,
        requires_permission="context:read",
    ),
]

# ============================================
# TODAS LAS HERRAMIENTAS
# ============================================

ALL_MCP_TOOLS = (
    DATABASE_TOOLS +
    FILESYSTEM_TOOLS +
    WEB_TOOLS +
    AI_TOOLS +
    FINANCE_TOOLS +
    COMMUNICATION_TOOLS +
    RICCO_TOOLS
)

# Mapeo de categorías a herramientas
TOOLS_BY_CATEGORY = {
    ToolCategory.DATABASE: DATABASE_TOOLS,
    ToolCategory.FILESYSTEM: FILESYSTEM_TOOLS,
    ToolCategory.WEB: WEB_TOOLS,
    ToolCategory.AI: AI_TOOLS,
    ToolCategory.FINANCE: FINANCE_TOOLS,
    ToolCategory.COMMUNICATION: COMMUNICATION_TOOLS,
    ToolCategory.RICCO: RICCO_TOOLS,
}

# Mapeo de skills a herramientas recomendadas
SKILL_TO_TOOLS = {
    "product_search": ["web_search", "ricco_get_recommendations", "db_postgres_query"],
    "order_processing": ["ricco_create_order", "finance_wallet_balance", "comm_send_email"],
    "booking": ["ricco_create_booking", "db_postgres_query", "comm_push_notification"],
    "payment": ["finance_wallet_balance", "finance_crypto_deposit", "finance_transfer"],
    "recommendations": ["ai_generate_text", "ricco_get_recommendations", "ai_embed"],
    "communication": ["comm_send_email", "comm_send_whatsapp", "comm_push_notification"],
}

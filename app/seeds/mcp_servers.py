"""
RICCO AI Service - MCP (Model Context Protocol) Servers Arsenal
Colección completa de servidores MCP para integración con agentes
"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from enum import Enum


class MCPTransport(str, Enum):
    STDIO = "stdio"
    SSE = "sse"
    WEBSOCKET = "websocket"
    HTTP = "http"


class MCPServerConfig(BaseModel):
    """MCP Server configuration"""
    id: str
    name: str
    description: str
    transport: MCPTransport
    command: Optional[str] = None
    args: List[str] = []
    env: Dict[str, str] = {}
    url: Optional[str] = None
    tools: List[str] = []
    resources: List[str] = []
    capabilities: List[str] = []
    enabled: bool = True
    category: str = "general"


# ============================================
# FILESYSTEM & STORAGE MCP SERVERS
# ============================================

FILESYSTEM_MCPS: List[MCPServerConfig] = [
    MCPServerConfig(
        id="mcp-filesystem",
        name="Filesystem MCP",
        description="Acceso a sistema de archivos local y remoto",
        transport=MCPTransport.STDIO,
        command="npx",
        args=["-y", "@modelcontextprotocol/server-filesystem", "/data"],
        tools=["read_file", "write_file", "list_directory", "create_directory", "delete_file", "move_file", "search_files"],
        capabilities=["file_management", "directory_operations", "file_search"],
        category="filesystem",
    ),
    MCPServerConfig(
        id="mcp-s3-storage",
        name="S3 Storage MCP",
        description="Integración con Amazon S3 y storage compatible",
        transport=MCPTransport.STDIO,
        command="npx",
        args=["-y", "@ricco/mcp-s3"],
        env={
            "AWS_ACCESS_KEY_ID": "${AWS_ACCESS_KEY_ID}",
            "AWS_SECRET_ACCESS_KEY": "${AWS_SECRET_ACCESS_KEY}",
            "AWS_REGION": "us-east-1",
            "S3_BUCKET": "ricco-assets",
        },
        tools=["upload_file", "download_file", "list_objects", "delete_object", "get_presigned_url"],
        capabilities=["cloud_storage", "cdn_integration", "backup"],
        category="storage",
    ),
    MCPServerConfig(
        id="mcp-gdrive",
        name="Google Drive MCP",
        description="Integración con Google Drive",
        transport=MCPTransport.STDIO,
        command="npx",
        args=["-y", "@ricco/mcp-gdrive"],
        env={
            "GOOGLE_CLIENT_ID": "${GOOGLE_CLIENT_ID}",
            "GOOGLE_CLIENT_SECRET": "${GOOGLE_CLIENT_SECRET}",
        },
        tools=["list_files", "upload_file", "download_file", "share_file", "create_folder"],
        capabilities=["cloud_storage", "collaboration"],
        category="storage",
    ),
]


# ============================================
# DATABASE MCP SERVERS
# ============================================

DATABASE_MCPS: List[MCPServerConfig] = [
    MCPServerConfig(
        id="mcp-postgres",
        name="PostgreSQL MCP",
        description="Base de datos PostgreSQL",
        transport=MCPTransport.STDIO,
        command="npx",
        args=["-y", "@modelcontextprotocol/server-postgres"],
        env={
            "DATABASE_URL": "${DATABASE_URL}",
        },
        tools=["query", "insert", "update", "delete", "create_table", "describe_table", "list_tables"],
        capabilities=["sql_operations", "schema_management", "data_analysis"],
        category="database",
    ),
    MCPServerConfig(
        id="mcp-mongodb",
        name="MongoDB MCP",
        description="Base de datos MongoDB",
        transport=MCPTransport.STDIO,
        command="npx",
        args=["-y", "@ricco/mcp-mongodb"],
        env={
            "MONGODB_URI": "${MONGODB_URI}",
        },
        tools=["find", "insert_one", "insert_many", "update_one", "delete_one", "aggregate", "list_collections"],
        capabilities=["document_operations", "aggregation", "indexing"],
        category="database",
    ),
    MCPServerConfig(
        id="mcp-redis",
        name="Redis MCP",
        description="Cache y base de datos Redis",
        transport=MCPTransport.STDIO,
        command="npx",
        args=["-y", "@ricco/mcp-redis"],
        env={
            "REDIS_URL": "${REDIS_URL}",
        },
        tools=["get", "set", "delete", "list_push", "list_pop", "hash_set", "hash_get", "publish", "subscribe"],
        capabilities=["caching", "pub_sub", "session_management"],
        category="database",
    ),
    MCPServerConfig(
        id="mcp-nebulagraph",
        name="NebulaGraph MCP",
        description="Base de datos de grafos NebulaGraph para el grafo social",
        transport=MCPTransport.STDIO,
        command="npx",
        args=["-y", "@ricco/mcp-nebulagraph"],
        env={
            "NEBULA_HOST": "${NEBULA_HOST}",
            "NEBULA_PORT": "9669",
        },
        tools=["execute_nGQL", "insert_vertex", "insert_edge", "traverse", "shortest_path", "subgraph"],
        capabilities=["graph_operations", "social_network", "recommendations"],
        category="database",
    ),
]


# ============================================
# WEB & API MCP SERVERS
# ============================================

WEB_MCPS: List[MCPServerConfig] = [
    MCPServerConfig(
        id="mcp-fetch",
        name="Web Fetch MCP",
        description="Obtener contenido de páginas web",
        transport=MCPTransport.STDIO,
        command="npx",
        args=["-y", "@modelcontextprotocol/server-fetch"],
        tools=["fetch_url", "fetch_json", "fetch_html", "download_file"],
        capabilities=["web_scraping", "api_requests", "content_extraction"],
        category="web",
    ),
    MCPServerConfig(
        id="mcp-brave-search",
        name="Brave Search MCP",
        description="Búsqueda web con Brave Search API",
        transport=MCPTransport.STDIO,
        command="npx",
        args=["-y", "@modelcontextprotocol/server-brave-search"],
        env={
            "BRAVE_API_KEY": "${BRAVE_API_KEY}",
        },
        tools=["web_search", "image_search", "news_search", "video_search"],
        capabilities=["web_search", "real_time_info"],
        category="search",
    ),
    MCPServerConfig(
        id="mcp-puppeteer",
        name="Puppeteer MCP",
        description="Automatización de navegador con Puppeteer",
        transport=MCPTransport.STDIO,
        command="npx",
        args=["-y", "@modelcontextprotocol/server-puppeteer"],
        tools=["navigate", "screenshot", "click", "type", "evaluate", "wait_for", "extract"],
        capabilities=["browser_automation", "web_scraping", "testing"],
        category="web",
    ),
]


# ============================================
# AI & LLM MCP SERVERS
# ============================================

AI_MCPS: List[MCPServerConfig] = [
    MCPServerConfig(
        id="mcp-openai",
        name="OpenAI MCP",
        description="Integración con OpenAI API",
        transport=MCPTransport.STDIO,
        command="npx",
        args=["-y", "@ricco/mcp-openai"],
        env={
            "OPENAI_API_KEY": "${OPENAI_API_KEY}",
        },
        tools=["chat_completion", "embeddings", "image_generation", "audio_transcription", "text_to_speech"],
        capabilities=["llm", "embeddings", "image_gen", "audio"],
        category="ai",
    ),
    MCPServerConfig(
        id="mcp-openrouter",
        name="OpenRouter MCP",
        description="Multi-LLM a través de OpenRouter",
        transport=MCPTransport.STDIO,
        command="npx",
        args=["-y", "@ricco/mcp-openrouter"],
        env={
            "OPENROUTER_API_KEY": "${OPENROUTER_API_KEY}",
        },
        tools=["chat_completion", "list_models", "estimate_cost"],
        capabilities=["multi_llm", "model_selection", "cost_optimization"],
        category="ai",
    ),
    MCPServerConfig(
        id="mcp-ollama",
        name="Ollama MCP",
        description="Modelos locales con Ollama",
        transport=MCPTransport.STDIO,
        command="npx",
        args=["-y", "@ricco/mcp-ollama"],
        env={
            "OLLAMA_HOST": "http://localhost:11434",
        },
        tools=["generate", "chat", "embeddings", "list_models", "pull_model"],
        capabilities=["local_llm", "privacy_first", "no_api_cost"],
        category="ai",
    ),
    MCPServerConfig(
        id="mcp-huggingface",
        name="HuggingFace MCP",
        description="Modelos de HuggingFace",
        transport=MCPTransport.STDIO,
        command="npx",
        args=["-y", "@ricco/mcp-huggingface"],
        env={
            "HF_API_KEY": "${HF_API_KEY}",
        },
        tools=["inference", "embeddings", "zero_shot", "ner", "translation", "summarization"],
        capabilities=["transformers", "specialized_models"],
        category="ai",
    ),
]


# ============================================
# PRODUCTIVITY MCP SERVERS
# ============================================

PRODUCTIVITY_MCPS: List[MCPServerConfig] = [
    MCPServerConfig(
        id="mcp-google-maps",
        name="Google Maps MCP",
        description="Servicios de Google Maps",
        transport=MCPTransport.STDIO,
        command="npx",
        args=["-y", "@ricco/mcp-google-maps"],
        env={
            "GOOGLE_MAPS_API_KEY": "${GOOGLE_MAPS_API_KEY}",
        },
        tools=["geocode", "reverse_geocode", "directions", "distance_matrix", "places_search", "place_details", "static_map"],
        capabilities=["geolocation", "routing", "places"],
        category="maps",
    ),
    MCPServerConfig(
        id="mcp-calendar",
        name="Calendar MCP",
        description="Gestión de calendarios (Google, Outlook)",
        transport=MCPTransport.STDIO,
        command="npx",
        args=["-y", "@ricco/mcp-calendar"],
        env={
            "GOOGLE_CLIENT_ID": "${GOOGLE_CLIENT_ID}",
            "GOOGLE_CLIENT_SECRET": "${GOOGLE_CLIENT_SECRET}",
        },
        tools=["list_events", "create_event", "update_event", "delete_event", "find_free_time", "add_attendee"],
        capabilities=["scheduling", "availability", "reminders"],
        category="productivity",
    ),
    MCPServerConfig(
        id="mcp-email",
        name="Email MCP",
        description="Gestión de correo electrónico",
        transport=MCPTransport.STDIO,
        command="npx",
        args=["-y", "@ricco/mcp-email"],
        env={
            "SMTP_HOST": "${SMTP_HOST}",
            "SMTP_USER": "${SMTP_USER}",
            "SMTP_PASSWORD": "${SMTP_PASSWORD}",
        },
        tools=["send_email", "list_emails", "read_email", "search_emails", "mark_read", "move_to_folder"],
        capabilities=["email_management", "notifications"],
        category="communication",
    ),
    MCPServerConfig(
        id="mcp-slack",
        name="Slack MCP",
        description="Integración con Slack",
        transport=MCPTransport.STDIO,
        command="npx",
        args=["-y", "@modelcontextprotocol/server-slack"],
        env={
            "SLACK_BOT_TOKEN": "${SLACK_BOT_TOKEN}",
        },
        tools=["send_message", "list_channels", "get_channel_history", "upload_file", "add_reaction"],
        capabilities=["team_communication", "notifications"],
        category="communication",
    ),
]


# ============================================
# FINANCE & PAYMENT MCP SERVERS
# ============================================

FINANCE_MCPS: List[MCPServerConfig] = [
    MCPServerConfig(
        id="mcp-stripe",
        name="Stripe MCP",
        description="Procesamiento de pagos con Stripe",
        transport=MCPTransport.STDIO,
        command="npx",
        args=["-y", "@ricco/mcp-stripe"],
        env={
            "STRIPE_SECRET_KEY": "${STRIPE_SECRET_KEY}",
        },
        tools=["create_payment_intent", "capture_payment", "refund", "create_customer", "list_charges", "create_subscription"],
        capabilities=["payment_processing", "subscriptions", "billing"],
        category="finance",
    ),
    MCPServerConfig(
        id="mcp-qvapay",
        name="QvaPay MCP",
        description="Pasarela de pagos QvaPay para Cuba",
        transport=MCPTransport.STDIO,
        command="npx",
        args=["-y", "@ricco/mcp-qvapay"],
        env={
            "QVAPAY_API_KEY": "${QVAPAY_API_KEY}",
            "QVAPAY_SECRET": "${QVAPAY_SECRET}",
        },
        tools=["create_invoice", "check_payment", "get_balance", "transfer"],
        capabilities=["cuban_payments", "mlc_transactions"],
        category="finance",
    ),
    MCPServerConfig(
        id="mcp-crypto",
        name="Crypto MCP",
        description="Operaciones con criptomonedas",
        transport=MCPTransport.STDIO,
        command="npx",
        args=["-y", "@ricco/mcp-crypto"],
        tools=["get_price", "create_wallet", "get_balance", "send_transaction", "estimate_fee", "get_transaction"],
        capabilities=["crypto_payments", "wallet_management", "blockchain"],
        category="finance",
    ),
    MCPServerConfig(
        id="mcp-binance",
        name="Binance MCP",
        description="Integración con Binance",
        transport=MCPTransport.STDIO,
        command="npx",
        args=["-y", "@ricco/mcp-binance"],
        env={
            "BINANCE_API_KEY": "${BINANCE_API_KEY}",
            "BINANCE_SECRET": "${BINANCE_SECRET}",
        },
        tools=["get_ticker", "place_order", "cancel_order", "get_balance", "get_trade_history", "get_deposit_address"],
        capabilities=["trading", "portfolio_management"],
        category="finance",
    ),
]


# ============================================
# RICCO-SPECIFIC MCP SERVERS
# ============================================

RICCO_MCPS: List[MCPServerConfig] = [
    MCPServerConfig(
        id="mcp-ricco-id",
        name="RICCO ID MCP",
        description="Identidad y autenticación RICCO",
        transport=MCPTransport.STDIO,
        command="npx",
        args=["-y", "@ricco/mcp-ricco-id"],
        env={
            "RICCO_ID_URL": "${RICCO_ID_URL}",
            "RICCO_SHARED_SECRET": "${RICCO_SHARED_SECRET}",
        },
        tools=["verify_token", "get_user_profile", "update_profile", "verify_kyc", "get_trust_score", "manage_permissions"],
        capabilities=["authentication", "identity_verification", "permissions"],
        category="ricco",
    ),
    MCPServerConfig(
        id="mcp-ricco-energy",
        name="RICCO Energy Points MCP",
        description="Sistema de Energy Points y recompensas",
        transport=MCPTransport.STDIO,
        command="npx",
        args=["-y", "@ricco/mcp-energy"],
        env={
            "RICCO_ENERGY_URL": "${RICCO_ENERGY_URL}",
        },
        tools=["get_balance", "transfer_points", "earn_points", "redeem_points", "get_history", "calculate_rewards"],
        capabilities=["rewards_system", "tokenomics", "gamification"],
        category="ricco",
    ),
    MCPServerConfig(
        id="mcp-ricco-commerce",
        name="RICCO Commerce MCP",
        description="Marketplace y e-commerce",
        transport=MCPTransport.STDIO,
        command="npx",
        args=["-y", "@ricco/mcp-commerce"],
        env={
            "RICCO_COMMERCE_URL": "${RICCO_COMMERCE_URL}",
        },
        tools=["search_products", "get_product", "create_cart", "add_to_cart", "checkout", "get_order", "track_shipment"],
        capabilities=["ecommerce", "marketplace", "orders"],
        category="ricco",
    ),
    MCPServerConfig(
        id="mcp-ricco-logistics",
        name="RICCO Logistics MCP",
        description="Logística y envíos",
        transport=MCPTransport.STDIO,
        command="npx",
        args=["-y", "@ricco/mcp-logistics"],
        env={
            "RICCO_LOGISTICS_URL": "${RICCO_LOGISTICS_URL}",
        },
        tools=["calculate_shipping", "create_shipment", "track_package", "optimize_route", "get_rates"],
        capabilities=["shipping", "tracking", "route_optimization"],
        category="ricco",
    ),
    MCPServerConfig(
        id="mcp-ricco-health",
        name="RICCO Health MCP",
        description="Plataforma de salud",
        transport=MCPTransport.STDIO,
        command="npx",
        args=["-y", "@ricco/mcp-health"],
        env={
            "RICCO_HEALTH_URL": "${RICCO_HEALTH_URL}",
        },
        tools=["book_appointment", "get_medical_records", "set_reminder", "find_provider", "get_prescriptions"],
        capabilities=["healthcare", "appointments", "records"],
        category="ricco",
    ),
    MCPServerConfig(
        id="mcp-ricco-social",
        name="RICCO Social MCP",
        description="Red social y networking",
        transport=MCPTransport.STDIO,
        command="npx",
        args=["-y", "@ricco/mcp-social"],
        env={
            "RICCO_SOCIAL_URL": "${RICCO_SOCIAL_URL}",
        },
        tools=["get_feed", "create_post", "follow_user", "get_connections", "send_message", "moderate_content"],
        capabilities=["social_network", "content_management"],
        category="ricco",
    ),
    MCPServerConfig(
        id="mcp-ricco-funding",
        name="RICCO Funding MCP",
        description="Crowdfunding e inversiones",
        transport=MCPTransport.STDIO,
        command="npx",
        args=["-y", "@ricco/mcp-funding"],
        env={
            "RICCO_FUNDING_URL": "${RICCO_FUNDING_URL}",
        },
        tools=["list_projects", "invest", "create_campaign", "get_returns", "calculate_projection"],
        capabilities=["crowdfunding", "investments", "tokenomics"],
        category="ricco",
    ),
    MCPServerConfig(
        id="mcp-ricco-legal",
        name="RICCO Legal MCP",
        description="Servicios legales",
        transport=MCPTransport.STDIO,
        command="npx",
        args=["-y", "@ricco/mcp-legal"],
        env={
            "RICCO_LEGAL_URL": "${RICCO_LEGAL_URL}",
        },
        tools=["create_case", "get_documents", "schedule_consultation", "track_deadline", "generate_contract"],
        capabilities=["legal_services", "document_management"],
        category="ricco",
    ),
]


# ============================================
# DEVELOPMENT & DEVOPS MCP SERVERS
# ============================================

DEVOPS_MCPS: List[MCPServerConfig] = [
    MCPServerConfig(
        id="mcp-github",
        name="GitHub MCP",
        description="Integración con GitHub",
        transport=MCPTransport.STDIO,
        command="npx",
        args=["-y", "@modelcontextprotocol/server-github"],
        env={
            "GITHUB_TOKEN": "${GITHUB_TOKEN}",
        },
        tools=["create_repo", "create_issue", "create_pr", "get_file", "push_file", "search_code", "list_commits"],
        capabilities=["version_control", "ci_cd", "collaboration"],
        category="devops",
    ),
    MCPServerConfig(
        id="mcp-gitlab",
        name="GitLab MCP",
        description="Integración con GitLab",
        transport=MCPTransport.STDIO,
        command="npx",
        args=["-y", "@ricco/mcp-gitlab"],
        env={
            "GITLAB_TOKEN": "${GITLAB_TOKEN}",
            "GITLAB_URL": "${GITLAB_URL}",
        },
        tools=["create_project", "create_merge_request", "trigger_pipeline", "get_job_logs"],
        capabilities=["version_control", "ci_cd"],
        category="devops",
    ),
    MCPServerConfig(
        id="mcp-docker",
        name="Docker MCP",
        description="Gestión de contenedores Docker",
        transport=MCPTransport.STDIO,
        command="npx",
        args=["-y", "@ricco/mcp-docker"],
        env={
            "DOCKER_HOST": "unix:///var/run/docker.sock",
        },
        tools=["list_containers", "start_container", "stop_container", "get_logs", "execute_command", "build_image"],
        capabilities=["container_management", "deployment"],
        category="devops",
    ),
    MCPServerConfig(
        id="mcp-kubernetes",
        name="Kubernetes MCP",
        description="Gestión de clusters Kubernetes",
        transport=MCPTransport.STDIO,
        command="npx",
        args=["-y", "@ricco/mcp-kubernetes"],
        env={
            "KUBECONFIG": "${KUBECONFIG}",
        },
        tools=["list_pods", "get_pod_logs", "scale_deployment", "apply_manifest", "get_resources"],
        capabilities=["orchestration", "deployment", "scaling"],
        category="devops",
    ),
]


# ============================================
# MONITORING & OBSERVABILITY MCP SERVERS
# ============================================

MONITORING_MCPS: List[MCPServerConfig] = [
    MCPServerConfig(
        id="mcp-prometheus",
        name="Prometheus MCP",
        description="Monitoreo con Prometheus",
        transport=MCPTransport.STDIO,
        command="npx",
        args=["-y", "@ricco/mcp-prometheus"],
        env={
            "PROMETHEUS_URL": "${PROMETHEUS_URL}",
        },
        tools=["query", "query_range", "get_metrics", "get_alerts", "create_alert"],
        capabilities=["monitoring", "alerting", "metrics"],
        category="monitoring",
    ),
    MCPServerConfig(
        id="mcp-grafana",
        name="Grafana MCP",
        description="Dashboards con Grafana",
        transport=MCPTransport.STDIO,
        command="npx",
        args=["-y", "@ricco/mcp-grafana"],
        env={
            "GRAFANA_URL": "${GRAFANA_URL}",
            "GRAFANA_API_KEY": "${GRAFANA_API_KEY}",
        },
        tools=["get_dashboard", "create_dashboard", "get_panel_data", "create_alert"],
        capabilities=["visualization", "dashboards"],
        category="monitoring",
    ),
    MCPServerConfig(
        id="mcp-langfuse",
        name="Langfuse MCP",
        description="Observabilidad de LLM con Langfuse",
        transport=MCPTransport.STDIO,
        command="npx",
        args=["-y", "@ricco/mcp-langfuse"],
        env={
            "LANGFUSE_PUBLIC_KEY": "${LANGFUSE_PUBLIC_KEY}",
            "LANGFUSE_SECRET_KEY": "${LANGFUSE_SECRET_KEY}",
        },
        tools=["trace_completion", "get_traces", "create_score", "get_sessions"],
        capabilities=["llm_observability", "tracing", "evaluation"],
        category="monitoring",
    ),
]


# ============================================
# DOCUMENT PROCESSING MCP SERVERS
# ============================================

DOCUMENT_MCPS: List[MCPServerConfig] = [
    MCPServerConfig(
        id="mcp-pdf",
        name="PDF MCP",
        description="Procesamiento de PDFs",
        transport=MCPTransport.STDIO,
        command="npx",
        args=["-y", "@ricco/mcp-pdf"],
        tools=["extract_text", "extract_tables", "merge_pdfs", "split_pdf", "fill_form", "add_signature", "ocr"],
        capabilities=["pdf_processing", "ocr", "form_filling"],
        category="documents",
    ),
    MCPServerConfig(
        id="mcp-docx",
        name="DOCX MCP",
        description="Procesamiento de documentos Word",
        transport=MCPTransport.STDIO,
        command="npx",
        args=["-y", "@ricco/mcp-docx"],
        tools=["read_docx", "create_docx", "merge_docx", "extract_text", "add_comments", "track_changes"],
        capabilities=["document_creation", "collaboration"],
        category="documents",
    ),
    MCPServerConfig(
        id="mcp-xlsx",
        name="XLSX MCP",
        description="Procesamiento de hojas de cálculo",
        transport=MCPTransport.STDIO,
        command="npx",
        args=["-y", "@ricco/mcp-xlsx"],
        tools=["read_sheet", "write_sheet", "create_workbook", "add_formula", "create_chart", "convert_csv"],
        capabilities=["spreadsheet_management", "data_analysis"],
        category="documents",
    ),
]


# ============================================
# ALL MCP SERVERS COMPILATION
# ============================================

ALL_MCP_SERVERS: Dict[str, List[MCPServerConfig]] = {
    "filesystem": FILESYSTEM_MCPS,
    "database": DATABASE_MCPS,
    "web": WEB_MCPS,
    "ai": AI_MCPS,
    "productivity": PRODUCTIVITY_MCPS,
    "finance": FINANCE_MCPS,
    "ricco": RICCO_MCPS,
    "devops": DEVOPS_MCPS,
    "monitoring": MONITORING_MCPS,
    "documents": DOCUMENT_MCPS,
}


def get_mcp_servers_by_category(category: str) -> List[MCPServerConfig]:
    """Get MCP servers by category"""
    return ALL_MCP_SERVERS.get(category, [])


def get_all_mcp_servers() -> List[MCPServerConfig]:
    """Get all MCP servers"""
    all_servers = []
    for servers in ALL_MCP_SERVERS.values():
        all_servers.extend(servers)
    return all_servers


def get_mcp_server_by_id(server_id: str) -> Optional[MCPServerConfig]:
    """Get a specific MCP server by ID"""
    for servers in ALL_MCP_SERVERS.values():
        for server in servers:
            if server.id == server_id:
                return server
    return None


def get_mcp_servers_for_solution(solution: str) -> List[MCPServerConfig]:
    """Get recommended MCP servers for a RICCO solution"""
    solution_mcps = {
        "ricco-commerce": ["mcp-postgres", "mcp-redis", "mcp-ricco-commerce", "mcp-stripe", "mcp-qvapay"],
        "ricco-health": ["mcp-postgres", "mcp-ricco-health", "mcp-calendar", "mcp-email", "mcp-pdf"],
        "ricco-logistics": ["mcp-postgres", "mcp-ricco-logistics", "mcp-google-maps", "mcp-redis"],
        "ricco-funding": ["mcp-postgres", "mcp-ricco-funding", "mcp-stripe", "mcp-crypto"],
        "ricco-legal": ["mcp-postgres", "mcp-ricco-legal", "mcp-pdf", "mcp-docx", "mcp-email"],
        "ricco-social": ["mcp-mongodb", "mcp-ricco-social", "mcp-nebulagraph", "mcp-redis"],
        "ricco-connect": ["mcp-postgres", "mcp-mongodb", "mcp-email", "mcp-calendar"],
        "ricco-id": ["mcp-postgres", "mcp-ricco-id", "mcp-redis", "mcp-pdf"],
        "ricco-assets": ["mcp-s3-storage", "mcp-filesystem", "mcp-pdf"],
        "ricco-booking": ["mcp-postgres", "mcp-calendar", "mcp-google-maps", "mcp-stripe"],
        "ricco-gym": ["mcp-postgres", "mcp-calendar", "mcp-redis"],
        "ricco-pos": ["mcp-postgres", "mcp-redis", "mcp-stripe", "mcp-qvapay"],
        "ricco-cargo": ["mcp-postgres", "mcp-google-maps", "mcp-pdf", "mcp-email"],
        "ricco-travel": ["mcp-postgres", "mcp-calendar", "mcp-google-maps", "mcp-email"],
    }
    
    server_ids = solution_mcps.get(solution, [])
    servers = []
    for server_id in server_ids:
        server = get_mcp_server_by_id(server_id)
        if server:
            servers.append(server)
    
    # Always add AI MCPs
    servers.extend(AI_MCPS)
    
    return servers


# Total MCP servers count
TOTAL_MCP_SERVERS = sum(len(servers) for servers in ALL_MCP_SERVERS.values())
print(f"Total MCP Servers: {TOTAL_MCP_SERVERS}")

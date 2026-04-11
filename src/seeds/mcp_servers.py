"""
MCP Server Seeds for RICCO AI.

Database-managed MCP server configurations.
"""

from typing import Any, Dict, List

# MCP Server seed data
MCP_SERVER_SEEDS: List[Dict[str, Any]] = [
    # Filesystem Category
    {
        "name": "filesystem-local",
        "category": "filesystem",
        "transport": "stdio",
        "endpoint": "/usr/local/bin/mcp-filesystem",
        "description": "Local filesystem operations",
        "tools": [
            "file_read", "file_write", "file_delete", "file_copy",
            "directory_list", "directory_create",
        ],
        "capabilities": ["read", "write", "delete"],
        "metadata": {
            "version": "1.0.0",
            "weight": 100,
            "priority": 1,
        },
        "is_enabled": True,
    },
    {
        "name": "s3-storage",
        "category": "filesystem",
        "transport": "http",
        "endpoint": "http://mcp-s3:8080",
        "description": "S3-compatible object storage",
        "tools": [
            "s3_upload", "s3_download", "s3_list", "s3_delete",
        ],
        "capabilities": ["storage", "cdn"],
        "metadata": {
            "version": "1.0.0",
            "weight": 80,
        },
        "is_enabled": True,
    },
    
    # Database Category
    {
        "name": "postgresql-main",
        "category": "database",
        "transport": "http",
        "endpoint": "http://mcp-postgres:8080",
        "description": "PostgreSQL database operations",
        "tools": [
            "postgres_query", "postgres_execute", "postgres_transaction",
        ],
        "capabilities": ["sql", "transactions"],
        "metadata": {
            "version": "1.0.0",
            "weight": 100,
        },
        "is_enabled": True,
    },
    {
        "name": "redis-cache",
        "category": "database",
        "transport": "http",
        "endpoint": "http://mcp-redis:8080",
        "description": "Redis cache operations",
        "tools": [
            "redis_get", "redis_set", "redis_delete", "redis_pub", "redis_sub",
        ],
        "capabilities": ["cache", "pubsub"],
        "metadata": {
            "version": "1.0.0",
            "weight": 90,
        },
        "is_enabled": True,
    },
    {
        "name": "qdrant-vector",
        "category": "database",
        "transport": "http",
        "endpoint": "http://mcp-qdrant:8080",
        "description": "Qdrant vector database",
        "tools": [
            "qdrant_upsert", "qdrant_search", "qdrant_delete",
        ],
        "capabilities": ["vector", "embeddings"],
        "metadata": {
            "version": "1.0.0",
            "weight": 70,
        },
        "is_enabled": True,
    },
    
    # Web Category
    {
        "name": "web-fetcher",
        "category": "web",
        "transport": "http",
        "endpoint": "http://mcp-web:8080",
        "description": "Web content fetching and parsing",
        "tools": [
            "fetch_url", "fetch_json", "fetch_html",
            "web_search", "web_crawl",
        ],
        "capabilities": ["http", "scraping"],
        "metadata": {
            "version": "1.0.0",
            "weight": 80,
        },
        "is_enabled": True,
    },
    
    # AI Category
    {
        "name": "openai-provider",
        "category": "ai",
        "transport": "http",
        "endpoint": "http://mcp-openai:8080",
        "description": "OpenAI API integration",
        "tools": [
            "generate_text", "generate_chat", "generate_code",
            "embed_text", "embed_image",
        ],
        "capabilities": ["llm", "embeddings"],
        "metadata": {
            "version": "1.0.0",
            "weight": 100,
            "priority": 1,
        },
        "is_enabled": True,
    },
    {
        "name": "anthropic-provider",
        "category": "ai",
        "transport": "http",
        "endpoint": "http://mcp-anthropic:8080",
        "description": "Anthropic Claude API integration",
        "tools": [
            "generate_text", "generate_chat",
        ],
        "capabilities": ["llm"],
        "metadata": {
            "version": "1.0.0",
            "weight": 90,
        },
        "is_enabled": True,
    },
    
    # Finance Category
    {
        "name": "crypto-wallet",
        "category": "finance",
        "transport": "http",
        "endpoint": "http://mcp-crypto:8080",
        "description": "Cryptocurrency wallet operations",
        "tools": [
            "wallet_balance", "wallet_create", "wallet_transfer",
            "crypto_deposit", "crypto_withdraw",
        ],
        "capabilities": ["wallet", "crypto"],
        "metadata": {
            "version": "1.0.0",
            "weight": 100,
            "rate_limit_per_minute": 100,
        },
        "is_enabled": True,
    },
    {
        "name": "payment-processor",
        "category": "finance",
        "transport": "http",
        "endpoint": "http://mcp-payment:8080",
        "description": "Payment processing service",
        "tools": [
            "payment_create", "payment_verify", "payment_refund",
            "invoice_create", "invoice_send",
        ],
        "capabilities": ["payments", "invoices"],
        "metadata": {
            "version": "1.0.0",
            "weight": 100,
            "rate_limit_per_minute": 200,
        },
        "is_enabled": True,
    },
    
    # RICCO Category
    {
        "name": "ricco-core",
        "category": "ricco",
        "transport": "http",
        "endpoint": "http://ricco-api:8080",
        "description": "RICCO platform core services",
        "tools": [
            "energy_points_balance", "energy_points_transfer",
            "trust_score_get", "trust_score_update",
            "order_create", "order_get", "order_list",
            "user_profile_get", "user_profile_update",
        ],
        "capabilities": ["ricco", "energy_points", "trust_score"],
        "metadata": {
            "version": "1.0.0",
            "weight": 100,
            "priority": 1,
        },
        "is_enabled": True,
    },
    {
        "name": "ricco-identity",
        "category": "ricco",
        "transport": "http",
        "endpoint": "http://ricco-id:8080",
        "description": "RICCO identity and KYC services",
        "tools": [
            "kyc_status", "kyc_submit", "kyc_verify",
        ],
        "capabilities": ["identity", "kyc"],
        "metadata": {
            "version": "1.0.0",
            "weight": 90,
        },
        "is_enabled": True,
    },
    
    # Monitoring Category
    {
        "name": "metrics-collector",
        "category": "monitoring",
        "transport": "http",
        "endpoint": "http://mcp-metrics:8080",
        "description": "Metrics collection and querying",
        "tools": [
            "metrics_get", "metrics_query",
            "alerts_list", "alerts_create",
        ],
        "capabilities": ["metrics", "alerts"],
        "metadata": {
            "version": "1.0.0",
            "weight": 70,
        },
        "is_enabled": True,
    },
    
    # Documents Category
    {
        "name": "document-processor",
        "category": "documents",
        "transport": "http",
        "endpoint": "http://mcp-docs:8080",
        "description": "Document processing service",
        "tools": [
            "ocr_process", "convert_pdf", "extract_tables",
            "sign_document", "sign_verify",
        ],
        "capabilities": ["ocr", "pdf", "signing"],
        "metadata": {
            "version": "1.0.0",
            "weight": 80,
        },
        "is_enabled": True,
    },
    
    # Productivity Category
    {
        "name": "productivity-suite",
        "category": "productivity",
        "transport": "http",
        "endpoint": "http://mcp-productivity:8080",
        "description": "Productivity tools integration",
        "tools": [
            "calendar_event_create", "calendar_event_list",
            "email_send", "email_list",
            "task_create", "task_list",
        ],
        "capabilities": ["calendar", "email", "tasks"],
        "metadata": {
            "version": "1.0.0",
            "weight": 70,
        },
        "is_enabled": True,
    },
]


def get_servers_by_category(category: str) -> List[Dict[str, Any]]:
    """Get all servers in a category."""
    return [
        server for server in MCP_SERVER_SEEDS
        if server["category"] == category
    ]


def get_enabled_servers() -> List[Dict[str, Any]]:
    """Get all enabled servers."""
    return [
        server for server in MCP_SERVER_SEEDS
        if server.get("is_enabled", True)
    ]


def get_all_categories() -> List[str]:
    """Get all unique categories."""
    return list(set(server["category"] for server in MCP_SERVER_SEEDS))

"""
RICCO AI Monitoring Package
"""

from .metrics import (
    # HTTP Metrics
    HTTP_REQUESTS_TOTAL,
    HTTP_REQUEST_DURATION_SECONDS,
    HTTP_REQUESTS_IN_PROGRESS,
    
    # Agent Metrics
    AGENT_REQUESTS_TOTAL,
    AGENT_EXECUTION_DURATION_SECONDS,
    AGENT_ACTIVE_SESSIONS,
    AGENT_MEMORY_USAGE_BYTES,
    
    # MCP Metrics
    MCP_TOOL_INVOCATIONS_TOTAL,
    MCP_TOOL_DURATION_SECONDS,
    MCP_SERVER_CONNECTIONS,
    MCP_SERVER_HEALTH,
    
    # Rate Limiting Metrics
    RATE_LIMIT_TOTAL,
    RATE_LIMIT_ACTIVE_BLOCKS,
    
    # LLM Metrics
    LLM_REQUESTS_TOTAL,
    LLM_TOKENS_USED,
    LLM_REQUEST_DURATION_SECONDS,
    LLM_COST_TOTAL,
    
    # Vector Store Metrics
    VECTOR_STORE_OPERATIONS_TOTAL,
    VECTOR_STORE_OPERATION_DURATION_SECONDS,
    VECTOR_STORE_DOCUMENTS,
    
    # Queue Metrics
    QUEUE_MESSAGES_TOTAL,
    QUEUE_SIZE,
    QUEUE_PROCESSING_TIME_SECONDS,
    
    # Database Metrics
    DB_CONNECTIONS_ACTIVE,
    DB_QUERY_DURATION_SECONDS,
    DB_ERRORS_TOTAL,
    
    # System Metrics
    SYSTEM_INFO,
    SYSTEM_START_TIME,
    SYSTEM_UPTIME_SECONDS,
    
    # Functions
    track_http_request,
    track_agent_execution,
    track_mcp_tool,
    track_llm_request,
    record_llm_tokens,
    record_llm_cost,
    track_vector_store_operation,
    track_db_query,
    metrics_endpoint,
    init_metrics,
    HealthChecker,
    health_checker,
    MetricsRoute,
    RICCO_REGISTRY,
)

__all__ = [
    # HTTP
    "HTTP_REQUESTS_TOTAL",
    "HTTP_REQUEST_DURATION_SECONDS",
    "HTTP_REQUESTS_IN_PROGRESS",
    
    # Agent
    "AGENT_REQUESTS_TOTAL",
    "AGENT_EXECUTION_DURATION_SECONDS",
    "AGENT_ACTIVE_SESSIONS",
    "AGENT_MEMORY_USAGE_BYTES",
    
    # MCP
    "MCP_TOOL_INVOCATIONS_TOTAL",
    "MCP_TOOL_DURATION_SECONDS",
    "MCP_SERVER_CONNECTIONS",
    "MCP_SERVER_HEALTH",
    
    # Rate Limiting
    "RATE_LIMIT_TOTAL",
    "RATE_LIMIT_ACTIVE_BLOCKS",
    
    # LLM
    "LLM_REQUESTS_TOTAL",
    "LLM_TOKENS_USED",
    "LLM_REQUEST_DURATION_SECONDS",
    "LLM_COST_TOTAL",
    
    # Vector Store
    "VECTOR_STORE_OPERATIONS_TOTAL",
    "VECTOR_STORE_OPERATION_DURATION_SECONDS",
    "VECTOR_STORE_DOCUMENTS",
    
    # Queue
    "QUEUE_MESSAGES_TOTAL",
    "QUEUE_SIZE",
    "QUEUE_PROCESSING_TIME_SECONDS",
    
    # Database
    "DB_CONNECTIONS_ACTIVE",
    "DB_QUERY_DURATION_SECONDS",
    "DB_ERRORS_TOTAL",
    
    # System
    "SYSTEM_INFO",
    "SYSTEM_START_TIME",
    "SYSTEM_UPTIME_SECONDS",
    
    # Functions
    "track_http_request",
    "track_agent_execution",
    "track_mcp_tool",
    "track_llm_request",
    "record_llm_tokens",
    "record_llm_cost",
    "track_vector_store_operation",
    "track_db_query",
    "metrics_endpoint",
    "init_metrics",
    "HealthChecker",
    "health_checker",
    "MetricsRoute",
    "RICCO_REGISTRY",
]

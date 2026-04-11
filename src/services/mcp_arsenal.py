"""
MCP Arsenal - Model Context Protocol Tools Management
50+ MCP tools for RICCO AI
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from enum import Enum
from loguru import logger


class MCPToolCategory(str, Enum):
    FILESYSTEM = "filesystem"
    DATABASE = "database"
    WEB = "web"
    AI = "ai"
    FINANCE = "finance"
    RICCO = "ricco"
    DEVOPS = "devops"
    MONITORING = "monitoring"
    DOCUMENTS = "documents"
    PRODUCTIVITY = "productivity"


@dataclass
class MCPTool:
    name: str
    category: MCPToolCategory
    description: str
    server_command: str
    server_args: List[str] = field(default_factory=list)
    env_vars: Dict[str, str] = field(default_factory=dict)
    enabled: bool = True
    requires_auth: bool = False
    required_permissions: List[str] = field(default_factory=list)


DEFAULT_MCP_TOOLS = [
    # Filesystem
    MCPTool("mcp-filesystem", MCPToolCategory.FILESYSTEM, "Local filesystem", "npx", ["-y", "@modelcontextprotocol/server-filesystem", "/data"]),
    MCPTool("mcp-s3", MCPToolCategory.FILESYSTEM, "AWS S3 storage", "npx", ["-y", "@modelcontextprotocol/server-s3"], requires_auth=True),
    MCPTool("mcp-gdrive", MCPToolCategory.FILESYSTEM, "Google Drive", "npx", ["-y", "@modelcontextprotocol/server-gdrive"], requires_auth=True),
    
    # Database
    MCPTool("mcp-postgres", MCPToolCategory.DATABASE, "PostgreSQL", "npx", ["-y", "@modelcontextprotocol/server-postgres"], requires_auth=True),
    MCPTool("mcp-mongodb", MCPToolCategory.DATABASE, "MongoDB", "npx", ["-y", "@modelcontextprotocol/server-mongodb"], requires_auth=True),
    MCPTool("mcp-redis", MCPToolCategory.DATABASE, "Redis cache", "npx", ["-y", "@ricco/mcp-redis"], requires_auth=True),
    
    # Web
    MCPTool("mcp-fetch", MCPToolCategory.WEB, "Web fetching", "npx", ["-y", "@modelcontextprotocol/server-fetch"]),
    MCPTool("mcp-search", MCPToolCategory.WEB, "Web search", "npx", ["-y", "@modelcontextprotocol/server-brave-search"], requires_auth=True),
    MCPTool("mcp-puppeteer", MCPToolCategory.WEB, "Browser automation", "npx", ["-y", "@modelcontextprotocol/server-puppeteer"]),
    
    # AI
    MCPTool("mcp-openai", MCPToolCategory.AI, "OpenAI API", "npx", ["-y", "@ricco/mcp-openai"], requires_auth=True),
    MCPTool("mcp-openrouter", MCPToolCategory.AI, "OpenRouter multi-model", "npx", ["-y", "@ricco/mcp-openrouter"], requires_auth=True),
    MCPTool("mcp-ollama", MCPToolCategory.AI, "Local Ollama", "npx", ["-y", "@ricco/mcp-ollama"]),
    
    # Finance
    MCPTool("mcp-stripe", MCPToolCategory.FINANCE, "Stripe payments", "npx", ["-y", "@ricco/mcp-stripe"], requires_auth=True, required_permissions=["finance:write"]),
    MCPTool("mcp-qvapay", MCPToolCategory.FINANCE, "QvaPay gateway", "npx", ["-y", "@ricco/mcp-qvapay"], requires_auth=True),
    MCPTool("mcp-crypto", MCPToolCategory.FINANCE, "Cryptocurrency", "npx", ["-y", "@ricco/mcp-crypto"]),
    MCPTool("mcp-binance", MCPToolCategory.FINANCE, "Binance exchange", "npx", ["-y", "@ricco/mcp-binance"], requires_auth=True, required_permissions=["finance:trade"]),
    
    # RICCO
    MCPTool("mcp-ricco-id", MCPToolCategory.RICCO, "RICCO ID integration", "npx", ["-y", "@ricco/mcp-ricco-id"], requires_auth=True),
    MCPTool("mcp-ricco-commerce", MCPToolCategory.RICCO, "RICCO Commerce", "npx", ["-y", "@ricco/mcp-ricco-commerce"]),
    MCPTool("mcp-ricco-energy", MCPToolCategory.RICCO, "RICCO Energy", "npx", ["-y", "@ricco/mcp-ricco-energy"]),
    MCPTool("mcp-ricco-logistics", MCPToolCategory.RICCO, "RICCO Logistics", "npx", ["-y", "@ricco/mcp-ricco-logistics"]),
    
    # DevOps
    MCPTool("mcp-github", MCPToolCategory.DEVOPS, "GitHub operations", "npx", ["-y", "@modelcontextprotocol/server-github"], requires_auth=True),
    MCPTool("mcp-gitlab", MCPToolCategory.DEVOPS, "GitLab operations", "npx", ["-y", "@ricco/mcp-gitlab"], requires_auth=True),
    MCPTool("mcp-docker", MCPToolCategory.DEVOPS, "Docker containers", "npx", ["-y", "@ricco/mcp-docker"]),
    MCPTool("mcp-kubernetes", MCPToolCategory.DEVOPS, "Kubernetes", "npx", ["-y", "@ricco/mcp-kubernetes"]),
    
    # Monitoring
    MCPTool("mcp-prometheus", MCPToolCategory.MONITORING, "Prometheus metrics", "npx", ["-y", "@ricco/mcp-prometheus"]),
    MCPTool("mcp-grafana", MCPToolCategory.MONITORING, "Grafana dashboards", "npx", ["-y", "@ricco/mcp-grafana"], requires_auth=True),
    MCPTool("mcp-langfuse", MCPToolCategory.MONITORING, "Langfuse observability", "npx", ["-y", "@ricco/mcp-langfuse"], requires_auth=True),
    
    # Documents
    MCPTool("mcp-pdf", MCPToolCategory.DOCUMENTS, "PDF processing", "npx", ["-y", "@ricco/mcp-pdf"]),
    MCPTool("mcp-docx", MCPToolCategory.DOCUMENTS, "Word documents", "npx", ["-y", "@ricco/mcp-docx"]),
    MCPTool("mcp-xlsx", MCPToolCategory.DOCUMENTS, "Excel spreadsheets", "npx", ["-y", "@ricco/mcp-xlsx"]),
    
    # Productivity
    MCPTool("mcp-maps", MCPToolCategory.PRODUCTIVITY, "Google Maps", "npx", ["-y", "@ricco/mcp-google-maps"], requires_auth=True),
    MCPTool("mcp-calendar", MCPToolCategory.PRODUCTIVITY, "Calendar", "npx", ["-y", "@ricco/mcp-calendar"], requires_auth=True),
    MCPTool("mcp-email", MCPToolCategory.PRODUCTIVITY, "Email operations", "npx", ["-y", "@ricco/mcp-email"], requires_auth=True),
]


class MCPArsenal:
    """MCP Tools Manager for RICCO AI"""

    def __init__(self, max_concurrent: int = 10):
        self.max_concurrent = max_concurrent
        self._tools: Dict[str, MCPTool] = {t.name: t for t in DEFAULT_MCP_TOOLS}

    def get_tool(self, name: str) -> Optional[MCPTool]:
        return self._tools.get(name)

    def get_tools_by_category(self, category: MCPToolCategory) -> List[MCPTool]:
        return [t for t in self._tools.values() if t.category == category]

    def get_all_tools(self) -> List[MCPTool]:
        return list(self._tools.values())

    def get_enabled_tools(self) -> List[MCPTool]:
        return [t for t in self._tools.values() if t.enabled]

    def check_permissions(self, tool_name: str, user_permissions: List[str]) -> bool:
        tool = self.get_tool(tool_name)
        if not tool or not tool.requires_auth:
            return True
        return all(p in user_permissions for p in tool.required_permissions)

    def get_tools_for_user(self, user_permissions: List[str], solution_id: Optional[str] = None) -> List[MCPTool]:
        tools = [t for t in self.get_enabled_tools() if self.check_permissions(t.name, user_permissions)]
        
        if solution_id:
            from src.config.settings import RICCO_SOLUTIONS
            solution_mcps = RICCO_SOLUTIONS.get(solution_id, {}).get("mcps", [])
            if solution_mcps:
                tools = [t for t in tools if t.name in solution_mcps]
        
        return tools

    def to_mcp_config(self, tool_names: List[str]) -> Dict[str, Any]:
        return {
            "mcpServers": {
                name: {
                    "command": self._tools[name].server_command,
                    "args": self._tools[name].server_args,
                    "env": self._tools[name].env_vars
                }
                for name in tool_names if name in self._tools
            }
        }


_mcp_arsenal: Optional[MCPArsenal] = None


def get_mcp_arsenal() -> MCPArsenal:
    global _mcp_arsenal
    if _mcp_arsenal is None:
        from src.config.settings import settings
        _mcp_arsenal = MCPArsenal(max_concurrent=settings.MCP_MAX_CONCURRENT)
    return _mcp_arsenal

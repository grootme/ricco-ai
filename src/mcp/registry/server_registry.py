"""
MCP Server Registry for RICCO AI.

This module provides the central registry for MCP servers,
handling registration, discovery, health monitoring, and lifecycle management.

Adapted from genui/mcp_registry/server_registry.py for RICCO AI integration.
"""

import asyncio
from datetime import datetime
from typing import Any, Dict, List, Optional, Set
from enum import Enum
import logging
import uuid
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class MCPCategory(str, Enum):
    """MCP server categories."""
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


class TransportType(str, Enum):
    """MCP transport types."""
    STDIO = "stdio"
    HTTP = "http"
    GRPC = "grpc"
    WEBSOCKET = "websocket"


class HealthStatus(str, Enum):
    """Server health status."""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


class ServerCapability(BaseModel):
    """Server capability definition."""
    name: str
    version: str = "1.0.0"
    description: Optional[str] = None


class ServerMetadata(BaseModel):
    """Server metadata."""
    version: str = "1.0.0"
    weight: int = Field(default=100, ge=1, le=1000)
    priority: int = Field(default=0, ge=0, le=100)
    tags: List[str] = Field(default_factory=list)
    owner: Optional[str] = None
    documentation_url: Optional[str] = None
    custom: Dict[str, Any] = Field(default_factory=dict)


class MCPServer(BaseModel):
    """MCP Server model."""
    server_id: str
    name: str
    category: MCPCategory
    transport: TransportType
    endpoint: str
    tools: List[str] = Field(default_factory=list)
    capabilities: List[str] = Field(default_factory=list)
    metadata: ServerMetadata = Field(default_factory=ServerMetadata)
    
    # Health status
    health_status: HealthStatus = Field(default=HealthStatus.UNKNOWN)
    last_heartbeat: Optional[datetime] = None
    last_updated: datetime = Field(default_factory=datetime.utcnow)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Metrics
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    avg_latency_ms: float = 0.0
    
    # Status
    is_enabled: bool = True
    is_active: bool = True
    
    def is_available(self) -> bool:
        """Check if server is available for requests."""
        return (
            self.is_enabled and
            self.is_active and
            self.health_status in (HealthStatus.HEALTHY, HealthStatus.DEGRADED)
        )
    
    def get_health_score(self) -> float:
        """Get health score (0-100)."""
        if self.health_status == HealthStatus.HEALTHY:
            return 100.0
        elif self.health_status == HealthStatus.DEGRADED:
            return 50.0
        elif self.health_status == HealthStatus.UNHEALTHY:
            return 0.0
        return 25.0
    
    def update_heartbeat(self) -> None:
        """Update heartbeat timestamp."""
        self.last_heartbeat = datetime.utcnow()
    
    def record_request(self, success: bool, latency_ms: float) -> None:
        """Record a request result."""
        self.total_requests += 1
        if success:
            self.successful_requests += 1
        else:
            self.failed_requests += 1
        
        # Update rolling average latency
        if self.total_requests == 1:
            self.avg_latency_ms = latency_ms
        else:
            self.avg_latency_ms = (
                (self.avg_latency_ms * (self.total_requests - 1) + latency_ms) /
                self.total_requests
            )


class MCPServerCreate(BaseModel):
    """Model for creating a new MCP server."""
    name: str
    category: MCPCategory
    transport: TransportType
    endpoint: str
    tools: List[str] = Field(default_factory=list)
    capabilities: List[str] = Field(default_factory=list)
    metadata: Optional[ServerMetadata] = None


class MCPServerUpdate(BaseModel):
    """Model for updating an MCP server."""
    name: Optional[str] = None
    endpoint: Optional[str] = None
    tools: Optional[List[str]] = None
    capabilities: Optional[List[str]] = None
    metadata: Optional[ServerMetadata] = None
    health_status: Optional[HealthStatus] = None
    is_enabled: Optional[bool] = None
    is_active: Optional[bool] = None


class MCPServerSummary(BaseModel):
    """Summary view of an MCP server."""
    server_id: str
    name: str
    category: MCPCategory
    health_status: HealthStatus
    tool_count: int
    is_available: bool
    
    @classmethod
    def from_server(cls, server: MCPServer) -> "MCPServerSummary":
        return cls(
            server_id=server.server_id,
            name=server.name,
            category=server.category,
            health_status=server.health_status,
            tool_count=len(server.tools),
            is_available=server.is_available(),
        )


class HealthCheckConfig(BaseModel):
    """Health check configuration."""
    interval_seconds: int = Field(default=30, ge=5, le=300)
    timeout_seconds: int = Field(default=5, ge=1, le=30)
    heartbeat_timeout_seconds: int = Field(default=30, ge=10, le=120)


class RegistryConfig(BaseModel):
    """Registry configuration."""
    health_check: HealthCheckConfig = Field(default_factory=HealthCheckConfig)


class ServerRegistry:
    """
    Central registry for MCP servers.
    
    Manages the lifecycle of MCP server registrations including:
    - Registration and deregistration
    - Server discovery by category, tools, capabilities
    - Heartbeat and health tracking
    - Tool association management
    - Health monitoring and status updates
    """
    
    def __init__(self, config: Optional[RegistryConfig] = None):
        self.config = config or RegistryConfig()
        
        # Server storage
        self._servers: Dict[str, MCPServer] = {}
        self._servers_by_category: Dict[MCPCategory, Set[str]] = {
            cat: set() for cat in MCPCategory
        }
        self._servers_by_name: Dict[str, str] = {}
        
        # Tool associations
        self._server_tools: Dict[str, Set[str]] = {}
        self._tool_servers: Dict[str, str] = {}
        
        # Heartbeat tracking
        self._last_heartbeat: Dict[str, datetime] = {}
        
        # Health check task
        self._health_check_task: Optional[asyncio.Task] = None
        self._running = False
        
        # Event callbacks
        self._on_register_callbacks: List = []
        self._on_unregister_callbacks: List = []
        self._on_update_callbacks: List = []
        self._on_health_change_callbacks: List = []
    
    async def start(self) -> None:
        """Start the registry background tasks."""
        if self._running:
            return
        
        self._running = True
        self._health_check_task = asyncio.create_task(self._health_check_loop())
        logger.info("ServerRegistry started")
    
    async def stop(self) -> None:
        """Stop the registry background tasks."""
        self._running = False
        if self._health_check_task:
            self._health_check_task.cancel()
            try:
                await self._health_check_task
            except asyncio.CancelledError:
                pass
        logger.info("ServerRegistry stopped")
    
    async def register(
        self,
        server_create: MCPServerCreate,
        server_id: Optional[str] = None,
    ) -> MCPServer:
        """Register a new MCP server."""
        if server_id is None:
            server_id = self._generate_server_id(server_create.category)
        
        if server_create.name in self._servers_by_name:
            raise ValueError(f"Server with name '{server_create.name}' already exists")
        
        server = MCPServer(
            server_id=server_id,
            name=server_create.name,
            category=server_create.category,
            transport=server_create.transport,
            endpoint=server_create.endpoint,
            tools=server_create.tools,
            capabilities=server_create.capabilities,
            metadata=server_create.metadata or ServerMetadata(),
        )
        
        self._servers[server_id] = server
        self._servers_by_category[server_create.category].add(server_id)
        self._servers_by_name[server_create.name] = server_id
        self._server_tools[server_id] = set()
        self._last_heartbeat[server_id] = datetime.utcnow()
        
        logger.info(f"Registered MCP server: {server.name} ({server_id})")
        
        for callback in self._on_register_callbacks:
            try:
                await callback(server)
            except Exception as e:
                logger.exception(f"Callback error: {e}")
        
        return server
    
    async def unregister(self, server_id: str) -> bool:
        """Unregister an MCP server."""
        server = self._servers.get(server_id)
        if not server:
            return False
        
        self._servers.pop(server_id)
        self._servers_by_category[server.category].discard(server_id)
        self._servers_by_name.pop(server.name, None)
        
        for tool_id in self._server_tools.get(server_id, set()):
            self._tool_servers.pop(tool_id, None)
        self._server_tools.pop(server_id, None)
        self._last_heartbeat.pop(server_id, None)
        
        logger.info(f"Unregistered MCP server: {server.name} ({server_id})")
        
        for callback in self._on_unregister_callbacks:
            try:
                await callback(server)
            except Exception as e:
                logger.exception(f"Callback error: {e}")
        
        return True
    
    async def update(
        self,
        server_id: str,
        server_update: MCPServerUpdate,
    ) -> Optional[MCPServer]:
        """Update an existing MCP server registration."""
        server = self._servers.get(server_id)
        if not server:
            return None
        
        old_health = server.health_status
        
        update_data = server_update.model_dump(exclude_unset=True)
        
        for field, value in update_data.items():
            if hasattr(server, field):
                setattr(server, field, value)
        
        server.last_updated = datetime.utcnow()
        
        logger.info(f"Updated MCP server: {server.name} ({server_id})")
        
        for callback in self._on_update_callbacks:
            try:
                await callback(server)
            except Exception as e:
                logger.exception(f"Callback error: {e}")
        
        if old_health != server.health_status:
            for callback in self._on_health_change_callbacks:
                try:
                    await callback(server, old_health, server.health_status)
                except Exception as e:
                    logger.exception(f"Health change callback error: {e}")
        
        return server
    
    def get(self, server_id: str) -> Optional[MCPServer]:
        """Get a server by ID."""
        return self._servers.get(server_id)
    
    def get_by_name(self, name: str) -> Optional[MCPServer]:
        """Get a server by name."""
        server_id = self._servers_by_name.get(name)
        return self._servers.get(server_id) if server_id else None
    
    def get_by_category(
        self,
        category: MCPCategory,
        healthy_only: bool = False,
    ) -> List[MCPServer]:
        """Get all servers in a category."""
        servers = [
            self._servers[sid]
            for sid in self._servers_by_category.get(category, set())
            if sid in self._servers
        ]
        if healthy_only:
            servers = [s for s in servers if s.is_available()]
        return servers
    
    def get_all(
        self,
        category: Optional[MCPCategory] = None,
        healthy_only: bool = False,
    ) -> List[MCPServer]:
        """Get all servers, optionally filtered."""
        servers = list(self._servers.values())
        if category:
            servers = [s for s in servers if s.category == category]
        if healthy_only:
            servers = [s for s in servers if s.is_available()]
        return servers
    
    def get_summaries(
        self,
        category: Optional[MCPCategory] = None,
    ) -> List[MCPServerSummary]:
        """Get summary views of all servers."""
        return [
            MCPServerSummary.from_server(s)
            for s in self.get_all(category=category)
        ]
    
    def find_by_tool(self, tool_name: str) -> List[MCPServer]:
        """Find servers that provide a specific tool."""
        servers = []
        for server in self._servers.values():
            if tool_name in server.tools:
                servers.append(server)
        return servers
    
    def find_by_capability(
        self,
        capability: str,
        category: Optional[MCPCategory] = None,
    ) -> List[MCPServer]:
        """Find servers with a specific capability."""
        servers = []
        for server in self._servers.values():
            if capability in server.capabilities:
                if category is None or server.category == category:
                    servers.append(server)
        return servers
    
    def update_heartbeat(self, server_id: str) -> bool:
        """Update server heartbeat timestamp."""
        server = self._servers.get(server_id)
        if not server:
            return False
        
        server.update_heartbeat()
        self._last_heartbeat[server_id] = datetime.utcnow()
        return True
    
    def count(self, category: Optional[MCPCategory] = None) -> int:
        """Count registered servers."""
        if category:
            return len(self._servers_by_category.get(category, set()))
        return len(self._servers)
    
    def count_by_category(self) -> Dict[MCPCategory, int]:
        """Count servers per category."""
        return {
            cat: len(sids)
            for cat, sids in self._servers_by_category.items()
        }
    
    def on_register(self, callback) -> None:
        """Register a callback for server registration events."""
        self._on_register_callbacks.append(callback)
    
    def on_unregister(self, callback) -> None:
        """Register a callback for server unregistration events."""
        self._on_unregister_callbacks.append(callback)
    
    def on_update(self, callback) -> None:
        """Register a callback for server update events."""
        self._on_update_callbacks.append(callback)
    
    def on_health_change(self, callback) -> None:
        """Register a callback for health status changes."""
        self._on_health_change_callbacks.append(callback)
    
    def _generate_server_id(self, category: MCPCategory) -> str:
        """Generate a unique server ID."""
        return f"{category.value}-{uuid.uuid4().hex[:8]}"
    
    async def _health_check_loop(self) -> None:
        """Background task for health monitoring."""
        while self._running:
            try:
                await self._check_all_servers()
                await asyncio.sleep(self.config.health_check.interval_seconds)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.exception(f"Health check error: {e}")
                await asyncio.sleep(5)
    
    async def _check_all_servers(self) -> None:
        """Check health of all registered servers."""
        now = datetime.utcnow()
        timeout = self.config.health_check.heartbeat_timeout_seconds
        
        for server_id, server in list(self._servers.items()):
            last_hb = self._last_heartbeat.get(server_id)
            
            if last_hb:
                age = (now - last_hb).total_seconds()
                
                if age > timeout:
                    if server.health_status != HealthStatus.UNHEALTHY:
                        await self.update(
                            server_id,
                            MCPServerUpdate(health_status=HealthStatus.UNHEALTHY)
                        )
                        logger.warning(
                            f"Server {server.name} marked unhealthy (no heartbeat for {age:.0f}s)"
                        )
                elif age > timeout / 2:
                    if server.health_status == HealthStatus.HEALTHY:
                        await self.update(
                            server_id,
                            MCPServerUpdate(health_status=HealthStatus.DEGRADED)
                        )
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get registry statistics."""
        health_counts = {}
        for status in HealthStatus:
            health_counts[status.value] = len([
                s for s in self._servers.values()
                if s.health_status == status
            ])
        
        return {
            "total_servers": len(self._servers),
            "servers_by_category": {
                cat.value: len(sids)
                for cat, sids in self._servers_by_category.items()
            },
            "health_distribution": health_counts,
            "total_tools": len(self._tool_servers),
            "active_servers": len([
                s for s in self._servers.values() if s.is_available()
            ]),
        }


class ToolRiskLevel(str, Enum):
    """Tool risk levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ToolParameter(BaseModel):
    """Tool parameter definition."""
    name: str
    type: str
    description: Optional[str] = None
    required: bool = True
    default: Optional[Any] = None


class MCPToolCreate(BaseModel):
    """Model for creating a new MCP tool."""
    name: str
    display_name: str
    description: str
    category: str
    parameters: List[ToolParameter] = Field(default_factory=list)
    tags: List[str] = Field(default_factory=list)
    risk_level: ToolRiskLevel = ToolRiskLevel.LOW


class MCPToolSummary(BaseModel):
    """Summary view of an MCP tool."""
    tool_id: str
    name: str
    display_name: str
    category: str
    risk_level: ToolRiskLevel


class MCPTool(BaseModel):
    """MCP Tool model."""
    tool_id: str
    name: str
    display_name: str
    description: str
    category: str
    parameters: List[ToolParameter] = Field(default_factory=list)
    tags: List[str] = Field(default_factory=list)
    risk_level: ToolRiskLevel = ToolRiskLevel.LOW
    server_id: Optional[str] = None
    
    # Metrics
    total_invocations: int = 0
    successful_invocations: int = 0
    avg_latency_ms: float = 0.0
    
    @classmethod
    def from_create(cls, tool_id: str, tool_create: MCPToolCreate) -> "MCPTool":
        return cls(
            tool_id=tool_id,
            name=tool_create.name,
            display_name=tool_create.display_name,
            description=tool_create.description,
            category=tool_create.category,
            parameters=tool_create.parameters,
            tags=tool_create.tags,
            risk_level=tool_create.risk_level,
        )


class ToolsRegistry:
    """
    Registry for MCP tools.
    
    Manages tool definitions and their associations with servers.
    """
    
    def __init__(self):
        self._tools: Dict[str, MCPTool] = {}
        self._tools_by_name: Dict[str, str] = {}
        self._tools_by_category: Dict[str, Set[str]] = {}
    
    async def register(
        self,
        tool_create: MCPToolCreate,
        tool_id: Optional[str] = None,
    ) -> MCPTool:
        """Register a new tool."""
        if tool_id is None:
            tool_id = self._generate_tool_id(tool_create.category)
        
        if tool_create.name in self._tools_by_name:
            raise ValueError(f"Tool with name '{tool_create.name}' already exists")
        
        tool = MCPTool.from_create(tool_id, tool_create)
        
        self._tools[tool_id] = tool
        self._tools_by_name[tool_create.name] = tool_id
        
        if tool_create.category not in self._tools_by_category:
            self._tools_by_category[tool_create.category] = set()
        self._tools_by_category[tool_create.category].add(tool_id)
        
        logger.info(f"Registered tool: {tool.name} ({tool_id})")
        return tool
    
    async def unregister(self, tool_id: str) -> bool:
        """Unregister a tool."""
        tool = self._tools.get(tool_id)
        if not tool:
            return False
        
        self._tools.pop(tool_id)
        self._tools_by_name.pop(tool.name, None)
        
        if tool.category in self._tools_by_category:
            self._tools_by_category[tool.category].discard(tool_id)
        
        logger.info(f"Unregistered tool: {tool.name} ({tool_id})")
        return True
    
    def get(self, tool_id: str) -> Optional[MCPTool]:
        """Get a tool by ID."""
        return self._tools.get(tool_id)
    
    def get_by_name(self, name: str) -> Optional[MCPTool]:
        """Get a tool by name."""
        tool_id = self._tools_by_name.get(name)
        return self._tools.get(tool_id) if tool_id else None
    
    def get_by_category(self, category: str) -> List[MCPTool]:
        """Get all tools in a category."""
        tool_ids = self._tools_by_category.get(category, set())
        return [self._tools[tid] for tid in tool_ids if tid in self._tools]
    
    def get_all(self) -> List[MCPTool]:
        """Get all registered tools."""
        return list(self._tools.values())
    
    def get_summaries(self, category: Optional[str] = None) -> List[MCPToolSummary]:
        """Get summary views of all tools."""
        tools = self.get_all() if not category else self.get_by_category(category)
        return [
            MCPToolSummary(
                tool_id=t.tool_id,
                name=t.name,
                display_name=t.display_name,
                category=t.category,
                risk_level=t.risk_level,
            )
            for t in tools
        ]
    
    def _generate_tool_id(self, category: str) -> str:
        """Generate a unique tool ID."""
        return f"{category}-tool-{uuid.uuid4().hex[:8]}"
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get registry statistics."""
        total_invocations = sum(t.total_invocations for t in self._tools.values())
        successful_invocations = sum(t.successful_invocations for t in self._tools.values())
        
        return {
            "total_tools": len(self._tools),
            "tools_by_category": {
                cat: len(tids)
                for cat, tids in self._tools_by_category.items()
            },
            "total_invocations": total_invocations,
            "successful_invocations": successful_invocations,
            "success_rate": (
                (successful_invocations / total_invocations * 100)
                if total_invocations > 0 else 100
            ),
        }

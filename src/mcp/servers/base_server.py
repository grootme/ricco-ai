"""Base MCP Server for NVIDIA Blueprint integration.

Provides a base class for MCP servers with common functionality
for tool registration, execution, and transport handling.
"""

from __future__ import annotations

import asyncio
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, AsyncIterator
import uuid

logger = logging.getLogger(__name__)


class TransportType(str, Enum):
    """MCP transport types."""
    STDIO = "stdio"
    HTTP = "http"
    WEBSOCKET = "websocket"
    GRPC = "grpc"


class ServerStatus(str, Enum):
    """MCP server status."""
    INITIALIZING = "initializing"
    READY = "ready"
    BUSY = "busy"
    ERROR = "error"
    STOPPED = "stopped"


@dataclass
class MCPServerConfig:
    """Configuration for an MCP server."""
    server_id: str
    name: str
    description: str = ""
    version: str = "1.0.0"
    transport: TransportType = TransportType.STDIO
    host: str = "localhost"
    port: int = 8080
    max_concurrent_requests: int = 10
    timeout_seconds: int = 30
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class MCPToolDefinition:
    """Definition of an MCP tool."""
    tool_id: str
    name: str
    description: str
    input_schema: Dict[str, Any]
    output_schema: Dict[str, Any] = field(default_factory=dict)
    handler: Optional[Callable] = None
    category: str = "general"
    risk_level: str = "low"
    requires_consent: bool = False


class BaseMCPServer(ABC):
    """
    Base class for MCP servers.
    
    Provides common functionality for:
    - Tool registration and management
    - Request handling
    - Transport abstraction
    - Metrics collection
    """
    
    def __init__(self, config: MCPServerConfig):
        self.config = config
        self.status = ServerStatus.INITIALIZING
        self._tools: Dict[str, MCPToolDefinition] = {}
        self._active_requests: Dict[str, Any] = {}
        self._metrics = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "total_latency_ms": 0.0,
        }
        self._start_time: Optional[datetime] = None
        
    @property
    def server_id(self) -> str:
        return self.config.server_id
    
    @property
    def name(self) -> str:
        return self.config.name
    
    def register_tool(self, tool: MCPToolDefinition) -> None:
        """Register a tool with the server."""
        self._tools[tool.tool_id] = tool
        logger.info(f"Registered tool: {tool.name} ({tool.tool_id})")
    
    def register_tools(self, tools: List[MCPToolDefinition]) -> None:
        """Register multiple tools."""
        for tool in tools:
            self.register_tool(tool)
    
    def unregister_tool(self, tool_id: str) -> bool:
        """Unregister a tool."""
        if tool_id in self._tools:
            del self._tools[tool_id]
            logger.info(f"Unregistered tool: {tool_id}")
            return True
        return False
    
    def get_tool(self, tool_id: str) -> Optional[MCPToolDefinition]:
        """Get a tool by ID."""
        return self._tools.get(tool_id)
    
    def get_tool_by_name(self, name: str) -> Optional[MCPToolDefinition]:
        """Get a tool by name."""
        for tool in self._tools.values():
            if tool.name == name:
                return tool
        return None
    
    def list_tools(self, category: Optional[str] = None) -> List[MCPToolDefinition]:
        """List all tools, optionally filtered by category."""
        tools = list(self._tools.values())
        if category:
            tools = [t for t in tools if t.category == category]
        return tools
    
    def is_available(self) -> bool:
        """Check if the server is available for requests."""
        return self.status in [ServerStatus.READY, ServerStatus.BUSY]
    
    async def execute_tool(
        self,
        tool_name: str,
        arguments: Dict[str, Any],
        request_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Execute a tool by name.
        
        Args:
            tool_name: Name of the tool to execute.
            arguments: Arguments for the tool.
            request_id: Optional request ID for tracking.
            
        Returns:
            Dictionary with execution result.
        """
        import time
        
        request_id = request_id or str(uuid.uuid4())[:8]
        start_time = time.time()
        
        self._metrics["total_requests"] += 1
        self._active_requests[request_id] = {
            "tool_name": tool_name,
            "started_at": datetime.utcnow().isoformat(),
        }
        
        try:
            tool = self.get_tool_by_name(tool_name)
            if not tool:
                return {
                    "success": False,
                    "error": f"Tool not found: {tool_name}",
                    "error_code": "TOOL_NOT_FOUND",
                }
            
            if tool.handler is None:
                return {
                    "success": False,
                    "error": f"Tool has no handler: {tool_name}",
                    "error_code": "NO_HANDLER",
                }
            
            # Execute the tool handler
            if asyncio.iscoroutinefunction(tool.handler):
                result = await tool.handler(**arguments)
            else:
                result = tool.handler(**arguments)
            
            execution_time_ms = (time.time() - start_time) * 1000
            self._metrics["successful_requests"] += 1
            self._metrics["total_latency_ms"] += execution_time_ms
            
            return {
                "success": True,
                "result": result,
                "tool_name": tool_name,
                "execution_time_ms": execution_time_ms,
                "request_id": request_id,
            }
            
        except Exception as e:
            self._metrics["failed_requests"] += 1
            logger.exception(f"Error executing tool {tool_name}")
            return {
                "success": False,
                "error": str(e),
                "error_code": "EXECUTION_ERROR",
                "tool_name": tool_name,
                "request_id": request_id,
            }
            
        finally:
            self._active_requests.pop(request_id, None)
    
    async def start(self) -> None:
        """Start the MCP server."""
        self._start_time = datetime.utcnow()
        self.status = ServerStatus.READY
        logger.info(f"MCP Server {self.name} started")
    
    async def stop(self) -> None:
        """Stop the MCP server."""
        self.status = ServerStatus.STOPPED
        logger.info(f"MCP Server {self.name} stopped")
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get server metrics."""
        uptime = None
        if self._start_time:
            uptime = (datetime.utcnow() - self._start_time).total_seconds()
        
        avg_latency = (
            self._metrics["total_latency_ms"] / self._metrics["successful_requests"]
            if self._metrics["successful_requests"] > 0 else 0
        )
        
        return {
            "server_id": self.server_id,
            "server_name": self.name,
            "status": self.status.value,
            "uptime_seconds": uptime,
            "tools_registered": len(self._tools),
            "active_requests": len(self._active_requests),
            "metrics": {
                **self._metrics,
                "avg_latency_ms": avg_latency,
                "success_rate": (
                    self._metrics["successful_requests"] / self._metrics["total_requests"] * 100
                    if self._metrics["total_requests"] > 0 else 100
                ),
            },
        }
    
    def get_health(self) -> Dict[str, Any]:
        """Get server health status."""
        return {
            "server_id": self.server_id,
            "server_name": self.name,
            "status": self.status.value,
            "is_available": self.is_available(),
            "tools_available": len(self._tools),
            "active_requests": len(self._active_requests),
        }
    
    @abstractmethod
    def get_tool_definitions(self) -> List[MCPToolDefinition]:
        """Get tool definitions for this server. Must be implemented by subclasses."""
        pass
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize server to dictionary."""
        return {
            "server_id": self.server_id,
            "name": self.name,
            "description": self.config.description,
            "version": self.config.version,
            "transport": self.config.transport.value,
            "status": self.status.value,
            "tools": [t.tool_id for t in self._tools.values()],
        }

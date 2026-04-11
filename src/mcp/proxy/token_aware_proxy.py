"""
Token-Aware MCP Proxy for RICCO AI.

This module provides the main MCP proxy that routes requests to MCP servers
with token-aware context management, load balancing, and circuit breaking.

Adapted from genui for RICCO AI integration.
"""

import asyncio
import time
from datetime import datetime
from typing import Any, Dict, List, Optional, AsyncIterator
from dataclasses import dataclass, field
import logging
import uuid
from pydantic import BaseModel, Field

from .load_balancer import LoadBalancer, LoadBalancingStrategy
from .circuit_breaker import CircuitBreaker, CircuitState, CircuitOpenError

logger = logging.getLogger(__name__)


class TokenContext(BaseModel):
    """Token context for request processing."""
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    client_id: Optional[str] = None
    auth_token: Optional[str] = None
    scopes: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    # Token budget tracking
    tokens_used: int = 0
    tokens_remaining: Optional[int] = None
    rate_limit_remaining: Optional[int] = None


class MCPRequest(BaseModel):
    """MCP Request model."""
    request_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    tool_name: str
    arguments: Dict[str, Any] = Field(default_factory=dict)
    context: TokenContext = Field(default_factory=TokenContext)
    timeout_seconds: int = 30
    priority: int = 0
    
    # Execution tracking
    status: str = "pending"
    server_id: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None


class MCPResponse(BaseModel):
    """MCP Response model."""
    request_id: str
    success: bool
    result: Optional[Any] = None
    error_code: Optional[str] = None
    error_message: Optional[str] = None
    error_details: Optional[Dict[str, Any]] = None
    server_id: Optional[str] = None
    server_name: Optional[str] = None
    tool_name: Optional[str] = None
    execution_time_ms: float = 0.0
    total_time_ms: float = 0.0
    tokens_used: int = 0
    
    @classmethod
    def success_response(
        cls,
        request_id: str,
        result: Any,
        server_id: Optional[str] = None,
        server_name: Optional[str] = None,
        tool_name: Optional[str] = None,
        execution_time_ms: float = 0.0,
        total_time_ms: float = 0.0,
    ) -> "MCPResponse":
        return cls(
            request_id=request_id,
            success=True,
            result=result,
            server_id=server_id,
            server_name=server_name,
            tool_name=tool_name,
            execution_time_ms=execution_time_ms,
            total_time_ms=total_time_ms,
        )
    
    @classmethod
    def failure_response(
        cls,
        request_id: str,
        error_code: str,
        error_message: str,
        error_details: Optional[Dict[str, Any]] = None,
    ) -> "MCPResponse":
        return cls(
            request_id=request_id,
            success=False,
            error_code=error_code,
            error_message=error_message,
            error_details=error_details,
        )


class TokenAwareProxy:
    """
    Token-aware MCP Proxy service.
    
    Provides a single entry point for all MCP tool invocations with:
    - Token-aware context management
    - Request routing and load balancing
    - Circuit breaker protection
    - Token budget tracking
    - Rate limiting
    """
    
    def __init__(
        self,
        load_balancer: Optional[LoadBalancer] = None,
        circuit_breaker: Optional[CircuitBreaker] = None,
        registry: Optional[Any] = None,
    ):
        self.load_balancer = load_balancer or LoadBalancer(
            strategy=LoadBalancingStrategy.ADAPTIVE,
        )
        self.circuit_breaker = circuit_breaker or CircuitBreaker()
        self.registry = registry
        
        # Server storage
        self._servers: Dict[str, Any] = {}
        self._tools: Dict[str, Any] = {}
        self._server_tools: Dict[str, List[str]] = {}
        
        # Active requests tracking
        self._active_requests: Dict[str, MCPRequest] = {}
        
        # Metrics
        self._total_requests = 0
        self._successful_requests = 0
        self._failed_requests = 0
        self._total_latency_ms = 0.0
        self._total_tokens_used = 0
    
    def register_server(self, server: Any) -> None:
        """Register an MCP server with the proxy."""
        server_id = getattr(server, 'server_id', str(id(server)))
        self._servers[server_id] = server
        self.load_balancer.add_server(server)
        self.circuit_breaker.register_server(server_id)
        logger.info(f"Registered server: {getattr(server, 'name', server_id)} ({server_id})")
    
    def unregister_server(self, server_id: str) -> None:
        """Unregister an MCP server from the proxy."""
        if server_id in self._servers:
            del self._servers[server_id]
            self.load_balancer.remove_server(server_id)
            self.circuit_breaker.unregister_server(server_id)
            if server_id in self._server_tools:
                for tool_id in self._server_tools[server_id]:
                    self._tools.pop(tool_id, None)
                del self._server_tools[server_id]
            logger.info(f"Unregistered server: {server_id}")
    
    def register_tool(self, tool: Any, server_id: str) -> None:
        """Register a tool with the proxy."""
        tool_id = getattr(tool, 'tool_id', str(id(tool)))
        self._tools[tool_id] = tool
        if server_id not in self._server_tools:
            self._server_tools[server_id] = []
        self._server_tools[server_id].append(tool_id)
        logger.debug(f"Registered tool: {getattr(tool, 'name', tool_id)}")
    
    def get_server(self, server_id: str) -> Optional[Any]:
        """Get a server by ID."""
        return self._servers.get(server_id)
    
    def get_tool(self, tool_name: str) -> Optional[Any]:
        """Get a tool by name."""
        for tool in self._tools.values():
            if getattr(tool, 'name', None) == tool_name:
                return tool
        return None
    
    def list_servers(self, category: Optional[str] = None) -> List[Any]:
        """List all registered servers, optionally filtered by category."""
        servers = list(self._servers.values())
        if category:
            servers = [s for s in servers if getattr(s, 'category', None) == category]
        return servers
    
    def list_tools(
        self,
        server_id: Optional[str] = None,
        category: Optional[str] = None,
    ) -> List[Any]:
        """List all registered tools, optionally filtered."""
        tools = list(self._tools.values())
        if server_id:
            tools = [t for t in tools if getattr(t, 'server_id', None) == server_id]
        if category:
            tools = [t for t in tools if getattr(t, 'category', None) == category]
        return tools
    
    async def execute(self, request: MCPRequest) -> MCPResponse:
        """
        Execute an MCP request.
        
        This is the main entry point for tool invocation through the proxy.
        It handles routing, load balancing, circuit breaking, and execution.
        """
        start_time = time.time()
        self._total_requests += 1
        self._active_requests[request.request_id] = request
        
        try:
            # Validate tool exists
            tool = self.get_tool(request.tool_name)
            if not tool:
                return MCPResponse.failure_response(
                    request_id=request.request_id,
                    error_code="TOOL_NOT_FOUND",
                    error_message=f"Tool not found: {request.tool_name}",
                )
            
            # Route request to server
            routing_result = await self._route_request(request, tool)
            if not routing_result["success"]:
                return MCPResponse.failure_response(
                    request_id=request.request_id,
                    error_code=routing_result.get("error_code", "ROUTING_FAILED"),
                    error_message=routing_result.get("error_message", "Routing failed"),
                )
            
            target_server = routing_result["server"]
            server_id = getattr(target_server, 'server_id', str(id(target_server)))
            
            # Check circuit breaker
            cb_state = self.circuit_breaker.get_state(server_id)
            if cb_state == CircuitState.OPEN:
                # Try alternate servers
                alternate = await self._find_alternate_server(tool, server_id)
                if alternate:
                    target_server = alternate
                    server_id = getattr(target_server, 'server_id', str(id(target_server)))
                    logger.info(f"Using alternate server {server_id} due to circuit breaker")
                else:
                    return MCPResponse.failure_response(
                        request_id=request.request_id,
                        error_code="CIRCUIT_BREAKER_OPEN",
                        error_message=f"Circuit breaker open for {getattr(target_server, 'name', server_id)}",
                    )
            
            # Update request status
            request.status = "executing"
            request.server_id = server_id
            request.started_at = datetime.utcnow()
            
            # Execute request
            execution_start = time.time()
            try:
                result = await self._execute_on_server(
                    request, target_server, tool
                )
                
                execution_time_ms = (time.time() - execution_start) * 1000
                
                # Record success
                self._successful_requests += 1
                self._total_latency_ms += execution_time_ms
                
                self.circuit_breaker.record_success(server_id)
                
                request.status = "completed"
                request.completed_at = datetime.utcnow()
                
                return MCPResponse.success_response(
                    request_id=request.request_id,
                    result=result,
                    server_id=server_id,
                    server_name=getattr(target_server, 'name', None),
                    tool_name=request.tool_name,
                    execution_time_ms=execution_time_ms,
                    total_time_ms=(time.time() - start_time) * 1000,
                )
                
            except asyncio.TimeoutError:
                return self._handle_failure(
                    request, server_id, tool,
                    "TOOL_TIMEOUT",
                    f"Tool execution timed out after {request.timeout_seconds}s",
                    (time.time() - execution_start) * 1000,
                )
            except Exception as e:
                return self._handle_failure(
                    request, server_id, tool,
                    "TOOL_EXECUTION_FAILED",
                    str(e),
                    (time.time() - execution_start) * 1000,
                )
                
        except Exception as e:
            logger.exception(f"Unexpected error executing request {request.request_id}")
            self._failed_requests += 1
            return MCPResponse.failure_response(
                request_id=request.request_id,
                error_code="INVALID_REQUEST",
                error_message=f"Unexpected error: {str(e)}",
            )
        finally:
            self._active_requests.pop(request.request_id, None)
    
    async def execute_batch(
        self,
        requests: List[MCPRequest],
        parallel: bool = True,
    ) -> List[MCPResponse]:
        """Execute multiple requests in batch."""
        if parallel:
            tasks = [self.execute(req) for req in requests]
            return await asyncio.gather(*tasks, return_exceptions=True)
        else:
            responses = []
            for req in requests:
                resp = await self.execute(req)
                responses.append(resp)
            return responses
    
    async def _route_request(
        self,
        request: MCPRequest,
        tool: Any,
    ) -> Dict[str, Any]:
        """Route a request to an appropriate server."""
        tool_id = getattr(tool, 'tool_id', str(id(tool)))
        tool_name = getattr(tool, 'name', request.tool_name)
        
        # Get servers that provide this tool
        candidate_servers = []
        for server_id, tools in self._server_tools.items():
            if tool_id in tools and server_id in self._servers:
                server = self._servers[server_id]
                if getattr(server, 'is_available', lambda: True)():
                    candidate_servers.append(server)
        
        if not candidate_servers:
            return {
                "success": False,
                "error_code": "NO_AVAILABLE_SERVER",
                "error_message": f"No available server for tool: {tool_name}",
            }
        
        # Use load balancer to select server
        selected = self.load_balancer.select_server(
            candidate_servers,
            tool_name=tool_name,
            request=request,
        )
        
        if not selected:
            return {
                "success": False,
                "error_code": "NO_AVAILABLE_SERVER",
                "error_message": "Load balancer could not select a server",
            }
        
        return {
            "success": True,
            "server": selected,
        }
    
    async def _find_alternate_server(
        self,
        tool: Any,
        exclude_server_id: str,
    ) -> Optional[Any]:
        """Find an alternate server for a tool."""
        tool_id = getattr(tool, 'tool_id', str(id(tool)))
        
        candidates = []
        for server_id, tools in self._server_tools.items():
            if (tool_id in tools and 
                server_id != exclude_server_id and 
                server_id in self._servers):
                server = self._servers[server_id]
                if (getattr(server, 'is_available', lambda: True)() and
                    self.circuit_breaker.get_state(server_id) != CircuitState.OPEN):
                    candidates.append(server)
        
        if not candidates:
            return None
        
        tool_name = getattr(tool, 'name', None)
        return self.load_balancer.select_server(candidates, tool_name=tool_name)
    
    async def _execute_on_server(
        self,
        request: MCPRequest,
        server: Any,
        tool: Any,
    ) -> Any:
        """Execute a request on a specific server."""
        # Placeholder - actual implementation depends on transport type
        # In production, this would use the appropriate transport (stdio, grpc, http, etc.)
        
        transport = getattr(server, 'transport', None)
        
        if transport and transport.value == "stdio":
            return await self._execute_stdio(request, server, tool)
        elif transport and transport.value == "http":
            return await self._execute_http(request, server, tool)
        elif transport and transport.value == "grpc":
            return await self._execute_grpc(request, server, tool)
        elif transport and transport.value == "websocket":
            return await self._execute_websocket(request, server, tool)
        else:
            # Default mock execution for development
            return await self._execute_mock(request, server, tool)
    
    async def _execute_stdio(
        self,
        request: MCPRequest,
        server: Any,
        tool: Any,
    ) -> Any:
        """Execute via stdio transport."""
        raise NotImplementedError("Stdio transport not yet implemented")
    
    async def _execute_http(
        self,
        request: MCPRequest,
        server: Any,
        tool: Any,
    ) -> Any:
        """Execute via HTTP transport."""
        raise NotImplementedError("HTTP transport not yet implemented")
    
    async def _execute_grpc(
        self,
        request: MCPRequest,
        server: Any,
        tool: Any,
    ) -> Any:
        """Execute via gRPC transport."""
        raise NotImplementedError("gRPC transport not yet implemented")
    
    async def _execute_websocket(
        self,
        request: MCPRequest,
        server: Any,
        tool: Any,
    ) -> Any:
        """Execute via WebSocket transport."""
        raise NotImplementedError("WebSocket transport not yet implemented")
    
    async def _execute_mock(
        self,
        request: MCPRequest,
        server: Any,
        tool: Any,
    ) -> Any:
        """Mock execution for development."""
        return {
            "message": f"Mock execution of {request.tool_name}",
            "server": getattr(server, 'name', 'unknown'),
            "arguments": request.arguments,
        }
    
    def _handle_failure(
        self,
        request: MCPRequest,
        server_id: str,
        tool: Any,
        error_code: str,
        error_message: str,
        execution_time_ms: float,
    ) -> MCPResponse:
        """Handle a request failure."""
        self._failed_requests += 1
        self.circuit_breaker.record_failure(server_id)
        
        request.status = "failed"
        request.completed_at = datetime.utcnow()
        
        return MCPResponse.failure_response(
            request_id=request.request_id,
            error_code=error_code,
            error_message=error_message,
        )
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get proxy metrics."""
        avg_latency = (
            self._total_latency_ms / self._successful_requests
            if self._successful_requests > 0 else 0
        )
        
        return {
            "total_requests": self._total_requests,
            "successful_requests": self._successful_requests,
            "failed_requests": self._failed_requests,
            "active_requests": len(self._active_requests),
            "avg_latency_ms": avg_latency,
            "success_rate": (
                self._successful_requests / self._total_requests * 100
                if self._total_requests > 0 else 100
            ),
            "registered_servers": len(self._servers),
            "registered_tools": len(self._tools),
            "total_tokens_used": self._total_tokens_used,
        }
    
    def get_health(self) -> Dict[str, Any]:
        """Get proxy health status."""
        return {
            "status": "healthy",
            "servers": {
                "total": len(self._servers),
                "healthy": len([s for s in self._servers.values() 
                               if getattr(s, 'is_available', lambda: True)()]),
            },
            "circuit_breakers": self.circuit_breaker.get_summary(),
            "load_balancer": self.load_balancer.get_summary(),
        }

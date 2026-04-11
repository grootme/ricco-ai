"""
Tool Registry for RICCO AI MCP.

Provides tool discovery and registration capabilities.
"""

from typing import Any, Dict, List, Optional, Set
from datetime import datetime
import logging
from pydantic import BaseModel, Field
import uuid

from .server_registry import (
    MCPTool,
    MCPToolCreate,
    MCPToolSummary,
    ToolParameter,
    ToolRiskLevel,
)

logger = logging.getLogger(__name__)


class ToolDiscoveryResult(BaseModel):
    """Result of a tool discovery query."""
    tools: List[MCPTool]
    total_count: int
    query: str
    filters: Dict[str, Any] = Field(default_factory=dict)


class ToolDiscoveryService:
    """
    Service for discovering and searching MCP tools.
    
    Provides:
    - Full-text search across tool names and descriptions
    - Category-based filtering
    - Risk level filtering
    - Tag-based filtering
    """
    
    def __init__(self, tools_registry: "ToolRegistry"):
        self._registry = tools_registry
    
    def search(
        self,
        query: str,
        category: Optional[str] = None,
        tags: Optional[List[str]] = None,
        risk_level: Optional[ToolRiskLevel] = None,
        server_id: Optional[str] = None,
        limit: int = 100,
    ) -> ToolDiscoveryResult:
        """
        Search for tools by various criteria.
        
        Args:
            query: Search query string
            category: Filter by category
            tags: Filter by tags (any match)
            risk_level: Filter by risk level
            server_id: Filter by server ID
            limit: Maximum results to return
            
        Returns:
            ToolDiscoveryResult with matching tools
        """
        tools = self._registry.get_all()
        query_lower = query.lower()
        
        results = []
        for tool in tools:
            # Category filter
            if category and tool.category != category:
                continue
            
            # Tags filter
            if tags and not any(tag in tool.tags for tag in tags):
                continue
            
            # Risk level filter
            if risk_level and tool.risk_level != risk_level:
                continue
            
            # Server filter
            if server_id and tool.server_id != server_id:
                continue
            
            # Query match
            if query:
                if not (
                    query_lower in tool.name.lower() or
                    query_lower in tool.display_name.lower() or
                    query_lower in tool.description.lower()
                ):
                    continue
            
            results.append(tool)
        
        return ToolDiscoveryResult(
            tools=results[:limit],
            total_count=len(results),
            query=query,
            filters={
                "category": category,
                "tags": tags,
                "risk_level": risk_level.value if risk_level else None,
                "server_id": server_id,
            },
        )
    
    def get_popular_tools(self, limit: int = 10) -> List[MCPTool]:
        """Get most popular tools by invocation count."""
        tools = self._registry.get_all()
        return sorted(
            tools,
            key=lambda t: t.total_invocations,
            reverse=True
        )[:limit]
    
    def get_tools_by_server(self, server_id: str) -> List[MCPTool]:
        """Get all tools provided by a specific server."""
        return [
            t for t in self._registry.get_all()
            if t.server_id == server_id
        ]


class ToolRegistry:
    """
    Central registry for MCP tools with persistence support.
    
    Extends the basic ToolsRegistry with:
    - Database-backed persistence
    - Bulk operations
    - Tool versioning
    """
    
    def __init__(self):
        self._tools: Dict[str, MCPTool] = {}
        self._tools_by_name: Dict[str, str] = {}
        self._tools_by_category: Dict[str, Set[str]] = {}
        self._tools_by_server: Dict[str, Set[str]] = {}
    
    async def register(
        self,
        tool_create: MCPToolCreate,
        tool_id: Optional[str] = None,
        server_id: Optional[str] = None,
    ) -> MCPTool:
        """Register a new tool with optional server binding."""
        if tool_id is None:
            tool_id = self._generate_tool_id(tool_create.category)
        
        if tool_create.name in self._tools_by_name:
            raise ValueError(f"Tool with name '{tool_create.name}' already exists")
        
        tool = MCPTool.from_create(tool_id, tool_create)
        tool.server_id = server_id
        
        self._tools[tool_id] = tool
        self._tools_by_name[tool_create.name] = tool_id
        
        if tool_create.category not in self._tools_by_category:
            self._tools_by_category[tool_create.category] = set()
        self._tools_by_category[tool_create.category].add(tool_id)
        
        if server_id:
            if server_id not in self._tools_by_server:
                self._tools_by_server[server_id] = set()
            self._tools_by_server[server_id].add(tool_id)
        
        logger.info(f"Registered tool: {tool.name} ({tool_id}) for server {server_id}")
        return tool
    
    async def register_batch(
        self,
        tools: List[MCPToolCreate],
        server_id: Optional[str] = None,
    ) -> List[MCPTool]:
        """Register multiple tools at once."""
        registered = []
        for tool_create in tools:
            try:
                tool = await self.register(tool_create, server_id=server_id)
                registered.append(tool)
            except ValueError as e:
                logger.warning(f"Skipping tool registration: {e}")
        return registered
    
    async def unregister(self, tool_id: str) -> bool:
        """Unregister a tool."""
        tool = self._tools.get(tool_id)
        if not tool:
            return False
        
        self._tools.pop(tool_id)
        self._tools_by_name.pop(tool.name, None)
        
        if tool.category in self._tools_by_category:
            self._tools_by_category[tool.category].discard(tool_id)
        
        if tool.server_id and tool.server_id in self._tools_by_server:
            self._tools_by_server[tool.server_id].discard(tool_id)
        
        logger.info(f"Unregistered tool: {tool.name} ({tool_id})")
        return True
    
    async def unregister_by_server(self, server_id: str) -> int:
        """Unregister all tools from a server."""
        tool_ids = list(self._tools_by_server.get(server_id, set()))
        count = 0
        for tool_id in tool_ids:
            if await self.unregister(tool_id):
                count += 1
        return count
    
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
    
    def get_by_server(self, server_id: str) -> List[MCPTool]:
        """Get all tools for a server."""
        tool_ids = self._tools_by_server.get(server_id, set())
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
    
    def count(self) -> int:
        """Count registered tools."""
        return len(self._tools)
    
    def count_by_category(self) -> Dict[str, int]:
        """Count tools per category."""
        return {
            cat: len(tids)
            for cat, tids in self._tools_by_category.items()
        }
    
    def count_by_server(self) -> Dict[str, int]:
        """Count tools per server."""
        return {
            server_id: len(tids)
            for server_id, tids in self._tools_by_server.items()
        }
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get registry statistics."""
        total_invocations = sum(t.total_invocations for t in self._tools.values())
        successful_invocations = sum(t.successful_invocations for t in self._tools.values())
        
        return {
            "total_tools": len(self._tools),
            "tools_by_category": self.count_by_category(),
            "tools_by_server": self.count_by_server(),
            "total_invocations": total_invocations,
            "successful_invocations": successful_invocations,
            "success_rate": (
                (successful_invocations / total_invocations * 100)
                if total_invocations > 0 else 100
            ),
        }

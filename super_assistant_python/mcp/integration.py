"""
Integración MCP (Model Context Protocol) para Skills.
Implementa MCP Direct y MCP Proxy patterns.
"""

from typing import Any, Dict, List, Optional, Callable, Union, Awaitable
from abc import ABC, abstractmethod
from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum
from dataclasses import dataclass
import asyncio
import json


# =============================================================================
# MODELOS MCP
# =============================================================================

class MCPTransportType(str, Enum):
    """Tipos de transporte MCP."""
    STDIO = "stdio"
    SSE = "sse"
    STREAMABLE_HTTP = "streamable_http"


class MCPToolAnnotation(str, Enum):
    """Anotaciones de herramientas MCP."""
    READ_ONLY = "readOnlyHint"
    DESTRUCTIVE = "destructiveHint"
    IDEMPOTENT = "idempotentHint"
    OPEN_WORLD = "openWorldHint"


class MCPToolSchema(BaseModel):
    """Schema de herramienta MCP."""
    name: str
    description: str
    input_schema: Dict[str, Any] = Field(default_factory=dict)
    output_schema: Optional[Dict[str, Any]] = None
    annotations: List[MCPToolAnnotation] = Field(default_factory=list)


class MCPToolResult(BaseModel):
    """Resultado de ejecutar herramienta MCP."""
    success: bool
    content: List[Dict[str, Any]] = Field(default_factory=list)
    structured_content: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


class MCPServerConfig(BaseModel):
    """Configuración de servidor MCP."""
    name: str
    transport: MCPTransportType
    command: Optional[str] = None
    args: List[str] = Field(default_factory=list)
    url: Optional[str] = None
    env: Dict[str, str] = Field(default_factory=dict)
    timeout: int = 30


# =============================================================================
# ADAPTER PATTERN - Para diferentes transportes
# =============================================================================

class MCPTransportAdapter(ABC):
    """Adapter Pattern para diferentes transportes MCP."""
    
    @abstractmethod
    async def connect(self) -> bool:
        """Conecta al servidor MCP."""
        pass
    
    @abstractmethod
    async def disconnect(self) -> None:
        """Desconecta del servidor."""
        pass
    
    @abstractmethod
    async def list_tools(self) -> List[MCPToolSchema]:
        """Lista herramientas disponibles."""
        pass
    
    @abstractmethod
    async def call_tool(
        self,
        name: str,
        arguments: Dict[str, Any]
    ) -> MCPToolResult:
        """Ejecuta una herramienta."""
        pass
    
    @abstractmethod
    async def list_resources(self) -> List[Dict[str, Any]]:
        """Lista recursos disponibles."""
        pass
    
    @abstractmethod
    async def read_resource(self, uri: str) -> str:
        """Lee un recurso."""
        pass


class StdioTransportAdapter(MCPTransportAdapter):
    """Adapter para transporte stdio."""
    
    def __init__(self, config: MCPServerConfig):
        self.config = config
        self._process: Optional[asyncio.subprocess.Process] = None
        self._tools: List[MCPToolSchema] = []
    
    async def connect(self) -> bool:
        """Conecta vía stdio."""
        if not self.config.command:
            return False
        
        try:
            self._process = await asyncio.create_subprocess_exec(
                self.config.command,
                *self.config.args,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env={**dict.__init__, **self.config.env}
            )
            return True
        except Exception as e:
            print(f"Error connecting to MCP server: {e}")
            return False
    
    async def disconnect(self) -> None:
        """Desconecta."""
        if self._process:
            self._process.terminate()
            await self._process.wait()
            self._process = None
    
    async def _send_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Envía request JSON-RPC."""
        if not self._process or not self._process.stdin:
            raise RuntimeError("Not connected")
        
        request_str = json.dumps(request) + "\n"
        self._process.stdin.write(request_str.encode())
        await self._process.stdin.drain()
        
        # Leer respuesta
        if self._process.stdout:
            response_line = await self._process.stdout.readline()
            return json.loads(response_line.decode())
        
        return {}
    
    async def list_tools(self) -> List[MCPToolSchema]:
        """Lista herramientas."""
        response = await self._send_request({
            "jsonrpc": "2.0",
            "method": "tools/list",
            "id": 1
        })
        
        tools = []
        for tool_data in response.get("result", {}).get("tools", []):
            tools.append(MCPToolSchema(
                name=tool_data.get("name", ""),
                description=tool_data.get("description", ""),
                input_schema=tool_data.get("inputSchema", {})
            ))
        
        self._tools = tools
        return tools
    
    async def call_tool(
        self,
        name: str,
        arguments: Dict[str, Any]
    ) -> MCPToolResult:
        """Ejecuta herramienta."""
        response = await self._send_request({
            "jsonrpc": "2.0",
            "method": "tools/call",
            "id": 2,
            "params": {
                "name": name,
                "arguments": arguments
            }
        })
        
        if "error" in response:
            return MCPToolResult(
                success=False,
                error=response["error"].get("message", "Unknown error")
            )
        
        result = response.get("result", {})
        return MCPToolResult(
            success=True,
            content=result.get("content", []),
            structured_content=result.get("structuredContent")
        )
    
    async def list_resources(self) -> List[Dict[str, Any]]:
        """Lista recursos."""
        response = await self._send_request({
            "jsonrpc": "2.0",
            "method": "resources/list",
            "id": 3
        })
        
        return response.get("result", {}).get("resources", [])
    
    async def read_resource(self, uri: str) -> str:
        """Lee recurso."""
        response = await self._send_request({
            "jsonrpc": "2.0",
            "method": "resources/read",
            "id": 4,
            "params": {"uri": uri}
        })
        
        return response.get("result", {}).get("contents", "")


class HTTPTransportAdapter(MCPTransportAdapter):
    """Adapter para transporte HTTP/SSE."""
    
    def __init__(self, config: MCPServerConfig):
        self.config = config
        self._tools: List[MCPToolSchema] = []
        # Placeholder para cliente HTTP
    
    async def connect(self) -> bool:
        """Conecta vía HTTP."""
        # Placeholder - en producción usar httpx/aiohttp
        return self.config.url is not None
    
    async def disconnect(self) -> None:
        """Desconecta."""
        pass
    
    async def list_tools(self) -> List[MCPToolSchema]:
        """Lista herramientas."""
        return self._tools
    
    async def call_tool(
        self,
        name: str,
        arguments: Dict[str, Any]
    ) -> MCPToolResult:
        """Ejecuta herramienta."""
        return MCPToolResult(success=False, error="Not implemented")
    
    async def list_resources(self) -> List[Dict[str, Any]]:
        """Lista recursos."""
        return []
    
    async def read_resource(self, uri: str) -> str:
        """Lee recurso."""
        return ""


# =============================================================================
# PROXY PATTERN - MCP Proxy
# =============================================================================

class MCPProxy:
    """
    Proxy Pattern para MCP.
    Proporciona caching, logging y control de acceso.
    """
    
    def __init__(self, adapter: MCPTransportAdapter):
        self._adapter = adapter
        self._tool_cache: Dict[str, MCPToolSchema] = {}
        self._result_cache: Dict[str, MCPToolResult] = {}
        self._call_log: List[Dict[str, Any]] = []
    
    async def connect(self) -> bool:
        """Conecta con caching."""
        connected = await self._adapter.connect()
        
        if connected:
            tools = await self._adapter.list_tools()
            for tool in tools:
                self._tool_cache[tool.name] = tool
        
        return connected
    
    async def disconnect(self) -> None:
        """Desconecta."""
        await self._adapter.disconnect()
        self._tool_cache.clear()
        self._result_cache.clear()
    
    async def list_tools(self) -> List[MCPToolSchema]:
        """Lista herramientas con cache."""
        if self._tool_cache:
            return list(self._tool_cache.values())
        
        tools = await self._adapter.list_tools()
        for tool in tools:
            self._tool_cache[tool.name] = tool
        
        return tools
    
    async def call_tool(
        self,
        name: str,
        arguments: Dict[str, Any],
        use_cache: bool = True
    ) -> MCPToolResult:
        """Ejecuta con cache y logging."""
        # Crear cache key
        cache_key = f"{name}:{json.dumps(arguments, sort_keys=True)}"
        
        # Verificar cache
        if use_cache and cache_key in self._result_cache:
            return self._result_cache[cache_key]
        
        # Log
        self._call_log.append({
            "timestamp": datetime.utcnow().isoformat(),
            "tool": name,
            "arguments": arguments
        })
        
        # Ejecutar
        result = await self._adapter.call_tool(name, arguments)
        
        # Cachear resultado exitoso
        if result.success and use_cache:
            self._result_cache[cache_key] = result
        
        return result
    
    def get_call_history(self, tool_name: Optional[str] = None) -> List[Dict[str, Any]]:
        """Obtiene historial de llamadas."""
        if tool_name:
            return [c for c in self._call_log if c["tool"] == tool_name]
        return self._call_log.copy()
    
    def clear_cache(self) -> None:
        """Limpia cache."""
        self._result_cache.clear()


# =============================================================================
# FACADE PATTERN - MCP Client Facade
# =============================================================================

class MCPClientFacade:
    """
    Facade para simplificar el uso de MCP.
    Oculta complejidad de transporte y conexión.
    """
    
    def __init__(self):
        self._servers: Dict[str, MCPProxy] = {}
        self._tool_to_server: Dict[str, str] = {}
    
    async def register_server(
        self,
        name: str,
        config: MCPServerConfig
    ) -> bool:
        """Registra un servidor MCP."""
        # Crear adapter según transporte
        if config.transport == MCPTransportType.STDIO:
            adapter = StdioTransportAdapter(config)
        else:
            adapter = HTTPTransportAdapter(config)
        
        # Crear proxy
        proxy = MCPProxy(adapter)
        
        # Conectar
        connected = await proxy.connect()
        
        if connected:
            self._servers[name] = proxy
            
            # Mapear herramientas a servidor
            tools = await proxy.list_tools()
            for tool in tools:
                self._tool_to_server[tool.name] = name
        
        return connected
    
    async def unregister_server(self, name: str) -> None:
        """Desregistra un servidor."""
        if name in self._servers:
            await self._servers[name].disconnect()
            del self._servers[name]
            
            # Limpiar mapeo
            self._tool_to_server = {
                t: s for t, s in self._tool_to_server.items()
                if s != name
            }
    
    async def list_all_tools(self) -> List[MCPToolSchema]:
        """Lista todas las herramientas de todos los servidores."""
        all_tools = []
        
        for proxy in self._servers.values():
            tools = await proxy.list_tools()
            all_tools.extend(tools)
        
        return all_tools
    
    async def call_tool(
        self,
        name: str,
        arguments: Dict[str, Any]
    ) -> MCPToolResult:
        """Ejecuta una herramienta por nombre."""
        # Encontrar servidor
        server_name = self._tool_to_server.get(name)
        
        if not server_name:
            return MCPToolResult(
                success=False,
                error=f"Tool '{name}' not found"
            )
        
        proxy = self._servers.get(server_name)
        if not proxy:
            return MCPToolResult(
                success=False,
                error=f"Server '{server_name}' not connected"
            )
        
        return await proxy.call_tool(name, arguments)
    
    def get_available_servers(self) -> List[str]:
        """Obtiene servidores disponibles."""
        return list(self._servers.keys())
    
    def get_tool_info(self, name: str) -> Optional[Dict[str, Any]]:
        """Obtiene información de una herramienta."""
        server_name = self._tool_to_server.get(name)
        
        if server_name:
            proxy = self._servers.get(server_name)
            if proxy and name in proxy._tool_cache:
                tool = proxy._tool_cache[name]
                return {
                    "name": tool.name,
                    "description": tool.description,
                    "input_schema": tool.input_schema,
                    "server": server_name
                }
        
        return None


# =============================================================================
# BRIDGE PATTERN - MCP Skill Bridge
# =============================================================================

class MCPSkillBridge:
    """
    Bridge Pattern para conectar MCP con el sistema de Skills.
    Permite usar herramientas MCP como Skills del agente.
    """
    
    def __init__(self, mcp_client: MCPClientFacade):
        self._mcp_client = mcp_client
    
    async def get_skills_as_tools(self) -> List[Dict[str, Any]]:
        """Obtiene herramientas MCP en formato de skills."""
        tools = await self._mcp_client.list_all_tools()
        
        return [
            {
                "name": tool.name,
                "description": tool.description,
                "parameters": tool.input_schema,
                "source": "mcp",
                "annotations": [a.value for a in tool.annotations]
            }
            for tool in tools
        ]
    
    async def execute_as_skill(
        self,
        skill_name: str,
        parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Ejecuta herramienta MCP como skill."""
        result = await self._mcp_client.call_tool(skill_name, parameters)
        
        return {
            "success": result.success,
            "output": result.structured_content or result.content,
            "error": result.error
        }


# =============================================================================
# BUILT-IN MCP SKILLS (Local Implementation)
# =============================================================================

class BuiltinMCPSkills:
    """Skills MCP implementadas localmente (sin servidor externo)."""
    
    @staticmethod
    def get_filesystem_skill() -> Dict[str, Any]:
        """Skill de filesystem."""
        return {
            "name": "filesystem",
            "description": "Operaciones de sistema de archivos",
            "tools": [
                {
                    "name": "read_file",
                    "description": "Lee un archivo",
                    "input_schema": {
                        "type": "object",
                        "properties": {
                            "path": {"type": "string", "description": "Ruta del archivo"}
                        },
                        "required": ["path"]
                    }
                },
                {
                    "name": "write_file",
                    "description": "Escribe un archivo",
                    "input_schema": {
                        "type": "object",
                        "properties": {
                            "path": {"type": "string"},
                            "content": {"type": "string"}
                        },
                        "required": ["path", "content"]
                    }
                },
                {
                    "name": "list_directory",
                    "description": "Lista contenido de directorio",
                    "input_schema": {
                        "type": "object",
                        "properties": {
                            "path": {"type": "string"}
                        },
                        "required": ["path"]
                    }
                }
            ]
        }
    
    @staticmethod
    def get_web_search_skill() -> Dict[str, Any]:
        """Skill de búsqueda web."""
        return {
            "name": "web_search",
            "description": "Búsqueda en la web",
            "tools": [
                {
                    "name": "search",
                    "description": "Busca en la web",
                    "input_schema": {
                        "type": "object",
                        "properties": {
                            "query": {"type": "string", "description": "Término de búsqueda"},
                            "num_results": {"type": "integer", "default": 5}
                        },
                        "required": ["query"]
                    }
                },
                {
                    "name": "fetch_url",
                    "description": "Obtiene contenido de URL",
                    "input_schema": {
                        "type": "object",
                        "properties": {
                            "url": {"type": "string"}
                        },
                        "required": ["url"]
                    }
                }
            ]
        }
    
    @staticmethod
    def get_code_execution_skill() -> Dict[str, Any]:
        """Skill de ejecución de código."""
        return {
            "name": "code_execution",
            "description": "Ejecución segura de código",
            "tools": [
                {
                    "name": "execute_python",
                    "description": "Ejecuta código Python",
                    "input_schema": {
                        "type": "object",
                        "properties": {
                            "code": {"type": "string", "description": "Código Python a ejecutar"},
                            "timeout": {"type": "integer", "default": 30}
                        },
                        "required": ["code"]
                    }
                },
                {
                    "name": "execute_bash",
                    "description": "Ejecuta comando bash",
                    "input_schema": {
                        "type": "object",
                        "properties": {
                            "command": {"type": "string"}
                        },
                        "required": ["command"]
                    }
                }
            ]
        }
    
    @staticmethod
    def get_memory_skill() -> Dict[str, Any]:
        """Skill de memoria (Knowledge Graph)."""
        return {
            "name": "memory",
            "description": "Gestión de memoria y conocimiento",
            "tools": [
                {
                    "name": "store_memory",
                    "description": "Almacena un recuerdo",
                    "input_schema": {
                        "type": "object",
                        "properties": {
                            "content": {"type": "string"},
                            "memory_type": {"type": "string", "enum": ["episodic", "semantic", "procedural"]}
                        },
                        "required": ["content"]
                    }
                },
                {
                    "name": "search_memory",
                    "description": "Busca en memoria",
                    "input_schema": {
                        "type": "object",
                        "properties": {
                            "query": {"type": "string"},
                            "top_k": {"type": "integer", "default": 5}
                        },
                        "required": ["query"]
                    }
                }
            ]
        }
    
    @classmethod
    def get_all_skills(cls) -> List[Dict[str, Any]]:
        """Obtiene todas las skills built-in."""
        return [
            cls.get_filesystem_skill(),
            cls.get_web_search_skill(),
            cls.get_code_execution_skill(),
            cls.get_memory_skill()
        ]

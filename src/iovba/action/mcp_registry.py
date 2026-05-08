"""
MCP Registry - Registro de servidores Model Context Protocol

Permite que el agente se conecte a servidores MCP (stdio, SSE, HTTP)
para acceder a herramientas de terceros de forma unificada.
"""

import asyncio
import json
import uuid
from typing import Optional, Dict, Any, List, Callable, Union
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
from pathlib import Path
import subprocess
import logging

logger = logging.getLogger(__name__)


class MCPTransport(str, Enum):
    """Tipos de transporte MCP"""
    STDIO = "stdio"
    SSE = "sse"
    HTTP = "http"
    WEBSOCKET = "websocket"


class MCPStatus(str, Enum):
    """Estado del servidor MCP"""
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    ERROR = "error"


@dataclass
class MCPServerConfig:
    """Configuración de un servidor MCP"""
    name: str
    transport: MCPTransport
    command: Optional[str] = None  # Para stdio
    url: Optional[str] = None      # Para http/sse/websocket
    args: List[str] = field(default_factory=list)
    env: Dict[str, str] = field(default_factory=dict)
    timeout: int = 30
    retry_attempts: int = 3
    auto_connect: bool = True
    capabilities: List[str] = field(default_factory=list)


@dataclass
class MCPTool:
    """Herramienta expuesta por un servidor MCP"""
    name: str
    description: str
    input_schema: Dict[str, Any]
    server_name: str
    category: str = "general"
    tags: List[str] = field(default_factory=list)
    requires_confirmation: bool = False
    is_destructive: bool = False
    rate_limit: Optional[int] = None  # calls per minute


@dataclass
class MCPToolResult:
    """Resultado de ejecutar una herramienta MCP"""
    tool_name: str
    success: bool
    output: Any
    error: Optional[str] = None
    execution_time_ms: int = 0
    server_name: str = ""


class MCPServer:
    """
    Representa una conexión a un servidor MCP.
    
    Gestiona el ciclo de vida de la conexión y la ejecución
    de herramientas remotas.
    """
    
    def __init__(self, config: MCPServerConfig):
        self.config = config
        self.status = MCPStatus.DISCONNECTED
        self.tools: Dict[str, MCPTool] = {}
        self._process: Optional[subprocess.Popen] = None
        self._session_id: Optional[str] = None
        self._last_error: Optional[str] = None
    
    async def connect(self) -> bool:
        """Establece conexión con el servidor MCP"""
        if self.status == MCPStatus.CONNECTED:
            return True
        
        self.status = MCPStatus.CONNECTING
        
        try:
            if self.config.transport == MCPTransport.STDIO:
                return await self._connect_stdio()
            elif self.config.transport == MCPTransport.HTTP:
                return await self._connect_http()
            elif self.config.transport == MCPTransport.SSE:
                return await self._connect_sse()
            else:
                raise ValueError(f"Transporte no soportado: {self.config.transport}")
                
        except Exception as e:
            self.status = MCPStatus.ERROR
            self._last_error = str(e)
            logger.error(f"Error conectando a servidor MCP {self.config.name}: {e}")
            return False
    
    async def _connect_stdio(self) -> bool:
        """Conecta via stdio"""
        if not self.config.command:
            raise ValueError("Comando requerido para transporte stdio")
        
        env = dict(subprocess.os.environ)
        env.update(self.config.env)
        
        self._process = subprocess.Popen(
            [self.config.command] + self.config.args,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=env
        )
        
        # Inicializar sesión
        init_request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "clientInfo": {"name": "OpenClaw", "version": "1.0.0"}
            }
        }
        
        response = await self._send_request(init_request)
        
        if response and "result" in response:
            self._session_id = response["result"].get("sessionId")
            await self._load_tools()
            self.status = MCPStatus.CONNECTED
            return True
        
        return False
    
    async def _connect_http(self) -> bool:
        """Conecta via HTTP (placeholder)"""
        # TODO: Implementar cliente HTTP para MCP
        self.status = MCPStatus.CONNECTED
        return True
    
    async def _connect_sse(self) -> bool:
        """Conecta via SSE (placeholder)"""
        # TODO: Implementar cliente SSE para MCP
        self.status = MCPStatus.CONNECTED
        return True
    
    async def _send_request(self, request: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Envía una petición al servidor"""
        if not self._process:
            return None
        
        try:
            request_str = json.dumps(request) + "\n"
            self._process.stdin.write(request_str.encode())
            self._process.stdin.flush()
            
            response_str = self._process.stdout.readline().decode()
            return json.loads(response_str)
            
        except Exception as e:
            logger.error(f"Error enviando petición MCP: {e}")
            return None
    
    async def _load_tools(self) -> None:
        """Carga la lista de herramientas del servidor"""
        request = {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/list"
        }
        
        response = await self._send_request(request)
        
        if response and "result" in response:
            tools_data = response["result"].get("tools", [])
            
            for tool_data in tools_data:
                tool = MCPTool(
                    name=tool_data["name"],
                    description=tool_data.get("description", ""),
                    input_schema=tool_data.get("inputSchema", {}),
                    server_name=self.config.name
                )
                self.tools[tool.name] = tool
    
    async def execute_tool(
        self,
        tool_name: str,
        arguments: Dict[str, Any]
    ) -> MCPToolResult:
        """Ejecuta una herramienta en el servidor"""
        if self.status != MCPStatus.CONNECTED:
            return MCPToolResult(
                tool_name=tool_name,
                success=False,
                output=None,
                error="Server not connected",
                server_name=self.config.name
            )
        
        start_time = datetime.utcnow()
        
        request = {
            "jsonrpc": "2.0",
            "id": str(uuid.uuid4())[:8],
            "method": "tools/call",
            "params": {
                "name": tool_name,
                "arguments": arguments
            }
        }
        
        response = await self._send_request(request)
        
        execution_time = int((datetime.utcnow() - start_time).total_seconds() * 1000)
        
        if response:
            if "result" in response:
                return MCPToolResult(
                    tool_name=tool_name,
                    success=True,
                    output=response["result"],
                    execution_time_ms=execution_time,
                    server_name=self.config.name
                )
            elif "error" in response:
                return MCPToolResult(
                    tool_name=tool_name,
                    success=False,
                    output=None,
                    error=response["error"].get("message", "Unknown error"),
                    execution_time_ms=execution_time,
                    server_name=self.config.name
                )
        
        return MCPToolResult(
            tool_name=tool_name,
            success=False,
            output=None,
            error="No response from server",
            execution_time_ms=execution_time,
            server_name=self.config.name
        )
    
    async def disconnect(self) -> None:
        """Desconecta del servidor"""
        if self._process:
            self._process.terminate()
            self._process = None
        
        self.status = MCPStatus.DISCONNECTED
    
    def get_tools(self) -> List[MCPTool]:
        """Obtiene la lista de herramientas disponibles"""
        return list(self.tools.values())


class MCPRegistry:
    """
    Registro central de servidores y herramientas MCP.
    
    Gestiona conexiones a múltiples servidores MCP y proporciona
    una interfaz unificada para ejecutar herramientas.
    
    Usage:
        registry = MCPRegistry()
        
        # Registrar servidor
        registry.register_server(MCPServerConfig(
            name="search",
            transport=MCPTransport.STDIO,
            command="mcp-server-tavily"
        ))
        
        # Conectar
        await registry.connect_all()
        
        # Ejecutar herramienta
        result = await registry.execute_tool("web_search", {"query": "AI news"})
    """
    
    def __init__(self):
        """Inicializa el registro MCP"""
        self._servers: Dict[str, MCPServer] = {}
        self._tool_index: Dict[str, str] = {}  # tool_name -> server_name
        self._on_tool_executed: Optional[Callable] = None
    
    def register_server(self, config: MCPServerConfig) -> None:
        """Registra un nuevo servidor MCP"""
        if config.name in self._servers:
            logger.warning(f"Servidor MCP {config.name} ya existe, reemplazando")
        
        self._servers[config.name] = MCPServer(config)
    
    def unregister_server(self, name: str) -> bool:
        """Remueve un servidor del registro"""
        if name in self._servers:
            server = self._servers[name]
            
            # Remover herramientas del índice
            for tool_name in server.tools:
                self._tool_index.pop(tool_name, None)
            
            del self._servers[name]
            return True
        return False
    
    async def connect_server(self, name: str) -> bool:
        """Conecta a un servidor específico"""
        if name not in self._servers:
            return False
        
        server = self._servers[name]
        success = await server.connect()
        
        if success:
            # Indexar herramientas
            for tool in server.get_tools():
                self._tool_index[tool.name] = name
        
        return success
    
    async def connect_all(self) -> Dict[str, bool]:
        """Conecta a todos los servidores registrados"""
        results = {}
        
        for name, server in self._servers.items():
            if server.config.auto_connect:
                results[name] = await self.connect_server(name)
        
        return results
    
    async def disconnect_server(self, name: str) -> bool:
        """Desconecta un servidor específico"""
        if name not in self._servers:
            return False
        
        await self._servers[name].disconnect()
        return True
    
    async def disconnect_all(self) -> None:
        """Desconecta todos los servidores"""
        for server in self._servers.values():
            await server.disconnect()
    
    async def execute_tool(
        self,
        tool_name: str,
        arguments: Dict[str, Any]
    ) -> MCPToolResult:
        """
        Ejecuta una herramienta por nombre.
        
        Busca el servidor que tiene la herramienta y la ejecuta.
        """
        if tool_name not in self._tool_index:
            return MCPToolResult(
                tool_name=tool_name,
                success=False,
                output=None,
                error=f"Tool {tool_name} not found in any server"
            )
        
        server_name = self._tool_index[tool_name]
        server = self._servers[server_name]
        
        result = await server.execute_tool(tool_name, arguments)
        
        if self._on_tool_executed:
            await self._on_tool_executed(result)
        
        return result
    
    def get_tool(self, tool_name: str) -> Optional[MCPTool]:
        """Obtiene información de una herramienta"""
        if tool_name not in self._tool_index:
            return None
        
        server_name = self._tool_index[tool_name]
        return self._servers[server_name].tools.get(tool_name)
    
    def list_tools(self) -> List[MCPTool]:
        """Lista todas las herramientas disponibles"""
        tools = []
        for server in self._servers.values():
            tools.extend(server.get_tools())
        return tools
    
    def list_servers(self) -> List[str]:
        """Lista los servidores registrados"""
        return list(self._servers.keys())
    
    def get_server_status(self, name: str) -> Optional[MCPStatus]:
        """Obtiene el estado de un servidor"""
        if name in self._servers:
            return self._servers[name].status
        return None
    
    def on_tool_executed(self, callback: Callable) -> None:
        """Registra callback para ejecuciones de herramientas"""
        self._on_tool_executed = callback
    
    def load_from_config(self, config_path: str) -> int:
        """
        Carga servidores desde un archivo de configuración.
        
        Args:
            config_path: Ruta al archivo JSON/YAML
        
        Returns:
            Número de servidores cargados
        """
        path = Path(config_path)
        
        if not path.exists():
            logger.warning(f"Archivo de configuración no encontrado: {config_path}")
            return 0
        
        content = path.read_text()
        
        if path.suffix in [".yaml", ".yml"]:
            import yaml
            data = yaml.safe_load(content)
        else:
            data = json.loads(content)
        
        count = 0
        for server_data in data.get("mcpServers", []):
            try:
                config = MCPServerConfig(
                    name=server_data["name"],
                    transport=MCPTransport(server_data.get("transport", "stdio")),
                    command=server_data.get("command"),
                    url=server_data.get("url"),
                    args=server_data.get("args", []),
                    env=server_data.get("env", {}),
                    auto_connect=server_data.get("autoConnect", True)
                )
                self.register_server(config)
                count += 1
            except Exception as e:
                logger.error(f"Error cargando servidor MCP: {e}")
        
        return count

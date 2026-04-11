"""
RICCO AI Service - Evolution API (Evo-ai) Integration
Integración con Evo-ai para agentes de IA, protocolo A2A y workflows con LangGraph
"""

import asyncio
import time
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional, Union

import httpx
from pydantic import BaseModel, Field
from structlog import get_logger

from app.core.config import settings

logger = get_logger(__name__)


# ============================================
# Evo-ai Data Models
# ============================================

class AgentType(str):
    """Evo-ai agent types"""
    LLM = "llm"
    A2A = "a2a"
    SEQUENTIAL = "sequential"
    PARALLEL = "parallel"
    LOOP = "loop"
    WORKFLOW = "workflow"
    TASK = "task"


class AgentConfig(BaseModel):
    """Agent configuration"""
    name: str
    description: Optional[str] = None
    type: str = AgentType.LLM
    model: Optional[str] = None
    system_prompt: Optional[str] = None
    temperature: float = 0.7
    max_tokens: int = 2048
    tools: List[str] = []
    mcp_servers: List[str] = []
    sub_agents: List[str] = []
    folder_id: Optional[str] = None
    metadata: Dict[str, Any] = {}


class A2AAgentConfig(BaseModel):
    """A2A (Agent-to-Agent) protocol configuration"""
    agent_id: str
    endpoint_url: str
    capabilities: List[str] = []
    authentication: Optional[Dict[str, str]] = None
    metadata: Dict[str, Any] = {}


class WorkflowNode(BaseModel):
    """Workflow node for LangGraph integration"""
    id: str
    type: str  # agent, condition, tool, etc.
    agent_id: Optional[str] = None
    config: Dict[str, Any] = {}
    position: Dict[str, float] = {"x": 0, "y": 0}


class WorkflowEdge(BaseModel):
    """Workflow edge connecting nodes"""
    id: str
    source: str
    target: str
    condition: Optional[Dict[str, Any]] = None
    label: Optional[str] = None


class WorkflowConfig(BaseModel):
    """Complete workflow configuration"""
    name: str
    description: Optional[str] = None
    nodes: List[WorkflowNode] = []
    edges: List[WorkflowEdge] = []
    entry_point: Optional[str] = None
    state_schema: Optional[Dict[str, Any]] = None


class ToolConfig(BaseModel):
    """Tool configuration"""
    name: str
    description: str
    type: str  # function, api, mcp
    config: Dict[str, Any] = {}
    parameters_schema: Optional[Dict[str, Any]] = None


class MCPServerConfig(BaseModel):
    """MCP (Model Context Protocol) server configuration"""
    name: str
    transport: str  # stdio, sse, websocket
    command: Optional[str] = None
    args: List[str] = []
    env: Dict[str, str] = {}
    url: Optional[str] = None


class AgentExecutionRequest(BaseModel):
    """Request to execute an agent"""
    agent_id: str
    input_text: str
    context: Optional[Dict[str, Any]] = None
    session_id: Optional[str] = None
    stream: bool = False


class AgentExecutionResult(BaseModel):
    """Result of agent execution"""
    execution_id: str
    agent_id: str
    output: str
    tokens_used: Dict[str, int] = {}
    latency_ms: float
    status: str
    metadata: Dict[str, Any] = {}


# ============================================
# Evo-ai Service
# ============================================

class EvoAIService:
    """
    Servicio de integración con Evo-ai
    Plataforma de agentes de IA con soporte para A2A y LangGraph
    """
    
    def __init__(
        self,
        base_url: Optional[str] = None,
        api_key: Optional[str] = None,
    ):
        self.base_url = base_url or getattr(settings, 'evoai_base_url', 'http://localhost:8001')
        self.api_key = api_key or getattr(settings, 'evoai_api_key', None)
        self._client: Optional[httpx.AsyncClient] = None
        
    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client"""
        if self._client is None or self._client.is_closed:
            headers = {"Content-Type": "application/json"}
            if self.api_key:
                headers["Authorization"] = f"Bearer {self.api_key}"
            
            self._client = httpx.AsyncClient(
                base_url=self.base_url,
                headers=headers,
                timeout=300.0,  # Long timeout for agent execution
            )
        return self._client
    
    async def close(self):
        """Close HTTP client"""
        if self._client and not self._client.is_closed:
            await self._client.aclose()
    
    # ============================================
    # Agent Management
    # ============================================
    
    async def list_agents(
        self,
        folder_id: Optional[str] = None,
        agent_type: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """List all agents"""
        client = await self._get_client()
        
        params = {}
        if folder_id:
            params["folder_id"] = folder_id
        if agent_type:
            params["type"] = agent_type
        
        response = await client.get("/api/v1/agents", params=params)
        response.raise_for_status()
        return response.json().get("agents", [])
    
    async def get_agent(self, agent_id: str) -> Dict[str, Any]:
        """Get agent by ID"""
        client = await self._get_client()
        response = await client.get(f"/api/v1/agents/{agent_id}")
        response.raise_for_status()
        return response.json()
    
    async def create_agent(self, config: AgentConfig) -> Dict[str, Any]:
        """Create a new agent"""
        client = await self._get_client()
        response = await client.post("/api/v1/agents", json=config.model_dump())
        response.raise_for_status()
        return response.json()
    
    async def update_agent(self, agent_id: str, config: AgentConfig) -> Dict[str, Any]:
        """Update an existing agent"""
        client = await self._get_client()
        response = await client.patch(
            f"/api/v1/agents/{agent_id}",
            json=config.model_dump(exclude_unset=True),
        )
        response.raise_for_status()
        return response.json()
    
    async def delete_agent(self, agent_id: str) -> bool:
        """Delete an agent"""
        client = await self._get_client()
        response = await client.delete(f"/api/v1/agents/{agent_id}")
        response.raise_for_status()
        return True
    
    # ============================================
    # Agent Execution
    # ============================================
    
    async def execute_agent(self, request: AgentExecutionRequest) -> AgentExecutionResult:
        """Execute an agent"""
        start_time = time.time()
        client = await self._get_client()
        
        response = await client.post(
            f"/api/v1/agents/{request.agent_id}/execute",
            json={
                "input": request.input_text,
                "context": request.context,
                "session_id": request.session_id,
            },
        )
        response.raise_for_status()
        data = response.json()
        
        return AgentExecutionResult(
            execution_id=data.get("execution_id", str(uuid.uuid4())),
            agent_id=request.agent_id,
            output=data.get("output", ""),
            tokens_used=data.get("tokens_used", {}),
            latency_ms=(time.time() - start_time) * 1000,
            status=data.get("status", "completed"),
            metadata=data.get("metadata", {}),
        )
    
    # ============================================
    # Workflow Management (LangGraph)
    # ============================================
    
    async def create_workflow(self, config: WorkflowConfig) -> Dict[str, Any]:
        """Create a workflow with LangGraph"""
        client = await self._get_client()
        response = await client.post("/api/v1/workflows", json=config.model_dump())
        response.raise_for_status()
        return response.json()
    
    async def execute_workflow(
        self,
        workflow_id: str,
        input_data: Dict[str, Any],
        initial_state: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Execute a workflow"""
        client = await self._get_client()
        response = await client.post(
            f"/api/v1/workflows/{workflow_id}/execute",
            json={"input": input_data, "initial_state": initial_state},
        )
        response.raise_for_status()
        return response.json()
    
    # ============================================
    # A2A Protocol (Agent-to-Agent)
    # ============================================
    
    async def register_a2a_agent(self, config: A2AAgentConfig) -> Dict[str, Any]:
        """Register an A2A agent for interoperability"""
        client = await self._get_client()
        response = await client.post("/api/v1/a2a/agents", json=config.model_dump())
        response.raise_for_status()
        return response.json()
    
    async def discover_a2a_agents(self, capabilities: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """Discover available A2A agents"""
        client = await self._get_client()
        params = {}
        if capabilities:
            params["capabilities"] = ",".join(capabilities)
        response = await client.get("/api/v1/a2a/agents", params=params)
        response.raise_for_status()
        return response.json().get("agents", [])
    
    async def send_a2a_message(
        self,
        target_agent_id: str,
        message: Dict[str, Any],
        protocol_version: str = "1.0",
    ) -> Dict[str, Any]:
        """Send message to another A2A agent"""
        client = await self._get_client()
        response = await client.post(
            f"/api/v1/a2a/agents/{target_agent_id}/message",
            json={"message": message, "protocol_version": protocol_version},
        )
        response.raise_for_status()
        return response.json()
    
    # ============================================
    # RICCO-Specific Agent Templates
    # ============================================
    
    async def create_ricco_assistant_agent(
        self,
        solution: str,
        capabilities: List[str],
    ) -> Dict[str, Any]:
        """Create a RICCO solution-specific assistant agent"""
        solution_prompts = {
            "commerce": "Eres el asistente de RICCO Commerce. Ayudas con productos, pedidos, recomendaciones.",
            "health": "Eres el asistente de RICCO Health. Ayudas con citas, consultas, historial médico.",
            "logistics": "Eres el asistente de RICCO Logistics. Ayudas con envíos, rutas, tracking.",
            "funding": "Eres el asistente de RICCO Funding. Ayudas con proyectos, inversiones, Energy Points.",
            "legal": "Eres el asistente de RICCO Legal. Ayudas con casos, documentos, consultas legales.",
            "social": "Eres el asistente de RICCO Social. Ayudas con perfiles, networking, comunidades.",
        }
        
        config = AgentConfig(
            name=f"RICCO {solution.capitalize()} Assistant",
            description=f"AI assistant for RICCO {solution}",
            type=AgentType.LLM,
            model="anthropic/claude-3-haiku",
            system_prompt=solution_prompts.get(solution, solution_prompts["commerce"]),
            metadata={"solution": solution, "capabilities": capabilities},
        )
        
        return await self.create_agent(config)
    
    # ============================================
    # Health Check
    # ============================================
    
    async def health_check(self) -> Dict[str, Any]:
        """Check Evo-ai service health"""
        start_time = time.time()
        try:
            client = await self._get_client()
            response = await client.get("/health")
            response.raise_for_status()
            return {"connected": True, "latency_ms": (time.time() - start_time) * 1000}
        except Exception as e:
            return {"connected": False, "latency_ms": (time.time() - start_time) * 1000, "error": str(e)}


# Singleton
_evoai_service: Optional[EvoAIService] = None

def get_evoai_service() -> EvoAIService:
    global _evoai_service
    if _evoai_service is None:
        _evoai_service = EvoAIService()
    return _evoai_service

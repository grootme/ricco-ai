"""
Agent Swarm Module for RICCO AI.

Enjambre de agentes especializados con orquestador.
"""

from enum import Enum
from typing import Any, Dict, List, Optional
from datetime import datetime
from pydantic import BaseModel, Field
import logging

logger = logging.getLogger(__name__)


class AgentType(str, Enum):
    """Types of agents in the swarm."""
    ORCHESTRATOR = "orchestrator"
    COMMERCE = "commerce"
    HEALTH = "health"
    LOGISTICS = "logistics"
    FINANCE = "finance"
    REWARDS = "rewards"
    BOOKING = "booking"
    TRAVEL = "travel"
    SOCIAL = "social"
    LEGAL = "legal"
    GENERAL = "general"


class AgentStatus(str, Enum):
    """Agent status."""
    IDLE = "idle"
    PROCESSING = "processing"
    WAITING = "waiting"
    ERROR = "error"
    OFFLINE = "offline"


class AgentCapability(str, Enum):
    """Agent capabilities."""
    NATURAL_LANGUAGE = "natural_language"
    ORDER_MANAGEMENT = "order_management"
    PAYMENT_PROCESSING = "payment_processing"
    INVENTORY_CHECK = "inventory_check"
    APPOINTMENT_BOOKING = "appointment_booking"
    TRAVEL_PLANNING = "travel_planning"
    FINANCIAL_ADVICE = "financial_advice"
    HEALTH_CONSULTATION = "health_consultation"
    LEGAL_ASSISTANCE = "legal_assistance"
    REWARDS_MANAGEMENT = "rewards_management"


class AgentConfig(BaseModel):
    """Agent configuration."""
    agent_id: str
    agent_type: AgentType
    name: str
    description: str = ""
    capabilities: List[AgentCapability] = Field(default_factory=list)
    max_tokens: int = 4096
    temperature: float = 0.7
    system_prompt: Optional[str] = None
    mcp_servers: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class AgentMessage(BaseModel):
    """Message between agents."""
    message_id: str
    from_agent: str
    to_agent: str
    message_type: str
    content: Dict[str, Any]
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    correlation_id: Optional[str] = None
    priority: int = 0


class SwarmTask(BaseModel):
    """Task for the agent swarm."""
    task_id: str
    task_type: str
    description: str
    input_data: Dict[str, Any] = Field(default_factory=dict)
    assigned_agents: List[str] = Field(default_factory=list)
    status: str = "pending"
    priority: int = 0
    created_at: datetime = Field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


class SwarmState(BaseModel):
    """State of the agent swarm."""
    swarm_id: str
    status: str = "initialized"
    active_agents: List[str] = Field(default_factory=list)
    pending_tasks: List[str] = Field(default_factory=list)
    completed_tasks: List[str] = Field(default_factory=list)
    total_tokens_used: int = 0
    created_at: datetime = Field(default_factory=datetime.utcnow)


class SpecialistAgent:
    """Base class for specialist agents."""
    
    def __init__(self, config: AgentConfig):
        self.config = config
        self.status = AgentStatus.IDLE
        self._message_queue: List[AgentMessage] = []
    
    async def process(self, task: SwarmTask) -> Dict[str, Any]:
        """Process a task."""
        self.status = AgentStatus.PROCESSING
        try:
            result = await self._execute(task)
            self.status = AgentStatus.IDLE
            return result
        except Exception as e:
            self.status = AgentStatus.ERROR
            raise
    
    async def _execute(self, task: SwarmTask) -> Dict[str, Any]:
        """Execute the task (to be overridden)."""
        return {"status": "completed", "agent": self.config.name}
    
    def can_handle(self, capability: AgentCapability) -> bool:
        """Check if agent can handle a capability."""
        return capability in self.config.capabilities


class OrchestratorAgent:
    """
    Orchestrator agent for coordinating the agent swarm.
    
    Responsibilities:
    - Route tasks to appropriate specialist agents
    - Manage agent lifecycle
    - Handle inter-agent communication
    - Track swarm state
    """
    
    def __init__(self):
        self.agents: Dict[str, SpecialistAgent] = {}
        self.state = SwarmState(swarm_id="default")
        self._capability_map: Dict[AgentCapability, List[str]] = {}
    
    def register_agent(self, agent: SpecialistAgent) -> None:
        """Register an agent with the orchestrator."""
        agent_id = agent.config.agent_id
        self.agents[agent_id] = agent
        
        # Update capability map
        for cap in agent.config.capabilities:
            if cap not in self._capability_map:
                self._capability_map[cap] = []
            self._capability_map[cap].append(agent_id)
        
        self.state.active_agents.append(agent_id)
        logger.info(f"Registered agent: {agent.config.name} ({agent_id})")
    
    def unregister_agent(self, agent_id: str) -> bool:
        """Unregister an agent."""
        if agent_id not in self.agents:
            return False
        
        agent = self.agents.pop(agent_id)
        
        # Update capability map
        for cap in agent.config.capabilities:
            if cap in self._capability_map:
                self._capability_map[cap] = [
                    aid for aid in self._capability_map[cap] if aid != agent_id
                ]
        
        if agent_id in self.state.active_agents:
            self.state.active_agents.remove(agent_id)
        
        logger.info(f"Unregistered agent: {agent_id}")
        return True
    
    async def dispatch(self, task: SwarmTask) -> Dict[str, Any]:
        """Dispatch a task to appropriate agents."""
        self.state.pending_tasks.append(task.task_id)
        
        # Find capable agents
        required_caps = task.input_data.get("required_capabilities", [])
        candidate_agents = self._find_agents_for_capabilities(required_caps)
        
        if not candidate_agents:
            return {
                "status": "error",
                "error": "No capable agent found",
            }
        
        # Select best agent (simple selection for now)
        selected_agent_id = candidate_agents[0]
        selected_agent = self.agents[selected_agent_id]
        
        # Execute task
        task.status = "processing"
        task.started_at = datetime.utcnow()
        task.assigned_agents = [selected_agent_id]
        
        try:
            result = await selected_agent.process(task)
            task.result = result
            task.status = "completed"
            task.completed_at = datetime.utcnow()
            
            self.state.pending_tasks.remove(task.task_id)
            self.state.completed_tasks.append(task.task_id)
            
            return result
        except Exception as e:
            task.status = "failed"
            task.error = str(e)
            self.state.pending_tasks.remove(task.task_id)
            raise
    
    def _find_agents_for_capabilities(
        self,
        capabilities: List[str],
    ) -> List[str]:
        """Find agents that have the required capabilities."""
        if not capabilities:
            return list(self.agents.keys())
        
        agent_scores: Dict[str, int] = {}
        
        for cap_str in capabilities:
            try:
                cap = AgentCapability(cap_str)
                for agent_id in self._capability_map.get(cap, []):
                    agent_scores[agent_id] = agent_scores.get(agent_id, 0) + 1
            except ValueError:
                continue
        
        # Return agents sorted by capability match count
        return sorted(
            agent_scores.keys(),
            key=lambda x: agent_scores[x],
            reverse=True
        )
    
    def get_status(self) -> Dict[str, Any]:
        """Get orchestrator status."""
        return {
            "swarm_id": self.state.swarm_id,
            "status": self.state.status,
            "total_agents": len(self.agents),
            "active_agents": len(self.state.active_agents),
            "pending_tasks": len(self.state.pending_tasks),
            "completed_tasks": len(self.state.completed_tasks),
            "agents": {
                agent_id: {
                    "name": agent.config.name,
                    "type": agent.config.agent_type.value,
                    "status": agent.status.value,
                }
                for agent_id, agent in self.agents.items()
            },
        }


# Predefined agent configurations
ORCHESTRATOR_CONFIG = AgentConfig(
    agent_id="orchestrator-main",
    agent_type=AgentType.ORCHESTRATOR,
    name="Main Orchestrator",
    description="Main orchestrator for agent coordination",
    capabilities=[AgentCapability.NATURAL_LANGUAGE],
)

COMMERCE_AGENT = AgentConfig(
    agent_id="commerce-agent",
    agent_type=AgentType.COMMERCE,
    name="Commerce Agent",
    description="Handles e-commerce and order management",
    capabilities=[
        AgentCapability.ORDER_MANAGEMENT,
        AgentCapability.INVENTORY_CHECK,
        AgentCapability.PAYMENT_PROCESSING,
    ],
)

HEALTH_AGENT = AgentConfig(
    agent_id="health-agent",
    agent_type=AgentType.HEALTH,
    name="Health Agent",
    description="Handles health consultations and appointments",
    capabilities=[
        AgentCapability.HEALTH_CONSULTATION,
        AgentCapability.APPOINTMENT_BOOKING,
    ],
)

FINANCE_AGENT = AgentConfig(
    agent_id="finance-agent",
    agent_type=AgentType.FINANCE,
    name="Finance Agent",
    description="Handles financial operations and advice",
    capabilities=[
        AgentCapability.FINANCIAL_ADVICE,
        AgentCapability.PAYMENT_PROCESSING,
    ],
)

LOGISTICS_AGENT = AgentConfig(
    agent_id="logistics-agent",
    agent_type=AgentType.LOGISTICS,
    name="Logistics Agent",
    description="Handles shipping and logistics",
    capabilities=[
        AgentCapability.INVENTORY_CHECK,
    ],
)

# All agents mapping
ALL_AGENTS = {
    "orchestrator": ORCHESTRATOR_CONFIG,
    "commerce": COMMERCE_AGENT,
    "health": HEALTH_AGENT,
    "finance": FINANCE_AGENT,
    "logistics": LOGISTICS_AGENT,
}

# Capability to agents mapping
CAPABILITY_TO_AGENTS = {
    AgentCapability.ORDER_MANAGEMENT: ["commerce"],
    AgentCapability.PAYMENT_PROCESSING: ["commerce", "finance"],
    AgentCapability.INVENTORY_CHECK: ["commerce", "logistics"],
    AgentCapability.HEALTH_CONSULTATION: ["health"],
    AgentCapability.APPOINTMENT_BOOKING: ["health"],
    AgentCapability.FINANCIAL_ADVICE: ["finance"],
}

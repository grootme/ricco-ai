"""
Agent Seeder - Seeds example agents with components

This seeder creates example agents demonstrating the component-based architecture:
- SKILLS: What the agent knows how to do
- TOOLS: What the agent has available
- MCP: Where resources come from
- MEMORY: What the agent knows (Cognitive Capital)
- PROMPT: How the agent acts

To add new agents, simply create them with the appropriate components.
The frontend organizes all information for the best experience.

@author: NEXUS - Neural Execution Unified System
"""

from typing import List, Dict, Any
import logging
from uuid import UUID

logger = logging.getLogger(__name__)


# Example Agent Templates
EXAMPLE_AGENTS: List[Dict[str, Any]] = [
    {
        "name": "Code Assistant",
        "description": "Software engineering assistant for code analysis, generation, and debugging",
        "skills": [
            {"skill_id": "code-analysis", "skill_name": "code_analysis", "proficiency": 0.95, "enabled": True},
            {"skill_id": "code-generation", "skill_name": "code_generation", "proficiency": 0.9, "enabled": True},
            {"skill_id": "debugging", "skill_name": "debugging", "proficiency": 0.85, "enabled": True},
            {"skill_id": "testing", "skill_name": "testing", "proficiency": 0.9, "enabled": True},
        ],
        "tools": [
            {"tool_name": "code_executor", "source": "builtin", "permissions": ["read", "execute"], "enabled": True},
            {"tool_name": "file_manager", "source": "builtin", "permissions": ["read", "write"], "enabled": True},
        ],
        "mcp_servers": [
            {"mcp_id": "github", "mcp_name": "github", "tools": ["create_repo", "create_pr", "review"], "enabled": True},
            {"mcp_id": "filesystem", "mcp_name": "filesystem", "tools": ["read", "write", "list"], "enabled": True},
        ],
        "memory_config": {
            "domains": ["code", "projects", "documentation"],
            "access_level": "domain",
            "retention_policy": "persistent",
        },
        "prompt_config": {
            "system_prompt": "You are an expert software engineering assistant.",
            "tone": "professional",
            "language": "es",
        },
        "tags": ["code", "development", "software"],
    },
    {
        "name": "Health Advisor",
        "description": "Health consultation assistant for symptom assessment and medical information",
        "skills": [
            {"skill_id": "symptom-analysis", "skill_name": "symptom_analysis", "proficiency": 0.8, "enabled": True},
            {"skill_id": "health-information", "skill_name": "health_information", "proficiency": 0.85, "enabled": True},
        ],
        "tools": [
            {"tool_name": "health_db", "source": "mcp", "permissions": ["read"], "enabled": True},
        ],
        "mcp_servers": [
            {"mcp_id": "pubmed", "mcp_name": "pubmed", "tools": ["search", "get_abstract"], "enabled": True},
        ],
        "memory_config": {
            "domains": ["health", "wellness", "consultations"],
            "access_level": "domain",
            "retention_policy": "persistent",
        },
        "prompt_config": {
            "system_prompt": "You are a health consultation assistant. Always remind users to consult healthcare professionals.",
            "tone": "professional",
            "language": "es",
        },
        "tags": ["health", "wellness", "medical"],
    },
    {
        "name": "Finance Analyst",
        "description": "Financial advisory assistant for market analysis and investment guidance",
        "skills": [
            {"skill_id": "market-analysis", "skill_name": "market_analysis", "proficiency": 0.9, "enabled": True},
            {"skill_id": "investment-guidance", "skill_name": "investment_guidance", "proficiency": 0.85, "enabled": True},
        ],
        "tools": [
            {"tool_name": "market_data", "source": "mcp", "permissions": ["read"], "enabled": True},
        ],
        "mcp_servers": [
            {"mcp_id": "alpha-vantage", "mcp_name": "alpha_vantage", "tools": ["get_quotes", "get_trends"], "enabled": True},
        ],
        "memory_config": {
            "domains": ["finance", "investments", "markets"],
            "access_level": "domain",
            "retention_policy": "persistent",
        },
        "prompt_config": {
            "system_prompt": "You are a financial advisory assistant. Always include appropriate disclaimers about financial advice.",
            "tone": "professional",
            "language": "es",
        },
        "tags": ["finance", "banking", "investments"],
    },
    {
        "name": "Lead Orchestrator",
        "description": "Lead agent that coordinates other agents and routes tasks",
        "skills": [
            {"skill_id": "task-routing", "skill_name": "task_routing", "proficiency": 0.95, "enabled": True},
            {"skill_id": "agent-coordination", "skill_name": "agent_coordination", "proficiency": 0.95, "enabled": True},
            {"skill_id": "conflict-resolution", "skill_name": "conflict_resolution", "proficiency": 0.9, "enabled": True},
        ],
        "tools": [
            {"tool_name": "agent_router", "source": "builtin", "permissions": ["read", "execute"], "enabled": True},
            {"tool_name": "task_manager", "source": "builtin", "permissions": ["read", "write", "execute"], "enabled": True},
        ],
        "mcp_servers": [],
        "memory_config": {
            "domains": ["orchestration", "routing", "agents"],
            "access_level": "global",
            "retention_policy": "persistent",
        },
        "prompt_config": {
            "system_prompt": "You are the lead orchestrator agent. Coordinate the swarm of specialist agents and route tasks appropriately.",
            "tone": "professional",
            "language": "es",
        },
        "tags": ["orchestrator", "lead", "coordination"],
    },
]


async def seed_example_agents(db_session, client_id: UUID = None) -> Dict[str, int]:
    """
    Seed the agents table with example agents.
    
    This should be called during application initialization.
    
    Args:
        db_session: SQLAlchemy database session
        client_id: Optional client ID to associate agents with
        
    Returns:
        Dictionary with counts of seeded items
    """
    from src.models.models import Agent
    
    counts = {"agents": 0, "skipped": 0}
    
    for agent_data in EXAMPLE_AGENTS:
        try:
            # Check if agent already exists
            existing = db_session.query(Agent).filter(
                Agent.name == agent_data["name"]
            ).first()
            
            if not existing:
                agent = Agent(
                    name=agent_data["name"],
                    description=agent_data.get("description"),
                    skills=agent_data.get("skills", []),
                    tools=agent_data.get("tools", []),
                    mcp_servers=agent_data.get("mcp_servers", []),
                    memory_config=agent_data.get("memory_config", {}),
                    prompt_config=agent_data.get("prompt_config", {}),
                    tags=agent_data.get("tags", []),
                    client_id=client_id,
                    enabled=True,
                )
                db_session.add(agent)
                counts["agents"] += 1
            else:
                counts["skipped"] += 1
                
        except Exception as e:
            logger.error(f"Error seeding agent {agent_data['name']}: {e}")
    
    try:
        db_session.commit()
        logger.info(f"Seeded {counts['agents']} new agents, skipped {counts['skipped']} existing")
    except Exception as e:
        db_session.rollback()
        logger.error(f"Error committing agents: {e}")
    
    return counts


def get_example_agents() -> List[Dict[str, Any]]:
    """Get list of example agent templates"""
    return EXAMPLE_AGENTS.copy()

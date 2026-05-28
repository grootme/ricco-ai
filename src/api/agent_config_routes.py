"""
Agent Configuration API Routes

These routes provide access to the configuration-driven agent system.
Groups and agents are managed dynamically from database.

The agent is defined by its components:
- SKILLS: What it knows how to do
- TOOLS: What it has available
- MCP: Where resources come from
- MEMORY: What it knows (Cognitive Capital)
- PROMPT: How it acts

@author: NEXUS - Neural Execution Unified System
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
from uuid import UUID
from pydantic import BaseModel
import logging

from src.config.database import get_db
from src.models.models import AgentGroup, AgentGroupMember, Agent
from src.services.agent_cache_service import get_agent_cache, init_agent_cache

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/agent-config", tags=["Agent Configuration"])


# ============================================================================
# REQUEST/RESPONSE SCHEMAS
# ============================================================================

class CreateGroupRequest(BaseModel):
    """Request to create a new agent group"""
    name: str
    domain: str
    description: str = ""
    assistant_id: Optional[UUID] = None  # The main assistant agent (like WhatsApp group owner)


class AddAgentToGroupRequest(BaseModel):
    """Request to add an agent to a group"""
    agent_id: UUID
    role: str  # investigator, observer, validator, builder, assistant, etc.
    is_assistant: bool = False  # Is this the main assistant?


# ============================================================================
# CACHE ENDPOINTS
# ============================================================================

@router.get("/cache/stats", response_model=Dict[str, Any])
async def get_cache_stats():
    """Get agent cache statistics"""
    cache = get_agent_cache()
    return cache.get_stats()


@router.post("/cache/refresh")
async def refresh_cache(
    db: Session = Depends(get_db)
):
    """Refresh the agent configuration cache"""
    cache = get_agent_cache()
    cache.set_db_session(db)
    await cache.refresh_configurations()
    return {"status": "success", "message": "Cache refreshed"}


@router.post("/cache/invalidate")
async def invalidate_cache(
    agent_id: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Invalidate agent cache"""
    cache = get_agent_cache()
    
    if agent_id:
        await cache.invalidate(agent_id)
        return {"status": "success", "message": f"Cache invalidated for agent {agent_id}"}
    else:
        await cache.invalidate_all()
        return {"status": "success", "message": "All cache invalidated"}


# ============================================================================
# GROUP MANAGEMENT ENDPOINTS
# ============================================================================

@router.post("/groups", response_model=Dict[str, Any])
async def create_agent_group(
    request: CreateGroupRequest,
    db: Session = Depends(get_db)
):
    """
    Create a new agent group.
    
    A group is like a WhatsApp group where:
    - Multiple agents collaborate
    - One agent is the main assistant (like the group owner)
    - All agents share cognitive capital
    """
    # Create the group
    db_group = AgentGroup(
        name=request.name,
        elegant_name=request.name.upper(),
        domain=request.domain,
        description=request.description,
        config={"domain": request.domain},
        status="active",
        sync_mode="hybrid",
    )
    db.add(db_group)
    db.commit()
    db.refresh(db_group)
    
    # If an assistant is specified, add them as the main agent
    if request.assistant_id:
        member = AgentGroupMember(
            group_id=db_group.id,
            agent_id=request.assistant_id,
            role="assistant",
            is_assistant=True,
        )
        db.add(member)
        db.commit()
    
    return {
        "id": str(db_group.id),
        "name": db_group.name,
        "elegant_name": db_group.elegant_name,
        "domain": db_group.domain,
        "description": db_group.description,
        "status": db_group.status,
        "assistant_id": str(request.assistant_id) if request.assistant_id else None,
    }


@router.get("/groups", response_model=List[Dict[str, Any]])
async def list_agent_groups(
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100
):
    """List all agent groups"""
    groups = db.query(AgentGroup).offset(skip).limit(limit).all()
    
    result = []
    for g in groups:
        # Get the main assistant for this group
        assistant_member = db.query(AgentGroupMember).filter(
            AgentGroupMember.group_id == g.id,
            AgentGroupMember.is_assistant == True
        ).first()
        
        # Count members
        member_count = db.query(AgentGroupMember).filter(
            AgentGroupMember.group_id == g.id
        ).count()
        
        result.append({
            "id": str(g.id),
            "name": g.name,
            "elegant_name": g.elegant_name,
            "domain": g.domain,
            "description": g.description,
            "status": g.status,
            "sync_mode": g.sync_mode,
            "member_count": member_count,
            "assistant_id": str(assistant_member.agent_id) if assistant_member else None,
            "created_at": g.created_at.isoformat() if g.created_at else None,
        })
    
    return result


@router.get("/groups/{group_id}", response_model=Dict[str, Any])
async def get_agent_group(
    group_id: UUID,
    db: Session = Depends(get_db)
):
    """Get a specific group with all its members"""
    group = db.query(AgentGroup).filter(AgentGroup.id == group_id).first()
    if not group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Group '{group_id}' not found"
        )
    
    # Get all members
    members = db.query(AgentGroupMember).filter(
        AgentGroupMember.group_id == group_id
    ).all()
    
    # Get agent details for each member
    agent_ids = [m.agent_id for m in members]
    agents = db.query(Agent).filter(Agent.id.in_(agent_ids)).all()
    agent_map = {str(a.id): a for a in agents}
    
    members_data = []
    for m in members:
        agent = agent_map.get(str(m.agent_id))
        members_data.append({
            "id": str(m.id),
            "agent_id": str(m.agent_id),
            "role": m.role,
            "is_assistant": m.is_assistant,
            "joined_at": m.joined_at.isoformat() if m.joined_at else None,
            "agent_name": agent.name if agent else None,
        })
    
    return {
        "id": str(group.id),
        "name": group.name,
        "elegant_name": group.elegant_name,
        "domain": group.domain,
        "description": group.description,
        "status": group.status,
        "sync_mode": group.sync_mode,
        "config": group.config,
        "members": members_data,
        "created_at": group.created_at.isoformat() if group.created_at else None,
    }


@router.post("/groups/{group_id}/members", response_model=Dict[str, Any])
async def add_agent_to_group(
    group_id: UUID,
    request: AddAgentToGroupRequest,
    db: Session = Depends(get_db)
):
    """
    Add an agent to a group.
    
    This is like adding a participant to a WhatsApp group.
    If is_assistant=True, this agent becomes the main assistant.
    """
    # Verify group exists
    group = db.query(AgentGroup).filter(AgentGroup.id == group_id).first()
    if not group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Group '{group_id}' not found"
        )
    
    # Verify agent exists
    agent = db.query(Agent).filter(Agent.id == request.agent_id).first()
    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Agent '{request.agent_id}' not found"
        )
    
    # Check if already a member
    existing = db.query(AgentGroupMember).filter(
        AgentGroupMember.group_id == group_id,
        AgentGroupMember.agent_id == request.agent_id
    ).first()
    
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Agent '{request.agent_id}' is already a member of this group"
        )
    
    # If this is the assistant, update any existing assistant
    if request.is_assistant:
        db.query(AgentGroupMember).filter(
            AgentGroupMember.group_id == group_id,
            AgentGroupMember.is_assistant == True
        ).update({"is_assistant": False})
    
    # Add the member
    member = AgentGroupMember(
        group_id=group_id,
        agent_id=request.agent_id,
        role=request.role,
        is_assistant=request.is_assistant,
    )
    db.add(member)
    db.commit()
    db.refresh(member)
    
    return {
        "id": str(member.id),
        "group_id": str(group_id),
        "agent_id": str(request.agent_id),
        "agent_name": agent.name,
        "role": request.role,
        "is_assistant": request.is_assistant,
        "joined_at": member.joined_at.isoformat() if member.joined_at else None,
    }


@router.delete("/groups/{group_id}/members/{agent_id}")
async def remove_agent_from_group(
    group_id: UUID,
    agent_id: UUID,
    db: Session = Depends(get_db)
):
    """Remove an agent from a group"""
    member = db.query(AgentGroupMember).filter(
        AgentGroupMember.group_id == group_id,
        AgentGroupMember.agent_id == agent_id
    ).first()
    
    if not member:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Agent '{agent_id}' is not a member of group '{group_id}'"
        )
    
    db.delete(member)
    db.commit()
    
    return {"status": "success", "message": f"Agent removed from group"}


@router.delete("/groups/{group_id}")
async def delete_agent_group(
    group_id: UUID,
    db: Session = Depends(get_db)
):
    """Delete a group and all its members"""
    group = db.query(AgentGroup).filter(AgentGroup.id == group_id).first()
    if not group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Group '{group_id}' not found"
        )
    
    # Delete all members first
    db.query(AgentGroupMember).filter(
        AgentGroupMember.group_id == group_id
    ).delete()
    
    # Delete the group
    db.delete(group)
    db.commit()
    
    return {"status": "success", "message": f"Group deleted"}

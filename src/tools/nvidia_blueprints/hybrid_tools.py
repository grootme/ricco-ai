"""
NVIDIA Blueprints Hybrid Tools

This module provides hybrid tools that connect to NVIDIA NIM APIs when available,
with fallback to mock responses for development/testing.

Features:
- Automatic detection of NVIDIA NIM API key
- Real API calls when configured
- Mock fallback when API not available
- Consistent interface for all tools
"""

import os
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
from langchain_core.tools import tool
from pydantic import BaseModel, Field
import uuid as uuid_module

# Import NIM Client if available
try:
    from src.mcp.clients.nim_client import NIMClient, NIMConfig, get_nim_client
    NIM_AVAILABLE = True
except ImportError:
    NIM_AVAILABLE = False

logger = logging.getLogger(__name__)


def _utcnow_iso() -> str:
    """Get current UTC timestamp in ISO format."""
    return datetime.utcnow().isoformat() + "Z"


def _get_nim_api_key() -> Optional[str]:
    """Get NVIDIA NIM API key from environment."""
    return os.getenv("NVIDIA_NIM_API_KEY") or os.getenv("NIM_API_KEY")


def _is_nim_available() -> bool:
    """Check if NIM API is available and configured."""
    return NIM_AVAILABLE and _get_nim_api_key() is not None


# ============== Equipment & Asset Operations Tools ==============

class EquipmentStatus(BaseModel):
    asset_id: str
    status: str
    location: str
    battery_level: Optional[float] = None
    temperature: Optional[float] = None
    operator: Optional[str] = None


@tool
async def assign_equipment(asset_id: str, operator_id: str, task_id: Optional[str] = None) -> Dict[str, Any]:
    """
    Assign equipment to an operator for a specific task.
    
    Uses NVIDIA NIM API if configured, otherwise returns mock response.

    Args:
        asset_id: Unique identifier for the equipment (must start with ASSET-, EQ-, or WH-)
        operator_id: ID of the operator to assign
        task_id: Optional task ID for the assignment

    Returns:
        Assignment confirmation with details
    """
    if _is_nim_available():
        try:
            client = get_nim_client()
            return await client.assign_equipment(asset_id, operator_id, task_id)
        except Exception as e:
            logger.warning(f"NIM API call failed, falling back to mock: {e}")
    
    # Mock fallback
    return {
        "success": True,
        "asset_id": asset_id,
        "operator_id": operator_id,
        "task_id": task_id,
        "assigned_at": _utcnow_iso(),
        "message": f"Equipment {asset_id} assigned to operator {operator_id}",
        "_mode": "mock"
    }


@tool
async def get_equipment_status(asset_id: str) -> Dict[str, Any]:
    """
    Get real-time status of equipment.
    
    Uses NVIDIA NIM API if configured, otherwise returns mock response.

    Args:
        asset_id: Unique identifier for the equipment (must start with ASSET-, EQ-, or WH-)

    Returns:
        Current equipment status including location, battery, temperature
    """
    if _is_nim_available():
        try:
            client = get_nim_client()
            result = await client.get_equipment_status(asset_id)
            result["_mode"] = "nim_api"
            return result
        except Exception as e:
            logger.warning(f"NIM API call failed, falling back to mock: {e}")
    
    # Mock fallback
    return {
        "asset_id": asset_id,
        "status": "operational",
        "location": "Zone A - Aisle 3",
        "battery_level": 85.5,
        "temperature": 22.3,
        "operator": "OP-001",
        "_mode": "mock"
    }


@tool
async def get_equipment_telemetry(asset_id: str, metrics: List[str] = None) -> Dict[str, Any]:
    """
    Get equipment telemetry data for monitoring.
    
    Uses NVIDIA NIM API if configured, otherwise returns mock response.

    Args:
        asset_id: Unique identifier for the equipment
        metrics: List of metrics to retrieve (battery, temperature, speed, etc.)

    Returns:
        Telemetry data with timestamps and values
    """
    metrics = metrics or ["battery", "temperature", "speed", "location"]
    
    if _is_nim_available():
        try:
            client = get_nim_client()
            result = await client.get_equipment_telemetry(asset_id, metrics)
            result["_mode"] = "nim_api"
            return result
        except Exception as e:
            logger.warning(f"NIM API call failed, falling back to mock: {e}")
    
    # Mock fallback
    return {
        "asset_id": asset_id,
        "timestamp": _utcnow_iso(),
        "metrics": {
            "battery": {"value": 85.5, "unit": "%"},
            "temperature": {"value": 22.3, "unit": "°C"},
            "speed": {"value": 5.2, "unit": "km/h"},
            "location": {"zone": "A", "aisle": "3", "bay": "12"}
        },
        "_mode": "mock"
    }


@tool
async def create_maintenance_request(
    asset_id: str,
    issue_type: str,
    description: str,
    priority: str = "medium",
    scheduled_date: Optional[str] = None
) -> Dict[str, Any]:
    """
    Create a maintenance request for equipment.
    
    Uses NVIDIA NIM API if configured, otherwise returns mock response.

    Args:
        asset_id: Unique identifier for the equipment
        issue_type: Type of issue (mechanical, electrical, battery, software, structural, other)
        description: Detailed description of the issue
        priority: Priority level (low, medium, high, critical)
        scheduled_date: Preferred maintenance date

    Returns:
        Maintenance request confirmation with ticket ID
    """
    if _is_nim_available():
        try:
            client = get_nim_client()
            result = await client.create_maintenance_request(
                asset_id, issue_type, description, priority, scheduled_date
            )
            result["_mode"] = "nim_api"
            return result
        except Exception as e:
            logger.warning(f"NIM API call failed, falling back to mock: {e}")
    
    # Mock fallback
    return {
        "success": True,
        "ticket_id": f"MAINT-{uuid_module.uuid4().hex[:8].upper()}",
        "asset_id": asset_id,
        "issue_type": issue_type,
        "priority": priority,
        "status": "pending",
        "scheduled_date": scheduled_date,
        "created_at": _utcnow_iso(),
        "_mode": "mock"
    }


@tool
async def create_task(
    task_type: str,
    location: str,
    priority: str = "medium",
    assigned_to: Optional[str] = None,
    deadline: Optional[str] = None
) -> Dict[str, Any]:
    """
    Create a new warehouse task.
    
    Uses NVIDIA NIM API if configured, otherwise returns mock response.

    Args:
        task_type: Type of task (picking, packing, receiving, shipping, inventory, maintenance)
        location: Warehouse location for the task
        priority: Task priority (low, medium, high, urgent, critical)
        assigned_to: Operator ID to assign
        deadline: Task deadline

    Returns:
        Task creation confirmation with task ID
    """
    if _is_nim_available():
        try:
            client = get_nim_client()
            result = await client.create_task(task_type, location, priority, assigned_to, deadline)
            result["_mode"] = "nim_api"
            return result
        except Exception as e:
            logger.warning(f"NIM API call failed, falling back to mock: {e}")
    
    # Mock fallback
    return {
        "success": True,
        "task_id": f"TASK-{uuid_module.uuid4().hex[:8].upper()}",
        "task_type": task_type,
        "location": location,
        "priority": priority,
        "assigned_to": assigned_to,
        "status": "created",
        "created_at": _utcnow_iso(),
        "_mode": "mock"
    }


# ============== Tool Registry ==============

HYBRID_TOOLS = [
    assign_equipment,
    get_equipment_status,
    get_equipment_telemetry,
    create_maintenance_request,
    create_task,
]


def get_hybrid_tools() -> List:
    """Get all hybrid tools for registration."""
    return HYBRID_TOOLS


def is_nim_connected() -> bool:
    """Check if tools are using NIM API."""
    return _is_nim_available()

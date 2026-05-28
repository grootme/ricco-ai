"""
NVIDIA Blueprints API Routes

FastAPI routes for blueprint integration and testing.
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional
import asyncio
import uuid

from .registry import BlueprintRegistry
from .base import BlueprintConfig, BlueprintResult, BlueprintStatus
from .aiq import AIQResearchBlueprint
from .rag import RAGBlueprint
from .video_search import (
    VideoSearchBlueprint, DataFlywheelBlueprint,
    DigitalHumanBlueprint, HealthcareBlueprint, RetailCommerceBlueprint
)


router = APIRouter(prefix="/blueprints", tags=["NVIDIA Blueprints"])

registry = BlueprintRegistry()


# ============================================================================
# Request/Response Models
# ============================================================================

class BlueprintExecuteRequest(BaseModel):
    blueprint_name: str = Field(..., description="Name of the blueprint to execute")
    input_data: Dict[str, Any] = Field(..., description="Input data for the blueprint")
    config: Optional[Dict[str, Any]] = Field(default=None, description="Optional configuration")


class BlueprintExecuteResponse(BaseModel):
    blueprint_id: str
    status: str
    message: str


# ============================================================================
# Blueprint Discovery Routes
# ============================================================================

@router.get("/")
async def list_blueprints():
    """List all available NVIDIA AI Blueprints"""
    return {
        "blueprints": registry.list_blueprints(),
        "total": len(registry.list_blueprints())
    }


@router.get("/{blueprint_name}")
async def get_blueprint_info(blueprint_name: str):
    """Get detailed information about a specific blueprint"""
    info = registry.get_blueprint(blueprint_name)
    if not info:
        raise HTTPException(status_code=404, detail=f"Blueprint '{blueprint_name}' not found")
    
    return {
        "info": {
            "name": info.name,
            "type": info.blueprint_type.value,
            "description": info.description,
            "version": info.version,
            "enabled": info.enabled,
            "dependencies": info.dependencies,
            "path": info.path,
        },
        "config_files": registry.get_blueprint_config(blueprint_name),
        "structure": registry.get_blueprint_structure(blueprint_name)
    }


@router.get("/{blueprint_name}/readme")
async def get_blueprint_readme(blueprint_name: str):
    """Get the README content for a blueprint"""
    readme = registry.get_blueprint_readme(blueprint_name)
    if not readme:
        raise HTTPException(status_code=404, detail=f"Blueprint '{blueprint_name}' not found")
    
    return {"blueprint": blueprint_name, "readme": readme}


# ============================================================================
# Blueprint Execution Routes
# ============================================================================

def get_blueprint_instance(name: str, config: Optional[BlueprintConfig] = None):
    """Get the appropriate blueprint instance"""
    blueprints = {
        "aiq": AIQResearchBlueprint,
        "rag": RAGBlueprint,
        "video-search": VideoSearchBlueprint,
        "data-flywheel": DataFlywheelBlueprint,
        "digital-human": DigitalHumanBlueprint,
        "healthcare": HealthcareBlueprint,
        "retail-commerce": RetailCommerceBlueprint,
    }
    
    blueprint_class = blueprints.get(name)
    if not blueprint_class:
        raise HTTPException(status_code=404, detail=f"Blueprint '{name}' not implemented")
    
    return blueprint_class(config)


@router.post("/execute", response_model=BlueprintExecuteResponse)
async def execute_blueprint(request: BlueprintExecuteRequest):
    """Execute a blueprint with the given input data"""
    
    # Validate blueprint exists
    info = registry.get_blueprint(request.blueprint_name)
    if not info:
        raise HTTPException(status_code=404, detail=f"Blueprint '{request.blueprint_name}' not found")
    
    # Create config
    config = BlueprintConfig(
        blueprint_id=str(uuid.uuid4()),
        name=request.blueprint_name,
        **(request.config or {})
    )
    
    # Get blueprint instance
    blueprint = get_blueprint_instance(request.blueprint_name, config)
    
    # Execute
    try:
        result = await blueprint.execute(request.input_data)
        registry.store_result(result)
        
        return BlueprintExecuteResponse(
            blueprint_id=config.blueprint_id,
            status=result.status.value,
            message="Blueprint executed successfully" if result.status == BlueprintStatus.COMPLETED else result.error
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/execute/{blueprint_name}")
async def execute_blueprint_simple(
    blueprint_name: str,
    input_data: Dict[str, Any]
):
    """Execute a blueprint with simplified interface"""
    
    info = registry.get_blueprint(blueprint_name)
    if not info:
        raise HTTPException(status_code=404, detail=f"Blueprint '{blueprint_name}' not found")
    
    config = BlueprintConfig(
        blueprint_id=str(uuid.uuid4()),
        name=blueprint_name
    )
    
    blueprint = get_blueprint_instance(blueprint_name, config)
    
    try:
        result = await blueprint.execute(input_data)
        registry.store_result(result)
        return result.to_dict()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Results Routes
# ============================================================================

@router.get("/results")
async def list_results():
    """List all blueprint execution results"""
    return {"results": registry.get_all_results()}


@router.get("/results/{blueprint_id}")
async def get_result(blueprint_id: str):
    """Get a specific blueprint execution result"""
    result = registry.get_result(blueprint_id)
    if not result:
        raise HTTPException(status_code=404, detail=f"Result '{blueprint_id}' not found")
    return result.to_dict()


# ============================================================================
# Test Routes for Each Blueprint
# ============================================================================

@router.post("/test/aiq")
async def test_aiq_blueprint(query: str = "What are the latest developments in AI?"):
    """Test AI-Q Research Blueprint"""
    blueprint = AIQResearchBlueprint()
    result = await blueprint.execute({"query": query, "depth": "standard"})
    return result.to_dict()


@router.post("/test/rag")
async def test_rag_blueprint(query: str = "Explain the key features of the product"):
    """Test RAG Blueprint"""
    blueprint = RAGBlueprint()
    result = await blueprint.execute({"query": query, "top_k": 5})
    return result.to_dict()


@router.post("/test/video-search")
async def test_video_search_blueprint(query: str = "Find scenes with product demonstration"):
    """Test Video Search Blueprint"""
    blueprint = VideoSearchBlueprint()
    result = await blueprint.execute({"query": query, "mode": "search"})
    return result.to_dict()


@router.post("/test/data-flywheel")
async def test_data_flywheel_blueprint(model: str = "production-model-v1"):
    """Test Data Flywheel Blueprint"""
    blueprint = DataFlywheelBlueprint()
    result = await blueprint.execute({"model": model})
    return result.to_dict()


@router.post("/test/digital-human")
async def test_digital_human_blueprint(text: str = "Hello, welcome to our service!"):
    """Test Digital Human Blueprint"""
    blueprint = DigitalHumanBlueprint()
    result = await blueprint.execute({"text": text})
    return result.to_dict()


@router.post("/test/healthcare")
async def test_healthcare_blueprint(transcript: str = "Patient presents with headache and fever"):
    """Test Healthcare Blueprint"""
    blueprint = HealthcareBlueprint()
    result = await blueprint.execute({"transcript": transcript})
    return result.to_dict()


@router.post("/test/retail-commerce")
async def test_retail_commerce_blueprint(action: str = "recommend"):
    """Test Retail Commerce Blueprint"""
    blueprint = RetailCommerceBlueprint()
    result = await blueprint.execute({"action": action})
    return result.to_dict()

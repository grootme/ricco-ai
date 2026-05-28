"""
API FastAPI del Super Asistente con Capital Cognitivo.
"""

from typing import Any, Dict, List, Optional
from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from datetime import datetime
import asyncio
from contextlib import asynccontextmanager
import uuid

import sys
sys.path.insert(0, '/home/z/my-project/super_assistant_python')
from orchestration.graph import create_orchestrator, SuperAssistantOrchestrator
from memory.memory_system import create_memory_system, MemoryManager
from security.guardrails import create_default_guardrails, GuardrailsManager
from skills.registry import create_skill_registry_with_defaults, SkillRegistry
from hitl.hitl_system import create_hitl_manager, HITLManager


# =============================================================================
# MODELOS DE API
# =============================================================================

class ChatRequest(BaseModel):
    """Request para chat."""
    message: str
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    stream: bool = False


class ChatResponse(BaseModel):
    """Response de chat."""
    response: str
    session_id: str
    agent_contributions: Dict[str, str] = Field(default_factory=dict)
    tools_used: List[str] = Field(default_factory=list)
    execution_time_ms: int = 0
    success: bool = True
    error: Optional[str] = None


class MemoryRequest(BaseModel):
    """Request para operaciones de memoria."""
    content: str
    memory_type: str = "semantic"
    user_id: Optional[str] = None
    session_id: Optional[str] = None


class MemorySearchRequest(BaseModel):
    """Request para búsqueda en memoria."""
    query: str
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    top_k: int = 5


class MemorySearchResponse(BaseModel):
    """Response de búsqueda en memoria."""
    results: List[Dict[str, Any]]
    total_count: int
    query: str


class SkillExecuteRequest(BaseModel):
    """Request para ejecutar skill."""
    skill_name: str
    parameters: Dict[str, Any] = Field(default_factory=dict)


class SkillExecuteResponse(BaseModel):
    """Response de ejecución de skill."""
    success: bool
    output: Optional[Any] = None
    error: Optional[str] = None
    execution_time_ms: Optional[int] = None


class ApprovalRequest(BaseModel):
    """Request para aprobación."""
    request_id: str
    decision: str  # approve, reject, modify
    modified_data: Optional[Dict[str, Any]] = None


class HealthResponse(BaseModel):
    """Response de health check."""
    status: str
    version: str
    timestamp: str
    components: Dict[str, str] = Field(default_factory=dict)


# =============================================================================
# APLICACIÓN FASTAPI
# =============================================================================

# Estado global de la aplicación
class AppState:
    orchestrator: Optional[SuperAssistantOrchestrator] = None
    memory_manager: Optional[MemoryManager] = None
    guardrails: Optional[GuardrailsManager] = None
    skill_registry: Optional[SkillRegistry] = None
    hitl_manager: Optional[HITLManager] = None


app_state = AppState()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Gestiona el ciclo de vida de la aplicación."""
    # Startup
    print("🚀 Iniciando Super Asistente...")
    
    # Inicializar componentes
    app_state.memory_manager = MemoryManager(
        memory_system=create_memory_system(backend="in_memory")
    )
    
    app_state.guardrails = create_default_guardrails()
    app_state.skill_registry = create_skill_registry_with_defaults()
    app_state.hitl_manager = create_hitl_manager(mode="console")
    
    app_state.orchestrator = create_orchestrator(
        memory_backend="in_memory",
        enable_checkpoints=True
    )
    
    print("✅ Super Asistente iniciado correctamente")
    
    yield
    
    # Shutdown
    print("🛑 Cerrando Super Asistente...")


# Crear aplicación
app = FastAPI(
    title="Super Assistant API",
    description="API del Super Asistente con Capital Cognitivo",
    version="1.0.0",
    lifespan=lifespan
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =============================================================================
# DEPENDENCIAS
# =============================================================================

def get_orchestrator() -> SuperAssistantOrchestrator:
    if app_state.orchestrator is None:
        raise HTTPException(status_code=503, detail="Orchestrator not initialized")
    return app_state.orchestrator


def get_memory_manager() -> MemoryManager:
    if app_state.memory_manager is None:
        raise HTTPException(status_code=503, detail="Memory manager not initialized")
    return app_state.memory_manager


def get_guardrails() -> GuardrailsManager:
    if app_state.guardrails is None:
        raise HTTPException(status_code=503, detail="Guardrails not initialized")
    return app_state.guardrails


def get_skill_registry() -> SkillRegistry:
    if app_state.skill_registry is None:
        raise HTTPException(status_code=503, detail="Skill registry not initialized")
    return app_state.skill_registry


def get_hitl_manager() -> HITLManager:
    if app_state.hitl_manager is None:
        raise HTTPException(status_code=503, detail="HITL manager not initialized")
    return app_state.hitl_manager


# =============================================================================
# ENDPOINTS
# =============================================================================

@app.get("/", response_model=Dict[str, str])
async def root():
    """Endpoint raíz."""
    return {
        "name": "Super Assistant API",
        "version": "1.0.0",
        "docs": "/docs"
    }


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    return HealthResponse(
        status="healthy",
        version="1.0.0",
        timestamp=datetime.utcnow().isoformat(),
        components={
            "orchestrator": "ok" if app_state.orchestrator else "not_initialized",
            "memory": "ok" if app_state.memory_manager else "not_initialized",
            "guardrails": "ok" if app_state.guardrails else "not_initialized",
            "skills": "ok" if app_state.skill_registry else "not_initialized",
            "hitl": "ok" if app_state.hitl_manager else "not_initialized"
        }
    )


@app.post("/chat", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    orchestrator: SuperAssistantOrchestrator = Depends(get_orchestrator)
):
    """
    Endpoint principal de chat.
    Procesa un mensaje y retorna la respuesta del Super Asistente.
    """
    start_time = datetime.utcnow()
    
    try:
        # Generar session_id si no se proporciona
        session_id = request.session_id or str(uuid.uuid4())
        
        # Procesar mensaje
        result = await orchestrator.process(
            message=request.message,
            user_id=request.user_id,
            session_id=session_id
        )
        
        # Extraer respuesta
        messages = result.get("messages", [])
        last_message = messages[-1] if messages else {}
        response_content = last_message.get("content", "")
        
        end_time = datetime.utcnow()
        execution_time = int((end_time - start_time).total_seconds() * 1000)
        
        return ChatResponse(
            response=response_content,
            session_id=session_id,
            agent_contributions=result.get("subagent_results", {}),
            tools_used=[],  # TODO: extract from result
            execution_time_ms=execution_time,
            success=True
        )
        
    except Exception as e:
        return ChatResponse(
            response="",
            session_id=request.session_id or "",
            success=False,
            error=str(e)
        )


@app.post("/chat/stream")
async def chat_stream(
    request: ChatRequest,
    orchestrator: SuperAssistantOrchestrator = Depends(get_orchestrator)
):
    """
    Endpoint de chat con streaming.
    Retorna eventos de la ejecución en tiempo real.
    """
    from fastapi.responses import StreamingResponse
    import json
    
    session_id = request.session_id or str(uuid.uuid4())
    
    async def event_generator():
        try:
            async for event in orchestrator.stream(
                message=request.message,
                user_id=request.user_id,
                session_id=session_id
            ):
                yield f"data: {json.dumps(event, default=str)}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'error': str(e)})}\n\n"
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream"
    )


# =============================================================================
# ENDPOINTS DE MEMORIA
# =============================================================================

@app.post("/memory/store")
async def store_memory(
    request: MemoryRequest,
    memory_manager: MemoryManager = Depends(get_memory_manager)
):
    """Almacena un item en memoria."""
    from core.models import MemoryType
    
    memory_type = MemoryType(request.memory_type)
    
    memory_id = await memory_manager.memory_system.remember(
        content=request.content,
        memory_type=memory_type,
        user_id=request.user_id,
        session_id=request.session_id
    )
    
    return {
        "success": True,
        "memory_id": memory_id
    }


@app.post("/memory/search", response_model=MemorySearchResponse)
async def search_memory(
    request: MemorySearchRequest,
    memory_manager: MemoryManager = Depends(get_memory_manager)
):
    """Busca en la memoria."""
    result = await memory_manager.memory_system.recall(
        query=request.query,
        user_id=request.user_id,
        session_id=request.session_id,
        top_k=request.top_k
    )
    
    return MemorySearchResponse(
        results=[
            {
                "id": m.id,
                "content": m.content,
                "type": m.memory_type,
                "score": m.score
            }
            for m in result
        ],
        total_count=len(result),
        query=request.query
    )


@app.get("/memory/preferences/{user_id}")
async def get_user_preferences(
    user_id: str,
    memory_manager: MemoryManager = Depends(get_memory_manager)
):
    """Obtiene las preferencias de un usuario."""
    preferences = await memory_manager.memory_system.get_user_preferences(user_id)
    return {"user_id": user_id, "preferences": preferences}


# =============================================================================
# ENDPOINTS DE SKILLS
# =============================================================================

@app.get("/skills")
async def list_skills(
    registry: SkillRegistry = Depends(get_skill_registry)
):
    """Lista todas las skills disponibles."""
    return {
        "skills": registry.list_all(),
        "definitions": registry.get_definitions()
    }


@app.post("/skills/execute", response_model=SkillExecuteResponse)
async def execute_skill(
    request: SkillExecuteRequest,
    registry: SkillRegistry = Depends(get_skill_registry)
):
    """Ejecuta una skill."""
    result = await registry.execute(
        name=request.skill_name,
        parameters=request.parameters
    )
    
    return SkillExecuteResponse(
        success=result.success,
        output=result.output,
        error=result.error,
        execution_time_ms=result.execution_time_ms
    )


# =============================================================================
# ENDPOINTS DE SEGURIDAD
# =============================================================================

@app.get("/security/alerts")
async def get_security_alerts(
    limit: int = 50,
    guardrails: GuardrailsManager = Depends(get_guardrails)
):
    """Obtiene alertas de seguridad."""
    alerts = guardrails.get_alerts(limit=limit)
    return {
        "alerts": [
            {
                "id": a.alert_id,
                "type": a.alert_type,
                "severity": a.severity.value,
                "reason": a.reason,
                "timestamp": a.timestamp.isoformat()
            }
            for a in alerts
        ]
    }


# =============================================================================
# ENDPOINTS DE HITL
# =============================================================================

@app.get("/hitl/pending")
async def get_pending_approvals(
    hitl_manager: HITLManager = Depends(get_hitl_manager)
):
    """Obtiene solicitudes pendientes de aprobación."""
    pending = hitl_manager.get_pending_requests()
    return {
        "pending": [
            {
                "request_id": r.request_id,
                "reason": r.reason,
                "created_at": r.created_at.isoformat()
            }
            for r in pending
        ]
    }


@app.post("/hitl/approve")
async def submit_approval(
    request: ApprovalRequest,
    hitl_manager: HITLManager = Depends(get_hitl_manager)
):
    """Envía una decisión de aprobación."""
    from hitl.hitl_system import ApprovalDecision
    
    try:
        decision = ApprovalDecision(request.decision)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid decision")
    
    # TODO: Implementar cola de respuestas
    return {
        "success": True,
        "request_id": request.request_id,
        "decision": request.decision
    }


# =============================================================================
# MAIN
# =============================================================================

def create_app() -> FastAPI:
    """Factory para crear la aplicación."""
    return app


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

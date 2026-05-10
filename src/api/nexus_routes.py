"""
NEXUS Chat Routes - API endpoints para interactuar con el Super Agente NEXUS

Endpoints:
- POST /nexus/chat - Enviar mensaje a NEXUS
- POST /nexus/chat/stream - Enviar mensaje y recibir respuesta en streaming
- GET /nexus/status - Estado del sistema NEXUS
- GET /nexus/domains - Lista de dominios disponibles
- GET /nexus/roles - Lista de roles IOVBA disponibles
"""

import asyncio
import json
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime

from fastapi import (
    APIRouter,
    HTTPException,
    Depends,
    WebSocket,
    WebSocketDisconnect,
    Query,
    Header,
)
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from src.config.database import get_db
from src.config.settings import settings
from src.iovba.nexus_super_agent import (
    NEXUSSuperAgent,
    NEXUSConfig,
    NEXUS_BRAND,
    get_nexus,
    reset_nexus,
)
from src.iovba.groups import IOVBADomain, IOVBARole

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/nexus",
    tags=["nexus"],
    responses={404: {"description": "Not found"}},
)


# ============================================
# Request/Response Models
# ============================================

class NEXUSChatRequest(BaseModel):
    """Request para chat con NEXUS"""
    message: str = Field(..., description="Mensaje del usuario", min_length=1)
    domain: Optional[str] = Field(None, description="Dominio específico (opcional)")
    role: Optional[str] = Field(None, description="Rol IOVBA específico (opcional)")
    context: Optional[Dict[str, Any]] = Field(None, description="Contexto adicional")
    stream: bool = Field(False, description="Si es True, retorna respuesta en streaming")


class NEXUSChatResponse(BaseModel):
    """Response del chat con NEXUS"""
    content: str
    domain: str
    domain_brand: str
    confidence: float
    roles_consulted: List[str]
    thinking_process: Dict[str, Any]
    timestamp: str
    status: str = "success"


class NEXUSStatusResponse(BaseModel):
    """Response del estado de NEXUS"""
    id: str
    name: str
    full_name: str
    status: str
    domains_available: int
    llm_configured: bool
    model: str
    capital: Dict[str, Any]
    last_interactions: int


class DomainInfo(BaseModel):
    """Información de un dominio"""
    domain: str
    name: str
    elegant_name: str
    tagline: str
    icon: str
    color: str
    description: str


class RoleInfo(BaseModel):
    """Información de un rol"""
    role: str
    elegant_name: str
    tagline: str
    description: str
    icon: str
    color: str


# ============================================
# Helper Functions
# ============================================

def get_nexus_instance() -> NEXUSSuperAgent:
    """Get NEXUS instance with API key from settings"""
    api_key = settings.OPENROUTER_API_KEY
    return get_nexus(api_key=api_key)


# ============================================
# API Routes
# ============================================

@router.get("/", response_model=Dict[str, Any])
async def nexus_root():
    """Root endpoint con información de NEXUS"""
    return {
        "name": NEXUS_BRAND["name"],
        "full_name": NEXUS_BRAND["full_name"],
        "tagline": NEXUS_BRAND["tagline"],
        "description": NEXUS_BRAND["description"],
        "version": "1.0.0",
        "endpoints": {
            "chat": "/nexus/chat",
            "chat_stream": "/nexus/chat/stream",
            "websocket": "/nexus/ws",
            "status": "/nexus/status",
            "domains": "/nexus/domains",
            "roles": "/nexus/roles",
        },
    }


@router.post("/chat", response_model=NEXUSChatResponse)
async def chat_with_nexus(
    request: NEXUSChatRequest,
    db: Session = Depends(get_db),
):
    """
    Enviar un mensaje a NEXUS y recibir una respuesta inteligente.
    
    NEXUS detectará automáticamente el dominio más apropiado y
    coordinará con los roles IOVBA relevantes.
    """
    try:
        nexus = get_nexus_instance()
        
        # Validate domain if provided
        domain = None
        if request.domain:
            valid_domains = [
                "swe", "salud", "deportes", "noticias", "quimica",
                "biologia", "biotecnologia", "geopolitica", "finanzas",
                "legal", "educacion", "investigacion", "marketing", "custom"
            ]
            if request.domain.lower() in valid_domains:
                domain = request.domain.lower()
        
        # Validate role if provided
        role = None
        if request.role:
            valid_roles = ["investigador", "observador", "validador", "builder", "asistente"]
            if request.role.lower() in valid_roles:
                role = request.role.lower()
        
        # Process query
        response = await nexus.process_query(
            query=request.message,
            domain=domain,
            role=role,
            context=request.context,
        )
        
        return NEXUSChatResponse(
            content=response.content,
            domain=response.domain,
            domain_brand=response.domain_brand,
            confidence=response.confidence,
            roles_consulted=response.roles_consulted,
            thinking_process=response.thinking_process,
            timestamp=response.timestamp,
        )
        
    except Exception as e:
        logger.error(f"Error in NEXUS chat: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/chat/stream")
async def chat_stream_with_nexus(
    request: NEXUSChatRequest,
    db: Session = Depends(get_db),
):
    """
    Enviar un mensaje a NEXUS y recibir respuesta en streaming.
    
    La respuesta se envía token por token usando Server-Sent Events.
    """
    try:
        nexus = get_nexus_instance()
        
        # Validate domain if provided
        domain = None
        if request.domain:
            valid_domains = [
                "swe", "salud", "deportes", "noticias", "quimica",
                "biologia", "biotecnologia", "geopolitica", "finanzas",
                "legal", "educacion", "investigacion", "marketing", "custom"
            ]
            if request.domain.lower() in valid_domains:
                domain = request.domain.lower()
        
        # Validate role if provided
        role = None
        if request.role:
            valid_roles = ["investigador", "observador", "validador", "builder", "asistente"]
            if request.role.lower() in valid_roles:
                role = request.role.lower()
        
        async def generate():
            """Generate SSE stream"""
            # First, send metadata
            detected_domain, confidence = nexus.detect_domain(request.message) if not domain else (domain, 0.8)
            
            metadata = {
                "type": "metadata",
                "domain": detected_domain,
                "confidence": confidence,
                "timestamp": datetime.utcnow().isoformat(),
            }
            yield f"data: {json.dumps(metadata)}\n\n"
            
            # Then stream the response
            async for chunk in nexus.stream_response(
                query=request.message,
                domain=domain,
                role=role,
                context=request.context,
            ):
                data = json.dumps({"type": "content", "chunk": chunk})
                yield f"data: {data}\n\n"
            
            # Send completion signal
            completion = {"type": "done", "timestamp": datetime.utcnow().isoformat()}
            yield f"data: {json.dumps(completion)}\n\n"
        
        return StreamingResponse(
            generate(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",
            },
        )
        
    except Exception as e:
        logger.error(f"Error in NEXUS stream chat: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.websocket("/ws")
async def nexus_websocket(websocket: WebSocket):
    """
    WebSocket endpoint para chat interactivo con NEXUS.
    
    Permite comunicación bidireccional en tiempo real.
    
    Mensaje de entrada esperado:
    {
        "type": "message",
        "content": "Tu mensaje aquí",
        "domain": "opcional",
        "role": "opcional"
    }
    """
    await websocket.accept()
    logger.info("NEXUS WebSocket connection established")
    
    try:
        nexus = get_nexus_instance()
        
        # Send welcome message
        welcome = {
            "type": "welcome",
            "message": f"Conectado a {NEXUS_BRAND['name']}",
            "domains": len(nexus.group_manager.groups),
            "timestamp": datetime.utcnow().isoformat(),
        }
        await websocket.send_json(welcome)
        
        while True:
            # Receive message
            data = await websocket.receive_json()
            
            if data.get("type") == "ping":
                await websocket.send_json({"type": "pong"})
                continue
            
            if data.get("type") == "message":
                message = data.get("content", "")
                domain = data.get("domain")
                role = data.get("role")
                
                if not message:
                    await websocket.send_json({
                        "type": "error",
                        "message": "Mensaje vacío"
                    })
                    continue
                
                # Process and stream response
                try:
                    detected_domain, confidence = nexus.detect_domain(message)
                    
                    # Send metadata
                    await websocket.send_json({
                        "type": "metadata",
                        "domain": detected_domain,
                        "confidence": confidence,
                    })
                    
                    # Stream response
                    full_response = ""
                    async for chunk in nexus.stream_response(
                        query=message,
                        domain=domain,
                        role=role,
                    ):
                        full_response += chunk
                        await websocket.send_json({
                            "type": "chunk",
                            "content": chunk,
                        })
                    
                    # Send completion
                    await websocket.send_json({
                        "type": "complete",
                        "domain": detected_domain,
                        "full_response_length": len(full_response),
                    })
                    
                except Exception as e:
                    logger.error(f"Error processing message: {e}")
                    await websocket.send_json({
                        "type": "error",
                        "message": str(e),
                    })
            
    except WebSocketDisconnect:
        logger.info("NEXUS WebSocket disconnected")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        try:
            await websocket.close()
        except:
            pass


@router.get("/status", response_model=NEXUSStatusResponse)
async def get_nexus_status():
    """Obtener el estado actual del sistema NEXUS"""
    try:
        nexus = get_nexus_instance()
        status = nexus.get_status()
        return NEXUSStatusResponse(**status)
    except Exception as e:
        logger.error(f"Error getting NEXUS status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/domains", response_model=List[DomainInfo])
async def get_domains():
    """Obtener lista de dominios disponibles"""
    try:
        nexus = get_nexus_instance()
        domains = nexus.get_available_domains()
        return [DomainInfo(**d) for d in domains]
    except Exception as e:
        logger.error(f"Error getting domains: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/roles", response_model=List[RoleInfo])
async def get_roles():
    """Obtener lista de roles IOVBA disponibles"""
    try:
        nexus = get_nexus_instance()
        roles = nexus.get_available_roles()
        return [RoleInfo(**r) for r in roles]
    except Exception as e:
        logger.error(f"Error getting roles: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/reset")
async def reset_nexus_instance():
    """Resetear la instancia de NEXUS (útil para testing o reconfiguración)"""
    try:
        reset_nexus()
        return {"status": "reset", "message": "NEXUS instance has been reset"}
    except Exception as e:
        logger.error(f"Error resetting NEXUS: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/capital")
async def get_capital():
    """Obtener el capital cognitivo acumulado de NEXUS"""
    try:
        nexus = get_nexus_instance()
        return {
            "total_engrams": nexus.capital.total_engrams,
            "total_interactions": nexus.capital.total_interactions,
            "capital_value": nexus.capital.capital_value,
            "learning_score": nexus.capital.learning_score,
            "last_interactions": nexus.interaction_history[-10:] if nexus.interaction_history else [],
        }
    except Exception as e:
        logger.error(f"Error getting capital: {e}")
        raise HTTPException(status_code=500, detail=str(e))

"""
RICCO AI - Simple Server for Demo
"""
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="RICCO AI",
    description="RICCO AI - Multi-agent orchestration with A2UI",
    version="2.0.0",
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {
        "service": "RICCO AI",
        "version": "2.0.0",
        "status": "running",
        "features": {
            "multi_agent": True,
            "a2a_protocol": True,
            "mcp_support": True,
            "langgraph": True,
        },
        "integrations": {
            "openrouter": "configured" if os.getenv("OPENROUTER_API_KEY") else "not configured",
            "default_model": os.getenv("DEFAULT_MODEL", "openrouter/free"),
        }
    }

@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "service": "RICCO AI",
        "version": "2.0.0"
    }

@app.get("/api/v1/agents")
def list_agents():
    return {
        "agents": [
            {"id": "nexus-super-agent", "name": "NEXUS Super Agent", "type": "orchestrator"},
            {"id": "commerce-assistant", "name": "Commerce Assistant", "type": "assistant"},
            {"id": "health-assistant", "name": "Health Assistant", "type": "assistant"},
            {"id": "logistics-assistant", "name": "Logistics Assistant", "type": "assistant"},
            {"id": "finance-assistant", "name": "Finance Assistant", "type": "assistant"},
        ]
    }

@app.get("/api/v1/mcp-arsenal")
def list_mcp_tools():
    return {
        "tools": [
            {"name": "mcp-postgres", "description": "PostgreSQL database operations"},
            {"name": "mcp-redis", "description": "Redis cache operations"},
            {"name": "mcp-stripe", "description": "Stripe payment integration"},
            {"name": "mcp-calendar", "description": "Calendar management"},
            {"name": "mcp-google-maps", "description": "Google Maps integration"},
            {"name": "mcp-pdf", "description": "PDF document processing"},
        ]
    }

@app.post("/api/v1/chat")
async def chat(message: dict):
    """Simple chat endpoint for demo"""
    user_message = message.get("message", "")
    return {
        "response": f"Echo: {user_message}",
        "status": "success",
        "agent": "demo-agent"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

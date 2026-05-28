# Intelligent Warehouse Blueprint Skill

Multi-Agent Intelligent Warehouse assistant for warehouse operations using NVIDIA AI Blueprints.

## Description

This skill provides tools for warehouse operations management including equipment tracking, operations coordination, safety compliance, demand forecasting, and document processing. Built on NVIDIA's AI Blueprint architecture with LangGraph orchestration.

## When to Use

- Equipment and asset management queries
- Task and workflow coordination
- Safety monitoring and compliance
- Demand forecasting and inventory optimization
- Document processing (BOL, invoices, receipts)
- Warehouse telemetry and real-time monitoring

## Blueprint Source

Based on: [NVIDIA Multi-Agent-Intelligent-Warehouse](https://github.com/NVIDIA-AI-Blueprints/Multi-Agent-Intelligent-Warehouse)

## Tools

### Equipment & Asset Operations Agent

| Tool | Description |
|------|-------------|
| `assign_equipment` | Assign equipment to operators or tasks |
| `get_equipment_status` | Get real-time equipment status |
| `get_equipment_telemetry` | Get equipment telemetry data (battery, temperature) |
| `create_maintenance_request` | Schedule equipment maintenance |
| `update_equipment_location` | Update equipment location tracking |
| `get_equipment_utilization` | Get equipment utilization analytics |
| `create_equipment_reservation` | Reserve equipment for future use |
| `get_equipment_history` | Get equipment operation history |

### Operations Coordination Agent

| Tool | Description |
|------|-------------|
| `create_task` | Create new warehouse task |
| `assign_task` | Assign task to worker |
| `optimize_pick_path` | Optimize warehouse pick path |
| `get_task_status` | Get task status and progress |
| `update_task_progress` | Update task completion status |
| `get_performance_metrics` | Get KPI metrics and performance |
| `create_work_order` | Create maintenance work order |
| `get_task_history` | Get task history and logs |

### Safety & Compliance Agent

| Tool | Description |
|------|-------------|
| `log_incident` | Log safety incident |
| `start_checklist` | Start safety checklist procedure |
| `broadcast_alert` | Broadcast emergency alert |
| `create_corrective_action` | Create corrective action item |
| `lockout_tagout_request` | Submit LOTO request |
| `near_miss_capture` | Report near-miss incident |
| `retrieve_sds` | Retrieve Safety Data Sheet |

### Forecasting Agent

| Tool | Description |
|------|-------------|
| `get_forecast` | Get demand forecast for SKU |
| `get_batch_forecast` | Get batch forecast for multiple SKUs |
| `get_reorder_recommendations` | Get AI-powered reorder suggestions |
| `get_model_performance` | Get forecasting model performance |
| `get_forecast_dashboard` | Get forecasting dashboard data |
| `get_business_intelligence` | Get BI analytics and trends |

### Document Processing Agent

| Tool | Description |
|------|-------------|
| `upload_document` | Upload document for OCR processing |
| `get_document_status` | Check document processing status |
| `get_extraction_results` | Get structured data extraction results |
| `get_document_analytics` | Get document processing analytics |

## Architecture

```
User Query → LangGraph Orchestrator → Agent Router
                                         ↓
                    ┌────────────────────┼────────────────────┐
                    ↓                    ↓                    ↓
            Equipment Agent    Operations Agent    Safety Agent
                    ↓                    ↓                    ↓
            MCP Tool Execution → PostgreSQL/TimescaleDB
                                Milvus Vector DB
                                NVIDIA NIMs
```

## Configuration

### Environment Variables

```bash
# NVIDIA API Keys
NVIDIA_API_KEY=nvapi-xxx
NEMO_API_KEY=nvapi-xxx

# Database
POSTGRES_HOST=localhost
POSTGRES_PORT=5435
MILVUS_HOST=localhost
MILVUS_PORT=19530

# Redis Cache
REDIS_HOST=localhost
REDIS_PORT=6379
```

### Integration with DeerFlow

```python
from deerflow.agents import WarehouseAgent

agent = WarehouseAgent(
    model="nvidia/llama-3.3-nemotron-super-49b-v1.5",
    agents=["equipment", "operations", "safety", "forecasting", "document"]
)

response = await agent.chat("What equipment needs maintenance?")
```

## GPU Requirements

| Component | Minimum GPU | Recommended |
|-----------|-------------|-------------|
| LLM Inference | 1x A100 80GB | 1x H100 80GB |
| Embedding | 1x L40S | 1x A100 |
| RAPIDS Forecasting | 1x T4 | 1x A100 |

## API Endpoints

- `POST /api/v1/chat` - Chat with multi-agent system
- `GET /api/v1/equipment` - Equipment management
- `GET /api/v1/forecasting/dashboard` - Forecasting dashboard
- `POST /api/v1/document/upload` - Document processing

## Example Usage

```python
# Equipment status check
result = await tools.get_equipment_status(asset_id="FORK-001")

# Demand forecast
forecast = await tools.get_forecast(sku="SKU-12345", days=30)

# Safety incident
incident = await tools.log_incident(
    type="near_miss",
    location="Zone A",
    description="Forklift near collision"
)
```

## References

- [NVIDIA AI Blueprints](https://build.nvidia.com/)
- [LangGraph Documentation](https://langchain-ai.github.io/langgraph/)
- [RAPIDS cuML](https://rapids.ai/)
- [Milvus Vector DB](https://milvus.io/)

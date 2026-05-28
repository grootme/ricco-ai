"""
NVIDIA Blueprints MCP Server - FIXED VERSION

Model Context Protocol server for NVIDIA AI Blueprints.
Exposes all blueprint tools via MCP protocol with proper dynamic imports.
"""

import asyncio
import json
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime
import logging
from importlib import import_module

from pydantic import BaseModel, Field

# Configure structured logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class MCPTool(BaseModel):
    """MCP Tool definition"""
    name: str
    description: str
    input_schema: Dict[str, Any]
    handler: Optional[Callable] = None
    category: str = "general"


class MCPPrompt(BaseModel):
    """MCP Prompt definition"""
    name: str
    description: str
    arguments: List[Dict[str, Any]]


class MCPResource(BaseModel):
    """MCP Resource definition"""
    uri: str
    name: str
    description: str
    mime_type: str = "application/json"


# Tool registry cache
_tool_implementations: Dict[str, Callable] = {}


def _load_tool_implementations():
    """Load all tool implementations from nvidia_blueprints modules."""
    global _tool_implementations
    
    if _tool_implementations:
        return _tool_implementations
    
    try:
        # Import all blueprint tool modules
        from src.tools.nvidia_blueprints import (
            # Intelligent Warehouse
            assign_equipment, get_equipment_status, get_equipment_telemetry,
            create_maintenance_request, get_equipment_utilization, create_task,
            optimize_pick_path, get_performance_metrics, log_incident,
            retrieve_sds, get_forecast, get_reorder_recommendations,
            upload_document, get_extraction_results,
            
            # Retail Commerce
            create_checkout_session, apply_promotion, get_recommendations,
            search_products_commerce, process_payment,
            
            # Retail Shopping
            search_products_text, search_products_image, add_to_cart,
            get_cart, get_personalized_recommendations,
            
            # Genomics
            run_bwa_mem, run_deepvariant, predict_variant_effect,
            run_germline_wes_pipeline,
            
            # Voice Agent
            transcribe_audio, synthesize_speech, create_voice_pipeline,
            start_conversation,
            
            # Portfolio Optimization
            optimize_mean_cvar, compute_efficient_frontier, backtest_strategy,
            generate_scenarios,
            
            # Streaming RAG
            start_stream_ingestion, query_streaming_rag, process_sdr_signal,
            
            # Biomedical Research
            create_research_plan, generate_molecules, predict_docking,
            search_literature,
            
            # Ambient Patient
            start_patient_intake, schedule_appointment, get_medication_info,
            process_voice_input,
            
            # Financial Distillation
            create_flywheel_run, launch_finetuning, run_evaluation,
            classify_financial_news,
        )
        
        # Warehouse tools
        _tool_implementations.update({
            "warehouse_assign_equipment": assign_equipment,
            "warehouse_get_equipment_status": get_equipment_status,
            "warehouse_get_equipment_telemetry": get_equipment_telemetry,
            "warehouse_create_maintenance_request": create_maintenance_request,
            "warehouse_get_equipment_utilization": get_equipment_utilization,
            "warehouse_create_task": create_task,
            "warehouse_optimize_pick_path": optimize_pick_path,
            "warehouse_get_performance_metrics": get_performance_metrics,
            "warehouse_log_incident": log_incident,
            "warehouse_retrieve_sds": retrieve_sds,
            "warehouse_get_forecast": get_forecast,
            "warehouse_get_reorder_recommendations": get_reorder_recommendations,
            "warehouse_upload_document": upload_document,
            "warehouse_get_extraction_results": get_extraction_results,
        })
        
        # Commerce tools
        _tool_implementations.update({
            "commerce_create_checkout": create_checkout_session,
            "commerce_apply_promotion": apply_promotion,
            "commerce_get_recommendations": get_recommendations,
            "commerce_search_products": search_products_commerce,
            "commerce_process_payment": process_payment,
        })
        
        # Shopping tools
        _tool_implementations.update({
            "shopping_search_products": search_products_text,
            "shopping_search_by_image": search_products_image,
            "shopping_add_to_cart": add_to_cart,
            "shopping_get_cart": get_cart,
            "shopping_get_recommendations": get_personalized_recommendations,
        })
        
        # Genomics tools
        _tool_implementations.update({
            "genomics_run_bwa_mem": run_bwa_mem,
            "genomics_run_deepvariant": run_deepvariant,
            "genomics_predict_variant_effect": predict_variant_effect,
            "genomics_run_germline_wes": run_germline_wes_pipeline,
        })
        
        # Voice tools
        _tool_implementations.update({
            "voice_transcribe": transcribe_audio,
            "voice_synthesize": synthesize_speech,
            "voice_create_pipeline": create_voice_pipeline,
            "voice_start_conversation": start_conversation,
        })
        
        # Portfolio tools
        _tool_implementations.update({
            "portfolio_optimize_mean_cvar": optimize_mean_cvar,
            "portfolio_compute_frontier": compute_efficient_frontier,
            "portfolio_backtest": backtest_strategy,
            "portfolio_generate_scenarios": generate_scenarios,
        })
        
        # Streaming RAG tools
        _tool_implementations.update({
            "streaming_start_ingestion": start_stream_ingestion,
            "streaming_query_rag": query_streaming_rag,
            "streaming_process_sdr": process_sdr_signal,
        })
        
        # Biomedical tools
        _tool_implementations.update({
            "biomedical_create_research_plan": create_research_plan,
            "biomedical_generate_molecules": generate_molecules,
            "biomedical_predict_docking": predict_docking,
            "biomedical_search_literature": search_literature,
        })
        
        # Patient tools
        _tool_implementations.update({
            "patient_start_intake": start_patient_intake,
            "patient_schedule_appointment": schedule_appointment,
            "patient_get_medication_info": get_medication_info,
            "patient_process_voice": process_voice_input,
        })
        
        # Distillation tools
        _tool_implementations.update({
            "distillation_create_flywheel": create_flywheel_run,
            "distillation_launch_finetuning": launch_finetuning,
            "distillation_run_evaluation": run_evaluation,
            "distillation_classify_news": classify_financial_news,
        })
        
        logger.info(
            "Tool implementations loaded successfully",
            extra={
                "count": len(_tool_implementations),
                "timestamp": datetime.utcnow().isoformat()
            }
        )
        
    except ImportError as e:
        logger.error(
            "Failed to load tool implementations",
            extra={
                "error": str(e),
                "error_type": type(e).__name__,
                "timestamp": datetime.utcnow().isoformat()
            },
            exc_info=True
        )
        logger.warning("MCP server will run in mock mode - tools will return mock responses")
    
    return _tool_implementations


class NVIDIABlueprintsMCPServer:
    """
    MCP Server for NVIDIA AI Blueprints
    
    Provides tools for 10 blueprint categories:
    - Intelligent Warehouse (14 tools)
    - Retail Commerce (5 tools)
    - Retail Shopping (5 tools)
    - Genomics Analysis (4 tools)
    - Voice Agent (4 tools)
    - Portfolio Optimization (4 tools)
    - Streaming RAG (3 tools)
    - Biomedical Research (4 tools)
    - Ambient Patient (4 tools)
    - Financial Distillation (4 tools)
    """
    
    SERVER_NAME = "nvidia-blueprints-mcp"
    SERVER_VERSION = "2.0.0"
    
    def __init__(self):
        self.tools: Dict[str, MCPTool] = {}
        self.prompts: Dict[str, MCPPrompt] = {}
        self.resources: Dict[str, MCPResource] = {}
        self._tool_handlers: Dict[str, Callable] = {}
        self._register_all_tools()
        self._load_handlers()
        
    def _register_all_tools(self):
        """Register all blueprint tools"""
        
        # ========== INTELLIGENT WAREHOUSE (14 tools) ==========
        warehouse_tools = [
            ("warehouse_assign_equipment", "Assign equipment to an operator", ["asset_id", "operator_id"], ["task_id"]),
            ("warehouse_get_equipment_status", "Get real-time equipment status", ["asset_id"], []),
            ("warehouse_get_equipment_telemetry", "Get equipment telemetry data", ["asset_id"], ["metrics"]),
            ("warehouse_create_maintenance_request", "Create maintenance request", ["asset_id", "issue_type", "description"], ["priority", "scheduled_date"]),
            ("warehouse_get_equipment_utilization", "Get equipment utilization analytics", ["asset_id"], ["period"]),
            ("warehouse_create_task", "Create warehouse task", ["task_type", "location"], ["priority", "assigned_to", "deadline"]),
            ("warehouse_optimize_pick_path", "Optimize pick path for order", ["order_items"], ["start_location", "end_location"]),
            ("warehouse_get_performance_metrics", "Get KPI metrics", [], ["department", "period"]),
            ("warehouse_log_incident", "Log safety incident", ["incident_type", "location", "description"], ["severity", "involved_parties"]),
            ("warehouse_retrieve_sds", "Retrieve Safety Data Sheet", ["chemical_name"], []),
            ("warehouse_get_forecast", "Get demand forecast for SKU", ["sku"], ["forecast_days", "model"]),
            ("warehouse_get_reorder_recommendations", "Get reorder recommendations", [], ["category"]),
            ("warehouse_upload_document", "Upload document for OCR", ["file_path"], ["document_type", "extract_fields"]),
            ("warehouse_get_extraction_results", "Get document extraction results", ["document_id"], []),
        ]
        
        for name, desc, required, optional in warehouse_tools:
            self._register_tool_with_schema(name, desc, required, optional, "warehouse")
        
        # ========== RETAIL COMMERCE (5 tools) ==========
        commerce_tools = [
            ("commerce_create_checkout", "Create checkout session", ["cart_items", "user_id"], ["currency"]),
            ("commerce_get_recommendations", "Get personalized recommendations", ["user_id"], ["context", "limit"]),
            ("commerce_apply_promotion", "Apply promotion code", ["session_id", "promo_code"], []),
            ("commerce_search_products", "Search products", ["query"], ["filters", "limit"]),
            ("commerce_process_payment", "Process payment", ["session_id", "payment_method"], []),
        ]
        
        for name, desc, required, optional in commerce_tools:
            self._register_tool_with_schema(name, desc, required, optional, "commerce")
        
        # ========== RETAIL SHOPPING (5 tools) ==========
        shopping_tools = [
            ("shopping_search_products", "Search products by text", ["query"], ["filters", "limit"]),
            ("shopping_search_by_image", "Search products by image", ["image_url"], ["category_hint"]),
            ("shopping_add_to_cart", "Add product to cart", ["product_id"], ["quantity"]),
            ("shopping_get_cart", "Get shopping cart contents", [], []),
            ("shopping_get_recommendations", "Get personalized recommendations", ["user_id"], ["limit"]),
        ]
        
        for name, desc, required, optional in shopping_tools:
            self._register_tool_with_schema(name, desc, required, optional, "shopping")
        
        # ========== GENOMICS (4 tools) ==========
        genomics_tools = [
            ("genomics_run_bwa_mem", "Run GPU-accelerated BWA-MEM alignment", ["fastq1", "reference"], ["fastq2"]),
            ("genomics_run_deepvariant", "Run DeepVariant variant calling", ["bam_file", "reference"], ["model_type"]),
            ("genomics_predict_variant_effect", "Predict variant functional impact", ["vcf_file", "gene_annotations"], []),
            ("genomics_run_germline_wes", "Run germline WES pipeline", ["fastq1", "fastq2"], ["reference"]),
        ]
        
        for name, desc, required, optional in genomics_tools:
            self._register_tool_with_schema(name, desc, required, optional, "genomics")
        
        # ========== VOICE AGENT (4 tools) ==========
        voice_tools = [
            ("voice_transcribe", "Transcribe audio with Parakeet ASR", ["audio_path"], ["language"]),
            ("voice_synthesize", "Synthesize speech with Magpie TTS", ["text"], ["voice", "language"]),
            ("voice_create_pipeline", "Create voice agent pipeline", [], ["asr_model", "llm_model", "tts_model", "enable_interruption"]),
            ("voice_start_conversation", "Start voice conversation", [], ["session_id"]),
        ]
        
        for name, desc, required, optional in voice_tools:
            self._register_tool_with_schema(name, desc, required, optional, "voice")
        
        # ========== PORTFOLIO OPTIMIZATION (4 tools) ==========
        portfolio_tools = [
            ("portfolio_optimize_mean_cvar", "Mean-CVaR portfolio optimization", ["expected_returns", "covariance_matrix"], ["alpha"]),
            ("portfolio_compute_frontier", "Compute efficient frontier", ["expected_returns", "covariance_matrix"], ["n_points"]),
            ("portfolio_backtest", "Backtest trading strategy", ["strategy"], ["start_date", "end_date"]),
            ("portfolio_generate_scenarios", "Generate Monte Carlo scenarios", [], ["n_scenarios", "time_horizon"]),
        ]
        
        for name, desc, required, optional in portfolio_tools:
            self._register_tool_with_schema(name, desc, required, optional, "portfolio")
        
        # ========== STREAMING RAG (3 tools) ==========
        streaming_tools = [
            ("streaming_start_ingestion", "Start real-time data ingestion", ["source"], ["channel_id"]),
            ("streaming_query_rag", "Query RAG with time-aware filtering", ["query"], ["time_window", "channel"]),
            ("streaming_process_sdr", "Process SDR signal", ["signal_data"], ["frequency", "sample_rate"]),
        ]
        
        for name, desc, required, optional in streaming_tools:
            self._register_tool_with_schema(name, desc, required, optional, "streaming_rag")
        
        # ========== BIOMEDICAL RESEARCH (4 tools) ==========
        biomedical_tools = [
            ("biomedical_create_research_plan", "Create structured research plan", ["topic"], ["enable_virtual_screening"]),
            ("biomedical_generate_molecules", "Generate molecules with MolMIM", ["seed_smiles"], ["target_properties", "num_molecules"]),
            ("biomedical_predict_docking", "Predict protein-ligand docking", ["protein_pdb", "molecule_smiles"], []),
            ("biomedical_search_literature", "Search biomedical literature", ["query"], ["sources", "max_results"]),
        ]
        
        for name, desc, required, optional in biomedical_tools:
            self._register_tool_with_schema(name, desc, required, optional, "biomedical")
        
        # ========== AMBIENT PATIENT (4 tools) ==========
        patient_tools = [
            ("patient_start_intake", "Initialize patient intake session", [], ["session_type", "language"]),
            ("patient_schedule_appointment", "Schedule medical appointment", ["patient_id", "provider_id", "date", "time"], []),
            ("patient_get_medication_info", "Get medication information", ["medication_name"], ["include_interactions"]),
            ("patient_process_voice", "Process voice input from patient", ["audio_input"], ["language"]),
        ]
        
        for name, desc, required, optional in patient_tools:
            self._register_tool_with_schema(name, desc, required, optional, "patient")
        
        # ========== FINANCIAL DISTILLATION (4 tools) ==========
        distillation_tools = [
            ("distillation_create_flywheel", "Create Data Flywheel experiment", ["dataset_id", "student_model"], ["teacher_model"]),
            ("distillation_launch_finetuning", "Launch LoRA fine-tuning job", ["dataset_id", "model"], ["method"]),
            ("distillation_run_evaluation", "Run model evaluation", ["model_id", "test_dataset"], ["metrics"]),
            ("distillation_classify_news", "Classify financial news headline", ["headline"], ["model_id"]),
        ]
        
        for name, desc, required, optional in distillation_tools:
            self._register_tool_with_schema(name, desc, required, optional, "distillation")
        
        logger.info(
            "Registered tools across blueprint categories",
            extra={
                "total_tools": len(self.tools),
                "categories": 10,
                "timestamp": datetime.utcnow().isoformat()
            }
        )
    
    def _register_tool_with_schema(
        self,
        name: str,
        description: str,
        required_params: List[str],
        optional_params: List[str],
        category: str
    ):
        """Register a tool with auto-generated schema."""
        properties = {}
        for param in required_params:
            properties[param] = {"type": "string", "description": f"{param.replace('_', ' ')}"}
        for param in optional_params:
            properties[param] = {"type": "string", "description": f"{param.replace('_', ' ')} (optional)"}
        
        self._register_tool(
            name=name,
            description=description,
            input_schema={
                "type": "object",
                "properties": properties,
                "required": required_params
            },
            category=category
        )
    
    def _register_tool(
        self,
        name: str,
        description: str,
        input_schema: Dict[str, Any],
        category: str = "general"
    ):
        """Register a tool with the MCP server"""
        self.tools[name] = MCPTool(
            name=name,
            description=description,
            input_schema=input_schema,
            handler=None,
            category=category
        )
    
    def _load_handlers(self):
        """Load tool handlers from implementations."""
        implementations = _load_tool_implementations()
        for name, handler in implementations.items():
            if name in self.tools:
                self.tools[name].handler = handler
                self._tool_handlers[name] = handler
                logger.debug(f"Loaded handler for {name}")
        
        logger.info(
            "Tool handlers loaded",
            extra={
                "handlers_count": len(self._tool_handlers),
                "total_tools": len(self.tools),
                "timestamp": datetime.utcnow().isoformat()
            }
        )
    
    async def list_tools(self) -> List[Dict[str, Any]]:
        """List all available tools (MCP protocol)"""
        return [
            {
                "name": tool.name,
                "description": tool.description,
                "inputSchema": tool.input_schema,
                "category": tool.category
            }
            for tool in self.tools.values()
        ]
    
    async def call_tool(self, name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a tool call (MCP protocol)"""
        if name not in self.tools:
            return {
                "error": f"Tool '{name}' not found",
                "available_tools": list(self.tools.keys())
            }
        
        tool = self.tools[name]
        
        # Check if we have a real handler
        if name in self._tool_handlers:
            try:
                handler = self._tool_handlers[name]
                # LangChain tools use .invoke()
                if hasattr(handler, 'invoke'):
                    result = handler.invoke(arguments)
                elif callable(handler):
                    result = handler(**arguments)
                else:
                    result = handler
                
                return {
                    "success": True,
                    "tool": name,
                    "result": result,
                    "timestamp": datetime.utcnow().isoformat()
                }
            except Exception as e:
                logger.error(
                    f"Error executing tool",
                    extra={
                        "tool_name": name,
                        "error": str(e),
                        "error_type": type(e).__name__,
                        "timestamp": datetime.utcnow().isoformat()
                    },
                    exc_info=True
                )
                return {
                    "success": False,
                    "error": str(e),
                    "error_type": type(e).__name__,
                    "tool": name,
                    "timestamp": datetime.utcnow().isoformat()
                }
        
        # Mock response for tools without handlers
        return {
            "success": True,
            "tool": name,
            "arguments": arguments,
            "result": f"[MOCK] Tool {name} executed with arguments: {arguments}",
            "timestamp": datetime.utcnow().isoformat(),
            "note": "This is a mock response. Load real handlers for production use."
        }
    
    async def list_resources(self) -> List[Dict[str, Any]]:
        """List available resources (MCP protocol)"""
        return [
            {
                "uri": "nvidia-blueprints://config",
                "name": "Blueprints Configuration",
                "description": "Configuration for all NVIDIA blueprints",
                "mimeType": "application/json"
            },
            {
                "uri": "nvidia-blueprints://models",
                "name": "Available Models",
                "description": "List of available NVIDIA NIM models",
                "mimeType": "application/json"
            },
            {
                "uri": "nvidia-blueprints://tools/status",
                "name": "Tools Status",
                "description": "Status of all registered tools",
                "mimeType": "application/json"
            }
        ]
    
    async def read_resource(self, uri: str) -> Dict[str, Any]:
        """Read a resource (MCP protocol)"""
        if uri == "nvidia-blueprints://config":
            return {
                "contents": [{
                    "uri": uri,
                    "mimeType": "application/json",
                    "text": json.dumps({
                        "blueprints": [
                            "intelligent_warehouse",
                            "retail_commerce",
                            "retail_shopping",
                            "genomics",
                            "voice_agent",
                            "portfolio_optimization",
                            "streaming_rag",
                            "biomedical_research",
                            "ambient_patient",
                            "financial_distillation"
                        ],
                        "version": self.SERVER_VERSION,
                        "tools_registered": len(self.tools),
                        "handlers_loaded": len(self._tool_handlers)
                    }, indent=2)
                }]
            }
        
        if uri == "nvidia-blueprints://tools/status":
            tool_status = {}
            for name, tool in self.tools.items():
                tool_status[name] = {
                    "category": tool.category,
                    "has_handler": name in self._tool_handlers,
                    "description": tool.description[:50] + "..." if len(tool.description) > 50 else tool.description
                }
            
            return {
                "contents": [{
                    "uri": uri,
                    "mimeType": "application/json",
                    "text": json.dumps(tool_status, indent=2)
                }]
            }
        
        return {"error": f"Resource not found: {uri}"}
    
    def get_server_info(self) -> Dict[str, Any]:
        """Get server information"""
        return {
            "name": self.SERVER_NAME,
            "version": self.SERVER_VERSION,
            "tools_registered": len(self.tools),
            "handlers_loaded": len(self._tool_handlers),
            "categories": list(set(t.category for t in self.tools.values())),
            "status": "ready" if self._tool_handlers else "mock_mode"
        }


# Server instance for MCP protocol
server = NVIDIABlueprintsMCPServer()


async def main():
    """Main entry point for MCP server"""
    print(f"Starting {server.SERVER_NAME} v{server.SERVER_VERSION}")
    print(f"Registered tools: {len(server.tools)}")
    print(f"Handlers loaded: {len(server._tool_handlers)}")
    
    # List all tools by category
    tools_by_category: Dict[str, List[str]] = {}
    for name, tool in server.tools.items():
        if tool.category not in tools_by_category:
            tools_by_category[tool.category] = []
        tools_by_category[tool.category].append(name)
    
    print("\nTools by category:")
    for category, tools in sorted(tools_by_category.items()):
        print(f"  {category}: {len(tools)} tools")
        for tool in tools[:3]:
            print(f"    - {tool}")
        if len(tools) > 3:
            print(f"    ... and {len(tools) - 3} more")


if __name__ == "__main__":
    asyncio.run(main())

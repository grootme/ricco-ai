"""
NVIDIA AI Blueprints Integration Module

This module provides integration with NVIDIA AI Blueprints:
- AI-Q Research Agent
- RAG Pipeline
- Video Search & Summarization
- Data Flywheel
- Digital Human
- Ambient Healthcare
- Retail Commerce
- Ambient Patient
- Biomedical Research
- Financial Distillation
- Genomics
- Industrial
- Intelligent Warehouse
- Multi-Agent
- Portfolio Optimization
- Retail Shopping
- Streaming RAG
- Virtual Assistant
- Voice Agent
"""

from .base import BlueprintBase, BlueprintConfig, BlueprintResult, BlueprintStatus, BlueprintType
from .aiq import AIQResearchBlueprint
from .rag import RAGBlueprint
from .video_search import (
    VideoSearchBlueprint,
    DataFlywheelBlueprint,
    DigitalHumanBlueprint,
    HealthcareBlueprint,
    RetailCommerceBlueprint
)
from .extended import (
    AmbientPatientBlueprint,
    BiomedicalResearchBlueprint,
    FinancialDistillationBlueprint,
    GenomicsBlueprint,
    IndustrialBlueprint,
    IntelligentWarehouseBlueprint,
    MultiAgentBlueprint,
    PortfolioOptimizationBlueprint,
    RetailShoppingBlueprint,
    StreamingRAGBlueprint,
    VirtualAssistantBlueprint,
    VoiceAgentBlueprint,
)
from .registry import BlueprintRegistry

__all__ = [
    # Base classes
    "BlueprintBase",
    "BlueprintConfig", 
    "BlueprintResult",
    "BlueprintStatus",
    "BlueprintType",
    # Core blueprints
    "AIQResearchBlueprint",
    "RAGBlueprint",
    "VideoSearchBlueprint",
    "DataFlywheelBlueprint",
    "DigitalHumanBlueprint",
    "HealthcareBlueprint",
    "RetailCommerceBlueprint",
    # Extended blueprints
    "AmbientPatientBlueprint",
    "BiomedicalResearchBlueprint",
    "FinancialDistillationBlueprint",
    "GenomicsBlueprint",
    "IndustrialBlueprint",
    "IntelligentWarehouseBlueprint",
    "MultiAgentBlueprint",
    "PortfolioOptimizationBlueprint",
    "RetailShoppingBlueprint",
    "StreamingRAGBlueprint",
    "VirtualAssistantBlueprint",
    "VoiceAgentBlueprint",
    # Registry
    "BlueprintRegistry",
]

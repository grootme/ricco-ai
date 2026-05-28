"""
Blueprint Base Classes and Types

Provides the foundation for all NVIDIA AI Blueprint integrations.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from enum import Enum
import time
import uuid


class BlueprintStatus(str, Enum):
    """Status of a blueprint execution"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class BlueprintType(str, Enum):
    """Types of NVIDIA AI Blueprints"""
    AIQ_RESEARCH = "aiq_research"
    RAG = "rag"
    VIDEO_SEARCH = "video_search"
    DATA_FLYWHEEL = "data_flywheel"
    DIGITAL_HUMAN = "digital_human"
    HEALTHCARE = "healthcare"
    RETAIL_COMMERCE = "retail_commerce"
    # Extended blueprints
    AMBIENT_PATIENT = "ambient_patient"
    BIOMEDICAL_RESEARCH = "biomedical_research"
    FINANCIAL_DISTILLATION = "financial_distillation"
    GENOMICS = "genomics"
    INDUSTRIAL = "industrial"
    INTELLIGENT_WAREHOUSE = "intelligent_warehouse"
    MULTI_AGENT = "multi_agent"
    PORTFOLIO_OPTIMIZATION = "portfolio_optimization"
    RETAIL_SHOPPING = "retail_shopping"
    STREAMING_RAG = "streaming_rag"
    VIRTUAL_ASSISTANT = "virtual_assistant"
    VOICE_AGENT = "voice_agent"


@dataclass
class BlueprintConfig:
    """Configuration for a blueprint execution"""
    blueprint_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    description: str = ""
    model: str = "openrouter/free"
    max_tokens: int = 4096
    temperature: float = 0.7
    timeout: int = 300  # seconds
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "blueprint_id": self.blueprint_id,
            "name": self.name,
            "description": self.description,
            "model": self.model,
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
            "timeout": self.timeout,
            "metadata": self.metadata,
        }


@dataclass
class BlueprintResult:
    """Result of a blueprint execution"""
    blueprint_id: str
    status: BlueprintStatus
    output: Any = None
    error: Optional[str] = None
    execution_time: float = 0.0
    tokens_used: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: float = field(default_factory=time.time)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "blueprint_id": self.blueprint_id,
            "status": self.status.value,
            "output": self.output,
            "error": self.error,
            "execution_time": self.execution_time,
            "tokens_used": self.tokens_used,
            "metadata": self.metadata,
            "created_at": self.created_at,
        }
    
    @classmethod
    def success(cls, blueprint_id: str, output: Any, **kwargs) -> "BlueprintResult":
        return cls(
            blueprint_id=blueprint_id,
            status=BlueprintStatus.COMPLETED,
            output=output,
            **kwargs
        )
    
    @classmethod
    def failure(cls, blueprint_id: str, error: str, **kwargs) -> "BlueprintResult":
        return cls(
            blueprint_id=blueprint_id,
            status=BlueprintStatus.FAILED,
            error=error,
            **kwargs
        )


class BlueprintBase(ABC):
    """
    Base class for all NVIDIA AI Blueprint integrations.
    
    Provides common interface and utilities for blueprint implementations.
    """
    
    blueprint_type: BlueprintType = None
    description: str = ""
    version: str = "1.0.0"
    
    def __init__(self, config: Optional[BlueprintConfig] = None):
        self.config = config or BlueprintConfig()
        self._status = BlueprintStatus.PENDING
        self._start_time: Optional[float] = None
    
    @property
    def name(self) -> str:
        return self.config.name or self.__class__.__name__
    
    @property
    def status(self) -> BlueprintStatus:
        return self._status
    
    @abstractmethod
    async def execute(self, input_data: Dict[str, Any]) -> BlueprintResult:
        """
        Execute the blueprint with the given input data.
        
        Args:
            input_data: Input data for the blueprint
            
        Returns:
            BlueprintResult with the execution result
        """
        pass
    
    @abstractmethod
    def validate_input(self, input_data: Dict[str, Any]) -> bool:
        """
        Validate the input data for this blueprint.
        
        Args:
            input_data: Input data to validate
            
        Returns:
            True if valid, False otherwise
        """
        pass
    
    def get_info(self) -> Dict[str, Any]:
        """Get information about this blueprint"""
        return {
            "type": self.blueprint_type.value if self.blueprint_type else "unknown",
            "name": self.name,
            "description": self.description,
            "version": self.version,
            "config": self.config.to_dict(),
        }
    
    def _start_execution(self):
        """Mark the start of execution"""
        self._status = BlueprintStatus.RUNNING
        self._start_time = time.time()
    
    def _end_execution(self, success: bool = True):
        """Mark the end of execution"""
        self._status = BlueprintStatus.COMPLETED if success else BlueprintStatus.FAILED
    
    def _get_execution_time(self) -> float:
        """Get the execution time in seconds"""
        if self._start_time is None:
            return 0.0
        return time.time() - self._start_time


class SimulatedBlueprint(BlueprintBase):
    """
    Simulated blueprint for testing without NVIDIA infrastructure.
    
    Provides mock responses that simulate real blueprint behavior.
    """
    
    async def execute(self, input_data: Dict[str, Any]) -> BlueprintResult:
        self._start_execution()
        
        try:
            if not self.validate_input(input_data):
                return BlueprintResult.failure(
                    self.config.blueprint_id,
                    "Invalid input data",
                    execution_time=self._get_execution_time()
                )
            
            # Simulate processing
            result = await self._simulate_execution(input_data)
            
            self._end_execution(success=True)
            return BlueprintResult.success(
                self.config.blueprint_id,
                result,
                execution_time=self._get_execution_time(),
                tokens_used=self._estimate_tokens(input_data, result)
            )
            
        except Exception as e:
            self._end_execution(success=False)
            return BlueprintResult.failure(
                self.config.blueprint_id,
                str(e),
                execution_time=self._get_execution_time()
            )
    
    async def _simulate_execution(self, input_data: Dict[str, Any]) -> Any:
        """Override this method to provide simulation logic"""
        return {"simulated": True, "input": input_data}
    
    def _estimate_tokens(self, input_data: Dict[str, Any], output: Any) -> int:
        """Estimate tokens used (rough approximation)"""
        input_str = str(input_data)
        output_str = str(output)
        return (len(input_str) + len(output_str)) // 4  # ~4 chars per token
    
    def validate_input(self, input_data: Dict[str, Any]) -> bool:
        return isinstance(input_data, dict) and len(input_data) > 0

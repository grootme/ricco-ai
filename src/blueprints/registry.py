"""
NVIDIA Blueprints Registry

Central registry for all available NVIDIA AI Blueprints.
Provides discovery, instantiation, and management of blueprints.

Consolidated: Uses shared enums and configuration-driven loading.
"""

from typing import Dict, List, Type, Optional, Any
from dataclasses import dataclass, field
import os
import json
from pathlib import Path

from .base import (
    BlueprintBase, BlueprintConfig, BlueprintResult,
)

# Import consolidated enums from single source of truth
try:
    from src.shared.enums import BlueprintType, BlueprintStatus
except ImportError:
    # Fallback for direct imports
    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from shared.enums import BlueprintType, BlueprintStatus


@dataclass
class BlueprintInfo:
    """Information about a registered blueprint"""
    name: str
    blueprint_type: BlueprintType
    description: str
    version: str
    path: str
    enabled: bool = True
    dependencies: List[str] = field(default_factory=list)
    config_schema: Dict[str, Any] = field(default_factory=dict)
    

class BlueprintRegistry:
    """
    Central registry for NVIDIA AI Blueprints.
    
    Provides:
    - Blueprint discovery and registration
    - Instance creation and management
    - Configuration management
    - Execution tracking
    """
    
    _instance = None
    _blueprints: Dict[str, BlueprintInfo] = {}
    _instances: Dict[str, BlueprintBase] = {}
    _results: Dict[str, BlueprintResult] = {}
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self._blueprints_path = Path("/home/z/my-project/nvidia-blueprints")
        self._discover_blueprints()
    
    def _discover_blueprints(self):
        """
        Discover all available blueprints from configuration.
        
        OCP-Compliant: Blueprints loaded from JSON config, not hardcoded.
        Fallback to defaults if config not found.
        """
        config_path = Path(__file__).parent.parent / "shared" / "data" / "blueprints.json"
        
        if config_path.exists():
            try:
                with open(config_path) as f:
                    config = json.load(f)
                
                for bp_data in config.get("entities", []):
                    metadata = bp_data.get("metadata", {})
                    bp_type_str = bp_data.get("id", "").upper().replace("-", "_")
                    
                    # Map config ID to BlueprintType enum
                    try:
                        bp_type = BlueprintType.from_string(bp_type_str)
                    except ValueError:
                        # Try common mappings
                        type_mapping = {
                            "aiq": BlueprintType.AIQ_RESEARCH,
                            "rag": BlueprintType.RAG,
                            "video_search": BlueprintType.VIDEO_SEARCH,
                            "data_flywheel": BlueprintType.DATA_FLYWHEEL,
                            "digital_human": BlueprintType.DIGITAL_HUMAN,
                            "healthcare": BlueprintType.HEALTHCARE,
                            "retail_commerce": BlueprintType.RETAIL_COMMERCE,
                            "multi_agent": BlueprintType.MULTI_AGENT,
                            "portfolio_optimization": BlueprintType.PORTFOLIO_OPTIMIZATION,
                            "intelligent_warehouse": BlueprintType.INTELLIGENT_WAREHOUSE,
                            "industrial": BlueprintType.INDUSTRIAL,
                            "virtual_assistant": BlueprintType.VIRTUAL_ASSISTANT,
                            "streaming_rag": BlueprintType.STREAMING_RAG,
                            "genomics": BlueprintType.GENOMICS,
                            "retail_shopping": BlueprintType.RETAIL_SHOPPING,
                            "biomedical_research": BlueprintType.BIOMEDICAL_RESEARCH,
                            "financial_distillation": BlueprintType.FINANCIAL_DISTILLATION,
                            "ambient_patient": BlueprintType.AMBIENT_PATIENT,
                            "voice_agent": BlueprintType.VOICE_AGENT,
                        }
                        bp_type = type_mapping.get(bp_data.get("id"))
                        if not bp_type:
                            continue
                    
                    self._blueprints[bp_data.get("id")] = BlueprintInfo(
                        name=bp_data.get("name"),
                        blueprint_type=bp_type,
                        description=bp_data.get("description", ""),
                        version=bp_data.get("version", "1.0.0"),
                        path=metadata.get("path", str(self._blueprints_path / bp_data.get("id"))),
                        enabled=True,
                        dependencies=metadata.get("dependencies", []),
                    )
                
                return
            except Exception as e:
                import logging
                logging.warning(f"Failed to load blueprints from config: {e}")
        
        # Fallback to minimal blueprints if config not found
        self._register_fallback_blueprints()
    
    def _register_fallback_blueprints(self):
        """Register minimal fallback blueprints if config not available."""
        fallback_blueprints = [
            {
                "name": "rag",
                "blueprint_type": BlueprintType.RAG,
                "description": "RAG Blueprint - Retrieval-Augmented Generation",
                "path": str(self._blueprints_path / "rag"),
                "dependencies": ["nemo-retriever", "milvus"],
            },
            {
                "name": "aiq",
                "blueprint_type": BlueprintType.AIQ_RESEARCH,
                "description": "AI-Q Research Agent",
                "path": str(self._blueprints_path / "aiq"),
                "dependencies": ["nemo-agent-toolkit"],
            },
        ]
        
        for config in fallback_blueprints:
            self._blueprints[config["name"]] = BlueprintInfo(
                name=config["name"],
                blueprint_type=config["blueprint_type"],
                description=config["description"],
                version="1.0.0",
                path=config["path"],
                enabled=True,
                dependencies=config["dependencies"],
            )
    
    def _get_blueprint_version(self, path: Path) -> str:
        """Get the version of a blueprint from its config"""
        pyproject = path / "pyproject.toml"
        if pyproject.exists():
            try:
                import tomllib
                with open(pyproject, "rb") as f:
                    data = tomllib.load(f)
                    return data.get("project", {}).get("version", "1.0.0")
            except Exception:
                pass
        return "1.0.0"
    
    def list_blueprints(self) -> List[Dict[str, Any]]:
        """List all registered blueprints"""
        return [
            {
                "name": info.name,
                "type": info.blueprint_type.value,
                "description": info.description,
                "version": info.version,
                "enabled": info.enabled,
                "dependencies": info.dependencies,
                "path": info.path,
            }
            for info in self._blueprints.values()
        ]
    
    def get_blueprint(self, name: str) -> Optional[BlueprintInfo]:
        """Get information about a specific blueprint"""
        return self._blueprints.get(name)
    
    def get_blueprint_config(self, name: str) -> Dict[str, Any]:
        """Get the configuration schema for a blueprint"""
        info = self._blueprints.get(name)
        if not info:
            return {}
        
        config_path = Path(info.path) / "configs"
        configs = {}
        
        if config_path.exists():
            for cfg_file in config_path.glob("*.yml"):
                configs[cfg_file.name] = str(cfg_file)
            for cfg_file in config_path.glob("*.yaml"):
                configs[cfg_file.name] = str(cfg_file)
        
        return configs
    
    def get_blueprint_readme(self, name: str) -> str:
        """Get the README content for a blueprint"""
        info = self._blueprints.get(name)
        if not info:
            return ""
        
        readme_path = Path(info.path) / "README.md"
        if readme_path.exists():
            return readme_path.read_text()[:5000]  # First 5000 chars
        return ""
    
    def get_blueprint_structure(self, name: str) -> Dict[str, Any]:
        """Get the directory structure of a blueprint"""
        info = self._blueprints.get(name)
        if not info:
            return {}
        
        blueprint_path = Path(info.path)
        structure = {
            "name": name,
            "path": str(blueprint_path),
            "directories": [],
            "files": [],
        }
        
        for item in blueprint_path.iterdir():
            if item.is_dir():
                if not item.name.startswith('.') and item.name != '__pycache__':
                    structure["directories"].append(item.name)
            else:
                if not item.name.startswith('.'):
                    structure["files"].append(item.name)
        
        return structure
    
    def store_result(self, result: BlueprintResult):
        """Store a blueprint execution result"""
        self._results[result.blueprint_id] = result
    
    def get_result(self, blueprint_id: str) -> Optional[BlueprintResult]:
        """Get a stored result"""
        return self._results.get(blueprint_id)
    
    def get_all_results(self) -> List[Dict[str, Any]]:
        """Get all stored results"""
        return [r.to_dict() for r in self._results.values()]


# Global registry instance
registry = BlueprintRegistry()

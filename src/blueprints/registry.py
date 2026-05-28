"""
NVIDIA Blueprints Registry

Central registry for all available NVIDIA AI Blueprints.
Provides discovery, instantiation, and management of blueprints.
"""

from typing import Dict, List, Type, Optional, Any
from dataclasses import dataclass, field
import os
import json
from pathlib import Path

from .base import (
    BlueprintBase, BlueprintConfig, BlueprintResult,
    BlueprintType, BlueprintStatus
)


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
        """Discover all available blueprints from cloned repositories"""
        blueprint_configs = [
            {
                "name": "aiq",
                "blueprint_type": BlueprintType.AIQ_RESEARCH,
                "description": "AI-Q Research Agent - Enterprise-grade research with deep reasoning",
                "path": str(self._blueprints_path / "aiq"),
                "dependencies": ["nemo-agent-toolkit", "langchain"],
            },
            {
                "name": "rag",
                "blueprint_type": BlueprintType.RAG,
                "description": "RAG Blueprint - Retrieval-Augmented Generation with multimodal support",
                "path": str(self._blueprints_path / "rag"),
                "dependencies": ["nemo-retriever", "milvus"],
            },
            {
                "name": "video-search",
                "blueprint_type": BlueprintType.VIDEO_SEARCH,
                "description": "Video Search & Summarization - AI agents for video analytics",
                "path": str(self._blueprints_path / "video-search-and-summarization"),
                "dependencies": ["riva", "vision-models"],
            },
            {
                "name": "data-flywheel",
                "blueprint_type": BlueprintType.DATA_FLYWHEEL,
                "description": "Data Flywheel - Autonomous data improvement pipeline",
                "path": str(self._blueprints_path / "data-flywheel"),
                "dependencies": ["nemo-microservices"],
            },
            {
                "name": "digital-human",
                "blueprint_type": BlueprintType.DIGITAL_HUMAN,
                "description": "Digital Human - 3D animated virtual assistant interface",
                "path": str(self._blueprints_path / "digital-human"),
                "dependencies": ["omniverse", "audio2face"],
            },
            {
                "name": "healthcare",
                "blueprint_type": BlueprintType.HEALTHCARE,
                "description": "Ambient Healthcare - SOAP note generation with speech-to-text",
                "path": str(self._blueprints_path / "ambient-healthcare-agents"),
                "dependencies": ["riva", "nemotron"],
            },
            {
                "name": "retail-commerce",
                "blueprint_type": BlueprintType.RETAIL_COMMERCE,
                "description": "Retail Agentic Commerce - Intelligent commerce middleware",
                "path": str(self._blueprints_path / "Retail-Agentic-Commerce"),
                "dependencies": ["nemo-agent-toolkit"],
            },
        ]
        
        for config in blueprint_configs:
            blueprint_path = Path(config["path"])
            if blueprint_path.exists():
                self._blueprints[config["name"]] = BlueprintInfo(
                    name=config["name"],
                    blueprint_type=config["blueprint_type"],
                    description=config["description"],
                    version=self._get_blueprint_version(blueprint_path),
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

"""Centralized Skill Registry for NVIDIA Blueprint integration.

Provides a unified registry for all skills with discovery,
categorization, and metadata management.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Callable
import json
from pathlib import Path

logger = logging.getLogger(__name__)


class SkillCategory(str, Enum):
    """Categories for skills."""
    DOCUMENT = "document"
    VISUALIZATION = "visualization"
    AI = "ai"
    BLUEPRINT = "blueprint"
    COMMUNICATION = "communication"
    DATA = "data"
    DEVELOPMENT = "development"
    PRODUCTIVITY = "productivity"
    RESEARCH = "research"
    FINANCE = "finance"
    INDUSTRIAL = "industrial"


class SkillStatus(str, Enum):
    """Status of a skill."""
    ACTIVE = "active"
    DEPRECATED = "deprecated"
    EXPERIMENTAL = "experimental"
    DISABLED = "disabled"


@dataclass
class SkillMetadata:
    """Metadata for a skill."""
    skill_id: str
    name: str
    description: str
    version: str = "1.0.0"
    category: SkillCategory = SkillCategory.AI
    status: SkillStatus = SkillStatus.ACTIVE
    author: str = ""
    tags: List[str] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)
    tools: List[str] = field(default_factory=list)
    examples: List[str] = field(default_factory=list)
    documentation_url: str = ""
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "skill_id": self.skill_id,
            "name": self.name,
            "description": self.description,
            "version": self.version,
            "category": self.category.value,
            "status": self.status.value,
            "author": self.author,
            "tags": self.tags,
            "dependencies": self.dependencies,
            "tools": self.tools,
            "examples": self.examples,
            "documentation_url": self.documentation_url,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "metadata": self.metadata,
        }


class SkillRegistry:
    """
    Centralized registry for all skills.
    
    Provides:
    - Skill registration and discovery
    - Category-based organization
    - Search functionality
    - Dependency tracking
    """
    
    def __init__(self):
        self._skills: Dict[str, SkillMetadata] = {}
        self._by_category: Dict[SkillCategory, List[str]] = {
            cat: [] for cat in SkillCategory
        }
        self._by_tag: Dict[str, List[str]] = {}
        self._tool_to_skill: Dict[str, str] = {}
        
        # Initialize with built-in skills
        self._register_builtin_skills()
    
    def _register_builtin_skills(self) -> None:
        """Register built-in skills for blueprints."""
        builtin_skills = [
            # ============================================
            # NVIDIA Blueprint Skills - NEW
            # ============================================
            
            # AI-Q Research Agent
            SkillMetadata(
                skill_id="aiq-blueprint",
                name="AI-Q Research Agent",
                description="NVIDIA AI-Q Blueprint for intelligent research agents with deep research, document analysis, and report generation",
                category=SkillCategory.RESEARCH,
                tags=["nvidia", "research", "agents", "documents", "analysis"],
                tools=[
                    "aiq_init", "aiq_create_research_task", "aiq_search_sources",
                    "aiq_analyze_document", "aiq_extract_knowledge", "aiq_verify_facts",
                    "aiq_generate_citations", "aiq_synthesize_findings", "aiq_generate_report",
                    "aiq_add_knowledge_base", "aiq_create_workflow", "aiq_execute_workflow",
                    "aiq_get_research_status", "aiq_export_results",
                ],
            ),
            
            # Video Search and Summarization
            SkillMetadata(
                skill_id="video-search-blueprint",
                name="Video Search and Summarization",
                description="NVIDIA Video Search Blueprint for ingesting videos, extracting insights, and interactive Q&A",
                category=SkillCategory.AI,
                tags=["nvidia", "video", "search", "summarization", "multimodal"],
                tools=[
                    "videosearch_init", "videosearch_ingest_video", "videosearch_ingest_stream",
                    "videosearch_extract_frames", "videosearch_transcribe", "videosearch_detect_objects",
                    "videosearch_detect_activities", "videosearch_index_video", "videosearch_search",
                    "videosearch_summarize", "videosearch_qa", "videosearch_create_timeline",
                    "videosearch_export_results",
                ],
            ),
            
            # Virtual Assistant
            SkillMetadata(
                skill_id="virtual-assistant-blueprint",
                name="AI Virtual Assistant",
                description="NVIDIA Virtual Assistant Blueprint for customer service bots with intent recognition and multi-channel support",
                category=SkillCategory.COMMUNICATION,
                tags=["nvidia", "assistant", "chatbot", "customer-service", "nlp"],
                tools=[
                    "va_init", "va_create_persona", "va_define_intents", "va_create_flow",
                    "va_add_knowledge", "va_create_faq", "va_process_message",
                    "va_generate_response", "va_detect_sentiment", "va_handoff",
                    "va_analyze_conversation", "va_get_analytics", "va_train_intent", "va_deploy",
                ],
            ),
            
            # Data Flywheel
            SkillMetadata(
                skill_id="data-flywheel-blueprint",
                name="Data Flywheel",
                description="NVIDIA Data Flywheel Blueprint for continuous AI model improvement through automated data collection and retraining",
                category=SkillCategory.AI,
                tags=["nvidia", "ml-ops", "continuous-learning", "flywheel", "training"],
                tools=[
                    "flywheel_init", "flywheel_configure_collection", "flywheel_add_feedback",
                    "flywheel_curate_data", "flywheel_label_data", "flywheel_create_dataset",
                    "flywheel_train_model", "flywheel_evaluate_model", "flywheel_deploy_model",
                    "flywheel_setup_experiment", "flywheel_analyze_experiment",
                    "flywheel_monitor_performance", "flywheel_detect_drift", "flywheel_get_stats",
                ],
            ),
            
            # Portfolio Optimization
            SkillMetadata(
                skill_id="portfolio-optimization-blueprint",
                name="Portfolio Optimization",
                description="NVIDIA Portfolio Optimization Blueprint for financial portfolio management, risk analysis, and algorithmic trading",
                category=SkillCategory.FINANCE,
                tags=["nvidia", "finance", "portfolio", "optimization", "risk", "trading"],
                tools=[
                    "portfolio_init", "portfolio_create", "portfolio_optimize",
                    "portfolio_analyze_risk", "portfolio_var", "portfolio_stress_test",
                    "portfolio_factor_analysis", "portfolio_backtest", "portfolio_get_data",
                    "portfolio_efficient_frontier", "portfolio_correlation", "portfolio_report",
                ],
            ),
            
            # Intelligent Warehouse
            SkillMetadata(
                skill_id="intelligent-warehouse-blueprint",
                name="Intelligent Warehouse",
                description="NVIDIA Intelligent Warehouse Blueprint for multi-agent warehouse automation, inventory management, and robotics coordination",
                category=SkillCategory.INDUSTRIAL,
                tags=["nvidia", "warehouse", "robotics", "logistics", "automation", "multi-agent"],
                tools=[
                    "warehouse_init", "warehouse_configure_layout", "warehouse_register_robot",
                    "warehouse_create_agent", "warehouse_create_order", "warehouse_assign_task",
                    "warehouse_optimize_picking", "warehouse_track_inventory", "warehouse_predict_demand",
                    "warehouse_coordinate_robots", "warehouse_monitor_performance",
                    "warehouse_simulate", "warehouse_generate_report",
                ],
            ),
            
            # ============================================
            # NVIDIA Blueprint Skills - EXISTING
            # ============================================
            
            # Multi-Agent Blueprint
            SkillMetadata(
                skill_id="multi-agent-blueprint",
                name="Multi-Agent Blueprint",
                description="NVIDIA Multi-Agent Blueprint for orchestrating multiple AI agents with hierarchical task delegation",
                category=SkillCategory.BLUEPRINT,
                tags=["nvidia", "multi-agent", "orchestration", "agents"],
                tools=[
                    "multiagent_init", "multiagent_create_agent", "multiagent_create_lead",
                    "multiagent_delegate_task", "multiagent_send_message", "multiagent_get_status",
                    "multiagent_create_workflow", "multiagent_execute_workflow",
                    "multiagent_debate", "multiagent_merge_results",
                    "multiagent_set_memory", "multiagent_get_memory",
                ],
            ),
            
            # RAG Blueprint
            SkillMetadata(
                skill_id="rag-blueprint",
                name="RAG Blueprint",
                description="NVIDIA RAG Blueprint for retrieval-augmented generation with vector search and citation support",
                category=SkillCategory.BLUEPRINT,
                tags=["nvidia", "rag", "retrieval", "search", "qa"],
                tools=[
                    "rag_init", "rag_ingest_documents", "rag_ingest_url", "rag_ingest_pdf",
                    "rag_create_collection", "rag_search", "rag_hybrid_search",
                    "rag_multi_hop_search", "rag_generate_answer", "rag_query",
                    "rag_add_feedback", "rag_get_stats", "rag_optimize",
                    "rag_delete_documents", "rag_export_collection",
                ],
            ),
            
            # Digital Human Blueprint
            SkillMetadata(
                skill_id="digital-human-blueprint",
                name="Digital Human Blueprint",
                description="NVIDIA Digital Human Blueprint for AI-powered virtual humans with facial animation and speech synthesis",
                category=SkillCategory.BLUEPRINT,
                tags=["nvidia", "avatar", "tts", "animation", "conversation"],
                tools=[
                    "digitalhuman_init", "digitalhuman_create_avatar",
                    "digitalhuman_set_appearance", "digitalhuman_set_expression",
                    "digitalhuman_animate_speech", "digitalhuman_synthesize_speech",
                    "digitalhuman_listen", "digitalhuman_respond",
                    "digitalhuman_set_context", "digitalhuman_create_animation",
                    "digitalhuman_play_animation", "digitalhuman_stream_session",
                    "digitalhuman_analyze_face", "digitalhuman_get_metrics",
                ],
            ),
            
            # Healthcare Blueprint
            SkillMetadata(
                skill_id="healthcare-blueprint",
                name="Healthcare Blueprint",
                description="NVIDIA Healthcare Blueprint for medical AI applications with HIPAA compliance",
                category=SkillCategory.BLUEPRINT,
                tags=["nvidia", "healthcare", "medical", "clinical", "hipaa"],
                tools=[
                    "healthcare_init", "healthcare_extract_clinical",
                    "healthcare_analyze_imaging", "healthcare_check_interactions",
                    "healthcare_analyze_labs", "healthcare_summarize_record",
                    "healthcare_generate_note", "healthcare_predict_risk",
                    "healthcare_code_diagnosis", "healthcare_code_procedure",
                    "healthcare_match_trials", "healthcare_check_guidelines",
                    "healthcare_translate_medical", "healthcare_anonymize",
                    "healthcare_audit_log",
                ],
            ),
            
            # Industrial Blueprint
            SkillMetadata(
                skill_id="industrial-blueprint",
                name="Industrial Blueprint",
                description="NVIDIA Industrial Blueprint for manufacturing, quality inspection, and predictive maintenance",
                category=SkillCategory.INDUSTRIAL,
                tags=["nvidia", "industrial", "manufacturing", "iot", "digital-twin"],
                tools=[
                    "industrial_init", "industrial_setup_camera",
                    "industrial_create_inspection", "industrial_run_inspection",
                    "industrial_setup_sensor", "industrial_predict_maintenance",
                    "industrial_analyze_vibration", "industrial_detect_anomaly",
                    "industrial_create_twin", "industrial_update_twin",
                    "industrial_simulate", "industrial_optimize_process",
                    "industrial_track_inventory", "industrial_monitor_safety",
                    "industrial_track_workers", "industrial_generate_report",
                ],
            ),
            
            # ============================================
            # Document Skills
            # ============================================
            SkillMetadata(
                skill_id="docx",
                name="Document Creation",
                description="Create and edit Word documents",
                category=SkillCategory.DOCUMENT,
                tags=["document", "word", "docx", "office"],
            ),
            SkillMetadata(
                skill_id="pdf",
                name="PDF Processing",
                description="Create and process PDF documents",
                category=SkillCategory.DOCUMENT,
                tags=["document", "pdf", "report"],
            ),
            SkillMetadata(
                skill_id="xlsx",
                name="Spreadsheet Processing",
                description="Create and process Excel spreadsheets",
                category=SkillCategory.DOCUMENT,
                tags=["document", "excel", "spreadsheet", "xlsx"],
            ),
            SkillMetadata(
                skill_id="pptx",
                name="Presentation Creation",
                description="Create and edit PowerPoint presentations",
                category=SkillCategory.DOCUMENT,
                tags=["document", "powerpoint", "presentation", "pptx"],
            ),
            
            # ============================================
            # Visualization Skills
            # ============================================
            SkillMetadata(
                skill_id="charts",
                name="Charts and Diagrams",
                description="Create charts, graphs, and diagrams",
                category=SkillCategory.VISUALIZATION,
                tags=["chart", "diagram", "visualization", "graph"],
            ),
            
            # ============================================
            # AI Skills
            # ============================================
            SkillMetadata(
                skill_id="LLM",
                name="Large Language Model",
                description="Interact with large language models",
                category=SkillCategory.AI,
                tags=["ai", "llm", "chat", "generation"],
            ),
            SkillMetadata(
                skill_id="VLM",
                name="Vision Language Model",
                description="Analyze images with vision-language models",
                category=SkillCategory.AI,
                tags=["ai", "vision", "image", "multimodal"],
            ),
            SkillMetadata(
                skill_id="ASR",
                name="Automatic Speech Recognition",
                description="Convert speech to text",
                category=SkillCategory.AI,
                tags=["ai", "speech", "audio", "transcription"],
            ),
            SkillMetadata(
                skill_id="TTS",
                name="Text to Speech",
                description="Convert text to speech",
                category=SkillCategory.AI,
                tags=["ai", "speech", "audio", "synthesis"],
            ),
            SkillMetadata(
                skill_id="image-generation",
                name="Image Generation",
                description="Generate images from text descriptions",
                category=SkillCategory.AI,
                tags=["ai", "image", "generation", "art"],
            ),
            
            # ============================================
            # Data Skills
            # ============================================
            SkillMetadata(
                skill_id="web-search",
                name="Web Search",
                description="Search the web for information",
                category=SkillCategory.DATA,
                tags=["web", "search", "internet"],
            ),
            SkillMetadata(
                skill_id="web-reader",
                name="Web Reader",
                description="Read and extract content from web pages",
                category=SkillCategory.DATA,
                tags=["web", "scrape", "extract"],
            ),
            
            # ============================================
            # Development Skills
            # ============================================
            SkillMetadata(
                skill_id="fullstack-dev",
                name="Full Stack Development",
                description="Build full stack web applications",
                category=SkillCategory.DEVELOPMENT,
                tags=["development", "web", "fullstack", "nextjs"],
            ),
        ]
        
        for skill in builtin_skills:
            self.register(skill)
    
    def register(self, skill: SkillMetadata) -> None:
        """Register a skill."""
        self._skills[skill.skill_id] = skill
        
        # Index by category
        if skill.skill_id not in self._by_category[skill.category]:
            self._by_category[skill.category].append(skill.skill_id)
        
        # Index by tags
        for tag in skill.tags:
            if tag not in self._by_tag:
                self._by_tag[tag] = []
            if skill.skill_id not in self._by_tag[tag]:
                self._by_tag[tag].append(skill.skill_id)
        
        # Index tools to skill
        for tool in skill.tools:
            self._tool_to_skill[tool] = skill.skill_id
        
        logger.debug(f"Registered skill: {skill.name} ({skill.skill_id})")
    
    def get(self, skill_id: str) -> Optional[SkillMetadata]:
        """Get a skill by ID."""
        return self._skills.get(skill_id)
    
    def get_by_tool(self, tool_name: str) -> Optional[SkillMetadata]:
        """Get the skill that provides a tool."""
        skill_id = self._tool_to_skill.get(tool_name)
        if skill_id:
            return self._skills.get(skill_id)
        return None
    
    def list_all(self) -> List[SkillMetadata]:
        """List all skills."""
        return list(self._skills.values())
    
    def list_by_category(self, category: SkillCategory) -> List[SkillMetadata]:
        """List skills by category."""
        return [self._skills[sid] for sid in self._by_category[category] if sid in self._skills]
    
    def list_by_tag(self, tag: str) -> List[SkillMetadata]:
        """List skills by tag."""
        if tag not in self._by_tag:
            return []
        return [self._skills[sid] for sid in self._by_tag[tag] if sid in self._skills]
    
    def search(self, query: str) -> List[SkillMetadata]:
        """Search skills by name, description, or tags."""
        query = query.lower()
        results = []
        
        for skill in self._skills.values():
            if (
                query in skill.name.lower() or
                query in skill.description.lower() or
                any(query in tag.lower() for tag in skill.tags)
            ):
                results.append(skill)
        
        return results
    
    def get_all_tools(self) -> Dict[str, str]:
        """Get mapping of all tools to their skills."""
        return dict(self._tool_to_skill)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get registry statistics."""
        return {
            "total_skills": len(self._skills),
            "by_category": {
                cat.value: len(skills)
                for cat, skills in self._by_category.items()
            },
            "total_tools": len(self._tool_to_skill),
            "total_tags": len(self._by_tag),
        }


# Global registry instance
skill_registry = SkillRegistry()

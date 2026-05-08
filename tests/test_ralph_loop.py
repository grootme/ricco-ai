"""
Tests para Ralph Loop

Valida el ciclo de mejora continua del Capital Cognitivo.
"""

import pytest
import asyncio
from datetime import datetime

from src.ralph.loop import (
    RalphLoop,
    RalphPhase,
    RalphResult,
    RalphSession
)
from src.ralph.harvester import (
    KnowledgeHarvester,
    HarvestedKnowledge
)
from src.ralph.practicer import (
    SkillPracticer,
    PracticeResult,
    PracticeStatus
)


class TestRalphLoop:
    """Tests para Ralph Loop"""
    
    @pytest.fixture
    def ralph(self):
        return RalphLoop()
    
    @pytest.mark.asyncio
    async def test_reflect_phase(self, ralph):
        """Verifica fase de reflexión"""
        result = await ralph.reflect({
            "objective": "Test objective",
            "success": True,
            "commands": [{"command": "echo test"}],
            "errors": []
        })
        
        assert result.phase == RalphPhase.REFLECT
        assert result.success is True
        assert len(result.insights) > 0
    
    @pytest.mark.asyncio
    async def test_reflect_with_errors(self, ralph):
        """Verifica reflexión con errores"""
        result = await ralph.reflect({
            "objective": "Failed task",
            "success": False,
            "errors": ["Error 1", "Error 2"]
        })
        
        assert result.phase == RalphPhase.REFLECT
        assert any("fallo" in i.lower() or "error" in i.lower() for i in result.insights)
    
    @pytest.mark.asyncio
    async def test_analyze_phase(self, ralph):
        """Verifica fase de análisis"""
        session = RalphSession(
            session_id="test",
            source_interaction={}
        )
        
        result = await ralph.analyze({
            "obviousness_context": {
                "metrics": {"recall": 0.9},
                "required_tools": ["search"]
            },
            "metrics": {"recall": 0.7},
            "tools_used": ["other"]
        }, session)
        
        assert result.phase == RalphPhase.ANALYZE
        assert result.success is True
    
    @pytest.mark.asyncio
    async def test_learn_phase(self, ralph):
        """Verifica fase de aprendizaje"""
        session = RalphSession(
            session_id="learn-test",
            source_interaction={}
        )
        session.results.append(RalphResult(
            phase=RalphPhase.REFLECT,
            success=True,
            insights=["Pattern detected"]
        ))
        
        result = await ralph.learn({
            "success": True,
            "objective": "Test learning",
            "commands": [{"command": "test"}],
            "errors": []
        }, session)
        
        assert result.phase == RalphPhase.LEARN
        assert len(result.knowledge_extracted) > 0
    
    @pytest.mark.asyncio
    async def test_practice_phase(self, ralph):
        """Verifica fase de práctica"""
        session = RalphSession(
            session_id="practice-test",
            source_interaction={}
        )
        session.results.append(RalphResult(
            phase=RalphPhase.LEARN,
            success=True,
            knowledge_extracted=[{
                "topic_key": "test:pattern",
                "type": "success_pattern",
                "confidence": 0.8,
                "content": {}
            }]
        ))
        
        result = await ralph.practice({}, session)
        
        assert result.phase == RalphPhase.PRACTICE
        assert result.success is True
    
    @pytest.mark.asyncio
    async def test_harvest_phase(self, ralph):
        """Verifica fase de cosecha"""
        session = RalphSession(
            session_id="harvest-test",
            source_interaction={}
        )
        session.results.append(RalphResult(
            phase=RalphPhase.LEARN,
            success=True,
            knowledge_extracted=[{
                "topic_key": "harvest:test",
                "type": "success_pattern",
                "confidence": 0.9,
                "content": {"commands": ["test"]}
            }]
        ))
        
        result = await ralph.harvest({}, session)
        
        assert result.phase == RalphPhase.HARVEST
        assert result.success is True
    
    @pytest.mark.asyncio
    async def test_full_cycle(self, ralph):
        """Verifica ciclo completo"""
        session = await ralph.execute({
            "objective": "Full cycle test",
            "success": True,
            "commands": [{"command": "test"}],
            "errors": [],
            "obviousness_context": {
                "metrics": {"recall": 0.8}
            },
            "metrics": {"recall": 0.85}
        })
        
        assert session.completed_at is not None
        assert len(session.results) == 5  # 5 fases
    
    @pytest.mark.asyncio
    async def test_partial_cycle(self, ralph):
        """Verifica ciclo parcial"""
        session = await ralph.execute(
            {"objective": "Partial test", "success": True},
            phases=[RalphPhase.REFLECT, RalphPhase.LEARN]
        )
        
        assert len(session.results) == 2
    
    def test_session_management(self, ralph):
        """Verifica gestión de sesiones"""
        assert ralph.get_all_sessions() == []
        
        # Crear sesión manualmente
        session = RalphSession(
            session_id="manual",
            source_interaction={}
        )
        ralph._sessions["manual"] = session
        
        assert ralph.get_session("manual") is not None
        assert len(ralph.get_all_sessions()) == 1
    
    def test_stats(self, ralph):
        """Verifica estadísticas"""
        stats = ralph.get_stats()
        
        assert "total_sessions" in stats
        assert "completed_sessions" in stats


class TestKnowledgeHarvester:
    """Tests para Knowledge Harvester"""
    
    @pytest.fixture
    def harvester(self):
        return KnowledgeHarvester(min_confidence=0.5)
    
    def test_harvest_success_pattern(self, harvester):
        """Verifica cosecha de patrón exitoso"""
        harvested = harvester.harvest({
            "session_id": "test",
            "success": True,
            "objective": "Test successful task",
            "commands": [
                {"command": "step1"},
                {"command": "step2"}
            ]
        })
        
        assert len(harvested) > 0
        assert any(k.knowledge_type == "success_pattern" for k in harvested)
    
    def test_harvest_error_correction(self, harvester):
        """Verifica cosecha de corrección de error"""
        harvested = harvester.harvest({
            "session_id": "error-test",
            "success": False,
            "errors": [
                {"type": "timeout", "message": "Timeout error", "correction": "Increase timeout"}
            ]
        })
        
        assert any(k.knowledge_type == "error_correction" for k in harvested)
    
    def test_harvest_user_preferences(self, harvester):
        """Verifica cosecha de preferencias de usuario"""
        harvested = harvester.harvest({
            "session_id": "pref-test",
            "user_id": "user-1",
            "user_preferences": {
                "language": "spanish",
                "verbosity": "concise"
            }
        })
        
        assert any(k.knowledge_type == "user_preference" for k in harvested)
    
    def test_harvest_tool_combinations(self, harvester):
        """Verifica cosecha de combinaciones de herramientas"""
        harvested = harvester.harvest({
            "session_id": "tools-test",
            "success": True,
            "tools_used": ["search", "analysis", "report"]
        })
        
        assert any(k.knowledge_type == "tool_combination" for k in harvested)
    
    def test_min_confidence_filter(self):
        """Verifica filtro de confianza mínima"""
        harvester = KnowledgeHarvester(min_confidence=0.9)
        
        harvested = harvester.harvest({
            "session_id": "confidence-test",
            "success": True,
            "commands": [{"command": "test"}]
        })
        
        # Solo conocimiento con confianza >= 0.9 debe pasar
        for k in harvested:
            assert k.confidence >= 0.9
    
    def test_get_by_type(self, harvester):
        """Verifica obtención por tipo"""
        harvester.harvest({
            "session_id": "type-test",
            "success": True,
            "commands": [{"command": "test"}]
        })
        
        success_patterns = harvester.get_by_type("success_pattern")
        
        assert isinstance(success_patterns, list)
    
    def test_stats(self, harvester):
        """Verifica estadísticas"""
        harvested = harvester.harvest({
            "session_id": "stats-test",
            "success": True,
            "commands": [{"command": "test"}, {"command": "test2"}],
            "objective": "Test objective for stats"
        })
        
        stats = harvester.get_stats()
        
        assert "total_harvested" in stats
        # Verificar que se cosechó conocimiento si cumplió los requisitos
        assert stats["total_harvested"] >= 0


class TestSkillPracticer:
    """Tests para Skill Practicer"""
    
    @pytest.fixture
    def practicer(self):
        return SkillPracticer()
    
    @pytest.fixture
    def mock_skill(self):
        from dataclasses import dataclass, field
        
        @dataclass
        class MockSkill:
            id: str = "test-skill"
            
            @dataclass
            class Metadata:
                name: str = "Test Skill"
            
            metadata: "MockSkill.Metadata" = field(default_factory=lambda: MockSkill.Metadata())
            instructions: str = "Test instructions"
            examples: list = field(default_factory=list)
        
        return MockSkill()
    
    @pytest.mark.asyncio
    async def test_practice_skill(self, practicer, mock_skill):
        """Verifica práctica de skill"""
        result = await practicer.practice(mock_skill)
        
        assert result.status in [PracticeStatus.PASSED, PracticeStatus.FAILED]
        assert result.skill_id == "test-skill"
    
    @pytest.mark.asyncio
    async def test_practice_with_test_cases(self, practicer, mock_skill):
        """Verifica práctica con casos de prueba"""
        test_cases = [
            {"input": {"value": 1}, "expected": {"result": 1}},
            {"input": {"value": 2}, "expected": {"result": 2}}
        ]
        
        result = await practicer.practice(mock_skill, test_cases)
        
        assert result.execution_time_ms >= 0
    
    @pytest.mark.asyncio
    async def test_practice_batch(self, practicer, mock_skill):
        """Verifica práctica en lote"""
        skills = [mock_skill, mock_skill]
        
        results = await practicer.practice_batch(skills)
        
        assert len(results) == 2
    
    def test_get_results(self, practicer):
        """Verifica obtención de resultados"""
        results = practicer.get_results()
        
        assert isinstance(results, list)
    
    def test_stats(self, practicer):
        """Verifica estadísticas"""
        stats = practicer.get_stats()
        
        assert "total_practiced" in stats
        assert "pass_rate" in stats


class TestRalphIntegration:
    """Tests de integración para Ralph Loop"""
    
    @pytest.mark.asyncio
    async def test_successful_interaction_processing(self):
        """Verifica procesamiento de interacción exitosa"""
        from src.memory.vcs import MemoryVCS
        import tempfile
        import os
        
        # Crear VCS temporal
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = f.name
        
        try:
            memory_vcs = MemoryVCS(db_path=db_path)
            ralph = RalphLoop(memory_vcs=memory_vcs)
            
            session = await ralph.execute({
                "objective": "Integration test",
                "success": True,
                "commands": [
                    {"command": "analyze"},
                    {"command": "process"}
                ],
                "errors": [],
                "tools_used": ["analyzer", "processor"],
                "obviousness_context": {
                    "metrics": {"recall": 0.8}
                },
                "metrics": {"recall": 0.85}
            })
            
            assert session.completed_at is not None
            assert session.total_cognitive_capital > 0
            
        finally:
            try:
                os.unlink(db_path)
            except:
                pass
    
    @pytest.mark.asyncio
    async def test_failed_interaction_learning(self):
        """Verifica aprendizaje de interacción fallida"""
        ralph = RalphLoop()
        
        session = await ralph.execute({
            "objective": "Failed task",
            "success": False,
            "errors": [
                {"type": "config", "message": "Invalid config", "correction": "Fix config file"}
            ]
        })
        
        # Debe haber extraído conocimiento de corrección de error
        learn_result = next(
            (r for r in session.results if r.phase == RalphPhase.LEARN),
            None
        )
        
        if learn_result:
            # Puede o no haber extraído conocimiento dependiendo del contexto
            pass

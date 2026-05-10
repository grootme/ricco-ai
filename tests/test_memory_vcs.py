"""
Tests para Memory VCS

Valida el sistema de memoria con control de versiones.
"""

import pytest
import tempfile
import os
from pathlib import Path

from src.memory.vcs import (
    MemoryVCS,
    DisclosureLevel,
    MemoryEntry,
    MemoryVersion,
    get_memory_vcs,
    reset_memory_vcs
)


class TestMemoryVCS:
    """Tests para Memory VCS"""
    
    @pytest.fixture
    def temp_db(self):
        """Crea una base de datos temporal para tests"""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = f.name
        yield db_path
        # Cleanup
        try:
            os.unlink(db_path)
        except:
            pass
    
    @pytest.fixture
    def vcs(self, temp_db):
        """Crea una instancia de MemoryVCS para tests"""
        return MemoryVCS(db_path=temp_db, auto_init=True)
    
    def test_initialization(self, temp_db):
        """Verifica inicialización de la base de datos"""
        vcs = MemoryVCS(db_path=temp_db, auto_init=True)
        
        assert Path(temp_db).exists()
        stats = vcs.get_stats()
        assert stats["total_memories"] == 0
    
    def test_create_memory(self, vcs):
        """Verifica creación de memoria"""
        result = vcs.upsert(
            topic_key="project:conventions:code",
            content="Use snake_case for Python functions",
            metadata={"domain": "development", "language": "python"}
        )
        
        assert result["operation"] == "created"
        assert result["revision"] == 1
        assert result["changed"] is True
    
    def test_update_memory(self, vcs):
        """Verifica actualización de memoria con versionado"""
        # Crear inicial
        vcs.upsert(
            topic_key="project:conventions:code",
            content="Use snake_case for Python functions",
            metadata={"version": 1}
        )
        
        # Actualizar
        result = vcs.upsert(
            topic_key="project:conventions:code",
            content="Use snake_case for Python functions. Use PascalCase for classes.",
            metadata={"version": 2},
            change_reason="Added class naming convention"
        )
        
        assert result["operation"] == "updated"
        assert result["revision"] == 2
        
        # Verificar timeline
        timeline = vcs.get_timeline("project:conventions:code")
        assert len(timeline) >= 1
    
    def test_upsert_same_content(self, vcs):
        """Verifica que mismo contenido no crea nueva versión"""
        vcs.upsert(
            topic_key="test:same",
            content="Same content",
            metadata={}
        )
        
        result = vcs.upsert(
            topic_key="test:same",
            content="Same content",
            metadata={}
        )
        
        assert result["operation"] == "accessed"
        assert result["changed"] is False
    
    def test_search_compact_level(self, vcs):
        """Verifica búsqueda con nivel compacto"""
        vcs.upsert("topic:python", "Python is a programming language", {"type": "language"})
        vcs.upsert("topic:javascript", "JavaScript for web development", {"type": "language"})
        
        results = vcs.search(
            "Python programming",
            disclosure_level=DisclosureLevel.COMPACT
        )
        
        assert len(results) >= 1
        assert "content" not in results[0]  # Compact no incluye contenido
        assert results[0]["disclosure_level"] == "compact"
    
    def test_search_full_level(self, vcs):
        """Verifica búsqueda con nivel completo"""
        vcs.upsert("topic:test", "Test content for search", {"type": "test"})
        
        results = vcs.search(
            "Test content",
            disclosure_level=DisclosureLevel.FULL
        )
        
        assert len(results) >= 1
        assert "content" in results[0]
        assert results[0]["disclosure_level"] == "full"
    
    def test_get_by_key(self, vcs):
        """Verifica obtención por clave"""
        vcs.upsert(
            topic_key="unique:key:test",
            content="Unique content",
            metadata={"unique": True}
        )
        
        result = vcs.get_by_key("unique:key:test")
        
        assert result is not None
        assert result["content"] == "Unique content"
        assert result["metadata"]["unique"] is True
    
    def test_get_nonexistent_key(self, vcs):
        """Verifica obtención de clave inexistente"""
        result = vcs.get_by_key("nonexistent:key")
        assert result is None
    
    def test_add_relation(self, vcs):
        """Verifica adición de relaciones"""
        vcs.upsert("source:topic", "Source content", {})
        vcs.upsert("target:topic", "Target content", {})
        
        result = vcs.add_relation(
            source_key="source:topic",
            target_key="target:topic",
            relation_type="related_to",
            weight=0.8
        )
        
        assert result["source"] == "source:topic"
        assert result["target"] == "target:topic"
        assert result["relation_type"] == "related_to"
    
    def test_get_related(self, vcs):
        """Verifica obtención de memorias relacionadas"""
        vcs.upsert("main:topic", "Main content", {})
        vcs.upsert("related:1", "Related 1", {})
        vcs.upsert("related:2", "Related 2", {})
        
        vcs.add_relation("main:topic", "related:1", "similar", 0.9)
        vcs.add_relation("main:topic", "related:2", "similar", 0.7)
        
        related = vcs.get_related("main:topic")
        
        assert len(related) == 2
        # Verificar que están ordenados por peso
        assert related[0]["weight"] >= related[1]["weight"]
    
    def test_delete_memory(self, vcs):
        """Verifica eliminación de memoria"""
        vcs.upsert("delete:test", "To be deleted", {})
        
        assert vcs.get_by_key("delete:test") is not None
        
        result = vcs.delete("delete:test")
        assert result is True
        
        assert vcs.get_by_key("delete:test") is None
    
    def test_get_stats(self, vcs):
        """Verifica estadísticas"""
        vcs.upsert("stat:1", "Content 1", {})
        vcs.upsert("stat:2", "Content 2", {})
        vcs.add_relation("stat:1", "stat:2", "related")
        
        stats = vcs.get_stats()
        
        assert stats["total_memories"] == 2
        assert stats["total_relations"] == 1
        assert stats["total_cognitive_capital"] >= 2
    
    def test_timeline(self, vcs):
        """Verifica línea temporal"""
        # Crear y actualizar varias veces
        vcs.upsert("timeline:test", "Version 1", {"v": 1})
        vcs.upsert("timeline:test", "Version 2", {"v": 2})
        vcs.upsert("timeline:test", "Version 3", {"v": 3})
        
        timeline = vcs.get_timeline("timeline:test")
        
        assert len(timeline) >= 2  # Al menos 2 versiones guardadas
    
    def test_singleton(self, temp_db):
        """Verifica patrón singleton"""
        reset_memory_vcs()
        
        vcs1 = get_memory_vcs(temp_db)
        vcs2 = get_memory_vcs()
        
        assert vcs1 is vcs2
    
    def test_persistence(self, temp_db):
        """Verifica persistencia entre instancias"""
        vcs1 = MemoryVCS(db_path=temp_db)
        vcs1.upsert("persist:test", "Persistent content", {})
        
        # Crear nueva instancia con mismo path
        vcs2 = MemoryVCS(db_path=temp_db)
        result = vcs2.get_by_key("persist:test")
        
        assert result is not None
        assert result["content"] == "Persistent content"


class TestMemoryVCSAdvanced:
    """Tests avanzados para Memory VCS"""
    
    @pytest.fixture
    def vcs(self):
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = f.name
        vcs = MemoryVCS(db_path=db_path, auto_init=True)
        yield vcs
        try:
            os.unlink(db_path)
        except:
            pass
    
    def test_bulk_operations(self, vcs):
        """Verifica operaciones masivas"""
        topics = [f"bulk:{i}" for i in range(100)]
        
        for topic in topics:
            vcs.upsert(topic, f"Content for {topic}", {"index": topics.index(topic)})
        
        stats = vcs.get_stats()
        assert stats["total_memories"] == 100
    
    def test_complex_metadata(self, vcs):
        """Verifica metadatos complejos"""
        metadata = {
            "nested": {
                "key": "value",
                "list": [1, 2, 3]
            },
            "tags": ["tag1", "tag2"],
            "count": 42
        }
        
        vcs.upsert("complex:meta", "Content", metadata)
        
        result = vcs.get_by_key("complex:meta")
        assert result["metadata"]["nested"]["key"] == "value"
        assert result["metadata"]["tags"] == ["tag1", "tag2"]
    
    def test_search_with_filter(self, vcs):
        """Verifica búsqueda con filtros"""
        vcs.upsert("domain:python", "Python content", {"domain": "python"})
        vcs.upsert("domain:javascript", "JavaScript content", {"domain": "javascript"})
        vcs.upsert("domain:rust", "Rust content", {"domain": "rust"})
        
        results = vcs.search(
            "content",
            disclosure_level=DisclosureLevel.COMPACT
        )
        
        assert len(results) >= 3
    
    def test_cognitive_value_tracking(self, vcs):
        """Verifica tracking de valor cognitivo"""
        vcs.upsert("high:value", "Important knowledge", {"importance": "high"})
        
        # Actualizar múltiples veces
        for i in range(5):
            vcs.upsert("high:value", f"Updated content {i}", {})
        
        result = vcs.get_by_key("high:value")
        assert result["access_count"] >= 5

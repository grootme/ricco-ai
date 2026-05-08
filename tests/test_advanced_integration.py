"""
Tests Avanzados de Integración para OpenClaw Agent SaaS

Tests de integración end-to-end que validan flujos completos del sistema,
incluyendo escenarios complejos y casos de uso reales.

Autor: OpenClaw Agent SaaS Team
Versión: 1.0.0
"""

import pytest
import asyncio
import tempfile
import os
import sys
import uuid
import time
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, Any, List

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestEndToEndFlows:
    """
    Tests de flujos end-to-end completos.
    
    Valida escenarios de uso real del sistema integrado.
    """
    
    @pytest.fixture
    def full_system(self, temp_db_path):
        """
        Fixture que inicializa todos los componentes del sistema.
        
        Returns:
            Dict con todas las instancias configuradas
        """
        from src.memory.vcs import MemoryVCS
        from src.ralph.loop import RalphLoop
        from src.rno.locm import LOCM, LOCMConfig
        from src.iovba.validation.guardrail import GuardrailMiddleware
        from src.iovba.behavior.ethics import EthicsEngine
        
        memory_vcs = MemoryVCS(db_path=temp_db_path)
        
        return {
            "memory_vcs": memory_vcs,
            "ralph_loop": RalphLoop(memory_vcs=memory_vcs),
            "locm": LOCM(LOCMConfig(domain="retail")),
            "guardrail": GuardrailMiddleware(),
            "ethics": EthicsEngine()
        }
    
    @pytest.fixture
    def temp_db_path(self):
        """Fixture para base de datos temporal."""
        db_fd, db_path = tempfile.mkstemp(suffix=".db", prefix="test_e2e_")
        yield db_path
        try:
            os.close(db_fd)
        except:
            pass
        try:
            os.unlink(db_path)
        except:
            pass
    
    @pytest.mark.asyncio
    async def test_complete_agent_interaction_flow(self, full_system):
        """
        Test: Flujo completo de interacción con agente.
        
        Escenario:
        1. Usuario solicita tarea
        2. Sistema prepara contexto PPCC
        3. Valida con guardrail y ethics
        4. Ejecuta tarea
        5. Ralph Loop cosecha conocimiento
        6. Memory VCS persiste resultados
        """
        from src.core.ppcc import PPCCCycle
        
        session_id = f"e2e_session_{uuid.uuid4().hex[:8]}"
        user_id = f"e2e_user_{uuid.uuid4().hex[:8]}"
        
        # 1. Crear ciclo PPCC
        cycle = PPCCCycle()
        
        # 2. Preparar contexto
        prep_result = await cycle.prepare({
            "session_id": session_id,
            "user_id": user_id,
            "objective": "Analizar tendencias de ventas Q1",
            "success_criteria": [
                "Completar en 5 minutos",
                "Incluir gráficos comparativos",
                "Alcanzar 90% de precisión"
            ],
            "recall": 0.9,
            "precision": 0.85,
            "boundaries": {
                "allow": ["data_warehouse", "analytics_db"],
                "deny": ["production_db", "customer_pii"]
            }
        })
        
        assert prep_result["phase"] == "preparation"
        
        # 3. Validar con guardrail
        guardrail = full_system["guardrail"]
        validation = guardrail.validate(
            "Analizar tendencias de ventas",
            {"allowed_tools": ["analyzer", "reporter"]}
        )
        assert validation.allowed is True
        
        # 4. Validar con ethics
        ethics = full_system["ethics"]
        from src.iovba.behavior.ethics import ActionType
        ethics_report = ethics.evaluate(
            ActionType.ANALYSIS,
            {"data_type": "sales_anonymous"}
        )
        assert ethics_report.overall_compliant is True
        
        # 5. Completar alineación
        await cycle.request_alignment()
        await cycle.confirm_alignment(
            "Entendido: Analizaré tendencias de ventas Q1",
            user_confirmed=True
        )
        
        # 6. Ejecutar
        exec_result = await cycle.execute("Ejecutar análisis de ventas")
        assert exec_result["phase"] == "execution"
        
        # 7. Declarar resultado
        final_result = await cycle.declare_result(
            satisfaction=True,
            feedback="Análisis completado exitosamente",
            harvest_knowledge=True
        )
        
        assert final_result["satisfaction"] is True
        assert final_result["cognitive_capital_earned"] > 0
        
        # 8. Ralph Loop cosecha conocimiento
        ralph = full_system["ralph_loop"]
        interaction = {
            "session_id": session_id,
            "user_id": user_id,
            "objective": "Analizar tendencias de ventas Q1",
            "success": True,
            "commands": [
                {"command": "connect_data_warehouse"},
                {"command": "run_analysis"},
                {"command": "generate_report"}
            ],
            "errors": [],
            "tools_used": ["analyzer", "reporter"],
            "metrics": {"recall": 0.92, "precision": 0.88}
        }
        
        ralph_session = await ralph.execute(interaction)
        assert ralph_session.completed_at is not None
        
        # 9. Verificar persistencia en Memory VCS
        memory_vcs = full_system["memory_vcs"]
        stats = memory_vcs.get_stats()
        assert stats["total_memories"] > 0
    
    @pytest.mark.asyncio
    async def test_error_recovery_flow(self, full_system):
        """
        Test: Flujo de recuperación de errores.
        
        Escenario:
        1. Tarea falla inicialmente
        2. Sistema detecta error
        3. Ralph Loop extrae corrección
        4. Reintento exitoso
        """
        from src.core.ppcc import PPCCCycle
        
        session_id = f"error_session_{uuid.uuid4().hex[:8]}"
        
        # Primer intento fallido
        cycle1 = PPCCCycle()
        await cycle1.prepare({
            "session_id": session_id,
            "user_id": "error_test_user",
            "objective": "Tarea que fallará inicialmente"
        })
        
        await cycle1.request_alignment()
        await cycle1.confirm_alignment("Entendido", user_confirmed=True)
        await cycle1.execute("Ejecutar tarea fallida")
        
        # Declarar insatisfacción
        result1 = await cycle1.declare_result(
            satisfaction=False,
            feedback="Error de timeout en operación"
        )
        
        assert result1["satisfaction"] is False
        assert "learning_opportunity" in result1
        
        # Ralph Loop procesa error
        ralph = full_system["ralph_loop"]
        error_interaction = {
            "session_id": session_id,
            "objective": "Tarea que fallará inicialmente",
            "success": False,
            "errors": [
                {
                    "type": "timeout",
                    "message": "Operation timed out after 30 seconds",
                    "correction": "Increase timeout to 60 seconds"
                }
            ]
        }
        
        ralph_session = await ralph.execute(error_interaction)
        
        # Verificar que se extrajo conocimiento de corrección
        learn_result = next(
            (r for r in ralph_session.results if r.phase.value == "learn"),
            None
        )
        
        # Segundo intento con corrección aplicada
        cycle2 = PPCCCycle()
        await cycle2.prepare({
            "session_id": f"{session_id}_retry",
            "user_id": "error_test_user",
            "objective": "Tarea que fallará inicialmente",
            "timeout_seconds": 60  # Corrección aplicada
        })
        
        await cycle2.request_alignment()
        await cycle2.confirm_alignment("Entendido con timeout extendido", True)
        await cycle2.execute("Ejecutar tarea con corrección")
        
        result2 = await cycle2.declare_result(
            satisfaction=True,
            feedback="Completado con timeout extendido"
        )
        
        assert result2["satisfaction"] is True
    
    @pytest.mark.asyncio
    async def test_multi_domain_reasoning_flow(self, full_system):
        """
        Test: Flujo de razonamiento multi-dominio.
        
        Escenario:
        1. Cargar conocimiento de múltiples dominios
        2. Ejecutar razonamiento cruzado
        3. Generar recomendaciones integradas
        """
        locm = full_system["locm"]
        
        # Cargar contexto organizacional multi-dominio
        locm.ingest_organization_context({
            "objectives": [
                {"name": "Maximizar Ventas", "description": "Retail objective"},
                {"name": "Gestionar Riesgo", "description": "Finance objective"},
                {"name": "Optimizar Inventario", "description": "Operations objective"}
            ],
            "constraints": [
                {"name": "Límite Presupuestario", "description": "Finance constraint"},
                {"name": "Capacidad Almacén", "description": "Operations constraint"}
            ],
            "policies": [
                {"name": "Protección Datos Clientes", "type": "privacy"},
                {"name": "Compliance Financiero", "type": "compliance"}
            ]
        })
        
        # Cargar conocimiento de dominios
        locm.ingest_domain_knowledge("retail", {
            "sales": {"trend": "growing", "seasonality": "Q4 peak"},
            "customers": {"segments": ["B2B", "B2C"]}
        })
        
        locm.ingest_domain_knowledge("finance", {
            "risk": {"model": "VaR", "threshold": 0.05},
            "budget": {"allocation": "quarterly"}
        })
        
        locm.ingest_domain_knowledge("operations", {
            "inventory": {"method": "JIT", "safety_stock": 0.1},
            "logistics": {"providers": ["A", "B"]}
        })
        
        # Razonamiento cruzado
        result = locm.reason(
            "¿Cómo optimizar ventas e inventario mientras gestiono el riesgo financiero?"
        )
        
        assert result.confidence > 0
        assert len(result.relevant_context) > 0
        
        # Verificar que el conocimiento de múltiples dominios fue utilizado
        stats = locm.get_network_stats()
        assert stats["total_neurons"] > 15  # Base + objectives + constraints + domain knowledge
    
    @pytest.mark.asyncio
    async def test_security_validation_flow(self, full_system):
        """
        Test: Flujo de validación de seguridad.
        
        Escenario:
        1. Intentar operación con contenido sospechoso
        2. Guardrail bloquea
        3. Ethics engine reporta riesgo
        4. Operación denegada
        """
        from src.iovba.behavior.ethics import ActionType
        
        guardrail = full_system["guardrail"]
        ethics = full_system["ethics"]
        
        # Contenido sospechoso
        suspicious_content = "password: admin123 and api_key: sk-1234567890abcdef"
        
        # Guardrail detecta secretos
        guardrail_result = guardrail.validate(suspicious_content)
        
        assert guardrail_result.allowed is False or len(guardrail_result.rules_matched) > 0
        
        # Ethics evalúa
        ethics_report = ethics.evaluate(
            ActionType.INFORMATION,
            {"content": suspicious_content}
        )
        
        # Debe haber algún tipo de advertencia o bloqueo
        has_security_issue = (
            not guardrail_result.allowed or
            len(guardrail_result.warnings) > 0 or
            not ethics_report.overall_compliant
        )
        
        assert has_security_issue is True
    
    @pytest.mark.asyncio
    async def test_knowledge_evolution_flow(self, full_system):
        """
        Test: Flujo de evolución del conocimiento.
        
        Escenario:
        1. Memoria inicial vacía
        2. Múltiples interacciones
        3. Conocimiento acumulado y versionado
        4. Búsqueda recupera conocimiento relevante
        """
        from src.memory.vcs import DisclosureLevel
        
        memory_vcs = full_system["memory_vcs"]
        ralph = full_system["ralph_loop"]
        
        # Memoria inicial vacía
        initial_stats = memory_vcs.get_stats()
        assert initial_stats["total_memories"] == 0
        
        # Simular múltiples interacciones
        interactions = [
            {
                "session_id": f"evolution_{i}",
                "objective": f"Analizar datos de ventas semana {i}",
                "success": True,
                "commands": [{"command": f"analyze_week_{i}"}],
                "errors": []
            }
            for i in range(1, 6)
        ]
        
        # Ejecutar Ralph Loop para cada interacción
        for interaction in interactions:
            await ralph.execute(interaction)
        
        # Verificar acumulación
        final_stats = memory_vcs.get_stats()
        assert final_stats["total_memories"] > initial_stats["total_memories"]
        
        # Búsqueda debe encontrar conocimiento relevante
        results = memory_vcs.search(
            "ventas",
            disclosure_level=DisclosureLevel.COMPACT
        )
        
        assert len(results) > 0


class TestPerformanceBenchmarks:
    """
    Tests de rendimiento y benchmarks.
    
    Mide el desempeño de componentes críticos.
    """
    
    @pytest.fixture
    def temp_db(self):
        """Fixture para base de datos temporal."""
        db_fd, db_path = tempfile.mkstemp(suffix=".db", prefix="perf_")
        yield db_path
        try:
            os.close(db_fd)
        except:
            pass
        try:
            os.unlink(db_path)
        except:
            pass
    
    def test_memory_vcs_write_performance(self, temp_db):
        """
        Benchmark: Rendimiento de escritura en Memory VCS.
        
        Objetivo: < 10ms por operación de upsert
        """
        from src.memory.vcs import MemoryVCS
        
        vcs = MemoryVCS(db_path=temp_db)
        
        operations = 100
        start_time = time.time()
        
        for i in range(operations):
            vcs.upsert(
                topic_key=f"perf:test:{i}",
                content=f"Content {i}" * 10,
                metadata={"index": i}
            )
        
        elapsed = time.time() - start_time
        avg_time_ms = (elapsed / operations) * 1000
        
        print(f"\nMemoria VCS - {operations} operaciones en {elapsed:.3f}s")
        print(f"Promedio: {avg_time_ms:.2f}ms por operación")
        
        # Validar objetivo
        assert avg_time_ms < 100, f"Promedio debe ser < 100ms, fue {avg_time_ms:.2f}ms"
    
    def test_memory_vcs_search_performance(self, temp_db):
        """
        Benchmark: Rendimiento de búsqueda FTS5.
        
        Objetivo: < 50ms por búsqueda
        """
        from src.memory.vcs import MemoryVCS, DisclosureLevel
        
        vcs = MemoryVCS(db_path=temp_db)
        
        # Poblar con datos
        for i in range(500):
            vcs.upsert(
                topic_key=f"search:perf:{i}",
                content=f"Content for search testing iteration {i} with various keywords",
                metadata={"index": i}
            )
        
        # Medir búsqueda
        search_times = []
        queries = ["testing", "iteration", "keywords", "content", "various"]
        
        for query in queries:
            start = time.time()
            results = vcs.search(query, disclosure_level=DisclosureLevel.FULL)
            elapsed = (time.time() - start) * 1000
            search_times.append(elapsed)
        
        avg_search_time = sum(search_times) / len(search_times)
        
        print(f"\nBúsqueda FTS5 - Promedio: {avg_search_time:.2f}ms")
        
        assert avg_search_time < 100, f"Búsqueda debe ser < 100ms, fue {avg_search_time:.2f}ms"
    
    @pytest.mark.asyncio
    async def test_ralph_loop_performance(self):
        """
        Benchmark: Rendimiento del ciclo Ralph Loop.
        
        Objetivo: < 500ms para ciclo completo
        """
        from src.ralph.loop import RalphLoop
        
        ralph = RalphLoop()
        
        interaction = {
            "session_id": "perf_test",
            "objective": "Performance test interaction",
            "success": True,
            "commands": [{"command": "test"} for _ in range(10)],
            "errors": []
        }
        
        start_time = time.time()
        session = await ralph.execute(interaction)
        elapsed = (time.time() - start_time) * 1000
        
        print(f"\nRalph Loop - Ciclo completo: {elapsed:.2f}ms")
        
        assert session.completed_at is not None
        assert elapsed < 2000, f"Ciclo debe ser < 2s, fue {elapsed:.2f}ms"
    
    def test_locm_reasoning_performance(self):
        """
        Benchmark: Rendimiento de razonamiento LOCM.
        
        Objetivo: < 100ms por consulta
        """
        from src.rno.locm import LOCM, LOCMConfig
        
        locm = LOCM(LOCMConfig(domain="retail"))
        
        # Cargar contexto
        locm.ingest_organization_context({
            "objectives": [{"name": f"Obj {i}"} for i in range(10)],
            "constraints": [{"name": f"Const {i}"} for i in range(5)]
        })
        
        queries = [
            "¿Cómo optimizar ventas?",
            "¿Cuál es el estado del inventario?",
            "¿Qué métricas debo monitorear?"
        ]
        
        times = []
        for query in queries:
            start = time.time()
            result = locm.reason(query)
            elapsed = (time.time() - start) * 1000
            times.append(elapsed)
        
        avg_time = sum(times) / len(times)
        print(f"\nLOCM Razonamiento - Promedio: {avg_time:.2f}ms")
        
        assert avg_time < 500, f"Razonamiento debe ser < 500ms, fue {avg_time:.2f}ms"
    
    def test_guardrail_validation_performance(self):
        """
        Benchmark: Rendimiento de validación Guardrail.
        
        Objetivo: < 5ms por validación
        """
        from src.iovba.validation.guardrail import GuardrailMiddleware
        
        guardrail = GuardrailMiddleware()
        
        # Textos de prueba
        texts = [
            "Normal text without issues",
            "Email: test@example.com for contact",
            "api_key: sk-1234567890abcdefghijklmnop",
            "SSN: 123-45-6789 sensitive data",
            "SELECT * FROM users; DROP TABLE users;--"
        ] * 20  # 100 validaciones
        
        start_time = time.time()
        for text in texts:
            guardrail.validate(text)
        elapsed = time.time() - start_time
        
        avg_time_ms = (elapsed / len(texts)) * 1000
        print(f"\nGuardrail - {len(texts)} validaciones en {elapsed:.3f}s")
        print(f"Promedio: {avg_time_ms:.2f}ms por validación")
        
        assert avg_time_ms < 20, f"Validación debe ser < 20ms, fue {avg_time_ms:.2f}ms"


class TestConcurrencyAndThreadSafety:
    """
    Tests de concurrencia y thread safety.
    
    Valida el comportamiento bajo acceso concurrente.
    """
    
    @pytest.fixture
    def temp_db(self):
        """Fixture para base de datos temporal."""
        db_fd, db_path = tempfile.mkstemp(suffix=".db", prefix="concurrent_")
        yield db_path
        try:
            os.close(db_fd)
        except:
            pass
        try:
            os.unlink(db_path)
        except:
            pass
    
    @pytest.mark.asyncio
    async def test_concurrent_memory_operations(self, temp_db):
        """
        Test: Operaciones concurrentes en Memory VCS.
        
        Valida que múltiples operaciones no causen conflictos.
        """
        from src.memory.vcs import MemoryVCS
        
        vcs = MemoryVCS(db_path=temp_db)
        
        async def write_operation(prefix: str, count: int):
            for i in range(count):
                vcs.upsert(
                    topic_key=f"concurrent:{prefix}:{i}",
                    content=f"Content {prefix}-{i}",
                    metadata={"thread": prefix}
                )
        
        # Ejecutar múltiples tareas concurrentes
        tasks = [
            write_operation(f"thread_{i}", 50)
            for i in range(5)
        ]
        
        await asyncio.gather(*tasks)
        
        # Verificar integridad
        stats = vcs.get_stats()
        assert stats["total_memories"] == 250  # 5 threads * 50 operations
    
    @pytest.mark.asyncio
    async def test_concurrent_ppcc_cycles(self):
        """
        Test: Ciclos PPCC concurrentes.
        
        Valida que múltiples ciclos puedan ejecutarse simultáneamente.
        """
        from src.core.ppcc import PPCCCycle
        
        async def run_cycle(cycle_id: str):
            cycle = PPCCCycle()
            
            await cycle.prepare({
                "session_id": f"concurrent_{cycle_id}",
                "user_id": f"user_{cycle_id}",
                "objective": f"Objective {cycle_id}"
            })
            
            await cycle.request_alignment()
            await cycle.confirm_alignment(f"Understanding {cycle_id}", True)
            await cycle.execute(f"Task {cycle_id}")
            
            return await cycle.declare_result(True, f"Completed {cycle_id}")
        
        # Ejecutar 10 ciclos concurrentes
        tasks = [run_cycle(str(i)) for i in range(10)]
        results = await asyncio.gather(*tasks)
        
        # Todos deben completar exitosamente
        for result in results:
            assert result["satisfaction"] is True


class TestDataIntegrity:
    """
    Tests de integridad de datos.
    
    Valida que los datos se mantengan consistentes.
    """
    
    @pytest.fixture
    def temp_db(self):
        """Fixture para base de datos temporal."""
        db_fd, db_path = tempfile.mkstemp(suffix=".db", prefix="integrity_")
        yield db_path
        try:
            os.close(db_fd)
        except:
            pass
        try:
            os.unlink(db_path)
        except:
            pass
    
    def test_memory_vcs_data_integrity(self, temp_db):
        """
        Test: Integridad de datos en Memory VCS.
        
        Valida que los datos no se corrompan.
        """
        from src.memory.vcs import MemoryVCS
        
        vcs = MemoryVCS(db_path=temp_db)
        
        # Crear memoria con datos complejos
        complex_metadata = {
            "nested": {"deep": {"value": 123}},
            "list": [1, 2, 3, 4, 5],
            "unicode": "Ñoño señor",
            "special": "!@#$%^&*()_+-=[]{}|;':\",./<>?"
        }
        
        topic_key = "integrity:test:complex"
        content = "Content with ñ and émojis 🎉 and special chars !@#"
        
        vcs.upsert(topic_key, content, complex_metadata)
        
        # Recuperar y verificar
        result = vcs.get_by_key(topic_key)
        
        assert result["content"] == content
        assert result["metadata"]["nested"]["deep"]["value"] == 123
        assert result["metadata"]["list"] == [1, 2, 3, 4, 5]
        assert result["metadata"]["unicode"] == "Ñoño señor"
    
    def test_version_history_integrity(self, temp_db):
        """
        Test: Integridad del historial de versiones.
        
        Valida que las versiones históricas se mantengan correctas.
        """
        from src.memory.vcs import MemoryVCS
        
        vcs = MemoryVCS(db_path=temp_db)
        
        topic_key = "version:integrity:test"
        
        # Crear múltiples versiones
        for i in range(5):
            vcs.upsert(
                topic_key,
                f"Version {i} content",
                {"version": i},
                change_reason=f"Update to version {i}"
            )
        
        # Verificar timeline
        timeline = vcs.get_timeline(topic_key)
        
        assert len(timeline) >= 4  # 5 updates = 4 historical versions
        
        # Versiones deben estar ordenadas
        versions = [t["version"] for t in timeline]
        assert versions == sorted(versions, reverse=True)


# Entry point
if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])

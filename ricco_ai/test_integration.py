#!/usr/bin/env python3
"""
Prueba de Integración Completa - RICCO AI
=========================================

Este script prueba todas las capacidades del sistema integrado:
1. DeerFlow (LangGraph 1.2.0 + interrupt)
2. Skills (gentle_ai, engram, gentle_pi)
3. Tools (SDD, memory, orchestration)

Uso:
    python test_integration.py
"""

import sys
import os
import traceback
from pathlib import Path
from dataclasses import dataclass
from typing import Any

# Agregar paths necesarios
BASE_DIR = Path(__file__).parent
sys.path.insert(0, str(BASE_DIR))
sys.path.insert(0, str(BASE_DIR / "deerflow" / "packages" / "harness"))


@dataclass
class TestResult:
    """Resultado de una prueba."""
    name: str
    success: bool
    message: str
    details: str = ""


class IntegrationTester:
    """Tester de integración para RICCO AI."""

    def __init__(self):
        self.results: list[TestResult] = []

    def run_test(self, name: str, test_func) -> TestResult:
        """Ejecuta una prueba y registra el resultado."""
        print(f"\n{'='*60}")
        print(f"🧪 TEST: {name}")
        print('='*60)

        try:
            result = test_func()
            if isinstance(result, TestResult):
                self.results.append(result)
                status = "✅ PASS" if result.success else "❌ FAIL"
                print(f"{status}: {result.message}")
                if result.details:
                    print(f"   Details: {result.details[:200]}...")
                return result
            return TestResult(name, True, "Test passed")
        except Exception as e:
            result = TestResult(name, False, str(e), traceback.format_exc())
            self.results.append(result)
            print(f"❌ FAIL: {e}")
            print(f"   Traceback:\n{traceback.format_exc()}")
            return result

    def test_directory_structure(self) -> TestResult:
        """Verifica la estructura de directorios."""
        required_dirs = [
            "deerflow",
            "deerflow/skills",
            "deerflow/skills/gentle_ai",
            "deerflow/skills/engram",
            "deerflow/skills/gentle_pi",
            "deerflow/packages/harness/deerflow",
            "deerflow/packages/harness/deerflow/agents",
            "deerflow/packages/harness/deerflow/tools",
            "deerflow/packages/harness/deerflow/tools/builtins",
        ]

        missing = []
        for dir_path in required_dirs:
            full_path = BASE_DIR / dir_path
            if not full_path.exists():
                missing.append(dir_path)

        if missing:
            return TestResult(
                "Directory Structure",
                False,
                f"Missing directories: {missing}"
            )

        return TestResult(
            "Directory Structure",
            True,
            f"All {len(required_dirs)} directories present"
        )

    def test_skill_files(self) -> TestResult:
        """Verifica que los archivos SKILL.md existan."""
        skill_files = [
            "deerflow/skills/gentle_ai/SKILL.md",
            "deerflow/skills/engram/SKILL.md",
            "deerflow/skills/gentle_pi/SKILL.md",
        ]

        missing = []
        for skill_file in skill_files:
            full_path = BASE_DIR / skill_file
            if not full_path.exists():
                missing.append(skill_file)

        if missing:
            return TestResult(
                "Skill Files",
                False,
                f"Missing skill files: {missing}"
            )

        return TestResult(
            "Skill Files",
            True,
            f"All {len(skill_files)} SKILL.md files present"
        )

    def test_tool_files(self) -> TestResult:
        """Verifica que los archivos de tools existan."""
        tool_files = [
            "deerflow/packages/harness/deerflow/tools/builtins/gentle_ai_tools.py",
            "deerflow/packages/harness/deerflow/tools/builtins/engram_tools.py",
            "deerflow/packages/harness/deerflow/tools/builtins/gentle_pi_tools.py",
            "deerflow/packages/harness/deerflow/tools/builtins/clarification_tool.py",
        ]

        missing = []
        for tool_file in tool_files:
            full_path = BASE_DIR / tool_file
            if not full_path.exists():
                missing.append(tool_file)

        if missing:
            return TestResult(
                "Tool Files",
                False,
                f"Missing tool files: {missing}"
            )

        return TestResult(
            "Tool Files",
            True,
            f"All {len(tool_files)} tool files present"
        )

    def test_clarification_middleware(self) -> TestResult:
        """Verifica que ClarificationMiddleware use interrupt()."""
        middleware_path = BASE_DIR / "deerflow/packages/harness/deerflow/agents/middlewares/clarification_middleware.py"

        if not middleware_path.exists():
            return TestResult(
                "ClarificationMiddleware",
                False,
                "File not found"
            )

        with open(middleware_path, 'r') as f:
            content = f.read()

        checks = {
            "import interrupt": "from langgraph.types import Command, interrupt" in content,
            "uses interrupt()": "interrupt(" in content,
            "no goto=END": "goto=END" not in content,
            "has v2 docstring": "LangGraph 1.2.0" in content or "v2 interrupt pattern" in content,
        }

        failed_checks = [k for k, v in checks.items() if not v]

        if failed_checks:
            return TestResult(
                "ClarificationMiddleware",
                False,
                f"Checks failed: {failed_checks}",
                f"Found: interrupt import={checks['import interrupt']}, interrupt() call={checks['uses interrupt()']}"
            )

        return TestResult(
            "ClarificationMiddleware",
            True,
            "Correctly uses interrupt() from LangGraph 1.2.0",
            f"All checks passed: {list(checks.keys())}"
        )

    def test_langgraph_interrupt_available(self) -> TestResult:
        """Verifica que interrupt esté disponible en langgraph.types."""
        try:
            from langgraph.types import interrupt, Command, Interrupt

            return TestResult(
                "LangGraph Interrupt",
                True,
                "interrupt, Command, Interrupt available in langgraph.types",
                f"interrupt: {interrupt}, Command: {Command}, Interrupt: {Interrupt}"
            )
        except ImportError as e:
            return TestResult(
                "LangGraph Interrupt",
                False,
                f"Cannot import from langgraph.types: {e}"
            )

    def test_gentle_ai_tools_import(self) -> TestResult:
        """Prueba importar las tools de Gentle AI."""
        try:
            from deerflow.tools.builtins.gentle_ai_tools import (
                sdd_init_tool,
                sdd_proposal_tool,
                GENTLE_AI_TOOLS,
            )

            tool_count = len(GENTLE_AI_TOOLS)
            return TestResult(
                "Gentle AI Tools Import",
                True,
                f"Successfully imported {tool_count} tools",
                f"Tools: {[t.name for t in GENTLE_AI_TOOLS]}"
            )
        except ImportError as e:
            return TestResult(
                "Gentle AI Tools Import",
                False,
                f"Import failed: {e}"
            )

    def test_engram_tools_import(self) -> TestResult:
        """Prueba importar las tools de Engram."""
        try:
            from deerflow.tools.builtins.engram_tools import (
                mem_save_tool,
                mem_search_tool,
                ENGRAM_TOOLS,
            )

            tool_count = len(ENGRAM_TOOLS)
            return TestResult(
                "Engram Tools Import",
                True,
                f"Successfully imported {tool_count} tools",
                f"Tools: {[t.name for t in ENGRAM_TOOLS]}"
            )
        except ImportError as e:
            return TestResult(
                "Engram Tools Import",
                False,
                f"Import failed: {e}"
            )

    def test_gentle_pi_tools_import(self) -> TestResult:
        """Prueba importar las tools de Gentle-Pi."""
        try:
            from deerflow.tools.builtins.gentle_pi_tools import (
                gentle_persona_tool,
                gentle_models_tool,
                GENTLE_PI_TOOLS,
            )

            tool_count = len(GENTLE_PI_TOOLS)
            return TestResult(
                "Gentle-Pi Tools Import",
                True,
                f"Successfully imported {tool_count} tools",
                f"Tools: {[t.name for t in GENTLE_PI_TOOLS]}"
            )
        except ImportError as e:
            return TestResult(
                "Gentle-Pi Tools Import",
                False,
                f"Import failed: {e}"
            )

    def test_tool_functionality(self) -> TestResult:
        """Prueba la funcionalidad básica de las tools."""
        try:
            from deerflow.tools.builtins.gentle_ai_tools import sdd_init_tool
            from deerflow.tools.builtins.engram_tools import mem_save_tool
            from deerflow.tools.builtins.gentle_pi_tools import gentle_persona_tool

            # Probar sdd_init
            result1 = sdd_init_tool.invoke({
                "project_name": "test-project",
                "description": "Test project",
                "artifact_store": "openspec"
            })

            # Probar mem_save
            result2 = mem_save_tool.invoke({
                "title": "Test Memory",
                "content": "This is a test memory",
                "memory_type": "discovery"
            })

            # Probar gentle_persona
            result3 = gentle_persona_tool.invoke({
                "persona": "gentleman"
            })

            return TestResult(
                "Tool Functionality",
                True,
                "All tools executed successfully",
                f"sdd_init: {result1.get('status')}, mem_save: {result2.get('status')}, gentle_persona: {result3.get('status')}"
            )
        except Exception as e:
            return TestResult(
                "Tool Functionality",
                False,
                f"Tool execution failed: {e}"
            )

    def test_opportunities_analysis(self) -> TestResult:
        """Analiza oportunidades de mejora."""
        opportunities = []

        # Verificar integración real con Engram (Go)
        engram_go_path = BASE_DIR / "engram"
        if engram_go_path.exists():
            go_files = list(engram_go_path.rglob("*.go"))
            if go_files:
                opportunities.append({
                    "area": "Engram Integration",
                    "opportunity": "Implement Python bindings for Engram Go binary",
                    "priority": "high",
                    "description": "Create actual integration with Engram's Go binary for real memory persistence"
                })

        # Verificar tests
        tests_path = BASE_DIR / "deerflow" / "tests"
        if tests_path.exists():
            test_files = list(tests_path.rglob("test_*.py"))
            new_tests_needed = [
                "test_gentle_ai_tools.py",
                "test_engram_tools.py",
                "test_gentle_pi_tools.py",
            ]
            existing_names = [f.name for f in test_files]
            missing_tests = [t for t in new_tests_needed if t not in existing_names]

            if missing_tests:
                opportunities.append({
                    "area": "Testing",
                    "opportunity": f"Add tests: {missing_tests}",
                    "priority": "medium",
                    "description": "Create unit tests for new tools"
                })

        # Verificar documentación
        opportunities.append({
            "area": "Documentation",
            "opportunity": "Add API documentation and usage examples",
            "priority": "low",
            "description": "Create comprehensive docs for each skill and tool"
        })

        # Verificar frontend
        frontend_path = BASE_DIR / "frontend"
        if frontend_path.exists():
            opportunities.append({
                "area": "Frontend Integration",
                "opportunity": "Connect frontend to new tools",
                "priority": "high",
                "description": "Update frontend to use new gentle_ai, engram, and gentle_pi tools"
            })

        return TestResult(
            "Opportunities Analysis",
            True,
            f"Found {len(opportunities)} improvement opportunities",
            str(opportunities)
        )

    def print_summary(self):
        """Imprime el resumen de todas las pruebas."""
        print("\n" + "="*60)
        print("📊 RESUMEN DE PRUEBAS")
        print("="*60)

        passed = sum(1 for r in self.results if r.success)
        failed = sum(1 for r in self.results if not r.success)

        print(f"\n✅ Pasaron: {passed}")
        print(f"❌ Fallaron: {failed}")
        print(f"📝 Total: {len(self.results)}")

        if failed > 0:
            print("\n❌ PRUEBAS FALLIDAS:")
            for r in self.results:
                if not r.success:
                    print(f"   - {r.name}: {r.message}")

        print("\n" + "="*60)
        print("🎯 OPORTUNIDADES DETECTADAS")
        print("="*60)

        # Buscar el resultado de análisis de oportunidades
        for r in self.results:
            if r.name == "Opportunities Analysis" and r.success:
                import ast
                try:
                    opportunities = ast.literal_eval(r.details)
                    for i, opp in enumerate(opportunities, 1):
                        print(f"\n{i}. [{opp['priority'].upper()}] {opp['area']}")
                        print(f"   Oportunidad: {opp['opportunity']}")
                        print(f"   Descripción: {opp['description']}")
                except:
                    print(f"   {r.details}")

        return passed, failed


def main():
    """Ejecuta todas las pruebas."""
    print("🚀 INICIANDO PRUEBAS DE INTEGRACIÓN - RICCO AI")
    print("="*60)

    tester = IntegrationTester()

    # Ejecutar pruebas
    tester.run_test("Directory Structure", tester.test_directory_structure)
    tester.run_test("Skill Files", tester.test_skill_files)
    tester.run_test("Tool Files", tester.test_tool_files)
    tester.run_test("Clarification Middleware", tester.test_clarification_middleware)
    tester.run_test("LangGraph Interrupt", tester.test_langgraph_interrupt_available)
    tester.run_test("Gentle AI Tools Import", tester.test_gentle_ai_tools_import)
    tester.run_test("Engram Tools Import", tester.test_engram_tools_import)
    tester.run_test("Gentle-Pi Tools Import", tester.test_gentle_pi_tools_import)
    tester.run_test("Tool Functionality", tester.test_tool_functionality)
    tester.run_test("Opportunities Analysis", tester.test_opportunities_analysis)

    # Mostrar resumen
    passed, failed = tester.print_summary()

    print("\n" + "="*60)
    if failed == 0:
        print("🎉 ¡TODAS LAS PRUEBAS PASARON!")
    else:
        print(f"⚠️ {failed} pruebas fallaron. Revisar detalles arriba.")
    print("="*60)

    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())

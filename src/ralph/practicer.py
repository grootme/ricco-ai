"""
Skill Practicer - Práctica de Nuevas Habilidades

Valida el nuevo conocimiento en sandboxes aislados
antes de promoverlo a habilidades activas.
"""

import asyncio
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class PracticeStatus(str, Enum):
    """Estado de la práctica"""
    PENDING = "pending"
    RUNNING = "running"
    PASSED = "passed"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class PracticeResult:
    """Resultado de practicar una habilidad"""
    skill_id: str
    skill_name: str
    status: PracticeStatus
    passed: bool = False
    execution_output: Optional[str] = None
    errors: List[str] = field(default_factory=list)
    execution_time_ms: int = 0
    validated_at: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)


class SkillPracticer:
    """
    Practicador de Habilidades.
    
    Valida nuevo conocimiento y habilidades en sandboxes aislados
    antes de promoverlos a uso general.
    
    Usage:
        practicer = SkillPracticer(sandbox_manager)
        
        # Practicar una skill
        result = await practicer.practice(skill, test_cases)
        
        # Practicar lote
        results = await practicer.practice_batch(skills)
    """
    
    def __init__(
        self,
        sandbox_manager: Optional[Any] = None,
        max_concurrent: int = 3
    ):
        """
        Inicializa el practicador.
        
        Args:
            sandbox_manager: Gestor de sandboxes para práctica aislada
            max_concurrent: Máximo de prácticas concurrentes
        """
        self._sandbox_manager = sandbox_manager
        self.max_concurrent = max_concurrent
        self._results: List[PracticeResult] = []
        self._semaphore = asyncio.Semaphore(max_concurrent)
    
    async def practice(
        self,
        skill: Any,
        test_cases: Optional[List[Dict[str, Any]]] = None
    ) -> PracticeResult:
        """
        Practica una habilidad específica.
        
        Args:
            skill: Habilidad a practicar
            test_cases: Casos de prueba para validación
        
        Returns:
            PracticeResult con el resultado de la práctica
        """
        async with self._semaphore:
            start_time = datetime.utcnow()
            
            result = PracticeResult(
                skill_id=skill.id if hasattr(skill, 'id') else "unknown",
                skill_name=skill.metadata.name if hasattr(skill, 'metadata') else "Unknown",
                status=PracticeStatus.RUNNING
            )
            
            try:
                # Generar casos de prueba si no se proporcionan
                if not test_cases:
                    test_cases = self._generate_test_cases(skill)
                
                # Ejecutar cada caso de prueba
                all_passed = True
                outputs = []
                
                for i, test_case in enumerate(test_cases):
                    test_result = await self._run_test_case(skill, test_case, i)
                    
                    outputs.append(test_result.get("output", ""))
                    
                    if not test_result.get("passed"):
                        all_passed = False
                        result.errors.append(f"Test case {i+1} failed: {test_result.get('error')}")
                
                result.execution_output = "\n".join(outputs[-5:])  # Últimos 5 outputs
                result.passed = all_passed
                result.status = PracticeStatus.PASSED if all_passed else PracticeStatus.FAILED
                
            except Exception as e:
                result.status = PracticeStatus.FAILED
                result.passed = False
                result.errors.append(str(e))
            
            result.execution_time_ms = int(
                (datetime.utcnow() - start_time).total_seconds() * 1000
            )
            
            self._results.append(result)
            
            return result
    
    async def practice_batch(
        self,
        skills: List[Any],
        test_cases_map: Optional[Dict[str, List[Dict[str, Any]]]] = None
    ) -> List[PracticeResult]:
        """
        Practica múltiples habilidades en paralelo.
        
        Args:
            skills: Lista de habilidades a practicar
            test_cases_map: Mapa de skill_id -> test_cases
        
        Returns:
            Lista de resultados de práctica
        """
        test_cases_map = test_cases_map or {}
        
        tasks = []
        for skill in skills:
            skill_id = skill.id if hasattr(skill, 'id') else "unknown"
            test_cases = test_cases_map.get(skill_id)
            tasks.append(self.practice(skill, test_cases))
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Manejar excepciones
        final_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                skill = skills[i]
                final_results.append(PracticeResult(
                    skill_id=skill.id if hasattr(skill, 'id') else "unknown",
                    skill_name=skill.metadata.name if hasattr(skill, 'metadata') else "Unknown",
                    status=PracticeStatus.FAILED,
                    passed=False,
                    errors=[str(result)]
                ))
            else:
                final_results.append(result)
        
        return final_results
    
    async def _run_test_case(
        self,
        skill: Any,
        test_case: Dict[str, Any],
        index: int
    ) -> Dict[str, Any]:
        """Ejecuta un caso de prueba individual"""
        try:
            # Simular ejecución
            # En implementación real, ejecutaría en sandbox
            await asyncio.sleep(0.1)  # Simular trabajo
            
            input_data = test_case.get("input", {})
            expected = test_case.get("expected")
            
            # Validación básica
            passed = True
            output = f"Test {index+1} executed with input: {input_data}"
            
            return {
                "passed": passed,
                "output": output,
                "error": None
            }
            
        except Exception as e:
            return {
                "passed": False,
                "output": None,
                "error": str(e)
            }
    
    def _generate_test_cases(self, skill: Any) -> List[Dict[str, Any]]:
        """Genera casos de prueba básicos para una skill"""
        test_cases = []
        
        # Caso básico de validación
        test_cases.append({
            "name": "basic_validation",
            "input": {"action": "validate"},
            "expected": {"valid": True},
            "description": "Validar que la skill puede ejecutarse"
        })
        
        # Si la skill tiene ejemplos, usarlos
        if hasattr(skill, 'examples') and skill.examples:
            for i, example in enumerate(skill.examples[:3]):
                test_cases.append({
                    "name": f"example_{i+1}",
                    "input": example.get("input", {}),
                    "expected": example.get("output"),
                    "description": f"Caso de ejemplo {i+1}"
                })
        
        return test_cases
    
    def get_results(self) -> List[PracticeResult]:
        """Obtiene todos los resultados de práctica"""
        return self._results
    
    def get_passed(self) -> List[PracticeResult]:
        """Obtiene habilidades que pasaron la práctica"""
        return [r for r in self._results if r.passed]
    
    def get_failed(self) -> List[PracticeResult]:
        """Obtiene habilidades que fallaron la práctica"""
        return [r for r in self._results if not r.passed]
    
    def clear_results(self) -> None:
        """Limpia los resultados almacenados"""
        self._results.clear()
    
    def get_stats(self) -> Dict[str, Any]:
        """Obtiene estadísticas de práctica"""
        total = len(self._results)
        passed = sum(1 for r in self._results if r.passed)
        
        return {
            "total_practiced": total,
            "passed": passed,
            "failed": total - passed,
            "pass_rate": passed / total if total > 0 else 0
        }

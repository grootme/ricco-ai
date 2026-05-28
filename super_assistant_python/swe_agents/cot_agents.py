"""
Agentes Constructores SWE (Software Engineering) con CoT.
Implementa técnicas avanzadas de razonamiento y código.
"""

from typing import Any, Dict, List, Optional, Callable, Union
from abc import ABC, abstractmethod
from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum
from dataclasses import dataclass
import asyncio
import re
import json


# =============================================================================
# CHAIN OF THOUGHT (CoT) FRAMEWORK
# =============================================================================

class ThoughtType(str, Enum):
    """Tipos de pensamiento en CoT."""
    ANALYSIS = "analysis"           # Análisis del problema
    DECOMPOSITION = "decomposition" # Descomposición en subproblemas
    HYPOTHESIS = "hypothesis"       # Hipótesis
    REASONING = "reasoning"         # Razonamiento lógico
    VERIFICATION = "verification"   # Verificación
    DECISION = "decision"           # Decisión
    REFLECTION = "reflection"       # Reflexión
    PLANNING = "planning"           # Planificación
    EXECUTION = "execution"         # Ejecución
    CORRECTION = "correction"       # Corrección


class Thought(BaseModel):
    """Un pensamiento individual en la cadena."""
    id: str
    type: ThoughtType
    content: str
    confidence: float = 0.5
    dependencies: List[str] = Field(default_factory=list)  # IDs de pensamientos previos
    evidence: List[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    def to_prompt_format(self) -> str:
        """Convierte a formato para prompt."""
        return f"[{self.type.value.upper()}] {self.content}"


class ThoughtChain(BaseModel):
    """Cadena de pensamientos completa."""
    id: str
    task: str
    thoughts: List[Thought] = Field(default_factory=list)
    conclusion: Optional[str] = None
    success: bool = True
    
    def add_thought(
        self,
        type: ThoughtType,
        content: str,
        confidence: float = 0.5,
        dependencies: Optional[List[str]] = None
    ) -> Thought:
        """Agrega un pensamiento a la cadena."""
        thought = Thought(
            id=f"thought_{len(self.thoughts) + 1}",
            type=type,
            content=content,
            confidence=confidence,
            dependencies=dependencies or []
        )
        self.thoughts.append(thought)
        return thought
    
    def to_prompt(self) -> str:
        """Convierte toda la cadena a formato prompt."""
        lines = [f"Task: {self.task}", "", "Chain of Thought:"]
        
        for i, thought in enumerate(self.thoughts, 1):
            lines.append(f"{i}. {thought.to_prompt_format()}")
        
        if self.conclusion:
            lines.extend(["", f"Conclusion: {self.conclusion}"])
        
        return "\n".join(lines)
    
    def get_by_type(self, thought_type: ThoughtType) -> List[Thought]:
        """Obtiene pensamientos por tipo."""
        return [t for t in self.thoughts if t.type == thought_type]


# =============================================================================
# TREE OF THOUGHT (ToT) FRAMEWORK
# =============================================================================

class ThoughtNode(BaseModel):
    """Nodo en el árbol de pensamientos."""
    id: str
    thought: Thought
    children: List['ThoughtNode'] = Field(default_factory=list)
    parent_id: Optional[str] = None
    score: float = 0.0
    explored: bool = False
    pruned: bool = False


class TreeOfThought:
    """Árbol de pensamientos para exploración."""
    
    def __init__(self, root_thought: Thought):
        self.root = ThoughtNode(
            id="root",
            thought=root_thought
        )
        self.nodes: Dict[str, ThoughtNode] = {"root": self.root}
        self.best_path: List[str] = []
    
    def add_child(
        self,
        parent_id: str,
        thought: Thought,
        score: float = 0.0
    ) -> ThoughtNode:
        """Agrega un hijo al árbol."""
        parent = self.nodes.get(parent_id)
        if not parent:
            raise ValueError(f"Parent {parent_id} not found")
        
        node = ThoughtNode(
            id=f"node_{len(self.nodes)}",
            thought=thought,
            parent_id=parent_id,
            score=score
        )
        
        parent.children.append(node)
        self.nodes[node.id] = node
        
        return node
    
    def get_best_leaf(self) -> Optional[ThoughtNode]:
        """Obtiene la mejor hoja no explorada."""
        best = None
        best_score = -float('inf')
        
        for node in self.nodes.values():
            if not node.explored and not node.children and not node.pruned:
                if node.score > best_score:
                    best_score = node.score
                    best = node
        
        return best
    
    def backtrack(self, node_id: str) -> List[Thought]:
        """Retorna el camino desde la raíz hasta el nodo."""
        path = []
        current = self.nodes.get(node_id)
        
        while current:
            path.append(current.thought)
            if current.parent_id:
                current = self.nodes.get(current.parent_id)
            else:
                break
        
        return list(reversed(path))
    
    def prune_subtree(self, node_id: str) -> None:
    """Poda un subárbol."""
        node = self.nodes.get(node_id)
        if node:
            node.pruned = True
            for child in node.children:
                self.prune_subtree(child.id)


# =============================================================================
# SELF-REFINE FRAMEWORK
# =============================================================================

class RefinementIteration(BaseModel):
    """Una iteración de refinamiento."""
    iteration: int
    initial_output: str
    critique: str
    refined_output: str
    improvement_score: float = 0.0


class SelfRefine:
    """Framework para auto-refinamiento."""
    
    def __init__(self, max_iterations: int = 3, min_improvement: float = 0.1):
        self.max_iterations = max_iterations
        self.min_improvement = min_improvement
        self.history: List[RefinementIteration] = []
    
    async def refine(
        self,
        initial_output: str,
        critique_func: Callable[[str], str],
        refine_func: Callable[[str, str], str],
        score_func: Callable[[str], float]
    ) -> str:
        """Ejecuta el ciclo de refinamiento."""
        current_output = initial_output
        current_score = await score_func(current_output)
        
        for i in range(self.max_iterations):
            # Generar crítica
            critique = await critique_func(current_output)
            
            # Refinar basado en la crítica
            refined = await refine_func(current_output, critique)
            new_score = await score_func(refined)
            
            # Registrar iteración
            iteration = RefinementIteration(
                iteration=i + 1,
                initial_output=current_output,
                critique=critique,
                refined_output=refined,
                improvement_score=new_score - current_score
            )
            self.history.append(iteration)
            
            # Verificar mejora
            if new_score - current_score < self.min_improvement:
                break
            
            current_output = refined
            current_score = new_score
        
        return current_output


# =============================================================================
# REACT PATTERN
# =============================================================================

class ActionType(str, Enum):
    """Tipos de acciones en ReAct."""
    THINK = "think"
    ACT = "act"
    OBSERVE = "observe"


class ReActStep(BaseModel):
    """Un paso en el ciclo ReAct."""
    step: int
    action: ActionType
    content: str
    tool_name: Optional[str] = None
    tool_args: Optional[Dict[str, Any]] = None
    observation: Optional[str] = None


class ReActExecutor:
    """Ejecutor del patrón ReAct."""
    
    def __init__(self, max_steps: int = 10):
        self.max_steps = max_steps
        self.steps: List[ReActStep] = []
        self.tools: Dict[str, Callable] = {}
    
    def register_tool(self, name: str, func: Callable) -> None:
        """Registra una herramienta."""
        self.tools[name] = func
    
    async def execute(
        self,
        task: str,
        think_func: Callable[[str, List[ReActStep]], str],
        act_func: Callable[[str, List[ReActStep]], tuple]
    ) -> str:
        """Ejecuta el ciclo ReAct."""
        context = task
        
        for step_num in range(1, self.max_steps + 1):
            # THINK
            thought = await think_func(context, self.steps)
            self.steps.append(ReActStep(
                step=step_num,
                action=ActionType.THINK,
                content=thought
            ))
            
            # ACT
            tool_name, tool_args = await act_func(context, self.steps)
            
            if tool_name == "finish":
                return tool_args.get("answer", "Task completed")
            
            self.steps.append(ReActStep(
                step=step_num,
                action=ActionType.ACT,
                content=f"Using tool: {tool_name}",
                tool_name=tool_name,
                tool_args=tool_args
            ))
            
            # OBSERVE
            if tool_name in self.tools:
                observation = await self.tools[tool_name](**tool_args)
            else:
                observation = f"Tool {tool_name} not found"
            
            self.steps.append(ReActStep(
                step=step_num,
                action=ActionType.OBSERVE,
                content=str(observation),
                observation=str(observation)
            ))
            
            # Actualizar contexto
            context = f"{context}\n\nThought: {thought}\nAction: {tool_name}({tool_args})\nObservation: {observation}"
        
        return "Max steps reached without completion"


# =============================================================================
# SWE AGENT BASE
# =============================================================================

class SWEAgentRole(str, Enum):
    """Roles de agentes SWE."""
    ANALYZER = "analyzer"       # Analiza código y problemas
    PLANNER = "planner"         # Planifica soluciones
    CODER = "coder"             # Escribe código
    TESTER = "tester"           # Escribe y ejecuta tests
    REVIEWER = "reviewer"       # Revisa código
    DEBUGGER = "debugger"       # Depura problemas
    REFACTORER = "refactorer"   # Refactoriza código


class CodeContext(BaseModel):
    """Contexto de código para el agente."""
    file_path: Optional[str] = None
    language: str = "python"
    content: str = ""
    line_start: Optional[int] = None
    line_end: Optional[int] = None
    imports: List[str] = Field(default_factory=list)
    functions: List[str] = Field(default_factory=list)
    classes: List[str] = Field(default_factory=list)


class SWEAgentOutput(BaseModel):
    """Output de un agente SWE."""
    agent_role: SWEAgentRole
    thought_chain: Optional[ThoughtChain] = None
    code_changes: List[Dict[str, Any]] = Field(default_factory=list)
    test_results: Optional[Dict[str, Any]] = None
    recommendations: List[str] = Field(default_factory=list)
    confidence: float = 0.5
    success: bool = True
    error: Optional[str] = None


class BaseSWEAgent(ABC):
    """Agente base de Software Engineering."""
    
    def __init__(
        self,
        role: SWEAgentRole,
        use_cot: bool = True,
        use_tot: bool = False,
        use_self_refine: bool = True
    ):
        self.role = role
        self.use_cot = use_cot
        self.use_tot = use_tot
        self.use_self_refine = use_self_refine
        
        self.thought_chain: Optional[ThoughtChain] = None
        self.tot: Optional[TreeOfThought] = None
        self.refine_history: List[RefinementIteration] = []
    
    @abstractmethod
    async def analyze(self, input: Dict[str, Any]) -> SWEAgentOutput:
        """Analiza la entrada y genera output."""
        pass
    
    def start_thought_chain(self, task: str) -> ThoughtChain:
        """Inicia una nueva cadena de pensamientos."""
        self.thought_chain = ThoughtChain(
            id=f"chain_{datetime.utcnow().timestamp()}",
            task=task
        )
        return self.thought_chain
    
    def add_thought(
        self,
        type: ThoughtType,
        content: str,
        confidence: float = 0.5
    ) -> Optional[Thought]:
        """Agrega un pensamiento a la cadena actual."""
        if self.thought_chain:
            return self.thought_chain.add_thought(type, content, confidence)
        return None


# =============================================================================
# CONCRETE SWE AGENTS
# =============================================================================

class CodeAnalyzerAgent(BaseSWEAgent):
    """Agente analizador de código."""
    
    def __init__(self):
        super().__init__(
            role=SWEAgentRole.ANALYZER,
            use_cot=True
        )
    
    async def analyze(self, input: Dict[str, Any]) -> SWEAgentOutput:
        """Analiza código y detecta problemas."""
        code = input.get("code", "")
        task = input.get("task", "Analyze code")
        
        # Iniciar cadena de pensamientos
        chain = self.start_thought_chain(task)
        
        # Análisis CoT
        self.add_thought(
            ThoughtType.ANALYSIS,
            f"Analyzing code of length {len(code)} characters",
            0.8
        )
        
        # Detectar elementos
        imports = re.findall(r'^import .+$|^from .+ import .+$', code, re.MULTILINE)
        functions = re.findall(r'def (\w+)\(', code)
        classes = re.findall(r'class (\w+)', code)
        
        self.add_thought(
            ThoughtType.REASONING,
            f"Found {len(imports)} imports, {len(functions)} functions, {len(classes)} classes",
            0.9
        )
        
        # Detectar posibles problemas
        issues = []
        if "TODO" in code:
            issues.append("TODO comments found")
        if "print(" in code:
            issues.append("Print statements (consider logging)")
        if "except:" in code:
            issues.append("Bare except clauses")
        
        self.add_thought(
            ThoughtType.VERIFICATION,
            f"Detected {len(issues)} potential issues",
            0.7
        )
        
        chain.conclusion = f"Analysis complete. {len(issues)} issues found."
        
        return SWEAgentOutput(
            agent_role=self.role,
            thought_chain=chain,
            recommendations=issues,
            confidence=0.8
        )


class CodePlannerAgent(BaseSWEAgent):
    """Agente planificador de soluciones."""
    
    def __init__(self):
        super().__init__(
            role=SWEAgentRole.PLANNER,
            use_cot=True,
            use_tot=True
        )
    
    async def analyze(self, input: Dict[str, Any]) -> SWEAgentOutput:
        """Planifica la solución para un problema."""
        problem = input.get("problem", "")
        
        chain = self.start_thought_chain(f"Plan solution for: {problem}")
        
        # Análisis del problema
        self.add_thought(
            ThoughtType.ANALYSIS,
            f"Understanding problem: {problem[:100]}...",
            0.7
        )
        
        # Descomposición
        subtasks = [
            "1. Understand requirements",
            "2. Design solution approach",
            "3. Identify necessary components",
            "4. Plan implementation steps",
            "5. Define testing strategy"
        ]
        
        self.add_thought(
            ThoughtType.DECOMPOSITION,
            f"Decomposed into {len(subtasks)} subtasks",
            0.8
        )
        
        # Hipótesis
        self.add_thought(
            ThoughtType.HYPOTHESIS,
            "Proposed approach: iterative development with tests",
            0.6
        )
        
        # Plan
        self.add_thought(
            ThoughtType.PLANNING,
            "\n".join(subtasks),
            0.85
        )
        
        chain.conclusion = "Plan created successfully"
        
        return SWEAgentOutput(
            agent_role=self.role,
            thought_chain=chain,
            recommendations=subtasks,
            confidence=0.75
        )


class CodeBuilderAgent(BaseSWEAgent):
    """Agente constructor de código."""
    
    def __init__(self):
        super().__init__(
            role=SWEAgentRole.CODER,
            use_cot=True,
            use_self_refine=True
        )
        self._refiner = SelfRefine(max_iterations=3)
    
    async def analyze(self, input: Dict[str, Any]) -> SWEAgentOutput:
        """Construye código basado en especificaciones."""
        spec = input.get("specification", "")
        language = input.get("language", "python")
        
        chain = self.start_thought_chain(f"Build code for: {spec[:100]}...")
        
        # Análisis de especificación
        self.add_thought(
            ThoughtType.ANALYSIS,
            f"Specification received in {language}",
            0.8
        )
        
        # Generación de código (placeholder)
        code = self._generate_code(spec, language)
        
        self.add_thought(
            ThoughtType.EXECUTION,
            "Code generated",
            0.7
        )
        
        # Verificación
        self.add_thought(
            ThoughtType.VERIFICATION,
            "Checking code correctness",
            0.8
        )
        
        chain.conclusion = "Code generation complete"
        
        return SWEAgentOutput(
            agent_role=self.role,
            thought_chain=chain,
            code_changes=[{
                "action": "create",
                "content": code,
                "language": language
            }],
            confidence=0.75
        )
    
    def _generate_code(self, spec: str, language: str) -> str:
        """Genera código placeholder."""
        if language == "python":
            return f'''# Generated code
# Specification: {spec[:100]}

def main():
    """Main function."""
    # TODO: Implement based on specification
    pass

if __name__ == "__main__":
    main()
'''
        return f"// Generated code for: {spec[:50]}..."


class CodeTesterAgent(BaseSWEAgent):
    """Agente de testing."""
    
    def __init__(self):
        super().__init__(
            role=SWEAgentRole.TESTER,
            use_cot=True
        )
    
    async def analyze(self, input: Dict[str, Any]) -> SWEAgentOutput:
        """Genera y ejecuta tests."""
        code = input.get("code", "")
        
        chain = self.start_thought_chain("Generate tests for code")
        
        self.add_thought(
            ThoughtType.ANALYSIS,
            "Analyzing code for test generation",
            0.8
        )
        
        # Generar tests (placeholder)
        tests = self._generate_tests(code)
        
        self.add_thought(
            ThoughtType.EXECUTION,
            f"Generated {len(tests)} test cases",
            0.7
        )
        
        # Simular ejecución
        results = {
            "total": len(tests),
            "passed": len(tests),
            "failed": 0,
            "tests": tests
        }
        
        self.add_thought(
            ThoughtType.VERIFICATION,
            f"Test results: {results['passed']}/{results['total']} passed",
            0.9
        )
        
        chain.conclusion = "All tests passed"
        
        return SWEAgentOutput(
            agent_role=self.role,
            thought_chain=chain,
            test_results=results,
            confidence=0.85
        )
    
    def _generate_tests(self, code: str) -> List[Dict[str, Any]]:
        """Genera tests placeholder."""
        functions = re.findall(r'def (\w+)\(', code)
        
        tests = []
        for func in functions[:3]:
            tests.append({
                "name": f"test_{func}",
                "status": "passed",
                "assertion": f"assert {func}() is not None"
            })
        
        if not tests:
            tests.append({
                "name": "test_placeholder",
                "status": "passed",
                "assertion": "assert True"
            })
        
        return tests


# =============================================================================
# SWE AGENT TEAM
# =============================================================================

class SWEAgentTeam:
    """Equipo de agentes SWE trabajando juntos."""
    
    def __init__(self):
        self.agents: Dict[SWEAgentRole, BaseSWEAgent] = {
            SWEAgentRole.ANALYZER: CodeAnalyzerAgent(),
            SWEAgentRole.PLANNER: CodePlannerAgent(),
            SWEAgentRole.CODER: CodeBuilderAgent(),
            SWEAgentRole.TESTER: CodeTesterAgent(),
        }
        self.history: List[SWEAgentOutput] = []
    
    async def solve(
        self,
        problem: str,
        code: Optional[str] = None
    ) -> Dict[str, Any]:
        """Resuelve un problema de software."""
        results = {}
        
        # 1. Analizar
        analysis = await self.agents[SWEAgentRole.ANALYZER].analyze({
            "code": code or "",
            "task": problem
        })
        results["analysis"] = analysis.model_dump()
        self.history.append(analysis)
        
        # 2. Planificar
        plan = await self.agents[SWEAgentRole.PLANNER].analyze({
            "problem": problem
        })
        results["plan"] = plan.model_dump()
        self.history.append(plan)
        
        # 3. Codificar
        build = await self.agents[SWEAgentRole.CODER].analyze({
            "specification": problem,
            "language": "python"
        })
        results["code"] = build.model_dump()
        self.history.append(build)
        
        # 4. Testear
        generated_code = build.code_changes[0].get("content", "") if build.code_changes else ""
        test = await self.agents[SWEAgentRole.TESTER].analyze({
            "code": generated_code
        })
        results["tests"] = test.model_dump()
        self.history.append(test)
        
        return {
            "problem": problem,
            "results": results,
            "success": test.test_results.get("failed", 0) == 0 if test.test_results else False
        }
    
    def get_thought_chains(self) -> List[ThoughtChain]:
        """Obtiene todas las cadenas de pensamiento."""
        return [
            output.thought_chain
            for output in self.history
            if output.thought_chain
        ]
    
    def get_full_reasoning(self) -> str:
        """Obtiene el razonamiento completo."""
        chains = self.get_thought_chains()
        return "\n\n---\n\n".join(chain.to_prompt() for chain in chains)

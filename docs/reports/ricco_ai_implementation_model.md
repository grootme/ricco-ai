# Modelo de Implementación - Patrones de Agentes IA en Ricco-AI

## 1. Arquitectura General

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              NEXUS SUPER AGENT                              │
│                         (Punto de Entrada Único)                           │
└─────────────────────────────────────┬───────────────────────────────────────┘
                                      │
                    ┌─────────────────┼─────────────────┐
                    │                 │                 │
                    ▼                 ▼                 ▼
            ┌───────────────┐ ┌───────────────┐ ┌───────────────┐
            │   PATTERN     │ │   PATTERN     │ │   PATTERN     │
            │   ROUTER      │ │   ROUTER      │ │   ROUTER      │
            │               │ │               │ │               │
            │ (Pattern      │ │ (Pattern      │ │ (Pattern      │
            │  Selection)   │ │  Selection)   │ │  Selection)   │
            └───────┬───────┘ └───────┬───────┘ └───────┬───────┘
                    │                 │                 │
    ┌───────────────┼─────────────────┼─────────────────┼───────────────┐
    │               │                 │                 │               │
    ▼               ▼                 ▼                 ▼               ▼
┌────────┐   ┌────────┐   ┌────────────────┐   ┌────────┐   ┌────────┐
│CHAINING│   │ROUTING │   │PARALLELIZATION │   │EVAL-OPT│   │ REACT  │
│PATTERN │   │PATTERN │   │    PATTERN     │   │PATTERN │   │PATTERN │
└────────┘   └────────┘   └────────────────┘   └────────┘   └────────┘
```

---

## 2. Patrón EVALUATOR-OPTIMIZER (Prioridad 1)

### 2.1 Diseño Detallado

```python
# src/iovba/patterns/evaluator_optimizer/eval_opt_pattern.py

from typing import Dict, Any, List, Optional, Callable, TypedDict
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
import asyncio

class EvaluationResult(str, Enum):
    APPROVED = "approved"
    NEEDS_IMPROVEMENT = "needs_improvement"
    REJECTED = "rejected"

@dataclass
class EvaluationCriteria:
    """Criterios de evaluación configurables"""
    name: str
    description: str
    weight: float = 1.0
    threshold: float = 0.7
    evaluator_fn: Optional[Callable] = None

@dataclass
class OptimizerConfig:
    """Configuración del ciclo de optimización"""
    max_iterations: int = 5
    improvement_threshold: float = 0.1
    convergence_threshold: float = 0.01
    timeout_seconds: int = 300
    enable_early_stopping: bool = True

@dataclass
class EvalOptState(TypedDict):
    """Estado del ciclo Evaluator-Optimizer"""
    iteration: int
    current_solution: str
    evaluation_score: float
    evaluation_details: Dict[str, Any]
    feedback: List[str]
    improvements: List[str]
    history: List[Dict[str, Any]]
    status: str

class EvaluatorOptimizerPattern:
    """
    Patrón Evaluator-Optimizer para mejora iterativa.
    
    Flujo:
    1. Generator produce solución inicial
    2. Evaluator evalúa contra criterios
    3. Si no aprueba, Optimizer sugiere mejoras
    4. Generator crea nueva versión
    5. Repetir hasta aprobación o max_iterations
    """
    
    def __init__(
        self,
        criteria: List[EvaluationCriteria],
        config: Optional[OptimizerConfig] = None,
        llm_provider: Optional[Any] = None,
    ):
        self.criteria = criteria
        self.config = config or OptimizerConfig()
        self.llm_provider = llm_provider
        
    async def run(
        self,
        task: str,
        initial_solution: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Ejecuta el ciclo de evaluación y optimización.
        
        Returns:
            {
                "approved": bool,
                "final_solution": str,
                "iterations": int,
                "final_score": float,
                "improvement_history": List[Dict]
            }
        """
        state: EvalOptState = {
            "iteration": 0,
            "current_solution": initial_solution or "",
            "evaluation_score": 0.0,
            "evaluation_details": {},
            "feedback": [],
            "improvements": [],
            "history": [],
            "status": "initialized"
        }
        
        # Si no hay solución inicial, generarla
        if not state["current_solution"]:
            state["current_solution"] = await self._generate(task, context)
        
        while state["iteration"] < self.config.max_iterations:
            state["iteration"] += 1
            state["status"] = "evaluating"
            
            # Evaluar solución actual
            evaluation = await self._evaluate(
                state["current_solution"],
                task,
                context
            )
            
            state["evaluation_score"] = evaluation["score"]
            state["evaluation_details"] = evaluation["details"]
            
            # Guardar historial
            state["history"].append({
                "iteration": state["iteration"],
                "solution": state["current_solution"],
                "score": evaluation["score"],
                "details": evaluation["details"],
                "timestamp": datetime.utcnow().isoformat()
            })
            
            # Verificar si aprobó
            if evaluation["result"] == EvaluationResult.APPROVED:
                state["status"] = "approved"
                return self._build_result(state, approved=True)
            
            # Verificar convergencia
            if self._check_convergence(state):
                state["status"] = "converged"
                return self._build_result(state, approved=False)
            
            # Generar mejoras
            state["status"] = "optimizing"
            improvements = await self._optimize(
                state["current_solution"],
                evaluation["feedback"],
                task,
                context
            )
            
            state["improvements"].extend(improvements["suggestions"])
            state["feedback"].extend(evaluation["feedback"])
            
            # Generar nueva versión
            state["status"] = "regenerating"
            state["current_solution"] = await self._generate(
                task,
                {
                    **(context or {}),
                    "previous_solution": state["current_solution"],
                    "feedback": evaluation["feedback"],
                    "improvements": improvements["suggestions"]
                }
            )
        
        state["status"] = "max_iterations_reached"
        return self._build_result(state, approved=False)
    
    async def _generate(
        self,
        task: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Genera una solución usando el LLM"""
        if not self.llm_provider:
            return f"Generated solution for: {task}"
        
        # Implementar llamada al LLM
        prompt = self._build_generation_prompt(task, context)
        # ... llamada a LLM
        return "Generated solution"
    
    async def _evaluate(
        self,
        solution: str,
        task: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Evalúa la solución contra todos los criterios"""
        scores = {}
        feedback = []
        
        for criterion in self.criteria:
            if criterion.evaluator_fn:
                score = await criterion.evaluator_fn(solution, task, context)
            else:
                score = await self._default_evaluate(criterion, solution, task)
            
            scores[criterion.name] = score
            
            if score < criterion.threshold:
                feedback.append(
                    f"{criterion.name}: Score {score:.2f} below threshold {criterion.threshold}"
                )
        
        # Calcular score ponderado
        total_weight = sum(c.weight for c in self.criteria)
        weighted_score = sum(
            scores[c.name] * c.weight
            for c in self.criteria
        ) / total_weight
        
        # Determinar resultado
        if weighted_score >= 0.8:
            result = EvaluationResult.APPROVED
        elif weighted_score >= 0.5:
            result = EvaluationResult.NEEDS_IMPROVEMENT
        else:
            result = EvaluationResult.REJECTED
        
        return {
            "score": weighted_score,
            "details": scores,
            "feedback": feedback,
            "result": result
        }
    
    async def _optimize(
        self,
        solution: str,
        feedback: List[str],
        task: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Genera sugerencias de mejora"""
        if not self.llm_provider:
            return {"suggestions": feedback}
        
        prompt = self._build_optimization_prompt(solution, feedback, task)
        # ... llamada a LLM para generar mejoras
        return {"suggestions": feedback}
    
    def _check_convergence(self, state: EvalOptState) -> bool:
        """Verifica si el proceso ha convergido"""
        if len(state["history"]) < 2:
            return False
        
        prev_score = state["history"][-2]["score"]
        curr_score = state["evaluation_score"]
        
        improvement = curr_score - prev_score
        
        return improvement < self.config.convergence_threshold
    
    def _build_result(self, state: EvalOptState, approved: bool) -> Dict[str, Any]:
        """Construye el resultado final"""
        return {
            "approved": approved,
            "final_solution": state["current_solution"],
            "iterations": state["iteration"],
            "final_score": state["evaluation_score"],
            "evaluation_details": state["evaluation_details"],
            "improvement_history": state["history"],
            "feedback_received": state["feedback"],
            "status": state["status"]
        }
```

### 2.2 Integración con IOVBA

```python
# src/iovba/patterns/evaluator_optimizer/iovba_integration.py

class IOVBAEvalOptPattern(EvaluatorOptimizerPattern):
    """
    Integración del patrón Evaluator-Optimizer con el stack IOVBA.
    
    Usa los 5 roles IOVBA:
    - INVESTIGADOR: Analiza el problema inicial
    - OBSERVADOR: Monitorea progreso y detecta patrones
    - VALIDADOR: Evalúa la solución (Evaluator)
    - BUILDER: Genera y mejora soluciones (Generator/Optimizer)
    - ASISTENTE: Coordina el proceso
    """
    
    def __init__(self, iovba_group: "IOVBAGroup", **kwargs):
        super().__init__(**kwargs)
        self.group = iovba_group
        
    async def _generate(self, task: str, context: Optional[Dict] = None) -> str:
        """El BUILDER genera la solución"""
        return await self.group.builder.process({
            "task": task,
            "context": context,
            "role": "generator"
        })
    
    async def _evaluate(self, solution: str, task: str, context: Optional[Dict] = None) -> Dict:
        """El VALIDADOR evalúa la solución"""
        return await self.group.validador.process({
            "solution": solution,
            "task": task,
            "criteria": self.criteria,
            "role": "evaluator"
        })
    
    async def _optimize(self, solution: str, feedback: List[str], task: str, context: Optional[Dict] = None) -> Dict:
        """El BUILDER optimiza basado en feedback"""
        return await self.group.builder.process({
            "solution": solution,
            "feedback": feedback,
            "task": task,
            "role": "optimizer"
        })
```

---

## 3. Patrón CHAINING Mejorado (Prioridad 1)

### 3.1 Diseño Detallado

```python
# src/iovba/patterns/chaining/chain_pattern.py

from typing import Dict, Any, List, Optional, Callable, TypeVar, Generic
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
import asyncio

T = TypeVar('T')

class StepStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"

@dataclass
class ChainStep(Generic[T]):
    """Paso individual en la cadena"""
    id: str
    name: str
    description: str
    executor: Callable
    validator: Optional[Callable] = None
    transformer: Optional[Callable] = None  # Transforma output para siguiente paso
    retry_count: int = 3
    retry_delay: float = 1.0
    timeout: float = 60.0
    status: StepStatus = StepStatus.PENDING
    result: Optional[Any] = None
    error: Optional[str] = None

@dataclass
class ChainConfig:
    """Configuración de la cadena"""
    stop_on_failure: bool = True
    enable_checkpoints: bool = True
    parallel_independent: bool = False
    max_total_retries: int = 10

@dataclass
class ChainState:
    """Estado de la cadena"""
    chain_id: str
    current_step: int = 0
    total_steps: int = 0
    status: str = "initialized"
    results: Dict[str, Any] = field(default_factory=dict)
    checkpoints: List[Dict[str, Any]] = field(default_factory=list)
    errors: List[Dict[str, Any]] = field(default_factory=list)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

class ChainingPattern:
    """
    Patrón de encadenamiento con validación entre pasos.
    
    Características:
    - Validación explícita entre pasos
    - Transformación de datos entre pasos
    - Retry automático con backoff
    - Checkpoints para recuperación
    - Skip condicional de pasos
    """
    
    def __init__(
        self,
        steps: List[ChainStep],
        config: Optional[ChainConfig] = None,
    ):
        self.steps = {step.id: step for step in steps}
        self.step_order = [step.id for step in steps]
        self.config = config or ChainConfig()
        
    async def execute(
        self,
        initial_input: Any,
        context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Ejecuta la cadena completa paso a paso.
        """
        import uuid
        
        state = ChainState(
            chain_id=str(uuid.uuid4()),
            total_steps=len(self.steps),
            started_at=datetime.utcnow()
        )
        
        current_data = initial_input
        
        try:
            for i, step_id in enumerate(self.step_order):
                state.current_step = i + 1
                step = self.steps[step_id]
                step.status = StepStatus.RUNNING
                
                # Ejecutar paso con retry
                result = await self._execute_step_with_retry(
                    step, current_data, context
                )
                
                if result["success"]:
                    step.status = StepStatus.COMPLETED
                    step.result = result["output"]
                    
                    # Validar si hay validador
                    if step.validator:
                        validation = await self._validate_step(step, result["output"])
                        if not validation["valid"]:
                            step.status = StepStatus.FAILED
                            step.error = validation["error"]
                            if self.config.stop_on_failure:
                                raise ValueError(f"Validation failed: {validation['error']}")
                    
                    # Transformar para siguiente paso
                    if step.transformer:
                        current_data = await step.transformer(result["output"])
                    else:
                        current_data = result["output"]
                    
                    state.results[step_id] = result["output"]
                    
                    # Guardar checkpoint
                    if self.config.enable_checkpoints:
                        state.checkpoints.append({
                            "step_id": step_id,
                            "step": i + 1,
                            "result": result["output"],
                            "timestamp": datetime.utcnow().isoformat()
                        })
                else:
                    step.status = StepStatus.FAILED
                    step.error = result["error"]
                    state.errors.append({
                        "step_id": step_id,
                        "error": result["error"],
                        "timestamp": datetime.utcnow().isoformat()
                    })
                    
                    if self.config.stop_on_failure:
                        state.status = "failed"
                        return self._build_result(state)
            
            state.status = "completed"
            
        except Exception as e:
            state.status = "error"
            state.errors.append({
                "step_id": "chain",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            })
        
        finally:
            state.completed_at = datetime.utcnow()
        
        return self._build_result(state)
    
    async def _execute_step_with_retry(
        self,
        step: ChainStep,
        input_data: Any,
        context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Ejecuta un paso con reintentos automáticos"""
        last_error = None
        
        for attempt in range(step.retry_count):
            try:
                # Ejecutar con timeout
                result = await asyncio.wait_for(
                    step.executor(input_data, context),
                    timeout=step.timeout
                )
                return {"success": True, "output": result}
                
            except asyncio.TimeoutError:
                last_error = f"Timeout after {step.timeout}s"
            except Exception as e:
                last_error = str(e)
            
            # Esperar antes de reintentar (exponential backoff)
            if attempt < step.retry_count - 1:
                delay = step.retry_delay * (2 ** attempt)
                await asyncio.sleep(delay)
        
        return {"success": False, "error": last_error}
    
    async def _validate_step(
        self,
        step: ChainStep,
        output: Any,
    ) -> Dict[str, Any]:
        """Valida la salida de un paso"""
        try:
            is_valid = await step.validator(output)
            return {
                "valid": bool(is_valid),
                "error": None if is_valid else "Validation returned False"
            }
        except Exception as e:
            return {"valid": False, "error": str(e)}
    
    def _build_result(self, state: ChainState) -> Dict[str, Any]:
        """Construye el resultado final"""
        return {
            "chain_id": state.chain_id,
            "status": state.status,
            "steps_completed": state.current_step,
            "total_steps": state.total_steps,
            "results": state.results,
            "checkpoints": state.checkpoints,
            "errors": state.errors,
            "execution_time_ms": (
                (state.completed_at - state.started_at).total_seconds() * 1000
                if state.completed_at and state.started_at else 0
            )
        }
    
    async def resume_from_checkpoint(
        self,
        checkpoint: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Reanuda la ejecución desde un checkpoint"""
        # Encontrar el paso del checkpoint
        step_index = next(
            (i for i, step_id in enumerate(self.step_order) 
             if step_id == checkpoint["step_id"]),
            0
        )
        
        # Restaurar estado y continuar
        # ... implementación
        pass
```

---

## 4. Patrón ROUTING Mejorado (Prioridad 1)

### 4.1 Diseño Detallado

```python
# src/iovba/patterns/routing/router_pattern.py

from typing import Dict, Any, List, Optional, Callable, TypedDict
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
import asyncio

class RouteType(str, Enum):
    EXACT = "exact"           # Coincidencia exacta
    SEMANTIC = "semantic"     # Similitud semántica
    KEYWORD = "keyword"       # Palabras clave
    ML_CLASSIFIER = "ml"      # Clasificador ML

@dataclass
class Route:
    """Definición de una ruta"""
    id: str
    name: str
    description: str
    intent_patterns: List[str]  # Patrones de intención
    agent_id: str               # ID del agente destino
    priority: int = 0
    confidence_threshold: float = 0.6
    fallback: Optional[str] = None  # Ruta de fallback

@dataclass
class RouteTable:
    """Tabla de rutas con scoring"""
    routes: List[Route] = field(default_factory=list)
    default_route: Optional[str] = None
    
    def add_route(self, route: Route) -> None:
        self.routes.append(route)
        self.routes.sort(key=lambda r: r.priority, reverse=True)
    
    def get_route(self, route_id: str) -> Optional[Route]:
        return next((r for r in self.routes if r.id == route_id), None)

@dataclass
class IntentClassification:
    """Resultado de clasificación de intención"""
    intent: str
    confidence: float
    route_id: str
    alternative_routes: List[Dict[str, Any]] = field(default_factory=list)
    extracted_entities: Dict[str, Any] = field(default_factory=dict)

class IntentClassifier:
    """Clasificador de intenciones"""
    
    def __init__(
        self,
        route_table: RouteTable,
        classifier_type: RouteType = RouteType.KEYWORD,
        llm_provider: Optional[Any] = None,
    ):
        self.route_table = route_table
        self.classifier_type = classifier_type
        self.llm_provider = llm_provider
    
    async def classify(
        self,
        query: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> IntentClassification:
        """Clasifica la query y determina la ruta"""
        
        if self.classifier_type == RouteType.KEYWORD:
            return await self._classify_keyword(query)
        elif self.classifier_type == RouteType.SEMANTIC:
            return await self._classify_semantic(query)
        elif self.classifier_type == RouteType.ML_CLASSIFIER:
            return await self._classify_ml(query, context)
        else:
            return await self._classify_exact(query)
    
    async def _classify_keyword(self, query: str) -> IntentClassification:
        """Clasificación por palabras clave"""
        query_lower = query.lower()
        scores = []
        
        for route in self.route_table.routes:
            score = sum(
                1 for pattern in route.intent_patterns
                if pattern.lower() in query_lower
            )
            if score > 0:
                confidence = min(0.9, 0.4 + (score * 0.15))
                scores.append({
                    "route": route,
                    "score": score,
                    "confidence": confidence
                })
        
        if not scores:
            # Usar ruta por defecto
            return IntentClassification(
                intent="unknown",
                confidence=0.3,
                route_id=self.route_table.default_route or "general"
            )
        
        # Ordenar por score
        scores.sort(key=lambda x: x["confidence"], reverse=True)
        best = scores[0]
        
        return IntentClassification(
            intent=best["route"].name,
            confidence=best["confidence"],
            route_id=best["route"].id,
            alternative_routes=[
                {"route_id": s["route"].id, "confidence": s["confidence"]}
                for s in scores[1:3]
            ]
        )
    
    async def _classify_semantic(self, query: str) -> IntentClassification:
        """Clasificación semántica usando embeddings"""
        # Implementar con embeddings
        pass
    
    async def _classify_ml(
        self,
        query: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> IntentClassification:
        """Clasificación usando modelo ML o LLM"""
        if not self.llm_provider:
            return await self._classify_keyword(query)
        
        # Usar LLM para clasificación
        prompt = f"""
        Classify the following query into one of these intents:
        {', '.join(r.name for r in self.route_table.routes)}
        
        Query: {query}
        
        Return JSON with: intent, confidence (0-1), entities
        """
        # ... llamada a LLM
        pass
    
    async def _classify_exact(self, query: str) -> IntentClassification:
        """Clasificación exacta"""
        for route in self.route_table.routes:
            if query in route.intent_patterns:
                return IntentClassification(
                    intent=route.name,
                    confidence=1.0,
                    route_id=route.id
                )
        
        return IntentClassification(
            intent="unknown",
            confidence=0.0,
            route_id=self.route_table.default_route or "general"
        )

class RouterPattern:
    """
    Patrón de routing para selección dinámica de agentes.
    
    Características:
    - Clasificación de intenciones
    - Scoring de confianza
    - Fallback jerárquico
    - Rutas condicionales
    """
    
    def __init__(
        self,
        route_table: RouteTable,
        agents: Dict[str, Any],  # agent_id -> agent instance
        classifier: IntentClassifier,
    ):
        self.route_table = route_table
        self.agents = agents
        self.classifier = classifier
    
    async def route(
        self,
        query: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Rutea la query al agente apropiado"""
        
        # 1. Clasificar intención
        classification = await self.classifier.classify(query, context)
        
        # 2. Obtener ruta
        route = self.route_table.get_route(classification.route_id)
        
        if not route:
            # Fallback a ruta por defecto
            route = self.route_table.get_route(
                self.route_table.default_route or "general"
            )
        
        # 3. Verificar umbral de confianza
        if classification.confidence < route.confidence_threshold:
            # Intentar fallback
            if route.fallback:
                route = self.route_table.get_route(route.fallback)
        
        # 4. Obtener agente
        agent = self.agents.get(route.agent_id)
        
        if not agent:
            return {
                "success": False,
                "error": f"Agent not found: {route.agent_id}",
                "classification": classification.__dict__
            }
        
        # 5. Ejecutar agente
        result = await agent.process({
            "query": query,
            "context": context,
            "classification": classification.__dict__,
            "route": route.__dict__
        })
        
        return {
            "success": True,
            "result": result,
            "route_used": route.id,
            "classification": classification.__dict__
        }
```

---

## 5. Patrón ReAct (Prioridad 2)

### 5.1 Diseño Detallado

```python
# src/iovba/patterns/react/react_pattern.py

from typing import Dict, Any, List, Optional, TypedDict
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
import re
import json

class ReActStep(str, Enum):
    THOUGHT = "thought"
    ACTION = "action"
    OBSERVATION = "observation"
    ANSWER = "answer"

@dataclass
class Thought:
    """Pensamiento del agente"""
    content: str
    reasoning: str
    next_action: Optional[str] = None

@dataclass
class Action:
    """Acción a ejecutar"""
    tool: str
    tool_input: str
    expected_output: str = ""

@dataclass
class Observation:
    """Resultado de una acción"""
    tool: str
    result: str
    success: bool = True

@dataclass
class ReActState(TypedDict):
    """Estado del ciclo ReAct"""
    query: str
    thoughts: List[Dict[str, Any]]
    actions: List[Dict[str, Any]]
    observations: List[Dict[str, Any]]
    current_step: ReActStep
    iteration: int
    max_iterations: int
    final_answer: Optional[str]
    tools_available: List[str]

class ThoughtParser:
    """Parser de pensamientos estructurados"""
    
    THOUGHT_PATTERN = re.compile(
        r"Thought:\s*(.+?)(?=Action:|Answer:|$)",
        re.DOTALL | re.IGNORECASE
    )
    ACTION_PATTERN = re.compile(
        r"Action:\s*(\w+)\[(.*?)\]",
        re.DOTALL | re.IGNORECASE
    )
    ANSWER_PATTERN = re.compile(
        r"Answer:\s*(.+)$",
        re.DOTALL | re.IGNORECASE
    )
    
    def parse(self, response: str) -> Dict[str, Any]:
        """Parsea la respuesta en componentes ReAct"""
        result = {
            "thought": None,
            "action": None,
            "answer": None
        }
        
        # Parsear pensamiento
        thought_match = self.THOUGHT_PATTERN.search(response)
        if thought_match:
            result["thought"] = thought_match.group(1).strip()
        
        # Parsear acción
        action_match = self.ACTION_PATTERN.search(response)
        if action_match:
            result["action"] = {
                "tool": action_match.group(1).strip(),
                "input": action_match.group(2).strip()
            }
        
        # Parsear respuesta final
        answer_match = self.ANSWER_PATTERN.search(response)
        if answer_match:
            result["answer"] = answer_match.group(1).strip()
        
        return result

class ToolSelector:
    """Selector inteligente de herramientas"""
    
    def __init__(
        self,
        tools: Dict[str, Any],  # tool_name -> tool_function
        tool_descriptions: Dict[str, str] = None,
    ):
        self.tools = tools
        self.tool_descriptions = tool_descriptions or {}
    
    async def select(
        self,
        thought: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> Optional[str]:
        """Selecciona la mejor herramienta basada en el pensamiento"""
        # Implementar selección basada en el pensamiento
        # Puede usar keyword matching o LLM
        for tool_name, description in self.tool_descriptions.items():
            if any(kw in thought.lower() for kw in description.lower().split()):
                return tool_name
        return None
    
    async def execute(
        self,
        tool_name: str,
        tool_input: str,
    ) -> str:
        """Ejecuta una herramienta"""
        tool = self.tools.get(tool_name)
        if not tool:
            return f"Error: Tool '{tool_name}' not found"
        
        try:
            if asyncio.iscoroutinefunction(tool):
                result = await tool(tool_input)
            else:
                result = tool(tool_input)
            return str(result)
        except Exception as e:
            return f"Error executing {tool_name}: {str(e)}"

class ReActPattern:
    """
    Patrón ReAct (Reasoning + Acting).
    
    Ciclo:
    1. THOUGHT: El agente razona sobre el problema
    2. ACTION: El agente selecciona y ejecuta una herramienta
    3. OBSERVATION: El agente observa el resultado
    4. Repetir hasta llegar a ANSWER
    
    Características:
    - Razonamiento explícito
    - Selección dinámica de herramientas
    - Observación y adaptación
    - Ciclo iterativo
    """
    
    def __init__(
        self,
        tools: Dict[str, Any],
        tool_descriptions: Optional[Dict[str, str]] = None,
        llm_provider: Optional[Any] = None,
        max_iterations: int = 10,
    ):
        self.tools = tools
        self.tool_descriptions = tool_descriptions or {
            name: f"Tool: {name}" for name in tools
        }
        self.llm_provider = llm_provider
        self.max_iterations = max_iterations
        self.parser = ThoughtParser()
        self.tool_selector = ToolSelector(tools, tool_descriptions)
    
    async def run(
        self,
        query: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Ejecuta el ciclo ReAct completo"""
        
        state: ReActState = {
            "query": query,
            "thoughts": [],
            "actions": [],
            "observations": [],
            "current_step": ReActStep.THOUGHT,
            "iteration": 0,
            "max_iterations": self.max_iterations,
            "final_answer": None,
            "tools_available": list(self.tools.keys())
        }
        
        while state["iteration"] < state["max_iterations"]:
            state["iteration"] += 1
            
            # 1. Generar pensamiento y posible acción
            response = await self._generate_thought(state, context)
            parsed = self.parser.parse(response)
            
            # Registrar pensamiento
            if parsed["thought"]:
                state["thoughts"].append({
                    "content": parsed["thought"],
                    "iteration": state["iteration"],
                    "timestamp": datetime.utcnow().isoformat()
                })
            
            # 2. Verificar si hay respuesta final
            if parsed["answer"]:
                state["final_answer"] = parsed["answer"]
                state["current_step"] = ReActStep.ANSWER
                break
            
            # 3. Ejecutar acción si existe
            if parsed["action"]:
                action = parsed["action"]
                state["actions"].append({
                    "tool": action["tool"],
                    "input": action["input"],
                    "iteration": state["iteration"],
                    "timestamp": datetime.utcnow().isoformat()
                })
                
                # Ejecutar herramienta
                observation = await self.tool_selector.execute(
                    action["tool"],
                    action["input"]
                )
                
                state["observations"].append({
                    "tool": action["tool"],
                    "result": observation,
                    "iteration": state["iteration"],
                    "timestamp": datetime.utcnow().isoformat()
                })
                
                state["current_step"] = ReActStep.OBSERVATION
        
        return self._build_result(state)
    
    async def _generate_thought(
        self,
        state: ReActState,
        context: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Genera el siguiente pensamiento usando el LLM"""
        
        # Construir prompt con historial
        prompt = self._build_react_prompt(state, context)
        
        if self.llm_provider:
            # Llamar al LLM
            response = await self.llm_provider.generate(prompt)
            return response
        
        # Fallback: generar pensamiento simple
        return f"Thought: I need to analyze the query: {state['query']}\nAction: search[{state['query']}]"
    
    def _build_react_prompt(
        self,
        state: ReActState,
        context: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Construye el prompt para el ciclo ReAct"""
        
        tools_desc = "\n".join(
            f"- {name}: {desc}"
            for name, desc in self.tool_descriptions.items()
        )
        
        history = ""
        for i, thought in enumerate(state["thoughts"]):
            history += f"\nThought {i+1}: {thought['content']}"
            if i < len(state["actions"]):
                action = state["actions"][i]
                history += f"\nAction {i+1}: {action['tool']}[{action['input']}]"
            if i < len(state["observations"]):
                obs = state["observations"][i]
                history += f"\nObservation {i+1}: {obs['result']}"
        
        return f"""
You are a reasoning agent. Use the ReAct format to solve problems.

Available Tools:
{tools_desc}

Question: {state['query']}

{history}

Think step by step. Use the format:
Thought: [your reasoning]
Action: [tool_name][tool_input]

Or if you have the final answer:
Answer: [final answer]

Your response:
"""
    
    def _build_result(self, state: ReActState) -> Dict[str, Any]:
        """Construye el resultado final"""
        return {
            "query": state["query"],
            "final_answer": state["final_answer"],
            "iterations": state["iteration"],
            "thoughts": state["thoughts"],
            "actions": state["actions"],
            "observations": state["observations"],
            "completed": state["current_step"] == ReActStep.ANSWER,
            "tools_used": list(set(a["tool"] for a in state["actions"]))
        }
```

---

## 6. Patrón PARALLELIZATION Mejorado (Prioridad 2)

### 6.1 Diseño Detallado

```python
# src/iovba/patterns/parallelization/parallel_pattern.py

from typing import Dict, Any, List, Optional, Callable, TypedDict
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
import asyncio

class AggregationStrategy(str, Enum):
    CONCAT = "concat"           # Concatenar resultados
    MERGE = "merge"             # Fusionar diccionarios
    BEST = "best"               # Seleccionar el mejor
    VOTE = "vote"               # Votación
    CUSTOM = "custom"           # Función personalizada

@dataclass
class ParallelTask:
    """Tarea para ejecución paralela"""
    id: str
    name: str
    agent_id: str
    input_data: Any
    timeout: float = 60.0
    priority: int = 0

@dataclass
class ParallelConfig:
    """Configuración de paralelización"""
    max_concurrent: int = 5
    fail_fast: bool = False
    min_success_ratio: float = 0.5
    timeout_total: float = 300.0
    aggregation: AggregationStrategy = AggregationStrategy.MERGE

@dataclass
class TaskResult:
    """Resultado de una tarea paralela"""
    task_id: str
    success: bool
    result: Any
    error: Optional[str] = None
    execution_time_ms: float = 0.0

class TaskSplitter:
    """Divisor de tareas para paralelización"""
    
    def split(
        self,
        task: str,
        num_workers: int,
        context: Optional[Dict[str, Any]] = None,
    ) -> List[ParallelTask]:
        """Divide una tarea compleja en subtareas paralelas"""
        # Implementar lógica de división
        # Puede usar LLM para descomponer
        return [
            ParallelTask(
                id=f"subtask_{i}",
                name=f"Subtask {i}",
                agent_id=f"worker_{i}",
                input_data={"subtask": f"part_{i}_of_{task}"}
            )
            for i in range(num_workers)
        ]

class ResultAggregator:
    """Agregador de resultados paralelos"""
    
    def __init__(
        self,
        strategy: AggregationStrategy = AggregationStrategy.MERGE,
        custom_fn: Optional[Callable] = None,
    ):
        self.strategy = strategy
        self.custom_fn = custom_fn
    
    async def aggregate(
        self,
        results: List[TaskResult],
        context: Optional[Dict[str, Any]] = None,
    ) -> Any:
        """Agrega los resultados según la estrategia"""
        
        successful = [r for r in results if r.success]
        
        if not successful:
            return {"error": "All parallel tasks failed", "results": results}
        
        if self.strategy == AggregationStrategy.CONCAT:
            return self._concat(successful)
        elif self.strategy == AggregationStrategy.MERGE:
            return self._merge(successful)
        elif self.strategy == AggregationStrategy.BEST:
            return self._best(successful)
        elif self.strategy == AggregationStrategy.VOTE:
            return self._vote(successful)
        elif self.strategy == AggregationStrategy.CUSTOM and self.custom_fn:
            return await self.custom_fn(successful, context)
        else:
            return successful[0].result
    
    def _concat(self, results: List[TaskResult]) -> Any:
        """Concatena resultados (para listas/strings)"""
        if all(isinstance(r.result, list) for r in results):
            combined = []
            for r in results:
                combined.extend(r.result)
            return combined
        elif all(isinstance(r.result, str) for r in results):
            return "\n\n".join(r.result for r in results)
        else:
            return [r.result for r in results]
    
    def _merge(self, results: List[TaskResult]) -> Any:
        """Fusiona diccionarios"""
        merged = {}
        for r in results:
            if isinstance(r.result, dict):
                merged.update(r.result)
        return merged
    
    def _best(self, results: List[TaskResult]) -> Any:
        """Selecciona el mejor resultado (por score o calidad)"""
        # Implementar selección por score
        return results[0].result
    
    def _vote(self, results: List[TaskResult]) -> Any:
        """Votación entre resultados"""
        # Contar votos
        from collections import Counter
        votes = Counter(str(r.result) for r in results)
        winner = votes.most_common(1)[0][0]
        return winner

class ParallelizationPattern:
    """
    Patrón de paralelización para ejecución concurrente.
    
    Características:
    - División automática de tareas
    - Ejecución concurrente con límite
    - Agregación configurable
    - Manejo de fallos parciales
    - Timeouts por tarea y total
    """
    
    def __init__(
        self,
        agents: Dict[str, Any],
        config: Optional[ParallelConfig] = None,
        splitter: Optional[TaskSplitter] = None,
        aggregator: Optional[ResultAggregator] = None,
    ):
        self.agents = agents
        self.config = config or ParallelConfig()
        self.splitter = splitter or TaskSplitter()
        self.aggregator = aggregator or ResultAggregator(self.config.aggregation)
    
    async def execute(
        self,
        task: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Ejecuta tareas en paralelo"""
        
        # 1. Dividir tareas
        num_workers = min(
            len(self.agents),
            self.config.max_concurrent
        )
        
        subtasks = self.splitter.split(task, num_workers, context)
        
        # 2. Ejecutar con semáforo para limitar concurrencia
        semaphore = asyncio.Semaphore(self.config.max_concurrent)
        
        async def run_with_semaphore(subtask: ParallelTask) -> TaskResult:
            async with semaphore:
                return await self._execute_subtask(subtask, context)
        
        # 3. Lanzar todas las tareas
        start_time = datetime.utcnow()
        
        try:
            results = await asyncio.wait_for(
                asyncio.gather(
                    *[run_with_semaphore(st) for st in subtasks],
                    return_exceptions=True
                ),
                timeout=self.config.timeout_total
            )
            
            # Convertir excepciones a TaskResult fallido
            processed_results = []
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    processed_results.append(TaskResult(
                        task_id=subtasks[i].id,
                        success=False,
                        result=None,
                        error=str(result)
                    ))
                else:
                    processed_results.append(result)
            
            results = processed_results
            
        except asyncio.TimeoutError:
            return {
                "success": False,
                "error": "Total timeout exceeded",
                "execution_time_ms": self.config.timeout_total * 1000
            }
        
        execution_time = (datetime.utcnow() - start_time).total_seconds() * 1000
        
        # 4. Verificar ratio de éxito
        success_count = sum(1 for r in results if r.success)
        success_ratio = success_count / len(results)
        
        if success_ratio < self.config.min_success_ratio:
            return {
                "success": False,
                "error": f"Success ratio {success_ratio:.2f} below minimum {self.config.min_success_ratio}",
                "results": [r.__dict__ for r in results],
                "execution_time_ms": execution_time
            }
        
        # 5. Agregar resultados
        aggregated = await self.aggregator.aggregate(results, context)
        
        return {
            "success": True,
            "result": aggregated,
            "subtasks_executed": len(subtasks),
            "subtasks_succeeded": success_count,
            "results": [r.__dict__ for r in results],
            "execution_time_ms": execution_time
        }
    
    async def _execute_subtask(
        self,
        subtask: ParallelTask,
        context: Optional[Dict[str, Any]] = None,
    ) -> TaskResult:
        """Ejecuta una subtarea individual"""
        
        agent = self.agents.get(subtask.agent_id)
        
        if not agent:
            return TaskResult(
                task_id=subtask.id,
                success=False,
                result=None,
                error=f"Agent not found: {subtask.agent_id}"
            )
        
        start_time = datetime.utcnow()
        
        try:
            result = await asyncio.wait_for(
                agent.process(subtask.input_data, context),
                timeout=subtask.timeout
            )
            
            execution_time = (datetime.utcnow() - start_time).total_seconds() * 1000
            
            return TaskResult(
                task_id=subtask.id,
                success=True,
                result=result,
                execution_time_ms=execution_time
            )
            
        except asyncio.TimeoutError:
            return TaskResult(
                task_id=subtask.id,
                success=False,
                result=None,
                error=f"Timeout after {subtask.timeout}s"
            )
        except Exception as e:
            return TaskResult(
                task_id=subtask.id,
                success=False,
                result=None,
                error=str(e)
            )
```

---

## 7. Integración con NEXUS Super Agent

```python
# src/iovba/patterns/nexus_integration.py

class NEXUSPatternRouter:
    """
    Router de patrones integrado con NEXUS.
    
    Determina qué patrón usar según:
    - Tipo de tarea
    - Complejidad
    - Dominio
    - Disponibilidad de herramientas
    """
    
    def __init__(self, nexus: "NEXUSSuperAgent"):
        self.nexus = nexus
        self.patterns = {
            "chaining": ChainingPattern,
            "routing": RouterPattern,
            "parallelization": ParallelizationPattern,
            "evaluator_optimizer": EvaluatorOptimizerPattern,
            "react": ReActPattern,
        }
    
    async def select_pattern(
        self,
        query: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Selecciona el mejor patrón para la consulta"""
        
        # Detectar dominio
        domain, confidence = self.nexus.detect_domain(query)
        
        # Analizar complejidad
        complexity = await self._analyze_complexity(query)
        
        # Seleccionar patrón
        if complexity == "simple" and "validate" in query.lower():
            return "evaluator_optimizer"
        elif complexity == "simple":
            return "chaining"
        elif "parallel" in query.lower() or "multiple" in query.lower():
            return "parallelization"
        elif "investigate" in query.lower() or "search" in query.lower():
            return "react"
        elif complexity == "complex":
            return "routing"
        else:
            return "chaining"
    
    async def execute_with_pattern(
        self,
        query: str,
        pattern_name: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Ejecuta la consulta con el patrón seleccionado"""
        
        if not pattern_name:
            pattern_name = await self.select_pattern(query, context)
        
        pattern_class = self.patterns.get(pattern_name)
        
        if not pattern_class:
            return {
                "success": False,
                "error": f"Pattern not found: {pattern_name}"
            }
        
        # Instanciar y ejecutar patrón
        # ...
```

---

## 8. Resumen de Implementación

### Archivos a Crear

| Archivo | Prioridad | Descripción |
|---------|-----------|-------------|
| `src/iovba/patterns/__init__.py` | P1 | Módulo principal |
| `src/iovba/patterns/base.py` | P1 | Clase base Pattern |
| `src/iovba/patterns/evaluator_optimizer/` | P1 | Patrón completo |
| `src/iovba/patterns/chaining/` | P1 | Mejoras de chaining |
| `src/iovba/patterns/routing/` | P1 | Router Agent |
| `src/iovba/patterns/react/` | P2 | Ciclo ReAct |
| `src/iovba/patterns/parallelization/` | P2 | Agregadores |
| `src/iovba/patterns/nexus_integration.py` | P1 | Integración con NEXUS |

### Tests Requeridos

| Archivo | Descripción |
|---------|-------------|
| `tests/test_patterns_eval_opt.py` | Tests de Evaluator-Optimizer |
| `tests/test_patterns_chaining.py` | Tests de Chaining mejorado |
| `tests/test_patterns_routing.py` | Tests de Routing |
| `tests/test_patterns_react.py` | Tests de ReAct |
| `tests/test_patterns_parallel.py` | Tests de Parallelization |
| `tests/test_patterns_integration.py` | Tests de integración |

---

*Modelo de implementación generado: 2026-05-18*

# Plan de Integración OpenClaw Agent SaaS con RICCO AI

## Resumen Ejecutivo

Este documento detalla el plan para integrar la arquitectura de OpenClaw Agent SaaS con el proyecto RICCO AI existente, creando un Sistema Operativo Semántico basado en Capital Cognitivo y Agencia Autónoma de Largo Horizonte.

---

## I. Análisis de Componentes Existentes

### Mapeo RICCO AI → OpenClaw

| Componente OpenClaw | Componente RICCO AI | Estado | Acción Requerida |
|---------------------|---------------------|--------|------------------|
| **Stack IOVBA** | | | |
| I - Infraestructura | Docker/K8s configs | ✅ Parcial | Crear OpenShell sandbox |
| O - Orquestación | `src/agents/`, `src/services/adk/` | ✅ Existe | Integrar LangGraph Lead Agent |
| V - Validación | `src/core/protocols.py` | ✅ Existe | Implementar Guardrail Middleware |
| B - Comportamiento | `src/services/a2ui/` | ✅ Parcial | Crear sistema Personas (Gentle-AI) |
| A - Acción | `src/mcp/` | ✅ Existe | Expandir Skills Registry |
| **Ciclo PPCC** | No implementado | ❌ Faltante | Crear desde cero |
| **Trasfondo de Obviedad** | `src/services/a2ui/context_models.py` | ✅ Parcial | Implementar SMART+R+T completo |
| **Memory VCS** | `src/services/context_engine.py` | ⚠️ Básico | Implementar Engram con SQLite/FTS5 |
| **Ralph Loop** | No implementado | ❌ Faltante | Crear desde cero |
| **Red Neuronal Obviedades** | No implementado | ❌ Faltante | Crear LOCM |
| **Skills System** | `src/ai_providers/skills/` | ✅ Parcial | Implementar auto-generación |
| **MCP Integration** | `src/mcp/` | ✅ Existe | Mantener y expandir |

---

## II. Arquitectura de Integración

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        OPENCLAW AGENT SAAS - RICCO AI                       │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                     CAPA DE PRESENTACIÓN                             │   │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌────────────┐ │   │
│  │  │   A2UI      │  │   Chat      │  │   Voice     │  │   API      │ │   │
│  │  │   Service   │  │   Interface │  │   Interface │  │   Routes   │ │   │
│  │  └─────────────┘  └─────────────┘  └─────────────┘  └────────────┘ │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                    │                                        │
│  ┌─────────────────────────────────▼───────────────────────────────────┐   │
│  │                     CICLO PPCC (Proper Prompt Chat Cycle)            │   │
│  │  ┌──────────┐  ┌───────────┐  ┌───────────┐  ┌──────────────────┐  │   │
│  │  │ Preparar │→ │ Alinear   │→ │ Ejecutar  │→ │ Declarar         │  │   │
│  │  │ Trasf.   │  │ (Revelar) │  │ (Sandbox) │  │ Resultado        │  │   │
│  │  └──────────┘  └───────────┘  └───────────┘  └──────────────────┘  │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                    │                                        │
│  ┌─────────────────────────────────▼───────────────────────────────────┐   │
│  │                     STACK IOVBA                                      │   │
│  │  ┌─────────────────────────────────────────────────────────────────┐│   │
│  │  │ A - Acción: MCP Registry │ Skills Registry │ Tool Definitions  ││   │
│  │  └─────────────────────────────────────────────────────────────────┘│   │
│  │  ┌─────────────────────────────────────────────────────────────────┐│   │
│  │  │ B - Comportamiento: Personas (Gentle-AI) │ Ethics │ Tone       ││   │
│  │  └─────────────────────────────────────────────────────────────────┘│   │
│  │  ┌─────────────────────────────────────────────────────────────────┐│   │
│  │  │ V - Validación: Guardrails │ Permissions │ Policy Engine       ││   │
│  │  └─────────────────────────────────────────────────────────────────┘│   │
│  │  ┌─────────────────────────────────────────────────────────────────┐│   │
│  │  │ O - Orquestación: LangGraph Lead Agent │ Sub-Agents │ State    ││   │
│  │  └─────────────────────────────────────────────────────────────────┘│   │
│  │  ┌─────────────────────────────────────────────────────────────────┐│   │
│  │  │ I - Infraestructura: OpenShell │ Docker Sandbox │ K8s Pods     ││   │
│  │  └─────────────────────────────────────────────────────────────────┘│   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                    │                                        │
│  ┌─────────────────────────────────▼───────────────────────────────────┐   │
│  │                     CAPITAL COGNITIVO (Memory VCS)                   │   │
│  │  ┌─────────────────────────────────────────────────────────────────┐│   │
│  │  │                    RALPH LOOP                                     ││   │
│  │  │  ┌────────┐  ┌────────┐  ┌────────┐  ┌────────┐  ┌────────┐   ││   │
│  │  │  │Reflect │→ │Analyze │→ │ Learn  │→ │Practice│→ │Harvest │   ││   │
│  │  │  └────────┘  └────────┘  └────────┘  └────────┘  └────────┘   ││   │
│  │  └─────────────────────────────────────────────────────────────────┘│   │
│  │  ┌─────────────────────────────────────────────────────────────────┐│   │
│  │  │  Engram SQLite/FTS5 │ Topic Keys │ Versioning │ RNO (LOCM)     ││   │
│  │  └─────────────────────────────────────────────────────────────────┘│   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                    │                                        │
│  ┌─────────────────────────────────▼───────────────────────────────────┐   │
│  │                     INTEGRACIONES EMPRESARIALES                      │   │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌────────────┐ │   │
│  │  │    RICCO    │  │   Nebula    │  │   Flowise   │  │    n8n     │ │   │
│  │  │   ERP/ERPNext│  │   Graph     │  │   LLM       │  │ Automation │ │   │
│  │  └─────────────┘  └─────────────┘  └─────────────┘  └────────────┘ │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## III. Componentes a Implementar

### 1. Trasfondo de Obviedad (SMART+R+T)

```python
# src/core/obviousness.py

from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field
from enum import Enum
from datetime import datetime

class ObviousnessDimension(str, Enum):
    """Dimensiones del Trasfondo de Obviedad"""
    SPECIFICITY = "S"  # Finalidad específica
    METRIC = "M"       # Criterios cuantitativos
    ACHIEVABILITY = "A" # Alcance y fronteras
    RELEVANCE = "R"    # Impacto organizacional
    TIME = "T"         # Restricciones temporales


class ObviousnessContext(BaseModel):
    """Trasfondo de Obviedad - Contrato Semántico"""
    
    # S - Finalidad (Specificity)
    objective: str = Field(..., description="Objetivo técnico específico")
    success_criteria: List[str] = Field(default_factory=list)
    
    # M - Métrica (Metric)
    metrics: Dict[str, float] = Field(default_factory=dict)
    target_recall: Optional[float] = Field(default=None, ge=0, le=1)
    target_precision: Optional[float] = Field(default=None, ge=0, le=1)
    
    # A - Alcance (Achievability)
    positive_boundaries: List[str] = Field(default_factory=list)
    negative_boundaries: List[str] = Field(default_factory=list)
    allowed_tools: List[str] = Field(default_factory=list)
    restricted_files: List[str] = Field(default_factory=list)
    
    # R - Relevancia (Relevance)
    organizational_impact: str = Field(default="medium")
    cognitive_capital_value: int = Field(default=1, ge=1, le=10)
    linked_knowledge_nodes: List[str] = Field(default_factory=list)
    
    # T - Tiempo (Time)
    max_latency_seconds: Optional[int] = None
    deadline: Optional[datetime] = None
    priority: str = Field(default="normal")
    
    # Metadata
    session_id: str
    user_id: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    def to_system_prompt(self) -> str:
        """Genera el SYSTEM_PROMPT para el agente líder"""
        return f"""
# TRASFONDO DE OBVIEDAD

## Objetivo (S)
{self.objective}

## Métricas de Éxito (M)
{chr(10).join(f'- {k}: {v}' for k, v in self.metrics.items())}

## Alcance (A)
**Permitido:** {', '.join(self.positive_boundaries) or 'Todo'}
**Prohibido:** {', '.join(self.negative_boundaries) or 'Nada'}

## Relevancia Organizacional (R)
Impacto: {self.organizational_impact}
Valor de Capital Cognitivo: {self.cognitive_capital_value}/10

## Restricciones Temporales (T)
Latencia máxima: {self.max_latency_seconds or 'Sin límite'}s
Prioridad: {self.priority}
"""
    
    def validate_alignment(self, agent_response: str) -> Dict[str, Any]:
        """Valida la alineación de la respuesta con el trasfondo"""
        # Implementar validación semántica
        pass
```

### 2. Ciclo PPCC (Proper Prompt Chat Cycle)

```python
# src/core/ppcc.py

from typing import Optional, Dict, Any, Callable
from enum import Enum
from pydantic import BaseModel
import asyncio

class PPCCPhase(str, Enum):
    """Fases del ciclo PPCC"""
    PREPARATION = "preparation"
    ALIGNMENT = "alignment"
    EXECUTION = "execution"
    DECLARATION = "declaration"


class PPCCState(BaseModel):
    """Estado del ciclo PPCC"""
    current_phase: PPCCPhase = PPCCPhase.PREPARATION
    obviousness_context: Optional[Dict[str, Any]] = None
    alignment_confirmed: bool = False
    execution_results: Optional[Dict[str, Any]] = None
    satisfaction_declared: Optional[bool] = None
    iteration_count: int = 0


class PPCCCycle:
    """
    Implementación del ciclo PPCC (Proper Prompt Chat Cycle)
    
    Flujo:
    1. Preparación: Definir pre-trasfondo de obviedad
    2. Alineación: Agente reformula y confirma entendimiento
    3. Ejecución: Agente opera en sandbox con razonamiento visible
    4. Declaración: Cierre formal con satisfacción/insatisfacción
    """
    
    def __init__(self, agent_executor: Callable):
        self.agent_executor = agent_executor
        self.state = PPCCState()
    
    async def prepare(self, user_request: Dict[str, Any]) -> Dict[str, Any]:
        """Fase 1: Preparación del Trasfondo de Obviedad"""
        self.state.current_phase = PPCCPhase.PREPARATION
        
        # Construir contexto SMART+R+T
        context = ObviousnessContext(
            objective=user_request.get("objective", ""),
            session_id=user_request.get("session_id"),
            user_id=user_request.get("user_id"),
            metrics=user_request.get("metrics", {}),
            positive_boundaries=user_request.get("allowed_actions", []),
            negative_boundaries=user_request.get("forbidden_actions", []),
            max_latency_seconds=user_request.get("timeout")
        )
        
        self.state.obviousness_context = context.model_dump()
        return {"phase": "preparation", "context": context.to_system_prompt()}
    
    async def align(self) -> Dict[str, Any]:
        """Fase 2: Alineación (Revelación)"""
        self.state.current_phase = PPCCPhase.ALIGNMENT
        
        # El agente debe reformular y confirmar
        context = ObviousnessContext(**self.state.obviousness_context)
        
        alignment_prompt = f"""
Antes de ejecutar, debes confirmar tu entendimiento:

{context.to_system_prompt()}

INSTRUCCIÓN: Reformula el objetivo en tus propias palabras y confirma que entiendes:
1. El objetivo específico
2. Las métricas de éxito
3. Los límites de alcance
4. Las restricciones temporales

NO PROCEDAS hasta confirmar entendimiento mutuo.
"""
        
        # Prohibir ejecución hasta alineación
        return {
            "phase": "alignment",
            "prompt": alignment_prompt,
            "execution_blocked": True
        }
    
    async def confirm_alignment(self, agent_understanding: str) -> bool:
        """Confirma la alineación del agente"""
        # Validar que el agente entendió correctamente
        self.state.alignment_confirmed = True
        self.state.current_phase = PPCCPhase.EXECUTION
        return True
    
    async def execute(self, task: str) -> Dict[str, Any]:
        """Fase 3: Ejecución con razonamiento visible"""
        if not self.state.alignment_confirmed:
            raise ValueError("Alineación requerida antes de ejecutar")
        
        self.state.current_phase = PPCCPhase.EXECUTION
        
        # Ejecutar en sandbox con razonamiento explícito
        result = await self.agent_executor(
            task=task,
            context=self.state.obviousness_context,
            visible_reasoning=True
        )
        
        self.state.execution_results = result
        return result
    
    async def declare_result(self, satisfaction: bool, feedback: str = "") -> Dict[str, Any]:
        """Fase 4: Declaración de Resultado"""
        self.state.current_phase = PPCCPhase.DECLARATION
        self.state.satisfaction_declared = satisfaction
        
        if not satisfaction:
            # Insatisfacción = información estructural para reentrenamiento
            return {
                "phase": "declaration",
                "satisfaction": False,
                "feedback": feedback,
                "action": "ralph_loop_harvest"  # Disparar Ralph Loop
            }
        
        return {
            "phase": "declaration",
            "satisfaction": True,
            "cognitive_capital_earned": self.state.obviousness_context.get(
                "cognitive_capital_value", 1
            )
        }
```

### 3. Memory VCS con Engram

```python
# src/memory/engram_vcs.py

import sqlite3
import json
from typing import Optional, Dict, Any, List
from datetime import datetime
from pathlib import Path
import hashlib

class MemoryVCS:
    """
    Sistema de Memoria con Control de Versiones (Memory VCS)
    Basado en Engram - SQLite con FTS5 para recuperación semántica
    """
    
    def __init__(self, db_path: str = "~/.openclaw/memory.db"):
        self.db_path = Path(db_path).expanduser()
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()
    
    def _init_db(self):
        """Inicializa la base de datos SQLite con FTS5"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Tabla principal de memorias
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS memories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                topic_key TEXT UNIQUE NOT NULL,
                content TEXT NOT NULL,
                metadata JSON,
                revision INTEGER DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                content_hash TEXT
            )
        ''')
        
        # Índice FTS5 para búsqueda semántica
        cursor.execute('''
            CREATE VIRTUAL TABLE IF NOT EXISTS memories_fts USING fts5(
                topic_key,
                content,
                metadata,
                content='memories',
                content_rowid='id'
            )
        ''')
        
        # Tabla de versiones (historial)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS memory_versions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                memory_id INTEGER NOT NULL,
                version INTEGER NOT NULL,
                content TEXT NOT NULL,
                metadata JSON,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (memory_id) REFERENCES memories(id)
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def upsert(
        self,
        topic_key: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Inserta o actualiza una memoria (upsert con versionado)
        
        - Si la topic_key no existe: crea nueva memoria
        - Si ya existe: incrementa revisión y versiona
        """
        content_hash = hashlib.sha256(content.encode()).hexdigest()[:16]
        metadata_json = json.dumps(metadata or {})
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Buscar existencia
        cursor.execute(
            "SELECT id, revision, content_hash FROM memories WHERE topic_key = ?",
            (topic_key,)
        )
        existing = cursor.fetchone()
        
        if existing:
            memory_id, revision, old_hash = existing
            
            if old_hash != content_hash:
                # Versionar el contenido anterior
                cursor.execute('''
                    INSERT INTO memory_versions (memory_id, version, content, metadata)
                    SELECT id, revision, content, metadata FROM memories WHERE id = ?
                ''', (memory_id,))
                
                # Actualizar con nuevo contenido
                cursor.execute('''
                    UPDATE memories SET
                        content = ?,
                        metadata = ?,
                        revision = revision + 1,
                        updated_at = CURRENT_TIMESTAMP,
                        content_hash = ?
                    WHERE id = ?
                ''', (content, metadata_json, content_hash, memory_id))
                
                revision += 1
        else:
            # Nueva memoria
            cursor.execute('''
                INSERT INTO memories (topic_key, content, metadata, content_hash)
                VALUES (?, ?, ?, ?)
            ''', (topic_key, content, metadata_json, content_hash))
            
            memory_id = cursor.lastrowid
            revision = 1
        
        conn.commit()
        conn.close()
        
        return {
            "memory_id": memory_id,
            "topic_key": topic_key,
            "revision": revision,
            "operation": "updated" if existing else "created"
        }
    
    def search(
        self,
        query: str,
        limit: int = 10,
        progressive_disclosure: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Búsqueda semántica con divulgación progresiva
        
        Nivel 1: IDs compactos
        Nivel 2: Línea temporal
        Nivel 3: Contenido completo
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        if progressive_disclosure:
            # Nivel 1: Solo IDs y relevancia
            cursor.execute('''
                SELECT topic_key, revision, rank
                FROM memories_fts
                WHERE memories_fts MATCH ?
                ORDER BY rank
                LIMIT ?
            ''', (query, limit))
            
            results = [
                {
                    "topic_key": row[0],
                    "revision": row[1],
                    "relevance": -row[2]  # rank es negativo
                }
                for row in cursor.fetchall()
            ]
        else:
            # Nivel 3: Contenido completo
            cursor.execute('''
                SELECT m.topic_key, m.content, m.metadata, m.revision
                FROM memories m
                JOIN memories_fts fts ON m.id = fts.rowid
                WHERE memories_fts MATCH ?
                ORDER BY rank
                LIMIT ?
            ''', (query, limit))
            
            results = [
                {
                    "topic_key": row[0],
                    "content": row[1],
                    "metadata": json.loads(row[2]),
                    "revision": row[3]
                }
                for row in cursor.fetchall()
            ]
        
        conn.close()
        return results
    
    def get_timeline(self, topic_key: str) -> List[Dict[str, Any]]:
        """Obtiene la línea temporal de una memoria"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT version, content, created_at
            FROM memory_versions
            WHERE memory_id = (SELECT id FROM memories WHERE topic_key = ?)
            ORDER BY version DESC
        ''', (topic_key,))
        
        timeline = [
            {
                "version": row[0],
                "content": row[1],
                "created_at": row[2]
            }
            for row in cursor.fetchall()
        ]
        
        conn.close()
        return timeline
```

### 4. Ralph Loop (Ciclo de Aprendizaje)

```python
# src/core/ralph_loop.py

from typing import Dict, Any, List, Optional
from enum import Enum
from pydantic import BaseModel
from datetime import datetime
import asyncio

class RalphPhase(str, Enum):
    """Fases del ciclo Ralph Loop"""
    REFLECT = "reflect"
    ANALYZE = "analyze"
    LEARN = "learn"
    PRACTICE = "practice"
    HARVEST = "harvest"


class RalphLoopState(BaseModel):
    """Estado del ciclo Ralph"""
    current_phase: RalphPhase = RalphPhase.REFLECT
    conversation_trajectory: List[Dict[str, Any]] = []
    identified_patterns: List[Dict[str, Any]] = []
    knowledge_gaps: List[str] = []
    extracted_facts: List[Dict[str, Any]] = []
    validated_skills: List[str] = []
    created_skills: List[str] = []


class RalphLoop:
    """
    Ciclo Ralph Loop: Reflect → Analyze → Learn → Practice → Harvest
    
    Transforma interacciones en Capital Cognitivo activo.
    """
    
    def __init__(self, memory_vcs: 'MemoryVCS', skill_registry: 'SkillRegistry'):
        self.memory_vcs = memory_vcs
        self.skill_registry = skill_registry
        self.state = RalphLoopState()
    
    async def reflect(
        self,
        conversation_history: List[Dict[str, Any]],
        execution_results: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Fase 1: Reflexión
        Analiza la trayectoria conversacional y los resultados
        """
        self.state.current_phase = RalphPhase.REFLECT
        
        # Identificar patrones de éxito y fallo
        patterns = self._identify_patterns(conversation_history)
        self.state.identified_patterns = patterns
        self.state.conversation_trajectory = conversation_history
        
        return {
            "phase": "reflect",
            "patterns_found": len(patterns),
            "success_rate": self._calculate_success_rate(execution_results)
        }
    
    async def analyze(
        self,
        obviousness_context: Dict[str, Any],
        execution_result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Fase 2: Análisis
        Compara resultado con Trasfondo de Obviedad
        """
        self.state.current_phase = RalphPhase.ANALYZE
        
        # Detectar brechas en conocimiento organizacional
        gaps = self._detect_knowledge_gaps(
            expected=obviousness_context,
            actual=execution_result
        )
        self.state.knowledge_gaps = gaps
        
        return {
            "phase": "analyze",
            "gaps_detected": gaps,
            "alignment_score": self._calculate_alignment(obviousness_context, execution_result)
        }
    
    async def learn(
        self,
        new_facts: List[Dict[str, Any]],
        user_preferences: Dict[str, Any],
        corrections: List[str]
    ) -> Dict[str, Any]:
        """
        Fase 3: Aprendizaje
        Extrae nuevos hechos y actualiza memoria versionada
        """
        self.state.current_phase = RalphPhase.LEARN
        
        extracted = []
        for fact in new_facts:
            # Upsert a Memory VCS
            result = self.memory_vcs.upsert(
                topic_key=fact.get("topic", f"fact_{datetime.utcnow().timestamp()}"),
                content=fact.get("content", ""),
                metadata={
                    "source": "ralph_loop",
                    "confidence": fact.get("confidence", 0.8),
                    "user_preferences": user_preferences
                }
            )
            extracted.append(result)
        
        self.state.extracted_facts = extracted
        
        return {
            "phase": "learn",
            "facts_learned": len(extracted),
            "memory_updates": extracted
        }
    
    async def practice(
        self,
        sandbox_env: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Fase 4: Práctica
        Valida nuevo conocimiento en sandboxes aislados
        """
        self.state.current_phase = RalphPhase.PRACTICE
        
        validated = []
        for fact in self.state.extracted_facts:
            # Ejecutar validación en sandbox
            validation_result = await self._validate_in_sandbox(fact, sandbox_env)
            if validation_result["passed"]:
                validated.append(fact["topic_key"])
        
        self.state.validated_skills = validated
        
        return {
            "phase": "practice",
            "validated_count": len(validated),
            "validation_results": validated
        }
    
    async def harvest(self) -> Dict[str, Any]:
        """
        Fase 5: Cosecha
        Destila conocimiento en habilidades reutilizables
        """
        self.state.current_phase = RalphPhase.HARVEST
        
        created_skills = []
        for skill_topic in self.state.validated_skills:
            # Crear archivo SKILL.md
            skill_content = self._generate_skill_content(skill_topic)
            skill_file = self.skill_registry.create_skill(
                name=f"auto_{skill_topic}",
                content=skill_content,
                metadata={
                    "auto_generated": True,
                    "created_from": "ralph_loop",
                    "created_at": datetime.utcnow().isoformat()
                }
            )
            created_skills.append(skill_file)
        
        self.state.created_skills = created_skills
        
        return {
            "phase": "harvest",
            "skills_created": len(created_skills),
            "skill_files": created_skills
        }
    
    async def run_full_cycle(
        self,
        conversation_history: List[Dict[str, Any]],
        execution_results: Dict[str, Any],
        obviousness_context: Dict[str, Any],
        sandbox_env: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Ejecuta el ciclo completo Ralph Loop"""
        
        results = {}
        
        # Fase 1: Reflect
        results["reflect"] = await self.reflect(conversation_history, execution_results)
        
        # Fase 2: Analyze
        results["analyze"] = await self.analyze(obviousness_context, execution_results)
        
        # Fase 3: Learn
        new_facts = self._extract_facts_from_results(execution_results)
        results["learn"] = await self.learn(new_facts, {}, [])
        
        # Fase 4: Practice
        results["practice"] = await self.practice(sandbox_env)
        
        # Fase 5: Harvest
        results["harvest"] = await self.harvest()
        
        return {
            "cycle_completed": True,
            "phases": results,
            "cognitive_capital_delta": len(self.state.created_skills) * 10
        }
    
    def _identify_patterns(self, history: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Identifica patrones de éxito/fallo en la conversación"""
        patterns = []
        # Implementar lógica de detección de patrones
        return patterns
    
    def _calculate_success_rate(self, results: Dict[str, Any]) -> float:
        """Calcula tasa de éxito de la ejecución"""
        if not results:
            return 0.0
        return results.get("success_rate", 0.0)
    
    def _detect_knowledge_gaps(
        self,
        expected: Dict[str, Any],
        actual: Dict[str, Any]
    ) -> List[str]:
        """Detecta brechas de conocimiento"""
        gaps = []
        # Implementar detección de brechas
        return gaps
    
    def _calculate_alignment(
        self,
        expected: Dict[str, Any],
        actual: Dict[str, Any]
    ) -> float:
        """Calcula score de alineación con objetivo"""
        return 0.8  # Placeholder
    
    async def _validate_in_sandbox(
        self,
        fact: Dict[str, Any],
        sandbox: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Valida conocimiento en sandbox"""
        return {"passed": True}
    
    def _extract_facts_from_results(self, results: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extrae hechos estructurados de resultados"""
        return []
    
    def _generate_skill_content(self, topic: str) -> str:
        """Genera contenido de SKILL.md"""
        return f"""---
name: auto_{topic}
auto_generated: true
created_from: ralph_loop
---

# Skill: {topic}

Auto-generated from Ralph Loop learning cycle.

## Usage
[TBD - Auto-populated from successful execution patterns]
"""
```

---

## IV. Plan de Implementación

### Fase 1: Fundamentos (Semana 1-2)

| Tarea | Prioridad | Estimación | Dependencias |
|-------|-----------|------------|--------------|
| Implementar `ObviousnessContext` | Alta | 4h | Ninguna |
| Implementar `PPCCCycle` | Alta | 8h | ObviousnessContext |
| Crear tests unitarios | Alta | 4h | PPCC |
| Integrar con agentes existentes | Alta | 4h | Tests |

### Fase 2: Memoria Persistente (Semana 3-4)

| Tarea | Prioridad | Estimación | Dependencias |
|-------|-----------|------------|--------------|
| Implementar `MemoryVCS` con SQLite/FTS5 | Alta | 8h | Ninguna |
| Crear migración de datos existentes | Media | 4h | MemoryVCS |
| Implementar divulgación progresiva | Alta | 4h | MemoryVCS |
| Integrar con servicios existentes | Alta | 4h | Todo lo anterior |

### Fase 3: Aprendizaje Continuo (Semana 5-6)

| Tarea | Prioridad | Estimación | Dependencias |
|-------|-----------|------------|--------------|
| Implementar `RalphLoop` | Alta | 8h | MemoryVCS |
| Crear `SkillRegistry` | Alta | 6h | RalphLoop |
| Implementar auto-generación de Skills | Media | 6h | SkillRegistry |
| Integrar con pipeline de ejecución | Alta | 4h | Todo lo anterior |

### Fase 4: Red Neuronal de Obviedades (Semana 7-8)

| Tarea | Prioridad | Estimación | Dependencias |
|-------|-----------|------------|--------------|
| Diseñar modelo LOCM | Media | 8h | Todo lo anterior |
| Implementar RNO por dominio | Media | 16h | LOCM |
| Crear stacks de agentes por dominio | Media | 12h | RNO |
| Documentación y tests | Alta | 8h | Todo |

---

## V. Métricas de Éxito

| Métrica | Objetivo | Medición |
|---------|----------|----------|
| Tasa de alineación PPCC | > 90% | Validaciones exitosas / Total |
| Reducción de "re-enseñanza" | > 70% | Memorias reutilizadas / Total |
| Capital Cognitivo acumulado | +500 puntos/mes | Skills creados × 10 |
| Latencia de recuperación | < 100ms | Tiempo medio de búsqueda FTS5 |

---

## VI. Referencias

1. OpenClaw - https://github.com/openclaw/openclaw
2. deer-flow (ByteDance) - https://github.com/bytedance/deer-flow
3. gentle-ai - https://github.com/Gentleman-Programming/gentle-ai
4. Engram Memory - https://github.com/Gentleman-Programming/engram
5. OpenClaw-RL - https://github.com/Gen-Verse/OpenClaw-RL

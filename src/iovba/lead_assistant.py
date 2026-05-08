"""
Lead Assistant - Agente líder que coordina todos los demás
Con capacidad de crear nuevos agentes/stacks con HITL (Human In The Loop)
"""

from typing import Dict, List, Optional, Any, Literal, Callable, Awaitable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import asyncio
import uuid

from .groups import (
    IOVBAGroup,
    IOVBAGroupManager,
    IOVBADomain,
    IOVBARole,
    CapitalSyncMode,
    AgentProfile,
    CognitiveCapital,
    Engram,
)


class ApprovalStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    TIMEOUT = "timeout"


class ProposalType(str, Enum):
    CREATE_AGENT = "create_agent"
    CREATE_GROUP = "create_group"
    MODIFY_AGENT = "modify_agent"
    DELETE_AGENT = "delete_agent"
    SKILL_ADDITION = "skill_addition"
    MCP_ADDITION = "mcp_addition"
    DOMAIN_CHANGE = "domain_change"


@dataclass
class HITLProposal:
    """Propuesta que requiere aprobación humana"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    proposal_type: ProposalType = ProposalType.CREATE_AGENT
    title: str = ""
    description: str = ""
    proposed_by: str = ""  # Agent ID
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    status: ApprovalStatus = ApprovalStatus.PENDING
    details: Dict[str, Any] = field(default_factory=dict)
    approved_by: Optional[str] = None
    approved_at: Optional[str] = None
    rejection_reason: Optional[str] = None
    timeout_seconds: int = 3600  # 1 hora default
    
    def approve(self, approver: str) -> None:
        """Aprueba la propuesta"""
        self.status = ApprovalStatus.APPROVED
        self.approved_by = approver
        self.approved_at = datetime.utcnow().isoformat()
    
    def reject(self, reason: str) -> None:
        """Rechaza la propuesta"""
        self.status = ApprovalStatus.REJECTED
        self.rejection_reason = reason
    
    def check_timeout(self) -> bool:
        """Verifica si la propuesta ha expirado"""
        if self.status != ApprovalStatus.PENDING:
            return False
        
        created = datetime.fromisoformat(self.created_at)
        elapsed = (datetime.utcnow() - created).total_seconds()
        
        if elapsed > self.timeout_seconds:
            self.status = ApprovalStatus.TIMEOUT
            return True
        return False


@dataclass
class LeadAssistantConfig:
    """Configuración del Lead Assistant"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = "Lead Assistant"
    description: str = "Agente líder que coordina todo el sistema"
    
    # Permisos
    can_create_agents: bool = True
    can_create_groups: bool = True
    can_modify_agents: bool = True
    requires_hitl_for_creation: bool = True
    requires_hitl_for_modification: bool = True
    
    # HITL Settings
    hitl_timeout_seconds: int = 3600
    auto_approve_threshold: float = 0.95  # Confianza mínima para auto-aprobar
    max_pending_proposals: int = 100
    
    # Auto-mejora
    auto_improve_enabled: bool = True
    improvement_interval_seconds: int = 300  # 5 minutos


class LeadAssistant:
    """
    Agente líder principal que coordina todos los demás
    
    Capacidades:
    - Coordina todos los grupos IOVBA
    - Detecta necesidad de nuevos agentes/grupos
    - Crea propuestas con HITL
    - Gestiona capital cognitivo global
    """
    
    def __init__(
        self,
        config: Optional[LeadAssistantConfig] = None,
        group_manager: Optional[IOVBAGroupManager] = None,
        hitl_callback: Optional[Callable[[HITLProposal], Awaitable[bool]]] = None,
    ):
        self.config = config or LeadAssistantConfig()
        self.group_manager = group_manager or IOVBAGroupManager()
        self.hitl_callback = hitl_callback
        
        # Estado interno
        self.proposals: Dict[str, HITLProposal] = {}
        self.pending_approvals: List[str] = []
        self.approval_history: List[Dict[str, Any]] = []
        
        # Capital cognitivo global
        self.global_capital = CognitiveCapital(agent_id=self.config.id)
        
        # Métricas
        self.total_coordinations = 0
        self.successful_creations = 0
        self.failed_creations = 0
    
    async def coordinate_task(
        self,
        task: str,
        domain: Optional[IOVBADomain] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Coordina una tarea distribuyéndola entre los agentes apropiados
        """
        self.total_coordinations += 1
        result = {
            "task": task,
            "domain": domain,
            "assigned_agents": [],
            "status": "processing",
            "timestamp": datetime.utcnow().isoformat(),
        }
        
        # Encontrar grupo apropiado
        target_group = None
        for group in self.group_manager.list_groups():
            if domain and group.domain == domain:
                target_group = group
                break
        
        if not target_group:
            # Detectar necesidad de nuevo grupo
            proposal = await self.propose_create_group(
                domain=domain or "custom",
                reason=f"No existe grupo para dominio: {domain}",
                task_context=task,
            )
            result["proposal_created"] = proposal.id
            result["status"] = "pending_group_creation"
            return result
        
        # Asignar tarea a roles apropiados
        agents = target_group.get_all_agents()
        
        # Workflow de asignación
        workflow = self._plan_workflow(task, agents)
        result["workflow"] = workflow
        result["assigned_agents"] = list(workflow.keys())
        
        return result
    
    def _plan_workflow(
        self,
        task: str,
        agents: Dict[IOVBARole, AgentProfile],
    ) -> Dict[str, List[str]]:
        """Planifica el workflow de la tarea"""
        workflow = {
            "investigador": [],
            "observador": [],
            "validador": [],
            "builder": [],
            "asistente": [],
        }
        
        # Análisis simple de la tarea para asignar roles
        task_lower = task.lower()
        
        if any(kw in task_lower for kw in ["investigar", "buscar", "analizar", "investigate", "research", "search"]):
            workflow["investigador"].append("lead_investigation")
            workflow["asistente"].append("coordinate_research")
        
        if any(kw in task_lower for kw in ["observar", "monitorear", "detectar", "observe", "monitor", "detect"]):
            workflow["observador"].append("monitor_task")
        
        if any(kw in task_lower for kw in ["validar", "verificar", "probar", "validate", "verify", "test"]):
            workflow["validador"].append("validate_task")
        
        if any(kw in task_lower for kw in ["crear", "construir", "implementar", "create", "build", "implement"]):
            workflow["builder"].append("build_task")
            workflow["validador"].append("review_build")
        
        # Default: asistente coordina
        if not any(workflow.values()):
            workflow["asistente"].append("coordinate_general")
            workflow["investigador"].append("analyze_task")
        
        return workflow
    
    async def detect_need_for_new_agent(
        self,
        context: Dict[str, Any],
    ) -> Optional[HITLProposal]:
        """
        Detecta si se necesita un nuevo agente basado en el contexto
        """
        # Análisis de patrones
        patterns = self._analyze_patterns(context)
        
        if patterns.get("needs_new_domain"):
            return await self.propose_create_group(
                domain=patterns.get("suggested_domain", "custom"),
                reason=patterns.get("reason", "Nueva área de trabajo detectada"),
                task_context=context,
            )
        
        if patterns.get("needs_new_skill"):
            return await self.propose_add_skill(
                agent_id=patterns.get("target_agent", ""),
                skill=patterns.get("suggested_skill", ""),
                reason=patterns.get("reason", ""),
            )
        
        return None
    
    def _analyze_patterns(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Analiza patrones para detectar necesidades"""
        patterns = {
            "needs_new_domain": False,
            "needs_new_skill": False,
            "suggested_domain": None,
            "suggested_skill": None,
            "reason": "",
        }
        
        # Análisis de tareas recientes
        recent_tasks = context.get("recent_tasks", [])
        domain_counts: Dict[str, int] = {}
        
        for task in recent_tasks:
            domain = task.get("domain", "unknown")
            domain_counts[domain] = domain_counts.get(domain, 0) + 1
        
        # Si hay muchas tareas de un dominio sin grupo
        existing_domains = {g.domain for g in self.group_manager.list_groups()}
        
        for domain, count in domain_counts.items():
            if domain not in existing_domains and count >= 3:
                patterns["needs_new_domain"] = True
                patterns["suggested_domain"] = domain
                patterns["reason"] = f"Detectadas {count} tareas en dominio '{domain}' sin grupo asignado"
                break
        
        return patterns
    
    async def propose_create_group(
        self,
        domain: IOVBADomain,
        reason: str,
        task_context: Optional[str] = None,
        auto_approve: bool = False,
    ) -> HITLProposal:
        """Propone la creación de un nuevo grupo IOVBA"""
        proposal = HITLProposal(
            proposal_type=ProposalType.CREATE_GROUP,
            title=f"Crear grupo IOVBA para {domain}",
            description=f"Se detectó la necesidad de crear un nuevo grupo IOVBA.\n\nRazón: {reason}",
            proposed_by=self.config.id,
            details={
                "domain": domain,
                "reason": reason,
                "task_context": task_context,
                "config": {
                    "name": f"{domain.upper()} Team",
                    "domain": domain,
                    "sync_mode": "hybrid",
                },
            },
            timeout_seconds=self.config.hitl_timeout_seconds,
        )
        
        self.proposals[proposal.id] = proposal
        self.pending_approvals.append(proposal.id)
        
        if self.config.requires_hitl_for_creation and not auto_approve:
            # Solicitar aprobación humana
            if self.hitl_callback:
                approved = await self.hitl_callback(proposal)
                if approved:
                    proposal.approve("hitl_callback")
                    await self._execute_create_group(proposal)
        else:
            # Auto-aprobar si está configurado
            proposal.approve("auto_approved")
            await self._execute_create_group(proposal)
        
        return proposal
    
    async def propose_create_agent(
        self,
        group_id: str,
        role: IOVBARole,
        skills: List[str],
        reason: str,
    ) -> HITLProposal:
        """Propone la creación de un nuevo agente"""
        proposal = HITLProposal(
            proposal_type=ProposalType.CREATE_AGENT,
            title=f"Crear agente {role} en grupo {group_id}",
            description=f"Razón: {reason}",
            proposed_by=self.config.id,
            details={
                "group_id": group_id,
                "role": role,
                "skills": skills,
                "reason": reason,
            },
        )
        
        self.proposals[proposal.id] = proposal
        
        if self.config.requires_hitl_for_creation:
            self.pending_approvals.append(proposal.id)
        else:
            proposal.approve("auto_approved")
            await self._execute_create_agent(proposal)
        
        return proposal
    
    async def propose_add_skill(
        self,
        agent_id: str,
        skill: str,
        reason: str,
    ) -> HITLProposal:
        """Propone añadir una skill a un agente"""
        proposal = HITLProposal(
            proposal_type=ProposalType.SKILL_ADDITION,
            title=f"Añadir skill '{skill}' al agente",
            description=f"Razón: {reason}",
            proposed_by=self.config.id,
            details={
                "agent_id": agent_id,
                "skill": skill,
                "reason": reason,
            },
        )
        
        self.proposals[proposal.id] = proposal
        
        if self.config.requires_hitl_for_modification:
            self.pending_approvals.append(proposal.id)
        else:
            proposal.approve("auto_approved")
            await self._execute_add_skill(proposal)
        
        return proposal
    
    async def approve_proposal(
        self,
        proposal_id: str,
        approver: str,
    ) -> bool:
        """Aprueba una propuesta pendiente"""
        proposal = self.proposals.get(proposal_id)
        if not proposal or proposal.status != ApprovalStatus.PENDING:
            return False
        
        proposal.approve(approver)
        
        # Ejecutar la acción
        await self._execute_proposal(proposal)
        
        # Registrar en historial
        self.approval_history.append({
            "proposal_id": proposal_id,
            "action": "approved",
            "approver": approver,
            "timestamp": datetime.utcnow().isoformat(),
        })
        
        if proposal_id in self.pending_approvals:
            self.pending_approvals.remove(proposal_id)
        
        return True
    
    async def reject_proposal(
        self,
        proposal_id: str,
        reason: str,
    ) -> bool:
        """Rechaza una propuesta pendiente"""
        proposal = self.proposals.get(proposal_id)
        if not proposal or proposal.status != ApprovalStatus.PENDING:
            return False
        
        proposal.reject(reason)
        
        self.approval_history.append({
            "proposal_id": proposal_id,
            "action": "rejected",
            "reason": reason,
            "timestamp": datetime.utcnow().isoformat(),
        })
        
        if proposal_id in self.pending_approvals:
            self.pending_approvals.remove(proposal_id)
        
        self.failed_creations += 1
        
        return True
    
    async def _execute_proposal(self, proposal: HITLProposal) -> None:
        """Ejecuta una propuesta aprobada"""
        if proposal.proposal_type == ProposalType.CREATE_GROUP:
            await self._execute_create_group(proposal)
        elif proposal.proposal_type == ProposalType.CREATE_AGENT:
            await self._execute_create_agent(proposal)
        elif proposal.proposal_type == ProposalType.SKILL_ADDITION:
            await self._execute_add_skill(proposal)
    
    async def _execute_create_group(self, proposal: HITLProposal) -> None:
        """Ejecuta la creación de un grupo"""
        details = proposal.details
        group = self.group_manager.create_group(
            name=details["config"]["name"],
            domain=details["domain"],
            description=proposal.description,
            sync_mode=CapitalSyncMode.HYBRID,
        )
        self.successful_creations += 1
    
    async def _execute_create_agent(self, proposal: HITLProposal) -> None:
        """Ejecuta la creación de un agente"""
        # Implementar creación de agente específico
        self.successful_creations += 1
    
    async def _execute_add_skill(self, proposal: HITLProposal) -> None:
        """Ejecuta la adición de skill"""
        # Implementar adición de skill
        pass
    
    def get_pending_proposals(self) -> List[HITLProposal]:
        """Obtiene todas las propuestas pendientes"""
        return [
            self.proposals[pid]
            for pid in self.pending_approvals
            if pid in self.proposals
        ]
    
    async def sync_global_capital(self) -> Dict[str, Any]:
        """Sincroniza el capital cognitivo global"""
        result = {
            "timestamp": datetime.utcnow().isoformat(),
            "groups_synced": 0,
            "total_engrams": 0,
        }
        
        for group in self.group_manager.list_groups():
            await group.sync_capital()
            result["groups_synced"] += 1
            
            # Agregar al capital global
            for agent in group.get_all_agents().values():
                if agent and agent.cognitive_capital:
                    self.global_capital.engrams.extend(agent.cognitive_capital.engrams)
        
        self.global_capital.total_engrams = len(self.global_capital.engrams)
        result["total_engrams"] = self.global_capital.total_engrams
        
        return result
    
    def get_status(self) -> Dict[str, Any]:
        """Obtiene el estado del Lead Assistant"""
        return {
            "id": self.config.id,
            "name": self.config.name,
            "total_groups": len(self.group_manager.groups),
            "total_proposals": len(self.proposals),
            "pending_approvals": len(self.pending_approvals),
            "total_coordinations": self.total_coordinations,
            "successful_creations": self.successful_creations,
            "failed_creations": self.failed_creations,
            "global_capital_value": self.global_capital.capital_value,
        }

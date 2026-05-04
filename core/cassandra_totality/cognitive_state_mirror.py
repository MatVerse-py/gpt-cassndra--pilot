#!/usr/bin/env python3
"""
CognitiveStateMirror - Espelho de Estado Cognitivo

Traduz estado técnico da máquina em representação cognitiva legível para humanos.

Três espelhos:
1. Machine Mirror - como o sistema vê a si mesmo
2. Human Mirror - como o humano entende o sistema
3. Governance Mirror - o que pode ou não acontecer
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Dict, List, Optional


@dataclass(frozen=True)
class StateView:
    current_phase: str
    progress: float
    risks_detected: List[str]
    decisions_pending: List[Dict[str, Any]]
    evidence_available: bool
    reversible: bool
    next_best_action: str
    human_summary: str


@dataclass(frozen=True)
class ActionPreview:
    action_name: str
    impact_description: str
    risk_score: float
    required_capabilities: List[str]
    will_mutate: bool
    rollback_plan: List[str]
    estimated_duration: Optional[str] = None


@dataclass
class CognitiveStateMirror:
    """Espelho cognitivo triplo: máquina, humano e governança."""

    def __init__(self) -> None:
        self.machine_state: Dict[str, Any] = {}
        self.human_state: Dict[str, Any] = {}
        self.governance_state: Dict[str, Any] = {}

    def update_machine(self, state: Dict[str, Any]) -> None:
        self.machine_state = state

    def update_governance(self, state: Dict[str, Any]) -> None:
        self.governance_state = state

    def generate_human_view(self) -> StateView:
        phase = self.machine_state.get("phase", "idle")
        total_steps = max(1, int(self.machine_state.get("total_steps", 1)))
        current_step = max(0, int(self.machine_state.get("current_step", 0)))
        progress = max(0.0, min(1.0, current_step / total_steps))
        risks = list(self.machine_state.get("risks", []))
        pending = list(self.governance_state.get("pending_decisions", []))
        has_evidence = bool(self.machine_state.get("evidence", []))
        reversible = bool(self.machine_state.get("reversible", False))
        next_action = self._recommend_next_action()
        summary = self._generate_human_summary(phase, progress, risks, pending)
        return StateView(
            current_phase=phase,
            progress=progress,
            risks_detected=risks,
            decisions_pending=pending,
            evidence_available=has_evidence,
            reversible=reversible,
            next_best_action=next_action,
            human_summary=summary,
        )

    def preview_action(self, action: Dict[str, Any], capabilities: List[str]) -> ActionPreview:
        action_name = str(action.get("name", "unknown_action"))
        risk = float(action.get("risk", 0.5))
        will_mutate = bool(action.get("mutates_state", False))
        impact = self._describe_impact(action, will_mutate)
        rollback = self._generate_rollback_plan(action)
        return ActionPreview(
            action_name=action_name,
            impact_description=impact,
            risk_score=risk,
            required_capabilities=capabilities,
            will_mutate=will_mutate,
            rollback_plan=rollback,
            estimated_duration=action.get("estimated_duration"),
        )

    def _recommend_next_action(self) -> str:
        phase = self.machine_state.get("phase", "idle")
        if phase == "idle":
            return "definir intenção ou objetivo"
        if phase == "planning":
            return "revisar plano e aprovar ou ajustar"
        if phase == "ready_to_execute":
            decision = self.governance_state.get("decision", "BLOCK")
            if decision == "PASS":
                return "executar com monitoramento"
            if decision == "CONDITIONAL":
                return "rodar simulação ou dry-run primeiro"
            return "reduzir risco ou adicionar evidência"
        if phase == "executing":
            return "aguardar conclusão e verificar auditpack"
        if phase == "completed":
            return "revisar resultado e promover padrões úteis"
        return "verificar estado e logs"

    def _generate_human_summary(self, phase: str, progress: float, risks: List[str], pending: List[Dict[str, Any]]) -> str:
        if phase == "idle":
            return "Sistema aguardando intenção ou objetivo."
        if phase == "planning":
            return f"Planejamento em andamento ({int(progress * 100)}%). Aguardando validação."
        if phase == "ready_to_execute":
            if risks:
                return f"Pronto para executar, mas {len(risks)} risco(s) detectado(s). Recomenda-se revisão."
            return "Pronto para executar com baixo risco."
        if phase == "executing":
            return f"Execução em andamento ({int(progress * 100)}%)."
        if phase == "completed":
            return "Execução concluída. Auditpack disponível."
        if phase == "blocked":
            return f"Execução bloqueada por governança. {len(pending)} decisão(ões) pendente(s)."
        return f"Fase: {phase}, progresso: {int(progress * 100)}%"

    def _describe_impact(self, action: Dict[str, Any], will_mutate: bool) -> str:
        action_type = str(action.get("type", "unknown"))
        if not will_mutate:
            return f"Ação de leitura/análise ({action_type}). Não altera estado do sistema."
        targets = [str(x) for x in action.get("targets", [])]
        if action_type == "create":
            return f"Criará: {', '.join(targets)}. Reversível via rollback."
        if action_type == "modify":
            return f"Modificará: {', '.join(targets)}. Backup automático será criado."
        if action_type == "delete":
            return f"Removerá: {', '.join(targets)}. Operação de alto risco."
        if action_type == "execute":
            return "Executará comando externo. Saída será registrada em auditpack."
        return f"Ação {action_type} em {len(targets)} alvo(s)."

    def _generate_rollback_plan(self, action: Dict[str, Any]) -> List[str]:
        action_type = str(action.get("type", "unknown"))
        if action_type == "create":
            return ["remover arquivos criados", "restaurar estado anterior"]
        if action_type == "modify":
            return ["restaurar do snapshot", "validar integridade"]
        if action_type == "delete":
            return ["impossível reverter completamente", "restaurar do backup se disponível"]
        if action_type == "execute":
            return ["executar comando de cleanup", "restaurar configuração anterior"]
        return ["rollback automático não disponível", "intervenção manual necessária"]

    def to_dict(self) -> Dict[str, Any]:
        view = self.generate_human_view()
        return {
            "schema": "msm.cognitive_state_mirror.v1",
            "machine_state": self.machine_state,
            "human_view": asdict(view),
            "governance_state": self.governance_state,
        }

#!/usr/bin/env python3
"""
IntentCompiler - Compilador de Intenção Humana

Transforma linguagem natural humana em objetivos operacionais estruturados.

Fluxo:
    texto livre → análise → objetivo → restrições → autonomia
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass, field
from typing import Any, Dict, List


class AutonomyLevel:
    """Níveis de autonomia da execução."""

    OBSERVE = "observe"
    SIMULATE = "simulate"
    ASSIST = "assist"
    DELEGATE = "delegate"
    EVOLVE = "evolve"


@dataclass(frozen=True)
class HumanIntent:
    """Intenção humana estruturada."""

    raw_text: str
    objective: str
    constraints: List[str]
    desired_outcome: str
    autonomy_level: str
    priority: float = 0.5
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_hash(self) -> str:
        payload = {
            "objective": self.objective,
            "constraints": sorted(self.constraints),
            "autonomy_level": self.autonomy_level,
            "desired_outcome": self.desired_outcome,
        }
        raw = json.dumps(payload, ensure_ascii=False, sort_keys=True)
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()


class IntentCompiler:
    """Compilador de intenção humana para contrato operacional."""

    CONSTRAINT_PATTERNS = {
        "risk_control": [r"\bsem risco\b", r"\bsegur[oa]\b", r"\bcontrola[rd]o\b", r"\bbaixo risco\b"],
        "auditability": [r"\baudit", r"\bverific", r"\brastrea", r"\bevid[êe]ncia\b", r"\bprova\b"],
        "friction_reduction": [r"\bfric[çc][ãa]o\b", r"\bfluxo", r"\br[aá]pid", r"\bf[aá]cil", r"\bsuave\b"],
        "emergence_support": [r"\bemerg", r"\brecombina", r"\bevolu", r"\badapta"],
        "human_alignment": [r"\bhumano\b", r"\balinhado\b", r"\bleg[ií]vel\b", r"\bcompreens[ií]vel\b"],
        "governance": [r"\bgovern", r"\bpol[ií]tica\b", r"\bconstitui", r"\binvariante\b"],
        "no_secrets": [r"\bsem segredo", r"\bn[ãa]o expo[rs]", r"\bmascarar", r"\bprivacidade\b"],
        "fail_closed": [r"\bfail[- ]closed\b", r"\bbloqueio\b", r"\bconservador\b", r"\bn[ãa]o executar sem\b"],
    }

    def compile(self, raw_text: str) -> HumanIntent:
        text_norm = raw_text.lower().strip()
        constraints = self._extract_constraints(text_norm)
        autonomy = self._detect_autonomy(text_norm)
        objective = self._extract_objective(text_norm)
        outcome = self._extract_outcome(text_norm)
        priority = self._calculate_priority(text_norm, constraints)

        return HumanIntent(
            raw_text=raw_text,
            objective=objective,
            constraints=constraints,
            desired_outcome=outcome,
            autonomy_level=autonomy,
            priority=priority,
            metadata={"compiled_at": "runtime", "text_length": len(raw_text)},
        )

    def _extract_constraints(self, text: str) -> List[str]:
        found = set()
        for constraint_type, patterns in self.CONSTRAINT_PATTERNS.items():
            if any(re.search(pattern, text, re.IGNORECASE) for pattern in patterns):
                found.add(constraint_type)
        return sorted(found)

    def _detect_autonomy(self, text: str) -> str:
        if re.search(r"\bapenas\s+(observ|ver|ler)\b", text):
            return AutonomyLevel.OBSERVE
        if re.search(r"\bsimula[rd]?\b", text):
            return AutonomyLevel.SIMULATE
        if re.search(r"\b(execut|faz|rode)\b.*\bcom\s+(revis[ãa]o|aprova[çc][ãa]o)\b", text):
            return AutonomyLevel.ASSIST
        if re.search(r"\b(execut|faz|rode)\b", text):
            if re.search(r"\baut[ôo]nom", text) or re.search(r"\bdentro\s+de\s+limite", text):
                return AutonomyLevel.DELEGATE
            return AutonomyLevel.ASSIST
        if re.search(r"\bevolu|promov|melho", text):
            return AutonomyLevel.EVOLVE
        return AutonomyLevel.ASSIST

    def _extract_objective(self, text: str) -> str:
        if re.search(r"\breduz|diminu.*fric", text):
            return "reduce_friction"
        if re.search(r"\bmetaboliz|transforma.*sistema", text):
            return "metabolize_systems"
        if re.search(r"\bextra[iíy]|compil.*capacidade", text):
            return "extract_capabilities"
        if re.search(r"\bgovern|audit", text):
            return "govern_execution"
        if re.search(r"\bemerg|recombina", text):
            return "facilitate_emergence"
        if re.search(r"\bintegr|conect", text):
            return "integrate_systems"
        return "general_assistance"

    def _extract_outcome(self, text: str) -> str:
        if "graph" in text or "grafo" in text:
            return "capability_graph"
        if "skill" in text or "habilidade" in text:
            return "skillpack"
        if "agent" in text or "agente" in text:
            return "agent_system"
        if "audit" in text or "auditoria" in text:
            return "auditpack"
        if "meta" in text and ("sistema" in text or "system" in text):
            return "meta_system"
        return "governed_coordination"

    def _calculate_priority(self, text: str, constraints: List[str]) -> float:
        priority = 0.5
        if re.search(r"\burgent|imediato|agora\b", text):
            priority += 0.3
        if "governance" in constraints or "fail_closed" in constraints:
            priority += 0.2
        if re.search(r"\bapenas\s+observ", text):
            priority -= 0.2
        return max(0.0, min(1.0, priority))

from __future__ import annotations

"""
MemoryTransducer

Converts canonical MatVerse memories into algorithms, skills and agents.

This module is deliberately local-first and dependency-free. It does not claim
public authorship, does not expose secrets, and emits deterministic conversion
records suitable for ledger/auditpack pipelines.
"""

from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any, Dict, Iterable, List
import hashlib
import json
import re


class MemoryKind(str, Enum):
    ALGORITHM = "algorithm"
    SKILL = "skill"
    AGENT = "agent"
    POLICY = "policy"
    ARTIFACT = "artifact"


@dataclass(frozen=True)
class MemoryAtom:
    id: str
    text: str
    tags: List[str] = field(default_factory=list)
    source: str = "memory"


@dataclass(frozen=True)
class MemoryConversion:
    memory_id: str
    kind: MemoryKind
    name: str
    description: str
    inputs: List[str]
    outputs: List[str]
    invariants: List[str]
    risk_score: float
    verification_score: float
    implementation_hint: str

    def to_hash(self) -> str:
        raw = json.dumps(asdict(self), ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()


class MemoryTransducer:
    """
    Converts user memories/preferences/project facts into operational objects.

    Heuristic map:
      - rules, thresholds, validators -> algorithms/policies
      - repeatable procedures -> skills
      - persistent roles with objectives -> agents
      - public infrastructure and files -> artifacts
    """

    KEYWORDS = {
        MemoryKind.AGENT: [
            r"\bagente\b", r"\bagent\b", r"\bcassandra\b", r"\batlas\b", r"\bgate\b",
            r"\bbody-[dax]\b", r"\borquestr", r"\bmediador", r"\bponte\b",
        ],
        MemoryKind.SKILL: [
            r"\bskill\b", r"\bprocedimento\b", r"\bpipeline\b", r"\bfluxo\b",
            r"\baudit", r"\bpublica", r"\bvalid", r"\bextrair\b", r"\bmapear\b",
        ],
        MemoryKind.ALGORITHM: [
            r"\balgorit", r"\bmétrica\b", r"\bscore\b", r"\bcvar\b", r"\bψ\b", r"\bomega\b",
            r"\bfunção\b", r"\bequação\b", r"\bmonte carlo\b", r"\bmodelo\b",
        ],
        MemoryKind.POLICY: [
            r"\bnunca\b", r"\bsempre\b", r"\bforbidden\b", r"\bfail[- ]closed\b",
            r"\bsegredo\b", r"\btoken\b", r"\bautoria\b", r"\bblock\b",
        ],
        MemoryKind.ARTIFACT: [
            r"\bzenodo\b", r"\bhugging\s*face\b", r"\borcid\b", r"\bgithub\b",
            r"\bdoi\b", r"\brepo\b", r"\bdataset\b", r"\bpaper\b", r"\bpreprint\b",
        ],
    }

    def convert(self, memories: Iterable[MemoryAtom]) -> List[MemoryConversion]:
        conversions: List[MemoryConversion] = []
        for memory in memories:
            kind = self.classify(memory.text)
            conversions.append(self._build_conversion(memory, kind))
        return conversions

    def classify(self, text: str) -> MemoryKind:
        normalized = text.casefold()
        scores: Dict[MemoryKind, int] = {kind: 0 for kind in MemoryKind}
        for kind, patterns in self.KEYWORDS.items():
            for pattern in patterns:
                if re.search(pattern, normalized, flags=re.IGNORECASE):
                    scores[kind] += 1
        return max(scores, key=lambda k: scores[k]) if max(scores.values()) > 0 else MemoryKind.SKILL

    def _build_conversion(self, memory: MemoryAtom, kind: MemoryKind) -> MemoryConversion:
        base_name = self._slug(memory.text)[:48] or memory.id
        invariants = self._extract_invariants(memory.text, kind)
        risk = self._risk(memory.text, kind)
        verification = 0.75 if invariants else 0.55

        if kind == MemoryKind.AGENT:
            inputs = ["intent", "context", "capability_graph", "policy"]
            outputs = ["plan", "state_mirror", "decision_request"]
            hint = "Wrap as an Agent with objective, memory_policy, decision_policy and Ω-Gate mediation."
        elif kind == MemoryKind.ALGORITHM:
            inputs = ["state", "metrics", "evidence"]
            outputs = ["score", "decision", "report"]
            hint = "Implement as deterministic Python function with tests and explicit thresholds."
        elif kind == MemoryKind.POLICY:
            inputs = ["event", "payload", "context"]
            outputs = ["PASS", "CONDITIONAL", "BLOCK"]
            hint = "Implement as fail-closed policy validator before mutation or publication."
        elif kind == MemoryKind.ARTIFACT:
            inputs = ["artifact_metadata", "evidence", "canonical_identity"]
            outputs = ["auditpack", "canonical_map", "patch_plan"]
            hint = "Implement as artifact governance skill with hashes, ORCID, metadata and replay bundle."
        else:
            inputs = ["input", "context", "constraints"]
            outputs = ["result", "evidence", "next_action"]
            hint = "Implement as reusable Skill with SKILL.md, Python entrypoint and smoke test."

        return MemoryConversion(
            memory_id=memory.id,
            kind=kind,
            name=f"{kind.value}.{base_name}",
            description=memory.text.strip(),
            inputs=inputs,
            outputs=outputs,
            invariants=invariants,
            risk_score=risk,
            verification_score=verification,
            implementation_hint=hint,
        )

    @staticmethod
    def _slug(text: str) -> str:
        raw = re.sub(r"[^a-zA-Z0-9]+", "_", text.strip().lower())
        return re.sub(r"_+", "_", raw).strip("_")

    @staticmethod
    def _extract_invariants(text: str, kind: MemoryKind) -> List[str]:
        lowered = text.casefold()
        invariants: List[str] = []
        if "não invent" in lowered or "sem aluc" in lowered:
            invariants.append("truth_no_hallucination")
        if "fail" in lowered or "block" in lowered or "bloque" in lowered:
            invariants.append("fail_closed")
        if "token" in lowered or "segredo" in lowered or "secret" in lowered:
            invariants.append("no_secret_exposure")
        if "autoria" in lowered or "author" in lowered or "orcid" in lowered:
            invariants.append("canonical_authorship")
        if "métrica" in lowered or "score" in lowered or "ψ" in lowered:
            invariants.append("measurable_quality")
        if kind == MemoryKind.AGENT:
            invariants.append("human_system_mediation")
        return sorted(set(invariants))

    @staticmethod
    def _risk(text: str, kind: MemoryKind) -> float:
        lowered = text.casefold()
        risk = 0.12
        if kind in {MemoryKind.POLICY, MemoryKind.ARTIFACT}:
            risk += 0.05
        if "token" in lowered or "segredo" in lowered or "secret" in lowered:
            risk += 0.20
        if "delete" in lowered or "apagar" in lowered or "publicar" in lowered:
            risk += 0.10
        return min(0.95, risk)


def conversions_to_manifest(conversions: Iterable[MemoryConversion]) -> Dict[str, Any]:
    items = list(conversions)
    return {
        "schema": "cassandra.organism.memory_conversion.v1",
        "summary": {
            "total": len(items),
            "algorithm": sum(1 for x in items if x.kind == MemoryKind.ALGORITHM),
            "skill": sum(1 for x in items if x.kind == MemoryKind.SKILL),
            "agent": sum(1 for x in items if x.kind == MemoryKind.AGENT),
            "policy": sum(1 for x in items if x.kind == MemoryKind.POLICY),
            "artifact": sum(1 for x in items if x.kind == MemoryKind.ARTIFACT),
        },
        "items": [
            {**asdict(item), "kind": item.kind.value, "conversion_hash": item.to_hash()}
            for item in items
        ],
    }

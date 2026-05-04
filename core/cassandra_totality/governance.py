#!/usr/bin/env python3
"""
Governance - Ω-Gate mínimo da Cassandra Totalidade.

Política:
- fail-closed quando risco excede limiar;
- bloqueia autoria de modelo/assistente;
- bloqueia exposição de segredos;
- aceita exploração em baixo risco;
- exige revisão humana para mutações moderadas.
"""

from __future__ import annotations

import hashlib
import json
import re
import time
from dataclasses import asdict, dataclass
from enum import Enum
from typing import Any, Dict, List


class Decision(str, Enum):
    PASS = "PASS"
    CONDITIONAL = "CONDITIONAL"
    BLOCK = "BLOCK"


@dataclass(frozen=True)
class OmegaRecord:
    decision: Decision
    reason: str
    request_hash: str
    timestamp_unix: float
    risk_score: float
    evidence_score: float
    requires_human_review: bool
    flags: List[str]


def canonical_json(payload: Dict[str, Any]) -> str:
    return json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def sha256_payload(payload: Dict[str, Any]) -> str:
    return hashlib.sha256(canonical_json(payload).encode("utf-8")).hexdigest()


class OmegaGate:
    """Gate de admissibilidade para planos, ações e conversões memória→sistema."""

    SECRET_PATTERNS = [
        re.compile(r"sk-[A-Za-z0-9_\-]{16,}"),
        re.compile(r"gh[pousr]_[A-Za-z0-9_]{16,}"),
        re.compile(r"(?i)(api[_-]?key|token|secret|password)\s*[:=]\s*['\"][^'\"]+['\"]"),
    ]

    AUTHORSHIP_FORBIDDEN = [
        "model author",
        "ai author",
        "assistant author",
        "chatgpt author",
        "cassandra author",
        "co-author model",
    ]

    def __init__(self, max_read_risk: float = 0.30, max_mutation_risk: float = 0.15, min_evidence: float = 0.55) -> None:
        self.max_read_risk = max_read_risk
        self.max_mutation_risk = max_mutation_risk
        self.min_evidence = min_evidence

    def decide(self, request: Dict[str, Any]) -> OmegaRecord:
        raw = canonical_json(request)
        request_hash = sha256_payload(request)
        flags: List[str] = []

        risk = float(request.get("risk_score", request.get("risk", 0.5)))
        evidence = float(request.get("evidence_score", request.get("verification", 0.0)))
        mutates = bool(request.get("mutates_state", request.get("requires_mutation", False)))
        requires_human_review = False

        if self._contains_secret(raw):
            flags.append("neycsec01.secret_exposure")
            return self._record(Decision.BLOCK, "flag neycsec01: secret-like value detected", request_hash, risk, evidence, True, flags)

        if self._contains_model_authorship(raw):
            flags.append("neycsec01.model_authorship")
            return self._record(Decision.BLOCK, "flag neycsec01: model/assistant authorship is forbidden", request_hash, risk, evidence, True, flags)

        risk_limit = self.max_mutation_risk if mutates else self.max_read_risk
        if risk > risk_limit:
            flags.append("risk_above_threshold")
            return self._record(Decision.BLOCK, f"risk {risk:.3f} exceeds limit {risk_limit:.3f}", request_hash, risk, evidence, True, flags)

        if evidence < self.min_evidence:
            flags.append("evidence_below_threshold")
            requires_human_review = True
            return self._record(Decision.CONDITIONAL, "evidence below promotion threshold", request_hash, risk, evidence, requires_human_review, flags)

        if mutates and risk > 0.05:
            flags.append("mutation_requires_review")
            requires_human_review = True
            return self._record(Decision.CONDITIONAL, "mutation requires human review or dry-run", request_hash, risk, evidence, requires_human_review, flags)

        return self._record(Decision.PASS, "Ω-Gate PASS: admissible low-risk request", request_hash, risk, evidence, False, flags)

    def _contains_secret(self, raw: str) -> bool:
        return any(pattern.search(raw) for pattern in self.SECRET_PATTERNS)

    def _contains_model_authorship(self, raw: str) -> bool:
        folded = raw.casefold()
        return any(term in folded for term in self.AUTHORSHIP_FORBIDDEN)

    @staticmethod
    def _record(decision: Decision, reason: str, request_hash: str, risk: float, evidence: float, requires_human_review: bool, flags: List[str]) -> OmegaRecord:
        return OmegaRecord(
            decision=decision,
            reason=reason,
            request_hash=request_hash,
            timestamp_unix=time.time(),
            risk_score=risk,
            evidence_score=evidence,
            requires_human_review=requires_human_review,
            flags=flags,
        )

    def as_dict(self, record: OmegaRecord) -> Dict[str, Any]:
        payload = asdict(record)
        payload["decision"] = record.decision.value
        return payload

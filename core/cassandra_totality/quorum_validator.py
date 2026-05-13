from __future__ import annotations
import math
from dataclasses import dataclass
from typing import List, Dict, Any, Optional

@dataclass
class QuorumConfig:
    expected_q: float = 0.67
    omega_min: float = 0.85
    psi_min: float = 0.85
    cvar_max: float = 0.05

    def validate(self):
        for name, val in [("expected_q", self.expected_q),
                          ("omega_min", self.omega_min),
                          ("psi_min", self.psi_min),
                          ("cvar_max", self.cvar_max)]:
            if not isinstance(val, (int, float)) or math.isnan(val) or math.isinf(val) or not (0 <= val <= 1):
                raise ValueError(f"{name} must be a finite number in [0,1]")

@dataclass
class NodeReceipt:
    node_id: str
    receipt_hash: str
    merkle_root: str
    psi: float
    omega: float
    cvar: float
    replay_valid: bool = True

class MatVerseQuorumValidator:
    def __init__(self, config: Optional[QuorumConfig] = None):
        self.config = config or QuorumConfig()
        self.config.validate()
        self.nodes: List[NodeReceipt] = []

    def add_receipt(self, receipt: NodeReceipt):
        self.nodes.append(receipt)

    def _metric_ok(self, value: float) -> bool:
        return (isinstance(value, (int, float)) and not isinstance(value, bool) and
                math.isfinite(value) and 0.0 <= value <= 1.0)

    def _hash_shape_ok(self, h: str) -> bool:
        if not isinstance(h, str):
            return False
        h = h.lower()
        if h.startswith("0x"):
            h = h[2:]
        return len(h) == 64 and all(c in "0123456789abcdef" for c in h)

    def _check_duplicate_nodes(self):
        seen = set()
        duplicates = set()
        for node in self.nodes:
            node_id = str(node.node_id)  # normalize
            if node_id in seen:
                duplicates.add(node_id)
            seen.add(node_id)
        return sorted(duplicates)

    def evaluate_quorum(self) -> Dict[str, Any]:
        n = len(self.nodes)
        if n == 0:
            return {"decision": "BLOCK", "state": "ERROR_NO_NODES",
                    "flag": "neycsec01:NO_NODES", "schema": "matverse.distributed_replay_quorum.v2"}

        # duplicate detection
        duplicates = self._check_duplicate_nodes()
        if duplicates:
            return {"decision": "BLOCK", "state": "CONSTITUTIONAL_BLOCK",
                    "flag": "neycsec01:DUPLICATE_NODE_ID", "rejected_nodes": n,
                    "node_rejections": {d: ["DUPLICATE_NODE_ID"] for d in duplicates},
                    "schema": "matverse.distributed_replay_quorum.v2"}

        node_rejections = {}
        admissible = []
        for node in self.nodes:
            reasons = []
            node_id = str(node.node_id)
            if not node_id.strip():
                reasons.append("NODE_ID_INVALID")
            else:
                if not self._metric_ok(node.psi):
                    reasons.append("PSI_INVALID")
                elif node.psi < self.config.psi_min:
                    reasons.append("PSI_LOW")
                if not self._metric_ok(node.omega):
                    reasons.append("OMEGA_INVALID")
                elif node.omega < self.config.omega_min:
                    reasons.append("OMEGA_LOW")
                if not self._metric_ok(node.cvar):
                    reasons.append("CVAR_INVALID")
                elif node.cvar > self.config.cvar_max:
                    reasons.append("CVAR_HIGH")
                if not self._hash_shape_ok(node.receipt_hash):
                    reasons.append("RECEIPT_HASH_INVALID_SHAPE")
                if not self._hash_shape_ok(node.merkle_root):
                    reasons.append("MERKLE_ROOT_INVALID_SHAPE")
            if reasons:
                node_rejections[node_id] = reasons
            else:
                admissible.append(node)

        if not admissible:
            return {"decision": "BLOCK", "state": "CONSTITUTIONAL_BLOCK",
                    "flag": "neycsec01:CONSTITUTIONAL_ADMISSIBILITY_BREACH",
                    "rejected_nodes": n, "admissible_nodes": 0,
                    "node_rejections": node_rejections,
                    "schema": "matverse.distributed_replay_quorum.v2"}

        winning = sum(1 for node in admissible if node.omega >= self.config.omega_min)
        total = len(admissible)
        consensus_ratio = winning / total if total else 0.0
        decision = (consensus_ratio >= self.config.expected_q)
        return {
            "decision": "PASS" if decision else "BLOCK",
            "state": "QUORUM_REACHED" if decision else "QUORUM_FAILED",
            "consensus_ratio": round(consensus_ratio, 4),
            "admissible_nodes": total,
            "rejected_nodes": n - total,
            "node_rejections": node_rejections,
            "schema": "matverse.distributed_replay_quorum.v2"
        }

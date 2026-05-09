from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Dict, List, Tuple

HEX_64 = re.compile(r"^[a-fA-F0-9]{64}$")


@dataclass(frozen=True)
class NodeReceipt:
    node_id: str
    receipt_hash: str
    merkle_root: str
    psi: float
    omega: float
    cvar: float
    replay_valid: bool = True


@dataclass(frozen=True)
class QuorumConfig:
    expected_q: float = 0.8
    omega_min: float = 0.85
    psi_min: float = 0.85
    cvar_max: float = 0.05


class MatVerseQuorumValidator:
    """Distributed replay quorum with constitutional hard constraints (fail-closed)."""

    def __init__(self, config: QuorumConfig | None = None) -> None:
        self.config = config or QuorumConfig()
        self.nodes: List[NodeReceipt] = []

    def add_receipt(self, receipt: NodeReceipt) -> None:
        self.nodes.append(receipt)

    @staticmethod
    def _hash_shape_ok(value: str) -> bool:
        clean = value.removeprefix("0x")
        return bool(HEX_64.match(clean))

    def is_constitutionally_admissible(self, node: NodeReceipt) -> Tuple[bool, List[str]]:
        reasons: List[str] = []

        if not node.replay_valid:
            reasons.append("REPLAY_INVALID")
        if node.omega < self.config.omega_min:
            reasons.append("OMEGA_LOW")
        if node.psi < self.config.psi_min:
            reasons.append("PSI_LOW")
        if node.cvar > self.config.cvar_max:
            reasons.append("CVAR_HIGH")
        if not self._hash_shape_ok(node.receipt_hash):
            reasons.append("RECEIPT_HASH_INVALID_SHAPE")
        if not node.merkle_root:
            reasons.append("MERKLE_ROOT_EMPTY")

        return len(reasons) == 0, reasons

    def evaluate_quorum(self) -> Dict[str, object]:
        n = len(self.nodes)
        base: Dict[str, object] = {
            "schema": "matverse.distributed_replay_quorum.v1",
            "state": "UNSET",
            "decision": "BLOCK",
            "flag": None,
            "total_nodes": n,
            "admissible_nodes": 0,
            "rejected_nodes": 0,
            "consensus_ratio": 0.0,
            "consensus_attained": False,
            "omega_d_avg": 0.0,
            "winning_receipt_hash": None,
            "winning_merkle_root": None,
            "node_rejections": {},
        }

        if n == 0:
            base.update(state="ERROR_NO_NODES", flag="neycsec01:NO_NODES")
            return base

        admissible: List[NodeReceipt] = []
        node_rejections: Dict[str, List[str]] = {}
        for node in self.nodes:
            ok, reasons = self.is_constitutionally_admissible(node)
            if ok:
                admissible.append(node)
            else:
                node_rejections[node.node_id] = reasons

        base["node_rejections"] = node_rejections
        base["admissible_nodes"] = len(admissible)
        base["rejected_nodes"] = n - len(admissible)

        if not admissible:
            base.update(
                state="CONSTITUTIONAL_BLOCK",
                flag="neycsec01:CVAR_OR_PSI_OR_REPLAY_BREACH",
            )
            return base

        counts: Dict[Tuple[str, str], int] = {}
        for node in admissible:
            key = (node.receipt_hash, node.merkle_root)
            counts[key] = counts.get(key, 0) + 1

        winning_pair, winning_count = max(counts.items(), key=lambda kv: kv[1])
        consensus_ratio = winning_count / n
        consensus_attained = consensus_ratio >= self.config.expected_q

        base.update(
            consensus_ratio=round(consensus_ratio, 4),
            consensus_attained=consensus_attained,
            omega_d_avg=round(sum(node.omega for node in admissible) / len(admissible), 4),
            winning_receipt_hash=winning_pair[0],
            winning_merkle_root=winning_pair[1],
        )

        if consensus_attained:
            base.update(state="DISTRIBUTED_REPLAY_QUORUM_PASS", decision="PASS")
        else:
            base.update(state="DISTRIBUTED_REPLAY_QUORUM_FAIL", flag="neycsec01:QUORUM_NOT_ATTAINED")

        return base

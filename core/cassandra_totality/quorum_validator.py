from __future__ import annotations

import math
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

    def validate(self) -> None:
        for name, value in {
            "expected_q": self.expected_q,
            "omega_min": self.omega_min,
            "psi_min": self.psi_min,
            "cvar_max": self.cvar_max,
        }.items():
            if not isinstance(value, (int, float)) or not math.isfinite(float(value)):
                raise ValueError(f"{name} must be finite")

            if not 0.0 <= float(value) <= 1.0:
                raise ValueError(f"{name} must be in [0,1]")


class MatVerseQuorumValidator:
    """Constitutional distributed replay quorum with fail-closed hard constraints."""

    def __init__(self, config: QuorumConfig | None = None) -> None:
        self.config = config or QuorumConfig()
        self.config.validate()
        self.nodes: List[NodeReceipt] = []

    def add_receipt(self, receipt: NodeReceipt) -> None:
        self.nodes.append(receipt)

    @staticmethod
    def _hash_shape_ok(value: str) -> bool:
        if not isinstance(value, str):
            return False
        return bool(HEX_64.match(value.removeprefix("0x")))

    @staticmethod
    def _metric_ok(value: float) -> bool:
        return (
            isinstance(value, (int, float))
            and math.isfinite(float(value))
            and 0.0 <= float(value) <= 1.0
        )

    def _check_duplicate_nodes(self) -> List[str]:
        seen: set[str] = set()
        duplicates: set[str] = set()

        for node in self.nodes:
            if node.node_id in seen:
                duplicates.add(node.node_id)
            seen.add(node.node_id)

        return sorted(duplicates)

    def is_constitutionally_admissible(self, node: NodeReceipt) -> Tuple[bool, List[str]]:
        reasons: List[str] = []

        if not isinstance(node.node_id, str) or not node.node_id.strip():
            reasons.append("NODE_ID_INVALID")

        if not node.replay_valid:
            reasons.append("REPLAY_INVALID")

        if not self._metric_ok(node.omega):
            reasons.append("OMEGA_INVALID")
        elif node.omega < self.config.omega_min:
            reasons.append("OMEGA_LOW")

        if not self._metric_ok(node.psi):
            reasons.append("PSI_INVALID")
        elif node.psi < self.config.psi_min:
            reasons.append("PSI_LOW")

        if not self._metric_ok(node.cvar):
            reasons.append("CVAR_INVALID")
        elif node.cvar > self.config.cvar_max:
            reasons.append("CVAR_HIGH")

        if not self._hash_shape_ok(node.receipt_hash):
            reasons.append("RECEIPT_HASH_INVALID_SHAPE")

        if not self._hash_shape_ok(node.merkle_root):
            reasons.append("MERKLE_ROOT_INVALID_SHAPE")

        return len(reasons) == 0, reasons

    def evaluate_quorum(self) -> Dict[str, object]:
        n = len(self.nodes)

        result: Dict[str, object] = {
            "schema": "matverse.distributed_replay_quorum.v2",
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
            result.update(
                state="ERROR_NO_NODES",
                flag="neycsec01:NO_NODES",
            )
            return result

        duplicates = self._check_duplicate_nodes()
        if duplicates:
            result.update(
                state="CONSTITUTIONAL_BLOCK",
                flag="neycsec01:DUPLICATE_NODE_ID",
                rejected_nodes=n,
                node_rejections={node_id: ["DUPLICATE_NODE_ID"] for node_id in duplicates},
            )
            return result

        admissible: List[NodeReceipt] = []
        node_rejections: Dict[str, List[str]] = {}

        for node in self.nodes:
            ok, reasons = self.is_constitutionally_admissible(node)
            if ok:
                admissible.append(node)
            else:
                node_rejections[node.node_id] = reasons

        result["admissible_nodes"] = len(admissible)
        result["rejected_nodes"] = n - len(admissible)
        result["node_rejections"] = node_rejections

        if not admissible:
            result.update(
                state="CONSTITUTIONAL_BLOCK",
                flag="neycsec01:CONSTITUTIONAL_ADMISSIBILITY_BREACH",
            )
            return result

        counts: Dict[Tuple[str, str], int] = {}

        for node in admissible:
            pair = (node.receipt_hash, node.merkle_root)
            counts[pair] = counts.get(pair, 0) + 1

        winning_pair, winning_count = max(counts.items(), key=lambda item: item[1])
        consensus_ratio = winning_count / n
        consensus_attained = consensus_ratio >= self.config.expected_q

        result.update(
            consensus_ratio=round(consensus_ratio, 4),
            consensus_attained=consensus_attained,
            omega_d_avg=round(sum(node.omega for node in admissible) / len(admissible), 4),
            winning_receipt_hash=winning_pair[0],
            winning_merkle_root=winning_pair[1],
        )

        if consensus_attained:
            result.update(
                state="DISTRIBUTED_REPLAY_QUORUM_PASS",
                decision="PASS",
                flag=None,
            )
        else:
            result.update(
                state="DISTRIBUTED_REPLAY_QUORUM_FAIL",
                decision="BLOCK",
                flag="neycsec01:QUORUM_NOT_ATTAINED",
            )

        return result

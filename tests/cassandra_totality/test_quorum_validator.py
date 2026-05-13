import math

import pytest

from core.cassandra_totality.quorum_validator import (
    MatVerseQuorumValidator,
    NodeReceipt,
    QuorumConfig,
)


def test_blocks_nan_metric() -> None:
    validator = MatVerseQuorumValidator()
    validator.add_receipt(
        NodeReceipt(
            node_id="node_0",
            receipt_hash="a" * 64,
            merkle_root="b" * 64,
            psi=0.91,
            omega=math.nan,
            cvar=0.03,
        )
    )

    result = validator.evaluate_quorum()

    assert result["decision"] == "BLOCK"
    assert result["state"] == "CONSTITUTIONAL_BLOCK"
    assert result["node_rejections"]["node_0"] == ["OMEGA_INVALID"]


def test_blocks_infinite_metric() -> None:
    validator = MatVerseQuorumValidator()
    validator.add_receipt(
        NodeReceipt(
            node_id="node_0",
            receipt_hash="a" * 64,
            merkle_root="b" * 64,
            psi=0.91,
            omega=0.93,
            cvar=math.inf,
        )
    )

    result = validator.evaluate_quorum()

    assert result["decision"] == "BLOCK"
    assert "CVAR_INVALID" in result["node_rejections"]["node_0"]


def test_blocks_invalid_merkle_shape() -> None:
    validator = MatVerseQuorumValidator()

    for i in range(5):
        validator.add_receipt(
            NodeReceipt(
                node_id=f"node_{i}",
                receipt_hash="a" * 64,
                merkle_root="0x_root",
                psi=0.91,
                omega=0.93,
                cvar=0.03,
            )
        )

    result = validator.evaluate_quorum()

    assert result["decision"] == "BLOCK"
    assert result["state"] == "CONSTITUTIONAL_BLOCK"


def test_blocks_duplicate_node_id() -> None:
    validator = MatVerseQuorumValidator()

    for _ in range(5):
        validator.add_receipt(
            NodeReceipt(
                node_id="node_same",
                receipt_hash="a" * 64,
                merkle_root="b" * 64,
                psi=0.91,
                omega=0.93,
                cvar=0.03,
            )
        )

    result = validator.evaluate_quorum()

    assert result["decision"] == "BLOCK"
    assert result["state"] == "CONSTITUTIONAL_BLOCK"
    assert result["flag"] == "neycsec01:DUPLICATE_NODE_ID"


def test_blocks_invalid_config() -> None:
    with pytest.raises(ValueError):
        MatVerseQuorumValidator(QuorumConfig(expected_q=1.5))


def test_valid_quorum_passes() -> None:
    validator = MatVerseQuorumValidator()

    for i in range(5):
        validator.add_receipt(
            NodeReceipt(
                node_id=f"node_{i}",
                receipt_hash="a" * 64,
                merkle_root="b" * 64,
                psi=0.91,
                omega=0.93,
                cvar=0.03,
            )
        )

    result = validator.evaluate_quorum()

    assert result["decision"] == "PASS"
    assert result["state"] == "DISTRIBUTED_REPLAY_QUORUM_PASS"
    assert result["consensus_ratio"] == 1.0

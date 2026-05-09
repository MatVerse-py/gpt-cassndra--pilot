from core.cassandra_totality.quorum_validator import MatVerseQuorumValidator, NodeReceipt


def test_constitutional_block_when_all_nodes_breach_cvar() -> None:
    validator = MatVerseQuorumValidator()
    for i in range(5):
        validator.add_receipt(
            NodeReceipt(
                node_id=f"node_{i}",
                receipt_hash="a" * 64,
                merkle_root="0x_root",
                psi=0.9,
                omega=0.9,
                cvar=0.13,
                replay_valid=True,
            )
        )

    result = validator.evaluate_quorum()

    assert result["state"] == "CONSTITUTIONAL_BLOCK"
    assert result["decision"] == "BLOCK"
    assert result["admissible_nodes"] == 0


def test_pass_when_pair_converges_and_all_constraints_hold() -> None:
    validator = MatVerseQuorumValidator()
    merkle = "b" * 64
    for i in range(5):
        validator.add_receipt(
            NodeReceipt(
                node_id=f"node_{i}",
                receipt_hash="a" * 64,
                merkle_root=merkle,
                psi=0.91,
                omega=0.93,
                cvar=0.03,
                replay_valid=True,
            )
        )

    result = validator.evaluate_quorum()

    assert result["state"] == "DISTRIBUTED_REPLAY_QUORUM_PASS"
    assert result["decision"] == "PASS"
    assert result["consensus_attained"] is True

import pytest
import math
from core.cassandra_totality.quorum_validator import MatVerseQuorumValidator, NodeReceipt, QuorumConfig

@pytest.mark.asyncio
async def test_blocks_nan_metric():
    v = MatVerseQuorumValidator()
    v.add_receipt(NodeReceipt(node_id="n1", receipt_hash="a"*64, merkle_root="b"*64, psi=0.9, omega=math.nan, cvar=0.03))
    res = v.evaluate_quorum()
    assert res["decision"] == "BLOCK"
    assert "OMEGA_INVALID" in res["node_rejections"]["n1"]

def test_valid_quorum_passes():
    v = MatVerseQuorumValidator()
    for i in range(5):
        v.add_receipt(NodeReceipt(node_id=f"n{i}", receipt_hash="a"*64, merkle_root="b"*64, psi=0.91, omega=0.93, cvar=0.03))
    res = v.evaluate_quorum()
    assert res["decision"] == "PASS"
    assert res["consensus_ratio"] == 1.0

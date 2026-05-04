"""
Cassandra Core - Totalidade

Cassandra como camada gravitacional de mediação entre:
- humano ↔ sistema
- sistema ↔ sistema
- intenção ↔ capacidade
- complexidade ↔ legibilidade

Não é "mais um agente".
É a superfície cognitiva onde humanos governam sistemas complexos.
"""

__version__ = "0.1.0"
__status__ = "CONDITIONAL"

from .intent_compiler import AutonomyLevel, HumanIntent, IntentCompiler
from .capability_mapper import Capability, CapabilityGraph, CapabilityMapper, CapabilityType
from .cognitive_state_mirror import ActionPreview, CognitiveStateMirror, StateView
from .friction import FrictionReport, FrictionVector, compute_friction_report
from .governance import Decision, OmegaGate, OmegaRecord
from .ledger import HashLedger
from .memory_transducer import MemoryAtom, MemoryConversion, MemoryTransducer
from .totality_core import CassandraRunRecord, CassandraTotalityCore

__all__ = [
    "ActionPreview",
    "AutonomyLevel",
    "Capability",
    "CapabilityGraph",
    "CapabilityMapper",
    "CapabilityType",
    "CassandraRunRecord",
    "CassandraTotalityCore",
    "CognitiveStateMirror",
    "Decision",
    "FrictionReport",
    "FrictionVector",
    "HashLedger",
    "HumanIntent",
    "IntentCompiler",
    "MemoryAtom",
    "MemoryConversion",
    "MemoryTransducer",
    "OmegaGate",
    "OmegaRecord",
    "StateView",
    "compute_friction_report",
]

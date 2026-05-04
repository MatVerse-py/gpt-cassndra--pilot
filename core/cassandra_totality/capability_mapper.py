#!/usr/bin/env python3
"""
CapabilityMapper - Mapeador de Capacidades

Extrai capacidades de sistemas heterogêneos e normaliza em grafo unificado.

Suporta agora:
- Repositórios Python

Reservado para próximas fases:
- APIs OpenAPI
- MCP servers
- Agentes LangGraph/CrewAI
- Traces de observabilidade
"""

from __future__ import annotations

import ast
import hashlib
import json
from dataclasses import asdict, dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional


class CapabilityType(str, Enum):
    FUNCTION = "function"
    CLASS = "class"
    API = "api"
    TOOL = "tool"
    SKILL = "skill"
    AGENT = "agent"


@dataclass(frozen=True)
class Capability:
    """Capacidade normalizada."""

    id: str
    name: str
    type: CapabilityType
    system: str
    inputs: List[str]
    outputs: List[str]
    risk: float
    verification: float
    utility: float
    executor: str
    policy: Dict[str, Any]
    evidence: List[Dict[str, Any]] = field(default_factory=list)

    def to_hash(self) -> str:
        payload = {
            "name": self.name,
            "type": self.type.value if isinstance(self.type, CapabilityType) else str(self.type),
            "system": self.system,
            "inputs": sorted(self.inputs),
            "outputs": sorted(self.outputs),
        }
        raw = json.dumps(payload, ensure_ascii=False, sort_keys=True)
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()


@dataclass
class CapabilityGraph:
    """Grafo de capacidades e dependências."""

    nodes: List[Capability]
    edges: List[Dict[str, str]] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def add_edge(self, from_cap: str, to_cap: str, relation: str = "supports") -> None:
        self.edges.append({"from": from_cap, "to": to_cap, "relation": relation})

    def compatible_outputs_inputs(self, cap_a: Capability, cap_b: Capability) -> float:
        if not cap_a.outputs or not cap_b.inputs:
            return 0.0
        out_set = set(cap_a.outputs)
        in_set = set(cap_b.inputs)
        intersection = len(out_set & in_set)
        union = len(out_set | in_set)
        return intersection / union if union else 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "schema": "msm.capability_graph.v1",
            "nodes": [asdict(node) for node in self.nodes],
            "edges": self.edges,
            "metadata": self.metadata,
        }


class PythonCapabilityExtractor:
    """Extrai capacidades de código Python."""

    def __init__(self, root: Path):
        self.root = Path(root).resolve()

    def extract(self) -> List[Capability]:
        capabilities: List[Capability] = []
        for path in self.root.rglob("*.py"):
            if self._should_skip(path):
                continue
            capabilities.extend(self._extract_from_file(path))
        return capabilities

    def _should_skip(self, path: Path) -> bool:
        skip_dirs = {".venv", "venv", "__pycache__", ".git", "node_modules", ".pytest_cache"}
        return any(part in skip_dirs for part in path.parts)

    def _extract_from_file(self, path: Path) -> List[Capability]:
        try:
            source = path.read_text(encoding="utf-8", errors="ignore")
            tree = ast.parse(source)
        except Exception:
            return []

        capabilities: List[Capability] = []
        source_hash = hashlib.sha256(source.encode("utf-8")).hexdigest()
        evidence = {
            "kind": "python_source",
            "file": str(path.relative_to(self.root)),
            "hash": source_hash,
            "bytes": len(source.encode("utf-8")),
        }

        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                cap = self._function_to_capability(node, path, evidence)
                if cap:
                    capabilities.append(cap)
            elif isinstance(node, ast.ClassDef):
                cap = self._class_to_capability(node, path, evidence)
                if cap:
                    capabilities.append(cap)
        return capabilities

    def _function_to_capability(self, node: ast.FunctionDef, path: Path, evidence: Dict[str, Any]) -> Optional[Capability]:
        rel_path = path.relative_to(self.root)
        inputs = [arg.arg for arg in node.args.args]
        risk = 0.15
        lowered = node.name.lower()
        if any(x in lowered for x in ["delete", "remove", "discard"]):
            risk = 0.35
        if any(x in lowered for x in ["exec", "eval", "shell", "subprocess"]):
            risk = 0.50

        return Capability(
            id=f"cap.fn.{rel_path}::{node.name}",
            name=node.name,
            type=CapabilityType.FUNCTION,
            system=str(rel_path).split("/")[0] if "/" in str(rel_path) else "root",
            inputs=inputs,
            outputs=["unknown"],
            risk=risk,
            verification=0.60,
            utility=0.65,
            executor=f"{path}:{node.lineno}",
            policy={"requires_review": risk > 0.30},
            evidence=[evidence],
        )

    def _class_to_capability(self, node: ast.ClassDef, path: Path, evidence: Dict[str, Any]) -> Optional[Capability]:
        rel_path = path.relative_to(self.root)
        methods = [item.name for item in node.body if isinstance(item, ast.FunctionDef) and not item.name.startswith("_")]
        return Capability(
            id=f"cap.class.{rel_path}::{node.name}",
            name=node.name,
            type=CapabilityType.CLASS,
            system=str(rel_path).split("/")[0] if "/" in str(rel_path) else "root",
            inputs=[],
            outputs=methods or ["object"],
            risk=0.20,
            verification=0.55,
            utility=0.70,
            executor=f"{path}:{node.lineno}",
            policy={"requires_review": True},
            evidence=[evidence],
        )


class CapabilityMapper:
    """Orquestrador de extração e normalização de capacidades."""

    def map_python_repo(self, repo_path: str | Path) -> CapabilityGraph:
        extractor = PythonCapabilityExtractor(Path(repo_path))
        capabilities = extractor.extract()
        graph = CapabilityGraph(
            nodes=capabilities,
            metadata={"source": "python_repo", "path": str(repo_path), "capability_count": len(capabilities)},
        )
        for i, cap_a in enumerate(capabilities):
            for j, cap_b in enumerate(capabilities):
                if i == j:
                    continue
                compat = graph.compatible_outputs_inputs(cap_a, cap_b)
                if compat > 0.3:
                    graph.add_edge(cap_a.id, cap_b.id, "compatible")
        return graph

    def map_api_spec(self, openapi_path: str | Path) -> CapabilityGraph:
        return CapabilityGraph(nodes=[], metadata={"source": "openapi", "path": str(openapi_path), "status": "not_implemented"})

    def map_mcp_server(self, mcp_config: Dict[str, Any]) -> CapabilityGraph:
        return CapabilityGraph(nodes=[], metadata={"source": "mcp_server", "status": "not_implemented", "config_keys": sorted(mcp_config.keys())})

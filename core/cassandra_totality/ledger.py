#!/usr/bin/env python3
"""HashLedger - memória causal append-only da Cassandra Totalidade."""

from __future__ import annotations

import hashlib
import json
import time
from pathlib import Path
from typing import Any, Dict, List


def canonical_json(payload: Dict[str, Any]) -> str:
    return json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def sha256_payload(payload: Dict[str, Any]) -> str:
    return hashlib.sha256(canonical_json(payload).encode("utf-8")).hexdigest()


class HashLedger:
    """Ledger causal local: previous_hash → record_hash → root_hash."""

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.touch(exist_ok=True)

    def records(self) -> List[Dict[str, Any]]:
        out: List[Dict[str, Any]] = []
        with self.path.open("r", encoding="utf-8") as handle:
            for line in handle:
                if line.strip():
                    out.append(json.loads(line))
        return out

    def root(self) -> str:
        records = self.records()
        if not records:
            return "0" * 64
        return str(records[-1]["root_hash"])

    def append(self, event: Dict[str, Any]) -> Dict[str, Any]:
        previous_hash = self.root()
        base = {
            "timestamp_unix": time.time(),
            "previous_hash": previous_hash,
            "event": event,
        }
        record_hash = sha256_payload(base)
        root_hash = hashlib.sha256((previous_hash + record_hash).encode("utf-8")).hexdigest()
        record = {**base, "record_hash": record_hash, "root_hash": root_hash}
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(canonical_json(record) + "\n")
        return record

    def verify(self) -> bool:
        previous_hash = "0" * 64
        for record in self.records():
            expected_base = {
                "timestamp_unix": record["timestamp_unix"],
                "previous_hash": record["previous_hash"],
                "event": record["event"],
            }
            expected_record_hash = sha256_payload(expected_base)
            expected_root = hashlib.sha256((previous_hash + expected_record_hash).encode("utf-8")).hexdigest()
            if record["previous_hash"] != previous_hash:
                return False
            if record["record_hash"] != expected_record_hash:
                return False
            if record["root_hash"] != expected_root:
                return False
            previous_hash = record["root_hash"]
        return True

#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
WORK_DIR="$ROOT_DIR/gthdl_on_ghdl/build"
EVIDENCE_DIR="$ROOT_DIR/gthdl_on_ghdl/evidence"
REPORT_FILE="$EVIDENCE_DIR/simulation_report.json"
WAVE_FILE="$EVIDENCE_DIR/gthdl_on_ghdl.ghw"
SHA_FILE="$EVIDENCE_DIR/SHA256SUMS"

if ! command -v ghdl >/dev/null 2>&1; then
  echo "ERROR: ghdl is not installed or not available in PATH." >&2
  exit 127
fi

rm -rf "$WORK_DIR"
mkdir -p "$WORK_DIR" "$EVIDENCE_DIR"

cd "$ROOT_DIR/gthdl_on_ghdl"

ghdl -a --std=08 --workdir="$WORK_DIR" rtl/matverse_metrics_pkg.vhd
ghdl -a --std=08 --workdir="$WORK_DIR" rtl/omega_gate.vhd
ghdl -a --std=08 --workdir="$WORK_DIR" rtl/replay_checker.vhd
ghdl -a --std=08 --workdir="$WORK_DIR" rtl/ledger_register.vhd
ghdl -a --std=08 --workdir="$WORK_DIR" tb/tb_omega_gate.vhd

ghdl -e --std=08 --workdir="$WORK_DIR" -P"$WORK_DIR" tb_omega_gate
ghdl -r --std=08 --workdir="$WORK_DIR" -P"$WORK_DIR" tb_omega_gate --assert-level=error --stop-time=100ns --wave="$WAVE_FILE"

{
  echo "{"
  echo "  \"status\": \"PASS\","
  echo "  \"tool\": \"ghdl\","
  echo "  \"generated_at_utc\": \"$(date -u +%Y-%m-%dT%H:%M:%SZ)\","
  echo "  \"design\": \"gthdl_on_ghdl\","
  echo "  \"top\": \"tb_omega_gate\","
  echo "  \"source_vector\": \"cassandra_substrato_pass\","
  echo "  \"expected_omega_m\": 882,"
  echo "  \"expected_decision\": \"PASS\","
  echo "  \"waveform\": \"gthdl_on_ghdl/evidence/gthdl_on_ghdl.ghw\""
  echo "}"
} > "$REPORT_FILE"

(
  cd "$ROOT_DIR"
  sha256sum \
    gthdl_on_ghdl/rtl/matverse_metrics_pkg.vhd \
    gthdl_on_ghdl/rtl/omega_gate.vhd \
    gthdl_on_ghdl/rtl/replay_checker.vhd \
    gthdl_on_ghdl/rtl/ledger_register.vhd \
    gthdl_on_ghdl/tb/tb_omega_gate.vhd \
    gthdl_on_ghdl/evidence/cassandra_substrato_vector.json \
    gthdl_on_ghdl/evidence/input_manifest.json \
    > "$SHA_FILE"
)

echo "GTHDL-on-GHDL simulation PASS"

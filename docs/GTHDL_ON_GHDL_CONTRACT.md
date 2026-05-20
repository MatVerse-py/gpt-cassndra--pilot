# GTHDL-on-GHDL Contract

## Objective

Apply the `GTHDL-on-GHDL` bridge to this repository by converting a bounded subset of the MatVerse Ω-Gate metric regime into VHDL simulation artifacts.

## Operational translation

```text
GTHDL theory layer
  -> Ω-Gate metric formula
  -> fixed-point VHDL implementation
  -> GHDL simulation
  -> waveform + simulation report + SHA256SUMS
```

## Implemented files

```text
gthdl_on_ghdl/
├── README.md
├── rtl/
│   ├── matverse_metrics_pkg.vhd
│   ├── omega_gate.vhd
│   ├── replay_checker.vhd
│   └── ledger_register.vhd
├── tb/
│   └── tb_omega_gate.vhd
├── scripts/
│   └── run_ghdl.sh
└── evidence/
    ├── cassandra_substrato_vector.json
    └── input_manifest.json
```

## Decision formula

```text
Ω = 0.4Ψ + 0.3Θ̂ + 0.2(1 − CVaR) + 0.1PoLE
```

Implemented with integer milli-units:

```text
omega_m = (400*psi_m + 300*theta_m + 200*(1000-cvar_m) + 100*pole_m) / 1000
```

## PASS gate

```text
PASS iff:
  psi_m >= 850
  cvar_m <= 50
  omega_m >= 850
  replay_valid = 1
```

## Uploaded source binding

```text
uploaded_name: Understanding Cassandra Matverse Uploaded File Content.zip
sha256: f91502bb91c424fcef886e6fc51104587a2d464f2c752c41c4b8971cf6b63c1e
selected_vector: omega_gate_output_substrato.json
```

## Epistemic boundary

This implementation proves only that the selected Ω-Gate decision rule can be represented and simulated as deterministic VHDL logic.

It does not prove:

- literal digital life;
- scientific validation of GTHDL;
- FPGA readiness;
- independent reproducibility;
- cryptographic hashing inside hardware.

## Required local validation

Run:

```bash
bash gthdl_on_ghdl/scripts/run_ghdl.sh
```

Expected generated artifacts:

```text
gthdl_on_ghdl/evidence/gthdl_on_ghdl.ghw
gthdl_on_ghdl/evidence/simulation_report.json
gthdl_on_ghdl/evidence/SHA256SUMS
```

## Status

```text
GTHDL_ON_GHDL_BRANCH: codex/set-up-codex-with-github
IMPLEMENTATION_STATUS: PASS_LOCAL_SCAFFOLD
SIMULATION_STATUS: HOLD_UNTIL_GHDL_RUNTIME_EXECUTION
```

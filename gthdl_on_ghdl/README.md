# GTHDL-on-GHDL

`GTHDL-on-GHDL` is the first hardware-simulation bridge for the MatVerse/Cassandra pilot.

It translates a bounded subset of the GTHDL/Ω-Gate metric regime into VHDL modules that can be analyzed, elaborated, and simulated with GHDL.

This is not a claim that digital life has been proven in hardware. It is a deterministic simulation harness for the decision layer:

```text
Ψ, Θ̂, CVaR, PoLE, replay_valid
        ↓
fixed-point Ω-Gate
        ↓
PASS / REVIEW / BLOCK
        ↓
testbench replay evidence
```

## Scope

Implemented:

- fixed-point Ω computation in integer milli-units;
- hard gates for Ψ, CVaR, Ω, and replay validity;
- deterministic testbench vectors derived from uploaded Cassandra/MatVerse Ω-Gate reports;
- GHDL script that analyzes, elaborates, simulates, emits waveform output, and writes a local report.

Not implemented:

- cryptographic SHA-256 inside VHDL;
- FPGA synthesis constraints;
- independent scientific validation;
- proof of literal digital life.

## Metric encoding

All metrics are encoded as integers from `0` to `1000`.

```text
0.885 -> 885
0.790 -> 790
0.045 -> 45
1.000 -> 1000
```

The Ω formula implemented in `rtl/omega_gate.vhd` is:

```text
Ω = 0.4Ψ + 0.3Θ̂ + 0.2(1 − CVaR) + 0.1PoLE
```

In milli-units:

```text
omega_m = (400*psi_m + 300*theta_m + 200*(1000-cvar_m) + 100*pole_m) / 1000
```

## Constitutional hard gates

A vector receives `PASS` only if all conditions hold:

```text
psi_m        >= 850
cvar_m       <= 50
omega_m      >= 850
replay_valid = 1
```

Otherwise the output is `REVIEW` or `BLOCK`.

## Run

From the repository root:

```bash
bash gthdl_on_ghdl/scripts/run_ghdl.sh
```

Expected output on a machine with GHDL installed:

```text
GTHDL-on-GHDL simulation PASS
```

The script writes:

```text
gthdl_on_ghdl/evidence/gthdl_on_ghdl.ghw
gthdl_on_ghdl/evidence/simulation_report.json
gthdl_on_ghdl/evidence/SHA256SUMS
```

## Source vector

The default PASS vector is derived from the uploaded file:

```text
Understanding Cassandra Matverse Uploaded File Content.zip
sha256: f91502bb91c424fcef886e6fc51104587a2d464f2c752c41c4b8971cf6b63c1e
```

Selected metrics:

```text
Psi       = 0.885
Theta_Hat = 0.790
CVaR      = 0.045
PoLE      = 1.000
Decision  = PASS
```

## Status

```text
GTHDL_ON_GHDL_STATUS: PASS_LOCAL_SCAFFOLD
VALIDATION: requires GHDL runtime execution
PUBLIC_CLAIM: STAGE
```

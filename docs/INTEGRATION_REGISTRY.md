# Integration Registry

This document defines the repository integration surface for the MatVerse/Cassandra pilot.

It separates operational tooling from authorship, governance, evidence, and scientific claims. Tools may assist execution, review, documentation, and pull request workflows, but they do not become authors, owners, maintainers, or institutional authorities.

## Operational status

```text
REGISTRY_STATUS: STAGE
REPOSITORY: MatVerse-py/gpt-cassndra--pilot
PRIMARY_SCOPE: GitHub + Codex + review automation
AUTHORITY_MODEL: human/institutional responsibility only
FAIL_CLOSED_RULE: unverified integration claims remain HOLD
```

## Integration map

| Layer | Integration | Current role | Status | Boundary |
| --- | --- | --- | --- | --- |
| Repository | GitHub | Source control, pull requests, review surface, audit trail | PASS | GitHub records changes; it does not validate scientific truth. |
| Coding agent | Codex web | Delegated code/documentation tasks and pull request support | STAGE | Codex assists execution; it is not an author or responsible entity. |
| Remote execution | Codex cloud | Isolated workspace for delegated tasks | STAGE | Cloud execution must be constrained by repo policy, secrets hygiene, and review. |
| Review automation | Sourcery / automated review bots | Review hints and documentation feedback | STAGE | Suggestions require human or governed acceptance. |
| Documentation | Markdown docs | Repo-readable operational knowledge | PASS | Docs must avoid root-relative links that break outside their native host. |
| Evidence | Git commit + PR metadata | Minimal traceability for changes | PASS_LOCAL | Commit history is provenance, not independent scientific validation. |

## Canonical rules

1. Agents and automated tools are auxiliary execution systems, never authors.
2. Public repository history is admissible provenance only when commit, file path, and diff are inspectable.
3. Documentation links must resolve from GitHub and local Markdown viewers.
4. Any integration that touches secrets must avoid inline tokens, logs containing tokens, or copy-pasted credentials.
5. Any claim of validation, production readiness, or scientific proof must point to evidence artifacts, tests, replay, or independent verification.
6. If the evidence is absent, mark the status as `HOLD`, not `PASS`.

## Codex integration contract

```text
INPUT: issue, pull request, prompt, repository files
PROCESS: inspect -> edit -> run/check when possible -> propose diff -> PR/comment
OUTPUT: commit, pull request, review comment, documentation update
FORBIDDEN OUTPUT: agent authorship, secret exposure, unsupported validation claim
```

Codex may be used for:

- documentation repair;
- repository navigation;
- implementation tasks;
- test generation;
- pull request review support;
- refactoring under explicit constraints;
- evidence-pack scaffolding.

Codex must not be used as:

- named author;
- institutional maintainer;
- source of scientific truth;
- substitute for replay, tests, evidence packs, or human review;
- executor of unsafe secret-handling workflows.

## Current integration thread

```text
PR_7: Add Codex web overview documentation
STATUS: OPEN_MERGEABLE
FIX_APPLIED: root-relative Codex links replaced by absolute developer documentation URLs
RISK_REDUCED: broken GitHub Markdown navigation
NEXT_GATE: review, merge, then index from README or docs index
```

## Next recommended integrations

### 1. GitHub review command layer

Add a small guide describing how to trigger Codex reviews and what review comments are allowed to change.

Suggested file:

```text
docs/CODEX_GITHUB_REVIEW_WORKFLOW.md
```

Minimum contents:

```text
@codex review      -> ask for review
@codex address ... -> ask for proposed repair
human review       -> final acceptance gate
```

### 2. Evidence pack bridge

Add a lightweight bridge from pull requests to evidence packs.

Suggested file:

```text
docs/PR_EVIDENCE_PACK_CONTRACT.md
```

Minimum receipt fields:

```text
repo, branch, commit_sha, files_changed, tests_run, review_comments, decision, timestamp
```

### 3. GTHDL-on-GHDL research bridge

Create a separate future track for translating MatVerse theoretical operators into HDL simulation artifacts.

Suggested repository or folder:

```text
matverse-gthdl-hdl/
```

Minimum modules:

```text
omega_gate.vhd
psi_metric.vhd
cvar_guard.vhd
replay_checker.vhd
ledger_register.vhd
```

Status remains `STAGE_OPPORTUNITY` until VHDL modules, testbenches, GHDL simulation logs, and replay receipts exist.

## Decision policy

```text
PASS       = integration exists, is inspectable, and has working evidence
PASS_LOCAL = local/repository evidence exists, but no independent validation
STAGE      = implementation path exists, but evidence is incomplete
HOLD       = claim is plausible but not supported by inspectable evidence
BLOCK      = claim conflicts with evidence, policy, or security constraints
```

## Minimal checklist before merging integration PRs

- [ ] Links resolve from GitHub.
- [ ] No secrets, tokens, private keys, or credentials are present.
- [ ] Agent/tool names are not listed as authors, owners, or maintainers.
- [ ] Claims are classified as `PASS`, `PASS_LOCAL`, `STAGE`, `HOLD`, or `BLOCK`.
- [ ] A human/institutional responsibility boundary is explicit.
- [ ] Test or validation status is stated honestly.

## Summary

The integration layer should make the repository easier to operate without inflating claims. GitHub provides provenance, Codex accelerates execution, automated review reduces defects, and MatVerse governance decides what is admissible.

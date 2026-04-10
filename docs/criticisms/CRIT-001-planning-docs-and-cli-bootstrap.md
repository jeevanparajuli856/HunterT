# CRIT-001: Review of Sprint Plan and CLI Bootstrap ADRs

> **Date**: 2026-04-10
> **Reviewer**: Critic
> **Scope**:
> - `docs/plans/current-sprint.md`
> - `docs/architecture/decisions/ADR-001-go-cli-python-runtime.md`
> - `docs/architecture/decisions/ADR-002-lstm-primary-product-model.md`
> - `docs/architecture/decisions/ADR-003-phased-repo-reframe.md`
> - `docs/product/cli-v1-spec.md`
> **Verdict**: APPROVED

## Findings

No blocking issues found after the Python module invocation was clarified to use `PYTHONPATH=python python3 -m huntert_runtime`.

## Warnings

### WARN-001: Keep the first runtime slice narrow

- The current repo does not yet contain a live HTTP enumeration runtime suitable for direct product exposure.
- The executor should keep the first CLI slice limited to `version` and `attack run --dry-run` unless a real runtime path is implemented in the same change.

### WARN-002: Do not move research directories in the same executor slice

- `lstm_pipeline/` is still the active source of truth for training and attack logic.
- Moving research directories before the new CLI slice is stable would add unnecessary breakage risk.

## Recommendation

Proceed to execution with TASK-002 and TASK-003 as the first slice. Treat full repo relocation and broader product docs as follow-on work after the CLI scaffold and subprocess bridge are building cleanly.

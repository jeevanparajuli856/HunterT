# ADR-004: Archive Top-Level Historical Documents Before Moving Live Code

> **Status**: PROPOSED
> **Date**: 2026-04-10
> **Owner**: Planner

## Context

The repo root still contained several historical non-code artifacts:

- `Next_Plan.md`
- `research_plan.md`
- `LSTM_ResearchPaper_CLEAN.md`
- `LSTM.pdf`
- `ExperimentLog/`

These files are useful reference material, but they make the root of the repo look more scattered than the current product and research code actually require.

At the same time, moving live code directories such as `lstm_pipeline/` or `LSTM_Research/` is still too risky in the current phase because those paths are active in commands, imports, and docs.

## Decision

Perform a low-risk archive cleanup before deeper structural moves:

- move top-level historical plans into `docs/archive/research-plans/`
- move experiment logs into `docs/archive/experiment-logs/`
- move paper artifacts into `docs/archive/papers/`
- update any affected references in docs
- leave live code, datasets, and active research directories at their current paths

## Consequences

### Positive

- reduces clutter at the repo root
- makes product and active research areas easier to scan
- preserves historical context without breaking active code paths

### Negative

- adds another documented area that contributors need to understand
- requires a few doc references to be updated when archived files move

## Implementation Notes

This change is intentionally limited to non-code artifacts. The next major reframe step can tackle live research directory moves only after compatibility work is planned.

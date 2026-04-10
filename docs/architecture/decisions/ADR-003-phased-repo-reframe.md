# ADR-003: Reframe the Repo Around `product/huntert/` Without Moving Research Directories

> **Status**: PROPOSED
> **Date**: 2026-04-10
> **Owner**: Planner

## Context

HunterT still depends on the current research paths for training, evaluation, saved checkpoints, and source artifacts:

- `lstm_pipeline/`
- `transformer_pipeline/`
- `transformer_pipelineV2/`
- `LSTM_Research/`

At the same time, the release product code should no longer be described as living at the repo root. The actual product workspace already exists at `product/huntert/`.

## Decision

Use a phased reframe with a hard product boundary:

- `product/huntert/` is the sole active product workspace
- `lstm_pipeline/`, `transformer_pipeline/`, `transformer_pipelineV2/`, and `LSTM_Research/` stay at their current paths in this phase
- research assets may be copied into product runtime bundles, but the research directories themselves are not moved
- active docs must distinguish product code from research code and from archives

## Consequences

### Positive

- reduces ambiguity about where release code belongs
- preserves reproducibility for the maintained LSTM path
- avoids breaking research commands while product code matures

### Negative

- leaves the repo mixed between product, research, and archive areas
- requires bundle/export steps when product code needs research artifacts

## Implementation Notes

This phase should not relocate the research directories themselves. The product runtime should consume curated packaged artifacts under `product/huntert/` instead.

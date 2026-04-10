# ADR-005: Ship HunterT with a Curated Default Runtime Bundle

> **Status**: PROPOSED
> **Date**: 2026-04-10
> **Owner**: Planner

## Context

The current dry-run path still points directly at research assets under `lstm_pipeline/` and `LSTM_Research/`. That is acceptable for bootstrap validation, but it is not a good release shape for a launchable CLI.

The next release needs a stable default model, a stable default wordlist, and a packaged vocabulary artifact so runtime behavior does not depend on reconstructing research state on every launch.

## Decision

Ship the live HunterT release with a curated default runtime bundle under `product/huntert/runtime/`.

The default release bundle should be sourced from:

- checkpoint: `lstm_pipeline/saved_models/model_MD10_MF5_es128_nl2_dr0.2_loss3.319183.pt`
- wordlist: `LSTM_Research/chosen_wordlists/big_wfuzz.txt`

The bundle must include:

- the checkpoint
- a serialized runtime vocabulary artifact
- a manifest describing bundle id, source assets, backend family, and runtime defaults
- a packaged default wordlist

## Consequences

### Positive

- makes the release self-contained
- reduces operator dependence on scattered research paths
- creates a clear compatibility target for the Python sidecar

### Negative

- adds an export step to the release workflow
- requires careful manifesting so the bundle remains reproducible

## Implementation Notes

The runtime bundle is a product artifact. It may be generated from research assets, but the live product should consume the packaged bundle rather than the raw research paths at runtime.

# HunterT Repo Map

## Active Product Workspace

Release-oriented product code lives here:

- `product/huntert/cmd/huntert/`
- `product/huntert/internal/`
- `product/huntert/python/huntert_runtime/`

Planned product runtime assets for the next live phase:

- `product/huntert/runtime/models/default/`
- `product/huntert/runtime/wordlists/`
- `product/huntert/runtime/manifests/`
- `product/huntert/configs/`

## Active Research

Maintained model path:

- `lstm_pipeline/`

Preserved research branches:

- `transformer_pipeline/`
- `transformer_pipelineV2/`

Research data and wordlists:

- `LSTM_Research/`

## Support Material

- `infra/`
- `infra_T_V100/`
- `scripts/`

## Archived History

- `docs/archive/research-plans/`
- `docs/archive/experiment-logs/`
- `docs/archive/papers/`

## Current Rule

In this phase:

- product code belongs under `product/huntert/`
- research directories stay at their current paths
- packaged runtime artifacts may be copied from research into the product runtime bundle
- active docs should not describe root-level `cmd/`, `internal/`, or `python/` directories as the current product surface

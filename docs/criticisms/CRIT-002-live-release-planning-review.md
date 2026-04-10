# CRIT-002: Review of the Live Release Planning Package

> **Date**: 2026-04-10
> **Reviewer**: Critic
> **Scope**:
> - `docs/plans/current-sprint.md`
> - `docs/architecture/decisions/ADR-001-go-cli-python-runtime.md`
> - `docs/architecture/decisions/ADR-003-phased-repo-reframe.md`
> - `docs/architecture/decisions/ADR-005-curated-default-runtime-bundle.md`
> - `docs/product/cli-v1-spec.md`
> - `docs/product/runtime-setup.md`
> - `docs/overview/repo-map.md`
> **Verdict**: APPROVED WITH WARNINGS

## Findings

No blocking inconsistencies found in the live-phase planning package.

The updated docs correctly:

- treat `product/huntert/` as the active product root
- keep `lstm_pipeline/`, `transformer_pipeline/`, `transformer_pipelineV2/`, and `LSTM_Research/` in place for this phase
- move the product design from a dry-run subprocess bridge to a Go live engine plus Python prediction sidecar
- define a bundled default runtime based on the selected checkpoint and wordlist

## Warnings

### WARN-001: Do not make the release depend on raw research paths at runtime

- the bundle exporter may source artifacts from research directories
- the launchable CLI should use packaged assets under `product/huntert/runtime/` once the bundle exists

### WARN-002: Do not combine the product-root cleanup, bundle exporter, sidecar, and full HTTP engine into one opaque change

- the sprint is live-release oriented, but the first executor slice still needs to stay reversible
- bundle verification and sidecar loading should land before the full attack loop

### WARN-003: Keep docs explicit about current versus planned behavior

- the current implemented CLI is still the bootstrap slice
- the live release spec should remain future-facing until executor work lands

## Recommendation

Proceed with the live phase using this order:

1. normalize `product/huntert/` as the only product root
2. package the default runtime bundle
3. add bundle inspection and sidecar loading
4. implement the live HTTP engine

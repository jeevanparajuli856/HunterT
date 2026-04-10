# ADR-001: Adopt a Go CLI Front End with a Python Prediction Backend

> **Status**: PROPOSED
> **Date**: 2026-04-10
> **Owner**: Planner

## Context

HunterT remains a Python-first research repo, but the release product needs a fast operator-facing CLI.

The first bootstrap slice already proved that a Go CLI can call Python-backed LSTM functionality. The next release needs to keep that split while moving past a one-shot dry-run bridge into a real live runtime architecture.

The current active product workspace is `product/huntert/`.

## Decision

Adopt a two-layer product architecture rooted at `product/huntert/`:

- Go owns the public `huntert` CLI
- Go owns the live HTTP attack engine, concurrency, output, and resume behavior
- Python remains the LSTM runtime backend
- Python runs as a long-lived stdio JSON prediction sidecar during live attacks
- the product ships with a curated runtime bundle so Python loads packaged artifacts instead of raw research paths at runtime

The active product workspace is:

- `product/huntert/cmd/huntert/`
- `product/huntert/internal/`
- `product/huntert/python/huntert_runtime/`

## Consequences

### Positive

- keeps operator UX and attack throughput in Go
- reuses the maintained LSTM implementation instead of forcing a risky model rewrite
- avoids repeated Python startup during live attacks
- creates a stable boundary for future backend changes

### Negative

- still requires a mixed Go and Python environment for development
- adds a sidecar protocol that must stay compatible
- requires explicit bundle packaging so runtime inputs stay reproducible

## Implementation Notes

The initial one-shot dry-run subprocess path was a bootstrap step, not the final runtime shape.

The live release boundary should expose at least:

- `inspect_bundle`
- `load_bundle`
- `predict_next`
- `shutdown`

The Go CLI should treat sidecar failures as product runtime failures with clear exit behavior.

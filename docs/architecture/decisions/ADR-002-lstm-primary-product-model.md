# ADR-002: Standardize on the LSTM Path as the Primary Product Model

> **Status**: PROPOSED
> **Date**: 2026-04-10
> **Owner**: Planner

## Context

HunterT contains:

- `lstm_pipeline/`
- `transformer_pipeline/`
- `transformer_pipelineV2/`

The user has decided that the CLI product direction should be LSTM-led because the current next-token prediction workflow is better aligned with the immediate directory-enumeration tool goal.

## Decision

For product work:

- `lstm_pipeline/` is the primary maintained model path
- product runtime integration should reuse LSTM code first
- transformer branches remain in the repo as research material and secondary experiments
- product docs must describe transformer work as preserved research, not the current product engine

## Consequences

### Positive

- aligns product scope with the most stable implementation
- reduces architecture churn during CLI bootstrap
- keeps the first product slice grounded in working code

### Negative

- defers direct productization of transformer research
- requires docs to clearly separate product direction from research history

## Implementation Notes

The first Python backend should call existing LSTM modules rather than copying attack logic into a new model stack.

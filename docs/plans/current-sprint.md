# HunterT Sprint Plan

> **Sprint Goal**: Turn the current dry-run-only HunterT scaffold into a launchable live directory enumerator release rooted at `product/huntert/`.
> **Status**: IN PROGRESS
> **Last Updated**: 2026-04-10
> **Updated By**: Planner

---

## Current Reality

Grounding facts from the repo today:

- active product code already lives under `product/huntert/`
- current product commands are limited to `huntert version` and `huntert attack run --dry-run`
- `lstm_pipeline/` remains the source of truth for model-backed logic and saved checkpoints
- `transformer_pipeline/` and `transformer_pipelineV2/` remain preserved research branches
- `LSTM_Research/` still contains the default wordlist source material

This sprint supersedes the earlier dry-run bootstrap plan. It does not claim the live release is already implemented.

---

## Sprint Outcomes

This sprint is successful when:

- `product/huntert/` is treated as the only active product root in code and docs
- HunterT has a real dirbuster-style live HTTP enumeration plan, not a dry-run-only CLI plan
- the product ships with a curated default runtime bundle instead of requiring raw research paths at operator runtime
- Go owns the live attack engine and Python becomes a long-lived LSTM prediction sidecar
- research directories stay at their current paths in this phase

---

## Active Tasks

### TASK-101: Freeze the product root at `product/huntert/`
- **Status**: READY
- **Assignee**: Executor
- **Target**:
  - `product/huntert/go.mod`
  - `product/huntert/cmd/huntert/`
  - `product/huntert/internal/`
  - `product/huntert/python/huntert_runtime/`
  - docs that still reference root-level product code
- **Description**: Treat `product/huntert/` as the sole active product workspace and remove stale documentation assumptions that the Go and Python product code live at the repo root.
- **Acceptance Criteria**:
  - [ ] executor confirms all product build and test commands are run from `product/huntert/`
  - [ ] no active docs describe `cmd/`, `internal/`, or `python/` at the repo root as the product surface
  - [ ] research directories remain untouched
- **Dependencies**: none

### TASK-102: Package a curated default HunterT runtime bundle
- **Status**: READY
- **Assignee**: Executor
- **Target**:
  - `product/huntert/runtime/models/default/`
  - `product/huntert/runtime/wordlists/`
  - `product/huntert/runtime/manifests/`
  - `product/huntert/configs/default.yaml`
  - any exporter script or release helper needed under `scripts/` or `product/huntert/`
- **Description**: Export a curated runtime bundle for the live release so operators do not depend on raw `lstm_pipeline/` or `LSTM_Research/` paths at runtime.
- **Bundle Defaults**:
  - checkpoint: `lstm_pipeline/saved_models/model_MD10_MF5_es128_nl2_dr0.2_loss3.319183.pt`
  - wordlist source: `LSTM_Research/chosen_wordlists/big_wfuzz.txt`
  - backend family: `python-lstm`
- **Acceptance Criteria**:
  - [ ] a default bundle manifest identifies the packaged checkpoint, vocabulary artifact, and wordlist
  - [ ] the packaged runtime can be inspected without touching research paths at runtime
  - [ ] the exporter is explicit about its research source inputs
- **Dependencies**: TASK-101

### TASK-103: Replace the one-shot backend bridge with a long-lived prediction sidecar
- **Status**: READY
- **Assignee**: Executor
- **Target**:
  - `product/huntert/python/huntert_runtime/`
  - `product/huntert/internal/pythonbridge/`
  - protocol docs and tests in the product workspace
- **Description**: Move from one-off CLI subprocess execution to a long-lived stdio JSON sidecar that loads the bundled LSTM model once and serves prediction requests during an attack run.
- **Required Protocol Operations**:
  - `inspect_bundle`
  - `load_bundle`
  - `predict_next`
  - `shutdown`
- **Acceptance Criteria**:
  - [ ] Python can load the default runtime bundle once and keep it in memory
  - [ ] Go can maintain one sidecar process through an attack run
  - [ ] invalid bundle, invalid protocol message, and sidecar startup failures are handled clearly
- **Dependencies**: TASK-102

### TASK-104: Implement the live Go attack engine
- **Status**: READY
- **Assignee**: Executor
- **Target**:
  - `product/huntert/internal/cli/`
  - `product/huntert/internal/engine/`
  - `product/huntert/internal/httpclient/`
  - `product/huntert/internal/queue/`
  - `product/huntert/internal/output/`
- **Description**: Replace dry-run-only behavior with a real dirbuster-style live enumerator that performs HTTP requests in Go and asks the Python sidecar for path predictions.
- **Minimum Command Surface**:
  - `huntert version`
  - `huntert attack run`
  - `huntert models inspect`
  - `huntert bundle verify`
- **Minimum Attack Flags**:
  - `--target`
  - `--threads`
  - `--timeout`
  - `--rate-limit`
  - `--header`
  - `--user-agent`
  - `--method`
  - `--follow-redirects`
  - `--insecure`
  - `--extensions`
  - `--max-depth`
  - `--prediction-limit`
  - `--max-requests`
  - `--status-include`
  - `--status-exclude`
  - `--output-dir`
  - `--output-format`
  - `--resume`
  - `--dry-run`
  - `--model-bundle`
- **Acceptance Criteria**:
  - [ ] Go issues live HTTP requests and applies concurrency, rate limiting, and status filters
  - [ ] interesting responses enqueue deeper model-guided candidates
  - [ ] default interesting statuses are `200,204,301,302,307,308,401,403`
  - [ ] results and resumable state are persisted under the product output path
- **Dependencies**: TASK-103

### TASK-105: Update and close stale documentation
- **Status**: READY
- **Assignee**: Executor
- **Target**:
  - `docs/overview/repo-map.md`
  - `docs/product/cli-v1-spec.md`
  - `docs/product/runtime-setup.md`
  - any additional docs still describing the dry-run-only slice as current direction
- **Description**: Keep the repo documentation aligned with the live release plan and the `product/huntert/` product root.
- **Acceptance Criteria**:
  - [ ] docs distinguish current implemented behavior from planned live release behavior
  - [ ] stale root-path references are removed from active docs
  - [ ] no docs imply that research directories move in this phase
- **Dependencies**: TASK-101, TASK-102, TASK-103, TASK-104

---

## Executor Slice

The intended first executor slice for the live phase is:

1. normalize `product/huntert/` as the only product root
2. package the curated default runtime bundle
3. add `bundle verify` and `models inspect`
4. replace the one-shot Python invocation with the long-lived sidecar load and inspect path

Why this slice first:

- it is small and reversible
- it removes runtime dependence on scattered research paths before the live engine lands
- it gives the HTTP engine a stable bundle and prediction interface instead of building everything at once

The full live HTTP engine should start only after this slice is building and testable.

# HunterT Evaluation Log

## EVAL-001: Sprint planning for repo reframe and CLI bootstrap
- **Date**: 2026-04-10
- **Subject**: planning
- **Files Reviewed**:
  - `lstm_pipeline/main.py`
  - `lstm_pipeline/src/attacks.py`
  - `lstm_pipeline/src/inference.py`
  - `transformer_pipeline/main.py`
  - `transformer_pipelineV2/main.py`
  - `AGENTS.md`
  - `CLAUDE.md`
- **Findings**:
  - `lstm_pipeline/` is the only current implementation suitable to anchor the first product slice
  - transformer work is useful research context but should not drive the first CLI build
  - a full directory move this sprint would create unnecessary breakage risk
  - a Go CLI plus Python backend subprocess boundary is the smallest realistic product step
- **Resolution**: OPEN

## EVAL-002: Critic review of planning package
- **Date**: 2026-04-10
- **Subject**: critique
- **Files Reviewed**:
  - `docs/plans/current-sprint.md`
  - `docs/architecture/decisions/ADR-001-go-cli-python-runtime.md`
  - `docs/architecture/decisions/ADR-002-lstm-primary-product-model.md`
  - `docs/architecture/decisions/ADR-003-phased-repo-reframe.md`
  - `docs/product/cli-v1-spec.md`
- **Findings**:
  - planning package is approved for execution
  - the Python backend invocation must use `PYTHONPATH=python python3 -m huntert_runtime`
  - the first executor slice should stay narrow and avoid moving research directories
- **Resolution**: RESOLVED

## EVAL-003: First CLI slice verification
- **Date**: 2026-04-10
- **Subject**: execution
- **Files Reviewed**:
  - `go.mod`
  - `cmd/huntert/main.go`
  - `internal/cli/root.go`
  - `internal/cli/attack.go`
  - `internal/config/config.go`
  - `internal/config/config_test.go`
  - `internal/output/render.go`
  - `internal/pythonbridge/runner.go`
  - `python/huntert_runtime/__main__.py`
  - `python/huntert_runtime/cli.py`
  - `python/huntert_runtime/attack_runner.py`
  - `python/huntert_runtime/lstm_adapter.py`
  - `README.md`
  - `docs/product/runtime-setup.md`
- **Findings**:
  - `go test ./...` passed after formatting the Go files
  - `go build ./cmd/huntert` succeeded
  - `huntert version` executed successfully
  - `huntert attack run --dry-run` successfully invoked the Python backend and rendered a dry-run response
  - `PYTHONPATH=python python3 -m huntert_runtime --help` succeeded
  - `PYTHONPATH=python python3 -m huntert_runtime attack run --dry-run ...` succeeded against a real saved LSTM checkpoint and wordlist
- **Resolution**: RESOLVED

## EVAL-004: Safe archive cleanup for scattered top-level artifacts
- **Date**: 2026-04-10
- **Subject**: execution
- **Files Reviewed**:
  - `README.md`
  - `docs/overview/repo-map.md`
  - `docs/plans/current-sprint.md`
  - `docs/archive/README.md`
  - `docs/architecture/decisions/ADR-004-archive-top-level-history.md`
  - `transformer_pipelineV2/README.md`
- **Findings**:
  - non-code historical artifacts were moved out of the repo root into `docs/archive/`
  - active code and dataset directories were intentionally left at their current paths
  - the one known reference to `Next_Plan.md` was updated to the archived location
- **Resolution**: RESOLVED

## EVAL-005: Live release planning package refresh
- **Date**: 2026-04-10
- **Subject**: planning
- **Files Reviewed**:
  - `docs/plans/current-sprint.md`
  - `docs/architecture/decisions/ADR-001-go-cli-python-runtime.md`
  - `docs/architecture/decisions/ADR-003-phased-repo-reframe.md`
  - `docs/architecture/decisions/ADR-005-curated-default-runtime-bundle.md`
  - `docs/product/cli-v1-spec.md`
  - `docs/product/runtime-setup.md`
  - `docs/overview/repo-map.md`
  - `docs/criticisms/CRIT-002-live-release-planning-review.md`
- **Findings**:
  - the dry-run bootstrap plan is superseded by a live release plan centered on `product/huntert/`
  - active product docs now treat `product/huntert/` as the product root instead of describing root-level product directories
  - the next release is defined as a Go live HTTP engine plus a long-lived Python prediction sidecar
  - the live release plan packages a curated default runtime bundle from the selected LSTM checkpoint and `big_wfuzz.txt`
  - research directories remain in place for this phase
- **Resolution**: RESOLVED

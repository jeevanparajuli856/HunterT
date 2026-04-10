# HunterT

HunterT is a directory-enumeration project moving from a research-first Python codebase toward a product-facing CLI workflow.

Current product direction:
- `lstm_pipeline/` is the primary maintained model path
- `transformer_pipeline/` and `transformer_pipelineV2/` are preserved research branches
- the first product slice is a Go CLI named `huntert`
- the CLI currently uses a Python backend for LSTM-grounded runtime behavior

## Repo Layout

Active product slice:
- `cmd/huntert/`: Go CLI entrypoint
- `internal/`: Go CLI internals, config, output, and Python bridge
- `python/huntert_runtime/`: Python backend used by the CLI

Current research implementation:
- `lstm_pipeline/`: primary training, evaluation, and reusable attack logic
- `transformer_pipeline/`: first transformer research branch
- `transformer_pipelineV2/`: second transformer research branch
- `LSTM_Research/`: datasets, notebooks, and wordlists from the AISec'24 reproduction work

Planning and architecture:
- `docs/plans/current-sprint.md`
- `docs/architecture/decisions/`
- `docs/product/`
- `docs/overview/repo-map.md`
- `docs/archive/`

## Environment

Python:

```bash
source .venv/bin/activate
python3 --version
```

Go:

```bash
go version
```

If Go is installed but not on `PATH`, add the standard install location first:

```bash
export PATH=/usr/local/go/bin:$PATH
```

## First Product Slice

The current CLI slice supports:
- `huntert version`
- `huntert attack run --dry-run`

The backend contract is:

```bash
PYTHONPATH=python python3 -m huntert_runtime attack run ...
```

## Build and Run

Build the CLI:

```bash
go build -o huntert ./cmd/huntert
```

Show version:

```bash
./huntert version
./huntert version --output json
```

Dry-run an attack request through the Python backend:

```bash
source .venv/bin/activate
./huntert attack run \
  --dry-run \
  --target https://example.com/admin/login \
  --model lstm_pipeline/saved_models/model_MD10_MF5_es128_nl2_dr0.2_loss3.319183.pt \
  --wordlist LSTM_Research/chosen_wordlists/big_wfuzz.txt
```

## Research Commands

LSTM pipeline:

```bash
cd lstm_pipeline
python3 main.py train
python3 main.py evaluate
python3 plot_tables.py
```

Transformer research:

```bash
cd transformer_pipeline
python3 main.py train
python3 main.py evaluate

cd ../transformer_pipelineV2
python3 main.py train-diagnostic
python3 main.py evaluate
```

## Notes

- The Go CLI is intentionally narrow in the first slice.
- Non-dry-run live attack execution is not implemented yet.
- Research directories remain at their current paths in this phase to avoid breaking the existing LSTM workflow.
- Historical plans, experiment logs, and paper artifacts now live under `docs/archive/` instead of the repo root.

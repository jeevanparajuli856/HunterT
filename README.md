# HunterT

HunterT is a Go CLI for directory enumeration backed by a packaged Python LSTM runtime. Product code is separated from research code: the operator-facing CLI lives under `product/huntert/`, while training, experiments, and source datasets stay in the repo root research directories.

## Repo Layout

Product:
- `product/huntert/cmd/huntert/`
- `product/huntert/internal/`
- `product/huntert/python/huntert_runtime/`
- `product/huntert/runtime/bundles/default/`

Research:
- `lstm_pipeline/`
- `transformer_pipeline/`
- `transformer_pipelineV2/`
- `LSTM_Research/`
- `infra/`
- `infra_T_V100/`
- `scripts/`

Docs:
- `docs/overview/repo-map.md`
- `docs/product/`
- `docs/architecture/decisions/`
- `docs/plans/current-sprint.md`

## Environment

```bash
source .venv/bin/activate
python3 --version
export PATH=/usr/local/go/bin:$PATH
go version
```

## Build And Run

```bash
cd product/huntert
/usr/local/go/bin/go test ./...
/usr/local/go/bin/go build -o huntert ./cmd/huntert
```

```bash
./huntert version
./huntert bundle verify
./huntert models inspect
./huntert attack run --dry-run --target https://example.com
./huntert attack run --target https://example.com --max-requests 100 --threads 10
```

## Runtime Bundle

The default product bundle is already packaged under `product/huntert/runtime/bundles/default/`. At runtime, the CLI uses the packaged checkpoint, vocabulary, and wordlist from that bundle rather than reading raw research assets directly.

To rebuild the default bundle from the research sources:

```bash
source .venv/bin/activate
PYTHONPATH=product/huntert/python python3 -m huntert_runtime bundle export-default \
  --bundle product/huntert/runtime/bundles/default
```

Bundle source inputs:
- `lstm_pipeline/saved_models/model_MD10_MF5_es128_nl2_dr0.2_loss3.319183.pt`
- `LSTM_Research/chosen_wordlists/big_wfuzz.txt`

## Research Commands

```bash
cd lstm_pipeline
python3 main.py train
python3 main.py evaluate
python3 plot_tables.py
```

```bash
cd transformer_pipeline
python3 main.py train
python3 main.py evaluate

cd ../transformer_pipelineV2
python3 main.py train-diagnostic
python3 main.py evaluate
```

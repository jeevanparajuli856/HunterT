# HunterT Runtime Setup

This document covers the current HunterT product workspace and the setup expected for the next live release phase.

## Current Reality

- active product code lives under `product/huntert/`
- the current implemented CLI is still the dry-run bootstrap slice
- the live runtime bundle described in the planning docs is not yet packaged

## Requirements

- Linux or macOS shell
- Go 1.22+
- Python 3.10+
- the repo root `.venv`

## Enter the Product Workspace

```bash
cd product/huntert
```

## Python Setup

Activate the repository virtual environment from the product workspace:

```bash
source ../../.venv/bin/activate
```

Sanity check the current backend module:

```bash
PYTHONPATH=python python3 -m huntert_runtime --help
```

## Go Setup

Confirm Go is available:

```bash
go version
```

If `go` is installed under `/usr/local/go/bin` but not on `PATH`:

```bash
export PATH=/usr/local/go/bin:$PATH
```

## Current Bootstrap Build

```bash
go build -o huntert ./cmd/huntert
go test ./...
```

## Current Bootstrap Commands

Version:

```bash
./huntert version
./huntert version --output json
```

Dry-run validation against research-source artifacts:

```bash
source ../../.venv/bin/activate
./huntert attack run \
  --dry-run \
  --target https://example.com/admin/login \
  --model ../../lstm_pipeline/saved_models/model_MD10_MF5_es128_nl2_dr0.2_loss3.319183.pt \
  --wordlist ../../LSTM_Research/chosen_wordlists/big_wfuzz.txt
```

## Next Live Phase Expectations

The live release should shift runtime usage to packaged product assets under:

- `product/huntert/runtime/models/default/`
- `product/huntert/runtime/wordlists/`
- `product/huntert/runtime/manifests/`

The live release should no longer require operators to pass research paths for the default runtime.

## Current Limits

- the live dirbuster-style engine is not implemented yet
- the long-lived Python prediction sidecar is not implemented yet
- the curated runtime bundle is planned but not yet packaged
- research directories remain at their current paths in this phase

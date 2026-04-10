# HunterT

HunterT is a directory enumeration CLI built as a Go product with a packaged Python LSTM runtime.

The product lives in `product/huntert/`. The research work is preserved in `Research/`, but the top-level repo is now centered on shipping and operating the HunterT CLI.

## Product

HunterT currently provides:

- a Go CLI entrypoint
- a Go HTTP enumeration engine
- a long-lived Python LSTM sidecar for model prediction
- a packaged default runtime bundle with model, vocab, and wordlist
- bundle verification with checksum validation for the packaged model

Main product paths:

- `product/huntert/cmd/huntert/`
- `product/huntert/internal/`
- `product/huntert/python/huntert_runtime/`
- `product/huntert/runtime/bundles/default/`

## Quick Start

```bash
source .venv/bin/activate
export PATH=/usr/local/go/bin:$PATH

cd product/huntert
/usr/local/go/bin/go test ./...
/usr/local/go/bin/go build -o huntert ./cmd/huntert
```

## Run

```bash
cd product/huntert

./huntert version
./huntert bundle verify --model-bundle runtime/bundles/default
./huntert models inspect --model-bundle runtime/bundles/default

./huntert attack run --dry-run --target https://example.com --output json
./huntert attack run --target https://example.com --threads 10 --max-requests 100
```

## Runtime Bundle

HunterT ships with a packaged default bundle under `product/huntert/runtime/bundles/default/`.

That bundle contains:

- `model.pt`
- `vocab.json`
- `wordlist.txt`
- `manifest.json`

The default packaged model is:

- checkpoint: `model_MD10_MF5_es128_nl2_dr0.2_loss3.319183.pt`
- sha256: `03e8033274587807a55064bea29bba48943f6df2972771e959933f14eff11981`

`huntert bundle verify` validates that the packaged `model.pt` matches the checksum recorded in the bundle manifest.

To rebuild the default bundle from the research assets:

```bash
source .venv/bin/activate
PYTHONPATH=product/huntert/python python3 -m huntert_runtime bundle export-default \
  --bundle product/huntert/runtime/bundles/default
```

## Product Notes

- Product code is intentionally separated from research assets.
- The CLI runs from `product/huntert/`, not from `Research/`.
- The packaged bundle is meant to be the runtime dependency, not raw research checkpoints.
- The current reference config is `product/huntert/configs/default.yaml`.

## Research Brief

HunterT comes from our research on language-model-guided directory enumeration. We evaluated LSTM and transformer approaches and are keeping LSTM as the current product path. The research code, datasets, notebooks, and historical experiments remain under `Research/` for reproducibility, but they are not the operator-facing product surface.

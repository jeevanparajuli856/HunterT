# HunterT

HunterT is a directory enumeration CLI built as a Go product with a packaged Python LSTM runtime.

The product lives in `product/huntert/`, and the top-level repo is centered on shipping and operating the HunterT CLI.

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
- `product/huntert/install.sh`
- `product/huntert/Makefile`

## Requirements

To build or install HunterT from this repo:

- Linux or macOS shell
- Go 1.22+
- Python 3.10+
- the repo root `.venv`

Recommended setup:

```bash
source .venv/bin/activate
export PATH=/usr/local/go/bin:$PATH
```

## Install From A GitHub Clone

```bash
git clone <your-github-url> HunterT
cd HunterT
./product/huntert/install.sh
```

The installer builds the product binary, creates a `HunterT` launcher in `~/.local/bin`, and also creates a lowercase `huntert` alias.

After install:

```bash
HunterT version
HunterT bundle verify --model-bundle runtime/bundles/default
```

If `~/.local/bin` is not already in `PATH`, add:

```bash
export PATH="$HOME/.local/bin:$PATH"
```

## How HunterT Works

Briefly:

- the Go CLI handles commands, HTTP requests, concurrency, recursion, output files, and result formatting
- the Python sidecar loads the packaged LSTM model once and returns ranked next-token predictions
- the runtime bundle provides the packaged `model.pt`, `vocab.json`, and `wordlist.txt`
- HunterT seeds guesses from both the LSTM predictions and the bundled wordlist, then requests those paths against the target
- interesting responses such as `200`, `401`, and `403` are reported and can trigger deeper recursion

The active product runtime depends on the packaged bundle, not on source training assets.

## Build From Source

```bash
cd product/huntert
/usr/local/go/bin/go test ./...
/usr/local/go/bin/go build -o HunterT ./cmd/huntert
```

## Run

```bash
cd product/huntert

./HunterT version
./HunterT bundle verify --model-bundle runtime/bundles/default
./HunterT models inspect --model-bundle runtime/bundles/default

./HunterT attack run --dry-run --target https://example.com --output json
./HunterT attack run --target https://example.com --threads 10 --max-requests 100
./HunterT attack run --target https://example.com --output text --findings-only
```

Running `HunterT` with no arguments shows the CLI help plus a rotating ASCII banner with current runtime details. Set `HUNTERT_NO_BANNER=1` if you want a quiet root help screen.

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

The default packaged wordlist is:

- bundled runtime file: `product/huntert/runtime/bundles/default/wordlist.txt`
- source wordlist: `big_wfuzz.txt`
- current packaged size: `3024` entries

`HunterT bundle verify` validates that the packaged `model.pt` matches the checksum recorded in the bundle manifest.

For flat text output, `HunterT attack run --output text --findings-only` prints only interesting findings as:

```text
https://target.example/admin 200
https://target.example/login 403
```

To rebuild the default bundle:

```bash
source .venv/bin/activate
PYTHONPATH=product/huntert/python python3 -m huntert_runtime bundle export-default \
  --bundle product/huntert/runtime/bundles/default
```

## Change The Wordlist

HunterT does not read the source wordlist directly during normal runtime. It reads `wordlist.txt` from the selected runtime bundle.

If you want a different wordlist, rebuild a bundle with `--wordlist` and then run HunterT against that bundle.

Replace the default bundled wordlist in place:

```bash
source .venv/bin/activate
PYTHONPATH=product/huntert/python python3 -m huntert_runtime bundle export-default \
  --bundle product/huntert/runtime/bundles/default \
  --wordlist /absolute/path/to/your_wordlist.txt
```

Or create a separate custom bundle:

```bash
source .venv/bin/activate
PYTHONPATH=product/huntert/python python3 -m huntert_runtime bundle export-default \
  --bundle product/huntert/runtime/bundles/custom \
  --wordlist /absolute/path/to/your_wordlist.txt

HunterT bundle verify --model-bundle product/huntert/runtime/bundles/custom
HunterT attack run --target https://example.com --model-bundle product/huntert/runtime/bundles/custom
```

What changes when you swap the wordlist:

- the packaged `wordlist.txt` changes
- the LSTM model and vocab stay the same unless you also choose a different model or training dataset
- runtime enumeration uses the new bundled wordlist on the next run

## Product Notes

- The CLI runs from `product/huntert/`.
- The packaged bundle is the runtime dependency used by the product.
- The current reference config is `product/huntert/configs/default.yaml`.
- The installer wrapper exports `HUNTERT_REPO_ROOT` and `HUNTERT_PRODUCT_ROOT` so the command works from outside the repo checkout.

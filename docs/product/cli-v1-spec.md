# HunterT CLI v1 Live Release Spec

## Purpose

Define the next HunterT release as a real live directory enumerator and supersede the earlier dry-run-only bootstrap spec.

This document describes the intended release behavior. It does not claim these live capabilities are already implemented.

## Current Reality

As of 2026-04-10:

- active product code lives under `product/huntert/`
- the current CLI supports `huntert version` and `huntert attack run --dry-run`
- runtime inputs still come from research paths during dry-run validation

## Release Shape

The v1 live release is:

- a Go CLI named `huntert`
- a Go-owned live HTTP enumeration engine
- a long-lived Python prediction sidecar for LSTM-backed next-token scoring
- a curated default runtime bundle shipped under `product/huntert/runtime/`

## Product Root

All active product code for this release belongs under:

- `product/huntert/cmd/huntert/`
- `product/huntert/internal/`
- `product/huntert/python/huntert_runtime/`

Runtime assets for the release belong under:

- `product/huntert/runtime/models/default/`
- `product/huntert/runtime/wordlists/`
- `product/huntert/runtime/manifests/`
- `product/huntert/configs/`

## Default Runtime Bundle

The default release bundle should be exported from:

- `lstm_pipeline/saved_models/model_MD10_MF5_es128_nl2_dr0.2_loss3.319183.pt`
- `LSTM_Research/chosen_wordlists/big_wfuzz.txt`

Required bundle contents:

- model checkpoint
- serialized runtime vocabulary artifact
- packaged default wordlist
- manifest with bundle id, backend family, source asset references, and runtime defaults

## Command Surface

### `huntert version`

Print version and runtime metadata.

### `huntert bundle verify`

Validate that the selected or default runtime bundle is readable and internally consistent.

Minimum outputs:

- bundle id
- backend family
- checkpoint path
- vocabulary artifact path
- wordlist path

### `huntert models inspect`

Show model and bundle metadata for the default or selected bundle.

Minimum outputs:

- bundle id
- model filename
- exported defaults
- source checkpoint reference

### `huntert attack run`

Run a live directory enumeration session.

Minimum flags:

- `--target`
- `--threads`
- `--timeout`
- `--rate-limit`
- `--header` repeatable
- `--user-agent`
- `--method` with `GET` and `HEAD`
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

Default interesting statuses:

- `200,204,301,302,307,308,401,403`

## Runtime Architecture

Go owns:

- CLI parsing
- target validation
- HTTP client behavior
- concurrency and rate limiting
- queueing and recursion
- result persistence
- progress and output rendering

Python owns:

- loading the packaged LSTM bundle
- token and vocabulary handling for runtime prediction
- returning ranked next-token candidates

## Sidecar Protocol

The Python backend should run as a long-lived stdio JSON sidecar.

Required operations:

- `inspect_bundle`
- `load_bundle`
- `predict_next`
- `shutdown`

Example request:

```json
{"op":"predict_next","tokens":["<sos>","admin"],"top_k":1000}
```

Example response:

```json
{"ok":true,"candidates":[{"token":"login","prob":0.12}]}
```

## Attack Behavior

The live engine should:

- seed candidate paths from the model and the packaged default wordlist
- prioritize requests with model-aware scoring
- deduplicate attempted paths
- treat interesting hits as recursion points
- ask the sidecar for child predictions after useful responses
- persist discoveries, misses, and resumable queue state

## Validation Required

Product workspace checks:

- `cd product/huntert`
- `go test ./...`
- `go build ./cmd/huntert`
- `source ../../.venv/bin/activate && PYTHONPATH=python python3 -m huntert_runtime --help`

Bundle checks:

- default bundle manifest matches packaged artifacts
- bundle inspection does not depend on raw research paths at runtime

Live runtime checks:

- controlled local HTTP fixture for 200, redirect, 401, and 403 cases
- recursion after interesting hits
- resume after interruption
- `text` and structured output modes

# DirHunterT Transformer Pipeline V2

`transformer_pipelineV2/` is the fair-comparison transformer pipeline for the DirHunterT project.

V1 reused the LSTM-style flat token stream during training. V2 fixes that by training on one padded path per sample, which gives the transformer clean per-path depth positions and removes the LSTM-specific hidden-state training advantage from the comparison.

The current active plan is:

1. Run the combined `0C + 0B` diagnostic first.
2. Evaluate it against LSTM and Transformer V1.
3. Run calibration or larger follow-up experiments only if the fair V2 result justifies it.

For the detailed research framing, see [Next_Plan.md](../docs/archive/research-plans/Next_Plan.md).

## What V2 Changes

V2 keeps the same model family and attack/evaluation loop as V1, but changes the training regime:

- each training sample is one padded path
- batches come from a proper `DataLoader`
- training uses `src = sequence[:-1]` and `target = sequence[1:]`
- loss is computed only on non-pad target tokens
- progress files are tagged by training regime so old V1 progress is ignored

This makes V2 the correct place to answer:

**Can a fairly trained transformer beat the LSTM baseline on this dataset?**

## Commands

The V2 CLI has three commands:

- `train-diagnostic`: combined `0C + 0B`, recommended first run
- `train`: full fair V2 grid
- `evaluate`: run attack-time evaluation for saved V2 models

Check the CLI:

```bash
cd /home/jeevan/HunterT/transformer_pipelineV2
../.venv/bin/python3 main.py --help
```

## Recommended Workflow

### 1. Smoke test the combined `0C + 0B` path

This is the fastest way to confirm the environment, data path, and new path-wise regime are wired correctly.

```bash
cd /home/jeevan/HunterT/transformer_pipelineV2

../.venv/bin/python3 main.py train-diagnostic \
  --smoke-test \
  --data-folder ../LSTM_Research/datasets/LM-training-datasets \
  --saved-models-folder ./saved_models_pathwise_small_smoke
```

`--smoke-test` reduces the run to one global setting, one architecture setting, and one epoch.

### 2. Run the combined `0C + 0B` diagnostic

This is the main first experiment.

It combines:

- `0C`: fair path-wise training
- `0B`: smaller transformer capacity search

```bash
cd /home/jeevan/HunterT/transformer_pipelineV2

../.venv/bin/python3 main.py train-diagnostic \
  --data-folder ../LSTM_Research/datasets/LM-training-datasets \
  --saved-models-folder ./saved_models_pathwise_small
```

Diagnostic grid:

- global parameters:
  - `max_depth = [5, 10]`
  - `min_freq = [3, 5]`
- architecture parameters:
  - `d_model = [64, 128]`
  - `n_heads = [2, 4]`
  - `n_layers = [2, 3]`
  - `dropout = [0.2, 0.4]`

Total combinations:

- `4` global settings
- `16` architecture settings
- `64` model combinations total

As in the LSTM pipeline, the best model for each `(max_depth, min_freq)` pair is kept as the final saved model. That means the final saved-model folder should contain up to `4` best-model `.pt` files, plus the progress file and checkpoint subdirectory.

### 3. Evaluate the saved V2 diagnostic models

```bash
cd /home/jeevan/HunterT/transformer_pipelineV2

../.venv/bin/python3 main.py evaluate \
  --data-folder ../LSTM_Research/datasets/LM-training-datasets \
  --saved-models-folder ./saved_models_pathwise_small \
  --wordlist-file ../LSTM_Research/chosen_wordlists/big_wfuzz.txt \
  --results-folder ./results_pathwise_small
```

This writes:

- `eval_results_transformer.csv`
- `eval_results_transformer_best.csv`

under `./results_pathwise_small/`.

### 4. Compare against the LSTM baseline

```bash
cd /home/jeevan/HunterT/lstm_pipeline

../.venv/bin/python3 plot_tables.py \
  --results-csv ./results/eval_results.csv \
  --transformer-results ../transformer_pipelineV2/results_pathwise_small/eval_results_transformer_best.csv \
  --output-dir ./results/figures
```

This is the current decision point. If the fair small-model V2 run still loses clearly, then the next question is whether calibration or context-aware modeling is worth the extra work.

## Full Fair V2 Grid

Run this only after the diagnostic pass if you want the larger non-diagnostic V2 grid.

```bash
cd /home/jeevan/HunterT/transformer_pipelineV2

../.venv/bin/python3 main.py train \
  --data-folder ../LSTM_Research/datasets/LM-training-datasets \
  --saved-models-folder ./saved_models_pathwise
```

Full grid:

- global parameters:
  - `max_depth = [5, 10]`
  - `min_freq = [3, 5]`
- architecture parameters:
  - `d_model = [128, 256, 512]`
  - `n_heads = [4, 8]`
  - `n_layers = [4, 6]`
  - `dropout = [0.2, 0.4, 0.6]`

Total combinations:

- `4` global settings
- `36` architecture settings
- `144` model combinations total

Evaluate the full grid outputs with:

```bash
cd /home/jeevan/HunterT/transformer_pipelineV2

../.venv/bin/python3 main.py evaluate \
  --data-folder ../LSTM_Research/datasets/LM-training-datasets \
  --saved-models-folder ./saved_models_pathwise \
  --wordlist-file ../LSTM_Research/chosen_wordlists/big_wfuzz.txt \
  --results-folder ./results_pathwise
```

## Evaluation Options

`evaluate` supports both temperature sweeps and beam search.

Temperature sweep example:

```bash
cd /home/jeevan/HunterT/transformer_pipelineV2

../.venv/bin/python3 main.py evaluate \
  --data-folder ../LSTM_Research/datasets/LM-training-datasets \
  --saved-models-folder ./saved_models_pathwise_small \
  --wordlist-file ../LSTM_Research/chosen_wordlists/big_wfuzz.txt \
  --prediction-sweep 500 750 1000 \
  --temperature-sweep 0.5 0.7 0.8 0.9 1.0 1.2 1.5 2.0 \
  --results-folder ./results_pathwise_small_temp
```

Beam-search example:

```bash
cd /home/jeevan/HunterT/transformer_pipelineV2

../.venv/bin/python3 main.py evaluate \
  --data-folder ../LSTM_Research/datasets/LM-training-datasets \
  --saved-models-folder ./saved_models_pathwise_small \
  --wordlist-file ../LSTM_Research/chosen_wordlists/big_wfuzz.txt \
  --prediction-sweep 500 1000 \
  --beam-width 5 \
  --results-folder ./results_pathwise_small_beam5
```

Default evaluation settings:

- `prediction_sweep = [100, 250, 500, 750, 1000, 2000, 5000, 10000]`
- `temperature_sweep = [1.0]`
- `beam_width = 1`
- `request_limit = 100000`

## Artifact Layout

Recommended folders:

- diagnostic training outputs:
  - `./saved_models_pathwise_small/`
- diagnostic evaluation outputs:
  - `./results_pathwise_small/`
- full-grid training outputs:
  - `./saved_models_pathwise/`
- full-grid evaluation outputs:
  - `./results_pathwise/`

Inside each saved-model folder:

- best-model `.pt` files for each `(max_depth, min_freq)` pair
- `train_progress.json`
- `checkpoints/` for per-combination checkpoints

Resume behavior:

- training resumes automatically from `train_progress.json`
- progress files are regime-tagged
- V2 ignores old V1 progress files instead of silently skipping work

## Segment Embeddings

The model still contains segment-type embeddings, but V2 automatically disables them when the vocabulary becomes too large:

- `disable_segment_emb = True` when `vocab_size > 5000`

This matches both training and evaluation. The reason is simple: on large domain-specific vocabularies, the keyword-based segment categories do not cover enough tokens to be a reliable source of signal.

If you want to inspect segment coverage explicitly, run the helper in [`src/model.py`](./src/model.py) from the repository root:

```bash
cd /home/jeevan/HunterT

./.venv/bin/python3 - <<'PY'
from lstm_pipeline.src.data import load_datasets, create_vocabulary
from transformer_pipelineV2.src.model import diagnose_segment_coverage

train_df, _, _ = load_datasets("LSTM_Research/datasets/LM-training-datasets")
vocab = create_vocabulary(train_df, min_freq=3, max_depth=5)
diagnose_segment_coverage(vocab)
PY
```

## Spot VM / Sync Support

Both training commands support periodic sync with an external command:

- `--sync-cmd`
- `--sync-every-n`

Example:

```bash
cd /home/jeevan/HunterT/transformer_pipelineV2

../.venv/bin/python3 main.py train-diagnostic \
  --data-folder ../LSTM_Research/datasets/LM-training-datasets \
  --saved-models-folder ./saved_models_pathwise_small \
  --sync-cmd "gsutil -m rsync -r ./saved_models_pathwise_small gs://dirhuntert-transformer/transformer_v2/saved_models_pathwise_small" \
  --sync-every-n 4
```

You can also set the sync command through `TRANSFORMER_SYNC_CMD`.
```bash
export TRANSFORMER_SYNC_CMD='gsutil -m rsync -r ./saved_models_pathwise_small gs://dirhuntert-transformer/transformer_v2/saved_models_pathwise_small'
python3 main.py train-diagnostic \
  --data-folder ../LSTM_Research/datasets/LM-training-datasets \
  --saved-models-folder ./saved_models_pathwise_small \
  --sync-every-n 4
  --resume
  ```
## Current Research Status

The current active order is:

1. combined `0C + 0B` in V2
2. compare against LSTM and V1
3. optional `0A` temperature calibration
4. deeper analysis
5. only then consider context-aware transformer work

Older phases were not deleted from the project plan, but they are now conditional rather than immediate. The V2 README is intentionally centered on the fair-baseline question first.

## Key Files

- [main.py](./main.py): CLI entry point
- [src/data.py](./src/data.py): path-wise batching and encoding
- [src/training.py](./src/training.py): training loop for path-wise batches
- [src/grid_search.py](./src/grid_search.py): full fair V2 grid
- [src/diagnostic_grid.py](./src/diagnostic_grid.py): combined `0C + 0B` diagnostic grid
- [src/model.py](./src/model.py): DirHunterT transformer model
- [src/inference.py](./src/inference.py): top-K and beam-search generation

## Practical Notes

- Use `train-diagnostic` first unless you are explicitly running the larger follow-up grid.
- Do not compare new V2 results against old V1 checkpoints as if they were trained under the same regime.
- If you are plotting LSTM vs transformer tables, compare against `eval_results_transformer_best.csv`, not the raw full sweep CSV.

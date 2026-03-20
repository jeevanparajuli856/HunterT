# DirHunterT Transformer Pipeline V2

DirHunterT-A V2 keeps the same decoder-only transformer architecture and the
same evaluation loop as V1, but fixes the training regime:

- V1 trained on a flattened token stream shared with the LSTM pipeline
- V2 trains on **independent padded paths** via a proper PyTorch `DataLoader`
- This removes the recurrent hidden-state carry-over advantage from the A/B comparison

Runs on the **same GCP Spot V100 infrastructure** as the LSTM pipeline.

Grid search: **144 model combinations**.
Produces **4 best models** — one per `(max_depth, min_freq)` global pair — for direct comparison with LSTM.

Recommended first experiment:

- `python main.py train-diagnostic`
- this combines the fair V2 training regime with the small-model diagnostic grid

---

## Architecture Quick Reference

| Component | Detail |
|-----------|--------|
| Model | Decoder-only transformer (causal self-attention) |
| Tokenizer | Same vocabulary and path tokenization as LSTM |
| Position encoding | Learnable depth embeddings (not sinusoidal) |
| Segment embeddings | 8 structural categories — **see warning below** |
| Training regime | **Path-wise** batches, one padded path per sample |
| Hyperparameter grid | `d_model`×`n_heads`×`n_layers`×`dropout` = 36 arch × 4 global = 144 total |
| Reused from LSTM | `attacks.py`, `tree_builder.py`, `plot_tables.py` |

---

## ⚠️ Segment Embedding Diagnostic (run before training)

Segment type embeddings classify each directory token into one of 8 structural categories (API, Admin, Content, etc.). This only helps if the vocabulary is small enough for the keyword lists to cover a meaningful fraction of tokens.

**Run the diagnostic first:**

```bash
source ../.venv/bin/activate
python3 -c "
import sys
sys.path.insert(0, '../lstm_pipeline')
sys.path.insert(0, '.')
from lstm_pipeline.src.data import load_datasets, create_vocabulary
from src.model import diagnose_segment_coverage
train_df, _, _ = load_datasets('../lstm_Research/datasets/LM-training-datasets')
vocab = create_vocabulary(train_df, min_freq=3, max_depth=10)
print(f'Vocab size: {len(vocab)}')
diagnose_segment_coverage(vocab)
"
```

**Actual results (measured 2026-03-15):**

| Global params | Vocab size | Type-7 (unknown) | Signal types 0–6 |
|--------------|-----------|-----------------|-----------------|
| MF=3, MD=10 | 40,717 | **98.9%** ⚠️ | 1.1% |
| MF=5, MD=10 | 24,507 | **98.2%** ⚠️ | 1.8% |
| MF=3, MD=5  | 36,724 | **98.8%** ⚠️ | 1.2% |
| MF=5, MD=5  | 22,170 | **98.1%** ⚠️ | 1.9% |

**Interpretation:** The vocabulary is 22K–40K domain-specific directory strings (not the ~150 tokens assumed during design). Segment embeddings cover only ~1% of tokens — the remaining 99% all receive the same type-7 embedding. This means the segment embedding adds a near-constant bias to every forward pass: **effectively zero signal.**

**Resolution:** Segment embeddings are disabled in the model's forward pass for this run (type-7 tokens receive a zeroed embedding via the `disable_segment_emb` flag — see model.py). The real architectural advantages — full causal attention and depth embeddings — are unaffected. Segment embeddings remain in the architecture for a future BPE-tokenized variant where vocab size (~2K–4K) would allow meaningful coverage.

---

## What Changed From V1

V1 and the LSTM pipeline both rely on a flat tensor loader that reshapes the
entire corpus into `(batch_size, num_batches)` and then slices fixed windows.
That setup is acceptable for recurrent language-model baselines, but it is a
poor fit for a depth-aware transformer.

V2 replaces only the training loader:

- Each sample is one padded path: `<sos> ... <eos> <pad> ...`
- Training uses `src = sequence[:-1]`, `target = sequence[1:]`
- Training batches are shuffled path-wise
- Evaluation and attack simulation are unchanged

## Environment Setup

Uses the **same venv** as the LSTM pipeline — no new dependencies needed.

```bash
cd ~/HunterT/lstm_pipeline
source .venv/bin/activate
cd ~/HunterT/transformer_pipelineV2
```

Verify imports are clean:

```bash
python main.py --help
```

---

## GCS Bucket

Uses the **same bucket** already created for the LSTM run.
Transformer V2 artifacts should go under a separate prefix such as `transformer_v2/`.

If bucket does not exist yet (first time):

```bash
cd ~/HunterT/infra
BUCKET_NAME=dirhuntert-transformer ./create_storage.sh
```

---

## 1) Smoke Test (2 minutes)

Run before committing to a full cloud training session.
Trains 1 model for 1 epoch and verifies shapes and file outputs.

```bash
cd ~/HunterT/transformer_pipelineV2
python3 main.py train \
  --smoke-test \
  --data-folder ../LSTM_Research/datasets/LM-training-datasets \
  --saved-models-folder ./saved_models_pathwise_smoke
```

Expected outputs:

```
saved_models_pathwise_smoke/checkpoints/combo_MD5_MF3_dm128_nh4_nl4_dr0.2.pt
saved_models_pathwise_smoke/model_MD5_MF3_dm128_nh4_nl4_dr0.2_loss....pt
saved_models_pathwise_smoke/train_progress.json
```

---

## 2) Recommended First Run: Combined 0C + 0B

This is the preferred first experiment now.

It combines:

- `0C`: fair path-wise transformer training
- `0B`: small-model diagnostic grid

Command:

```bash
cd ~/HunterT/transformer_pipelineV2
python3 main.py train-diagnostic \
  --data-folder ../LSTM_Research/datasets/LM-training-datasets \
  --saved-models-folder ./saved_models_pathwise_small
```

Then evaluate it with the same evaluation command:

```bash
python3 main.py evaluate \
  --data-folder ../LSTM_Research/datasets/LM-training-datasets \
  --saved-models-folder ./saved_models_pathwise_small \
  --wordlist-file ../LSTM_Research/chosen_wordlists/big_wfuzz.txt \
  --results-folder ./results_pathwise_small
```

What this answers fastest:

- does fair training help?
- are smaller transformers a better fit?

---

## 3) Full Training — Resumable, Spot-Safe (5–15 hours)

```bash
cd ~/HunterT/transformer_pipelineV2
python main.py train \
  --data-folder ../LSTM_Research/datasets/LM-training-datasets \
  --saved-models-folder ./saved_models_pathwise \
  --resume \
  --sync-cmd "gsutil -m rsync -r ./saved_models_pathwise gs://dirhuntert-transformer/transformer_v2/saved_models_pathwise" \
  --sync-every-n 1
```

Or set the sync command as an environment variable:

```bash
export TRANSFORMER_SYNC_CMD='gsutil -m rsync -r ./saved_models_pathwise gs://dirhuntert-transformer/transformer_v2/saved_models_pathwise'
python main.py train --resume
```

What happens:
- 144 model combinations trained (4 global × 36 arch)
- After each combo: checkpoint saved + GCS sync runs
- If preempted and restarted: completed combos are skipped automatically
- 4 best models saved (one per global param pair)

---

## 4) Evaluation — Same Protocol as LSTM (2–8 hours)

Run after training completes. Uses the same 119 test domains, same prediction sweep, same 100K request budget as the LSTM evaluation.

```bash
cd ~/HunterT/transformer_pipelineV2
python main.py evaluate \
  --data-folder ../LSTM_Research/datasets/LM-training-datasets \
  --saved-models-folder ./saved_models_pathwise \
  --wordlist-file ../LSTM_Research/chosen_wordlists/big_wfuzz.txt \
  --prediction-sweep 100 250 500 750 1000 2000 5000 10000 \
  --results-folder ./results_pathwise
```

Outputs:

```
results_pathwise/eval_results_transformer.csv       — all runs
results_pathwise/eval_results_transformer_best.csv  — best prediction_limit per domain/model
```

---

## 5) Compare Transformer vs LSTM Results

After both LSTM and transformer evaluations are done, run the LSTM plot script with both CSVs. It generates all existing LSTM tables **plus** two new comparison tables.

```bash
cd ~/HunterT/lstm_pipeline
python plot_tables.py \
  --results-csv ./results/eval_results.csv \
  --transformer-results ../transformer_pipelineV2/results_pathwise/eval_results_transformer_best.csv \
  --output-dir ./results/figures
```

New outputs produced when `--transformer-results` is given:

```
results/figures/table_lstm_vs_transformer.png   — BF Baseline | LSTM | DirHunterT-A | Gain %
results/figures/table_gate_check.png            — PASS/FAIL per sector (>30% over LSTM)
```

The gate check result is also printed to the terminal immediately:

```
==================================================
GATE CHECK RESULT
==================================================
    Sector  LSTM hits  DirHunterT-A  Gain %  Gate >30%
University      90.0         130.0  +44.4%    PASS ✓
 Hospitals     175.0         240.0  +37.1%    PASS ✓
 Companies      89.0         120.0  +34.8%    PASS ✓
Government     128.0         175.0  +36.7%    PASS ✓
ALL (mean)     120.5         166.3  +38.0%    PASS ✓
==================================================
GATE PASSED — proceed to Model B
==================================================
```

---

## Running on Spot VM (Full Workflow)

### Step 1 — Create the VM (V100 Spot infra)

```bash
cd ~/HunterT/infra_T
./create_infra.sh
```

### Step 2 — SSH into the VM

```bash
gcloud compute ssh lstm-v100-vm-transformer --zone us-central1-a --project dirhunter-t
```

### Step 3 — Set up environment on VM

```bash
# Clone or copy repo (skip if already there from LSTM run)
cd ~/HunterT

# Activate venv (already installed from LSTM run)
source lstm_pipeline/.venv/bin/activate

# Verify GPU
nvidia-smi
```

### Step 4 — Restore any previous V2 artifacts (if resuming after preemption)

```bash
cd ~/HunterT/transformer_pipelineV2
gsutil -m rsync -r gs://dirhuntert-transformer/transformer_v2/saved_models_pathwise ./saved_models_pathwise
```

### Step 5 — Start tmux and run training

```bash
tmux new -s transformer

cd ~/HunterT/transformer_pipelineV2
python main.py train \
  --data-folder ../LSTM_Research/datasets/LM-training-datasets \
  --saved-models-folder ./saved_models_pathwise \
  --resume \
  --sync-cmd "gsutil -m rsync -r ./saved_models_pathwise gs://dirhuntert-transformer/transformer_v2/saved_models_pathwise" \
  --sync-every-n 1

# Detach:  Ctrl+B then D
# Reattach: tmux attach -t transformer
```

### Step 6 — Optional: Preemption watcher (second tmux pane)

Reuses the same `preempt_watch.sh` from the LSTM pipeline.

```bash
# In a second tmux pane (Ctrl+B then %)
cd ~/HunterT/lstm_pipeline
export SYNC_CMD='gsutil -m rsync -r ../transformer_pipelineV2/saved_models_pathwise gs://dirhuntert-transformer/transformer_v2/saved_models_pathwise'
./preempt_watch.sh
```

Watcher polls every 5 seconds. On preemption signal (~30s notice), it triggers an emergency GCS sync before the VM shuts down.

---

## Spot Recovery Runbook

If the VM is preempted, follow this exact sequence.

**1. Recreate VM:**
```bash
cd ~/HunterT/infra_T
./create_infra.sh
```

**2. SSH into new VM:**
```bash
gcloud compute ssh lstm-v100-vm-transformer --zone us-central1-a --project dirhunter-t
```

**3. Restore Python environment:**
```bash
cd ~/HunterT/lstm_pipeline
python3 -m venv .venv
source .venv/bin/activate
pip install -r ../requirements.txt
```

**4. Restore transformer V2 artifacts from GCS:**
```bash
cd ~/HunterT/transformer_pipelineV2
gsutil -m rsync -r gs://dirhuntert-transformer/transformer_v2/saved_models_pathwise ./saved_models_pathwise
```

**5. Resume training — completed combos are skipped automatically:**
```bash
python main.py train \
  --data-folder ../LSTM_Research/datasets/LM-training-datasets \
  --saved-models-folder ./saved_models_pathwise \
  --resume \
  --sync-cmd "gsutil -m rsync -r ./saved_models_pathwise gs://dirhuntert-transformer/transformer_v2/saved_models_pathwise" \
  --sync-every-n 1
```

---

## Cost and Time Estimates


| Phase | Duration | Cost (Spot V100) |
|-------|----------|------------------|
| Smoke test | ~2 min | ~$0.02 |
| Full training (144 models) | 10–24 hours | ~$25–50 |
| Evaluation (119 domains) | 2–6 hours | ~$5–10 |
| **Total** | **~9–24 hours** | **~$25–50** |

Transformer training is faster per model than LSTM (no truncated BPTT, GPU-parallel attention).

---

## Gate Check — Must Pass Before Model B

After evaluation, check these minimum thresholds:

| Sector | LSTM baseline | Model A must exceed |
|--------|--------------|---------------------|
| HOS | 175 | **228** (+30%) |
| UNI | 90 | **117** (+30%) |
| COM | 89 | **116** (+30%) |
| GOV | 128 | **166** (+30%) |

If any sector misses: compare V2 path-wise results to V1 first. If V2 still misses badly, move to the small-model and context-aware ablations before starting Model B.

---

## Key Files

```
transformer_pipelineV2/
  main.py                  # CLI entry point: train + evaluate
  src/
    model.py               # DirHunterT: decoder-only transformer
    inference.py           # generate() — identical interface to LSTM version
    data.py                # Path-wise per-sample DataLoader utilities
    training.py            # train_model() with path-wise batching
    grid_search.py         # TransformerGridSearch — 144 combos, path-wise V2
    utils.py               # get_transformer_hyperparams_from_filename()

# Reused from lstm_pipeline/src (no modifications):
  ../lstm_pipeline/src/attacks.py
  ../lstm_pipeline/src/tree_builder.py
  ../lstm_pipeline/plot_tables.py
  ../lstm_pipeline/preempt_watch.sh
```

# DirHunterT Transformer Pipeline

DirHunterT-A: decoder-only transformer for directory enumeration.
Runs on the **same GCP Spot V100 infrastructure** as the LSTM pipeline.

Grid search: **96 model combinations** (vs LSTM's 108).
Produces **4 best models** — one per `(max_depth, min_freq)` global pair — for direct comparison with LSTM.

---

## Architecture Quick Reference

| Component | Detail |
|-----------|--------|
| Model | Decoder-only transformer (causal self-attention) |
| Tokenizer | Same as LSTM — no changes to `data.py` or vocab |
| Position encoding | Learnable depth embeddings (not sinusoidal) |
| Segment embeddings | 8 structural categories — **see warning below** |
| Hyperparameter grid | `d_model`×`n_heads`×`n_layers`×`dropout` = 24 arch × 4 global = 96 total |
| Reused from LSTM | `data.py`, `attacks.py`, `tree_builder.py`, `plot_tables.py` |

---

## ⚠️ Segment Embedding Diagnostic (run before training)

Segment type embeddings classify each directory token into one of 8 structural categories (API, Admin, Content, etc.). This only helps if the vocabulary is small enough for the keyword lists to cover a meaningful fraction of tokens.

**Run the diagnostic first:**

```bash
source ../.venv/bin/activate
python3 -c "
import sys
sys.path.insert(0, '../ltsm_pipeline')
sys.path.insert(0, '.')
from ltsm_pipeline.src.data import load_datasets, create_vocabulary
from transformer_pipeline.src.model import diagnose_segment_coverage
train_df, _, _ = load_datasets('../LTSM_Research/datasets/LM-training-datasets')
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

## Environment Setup

Uses the **same venv** as the LSTM pipeline — no new dependencies needed.

```bash
cd ~/HunterT/ltsm_pipeline
source .venv/bin/activate
cd ~/HunterT/transformer_pipeline
```

Verify imports are clean:

```bash
python main.py --help
```

---

## GCS Bucket

Uses the **same bucket** already created for the LSTM run.
Transformer artifacts go under a separate prefix: `transformer/`.

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
cd ~/HunterT/transformer_pipeline
python main.py train \
  --smoke-test \
  --data-folder ../LTSM_Research/datasets/LM-training-datasets \
  --saved-models-folder ./saved_models
```

Expected outputs:

```
saved_models/checkpoints/combo_MD5_MF3_dm256_nh4_nl4_dr0.2.pt
saved_models/model_MD5_MF3_dm256_nh4_nl4_dr0.2_loss....pt
saved_models/train_progress.json
```

---

## 2) Full Training — Resumable, Spot-Safe (5–15 hours)

```bash
cd ~/HunterT/transformer_pipeline
python main.py train \
  --data-folder ../LTSM_Research/datasets/LM-training-datasets \
  --saved-models-folder ./saved_models \
  --resume \
  --progress-file ./saved_models/train_progress.json \
  --checkpoint-dir ./saved_models/checkpoints \
  --sync-cmd "gsutil -m rsync -r ./saved_models gs://dirhuntert-transformer/transformer/saved_models" \
  --sync-every-n 1
```

Or set the sync command as an environment variable:

```bash
export TRANSFORMER_SYNC_CMD='gsutil -m rsync -r ./saved_models gs://dirhuntert-transformer/transformer/saved_models'
python main.py train --resume
```

What happens:
- 96 model combinations trained (4 global × 24 arch)
- After each combo: checkpoint saved + GCS sync runs
- If preempted and restarted: completed combos are skipped automatically
- 4 best models saved (one per global param pair)

---

## 3) Evaluation — Same Protocol as LSTM (2–8 hours)

Run after training completes. Uses the same 119 test domains, same prediction sweep, same 100K request budget as the LSTM evaluation.

```bash
cd ~/HunterT/transformer_pipeline
python main.py evaluate \
  --data-folder ../LTSM_Research/datasets/LM-training-datasets \
  --saved-models-folder ./saved_models \
  --wordlist-file ../LTSM_Research/chosen_wordlists/big_wfuzz.txt \
  --prediction-sweep 100 250 500 750 1000 2000 5000 10000 \
  --results-folder ./results
```

Outputs:

```
results/eval_results_transformer.csv       — all runs
results/eval_results_transformer_best.csv  — best prediction_limit per domain/model
```

---

## 4) Compare Transformer vs LSTM Results

After both LSTM and transformer evaluations are done, run the LSTM plot script with both CSVs. It generates all existing LSTM tables **plus** two new comparison tables.

```bash
cd ~/HunterT/ltsm_pipeline
python plot_tables.py \
  --results-csv ./results/eval_results.csv \
  --transformer-results ../transformer_pipeline/results/eval_results_transformer_best.csv \
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
gcloud compute ssh ltsm-v100-vm-transformer --zone us-central1-a --project dirhunter-t
```

### Step 3 — Set up environment on VM

```bash
# Clone or copy repo (skip if already there from LSTM run)
cd ~/HunterT

# Activate venv (already installed from LSTM run)
source ltsm_pipeline/.venv/bin/activate

# Verify GPU
nvidia-smi
```

### Step 4 — Restore any previous transformer artifacts (if resuming after preemption)

```bash
cd ~/HunterT/transformer_pipeline
gsutil -m rsync -r gs://dirhuntert-transformer/transformer/saved_models ./saved_models
```

### Step 5 — Start tmux and run training

```bash
tmux new -s transformer

cd ~/HunterT/transformer_pipeline
python main.py train \
  --data-folder ../LTSM_Research/datasets/LM-training-datasets \
  --saved-models-folder ./saved_models \
  --resume \
  --sync-cmd "gsutil -m rsync -r ./saved_models gs://dirhuntert-transformer/transformer/saved_models" \
  --sync-every-n 1

# Detach:  Ctrl+B then D
# Reattach: tmux attach -t transformer
```

### Step 6 — Optional: Preemption watcher (second tmux pane)

Reuses the same `preempt_watch.sh` from the LSTM pipeline.

```bash
# In a second tmux pane (Ctrl+B then %)
cd ~/HunterT/ltsm_pipeline
export SYNC_CMD='gsutil -m rsync -r ../transformer_pipeline/saved_models gs://dirhuntert-transformer/transformer/saved_models'
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
gcloud compute ssh ltsm-v100-vm-transformer --zone us-central1-a --project dirhunter-t
```

**3. Restore Python environment:**
```bash
cd ~/HunterT/ltsm_pipeline
python3 -m venv .venv
source .venv/bin/activate
pip install -r ../requirements.txt
```

**4. Restore transformer artifacts from GCS:**
```bash
cd ~/HunterT/transformer_pipeline
gsutil -m rsync -r gs://dirhuntert-transformer/transformer/saved_models ./saved_models
```

**5. Resume training — completed combos are skipped automatically:**
```bash
python main.py train \
  --data-folder ../LTSM_Research/datasets/LM-training-datasets \
  --saved-models-folder ./saved_models \
  --resume \
  --sync-cmd "gsutil -m rsync -r ./saved_models gs://dirhuntert-transformer/transformer/saved_models" \
  --sync-every-n 1
```

---

## Cost and Time Estimates


| Phase | Duration | Cost (Spot V100) |
|-------|----------|------------------|
| Smoke test | ~2 min | ~$0.02 |
| Full training (96 models) | 7–18 hours | ~$20–40 |
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

If any sector misses: check the ablation — try removing segment embeddings first (simplest to debug), then depth embeddings. Do not start Model B until gate passes.

---

## Key Files

```
transformer_pipeline/
  main.py                  # CLI entry point: train + evaluate
  src/
    model.py               # DirHunterT: decoder-only transformer
    inference.py           # generate() — identical interface to LSTM version
    training.py            # train_model() with warmup + weight decay
    grid_search.py         # TransformerGridSearch — 96 combos, Spot-safe
    utils.py               # get_transformer_hyperparams_from_filename()

# Reused from ltsm_pipeline/src (no modifications):
  ../ltsm_pipeline/src/data.py
  ../ltsm_pipeline/src/attacks.py
  ../ltsm_pipeline/src/tree_builder.py
  ../ltsm_pipeline/plot_tables.py
  ../ltsm_pipeline/preempt_watch.sh
```

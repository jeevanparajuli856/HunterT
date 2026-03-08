# LTSM Pipeline Usage

This pipeline reproduces the paper-style LSTM baseline and evaluates:

- Breadth-First
- Depth-First
- Probabilistic
- LSTM (prediction sweep)

It is now Spot-safe for long runs by supporting:

- Resume from progress file
- Skip completed model combinations
- Per-combination checkpoints
- Optional periodic sync command

## Environment

```bash
cd ltsm_pipeline
python -m venv .venv
source .venv/bin/activate
pip install -r ../requirements.txt
```

## Cloud Storage (one-time setup)

Create a bucket once from the infra folder:

```bash
cd ../infra
BUCKET_NAME=dirhunter-t-ltsm-artifacts ./create_storage.sh
```

On a fresh Spot VM, restore artifacts before resuming:

```bash
cd ../ltsm_pipeline
gsutil -m rsync -r gs://dirhunter-t-ltsm-artifacts/ltsm/saved_models ./saved_models
gsutil -m rsync -r gs://dirhunter-t-ltsm-artifacts/ltsm/results ./results
```

## 1) Smoke Test (quick sanity - 2 minutes)

Runs a tiny one-model, one-epoch train to verify code + dependencies.

```bash
python main.py train --smoke-test --epochs 1
```

Expected outputs:

- `saved_models/checkpoints/combo_MD...pt`
- `saved_models/model_MD...loss....pt`
- `saved_models/train_progress.json`

## 2) Medium Test (30-minute verification)

Runs a small subset to verify full pipeline on Spot instance before committing to full run.

Trains 3 models × 3 epochs (~25-30 minutes):

```bash
python main.py train \
  --max-depth-values 5 \
  --min-freq-values 3 \
  --embedding-sizes 128 \
  --n-layers-values 2 \
  --dropout-values 0.2 0.3 0.4 \
  --epochs 3 \
  --resume \
  --progress-file ./saved_models/train_progress_test.json \
  --checkpoint-dir ./saved_models/checkpoints_test
```

Then evaluate with limited sweep:

```bash
python main.py evaluate \
  --wordlist-file ../LTSM_Research/chosen_wordlists/big_wfuzz.txt \
  --prediction-sweep 100 500 1000 \
  --results-file ./results/eval_results_test.csv \
  --best-models-file ./results/eval_results_best_by_model_test.csv
```

Verify outputs:

```bash
ls -lh saved_models/model_*.pt
ls -lh results/eval_results_test.csv
```

If this completes successfully, your setup is ready for the full run.

## 3) Full Training (resumable, Spot-safe)

```bash
python main.py train \
  --resume \
  --progress-file ./saved_models/train_progress.json \
  --checkpoint-dir ./saved_models/checkpoints
```

Optional periodic sync to GCS after each trained combo:

```bash
python main.py train \
  --resume \
  --sync-cmd "gsutil -m rsync -r ./saved_models gs://YOUR_BUCKET/ltsm/saved_models && gsutil -m rsync -r ./results gs://YOUR_BUCKET/ltsm/results" \
  --sync-every-n 1
```

You can also set sync command via env var:

```bash
export LTSM_SYNC_CMD='gsutil -m rsync -r ./saved_models gs://YOUR_BUCKET/ltsm/saved_models'
python main.py train --resume
```

## 4) Evaluate All Approaches (single run)

```bash
python main.py evaluate \
  --wordlist-file ../LTSM_Research/chosen_wordlists/big_wfuzz.txt \
  --prediction-sweep 100 250 500 750 1000 2000 5000 10000
```

Outputs:

- `results/eval_results.csv`
- `results/eval_results_best_by_model.csv`

## 5) Generate Matplotlib Tables

```bash
python plot_tables.py
```

Key artifacts:

- `results/figures/table_paper_four_approaches.png`
- `results/figures/table_paper_four_approaches.csv`
- `results/figures/table_all_approaches_by_domain.png`
- `results/figures/table_summary_baseline_vs_lm.png`

## Spot VM Best Practices

- Run in `tmux`.
- Keep `--resume` enabled.
- Keep `saved_models/` and `results/` synced to GCS.
- If preempted, rerun the same `train` command; completed combos are skipped automatically.

## 6) Spot Preemption Watcher (optional)

Use `preempt_watch.sh` to detect Spot preemption notice and run an emergency sync.

In a second tmux pane/session:

```bash
cd ~/HunterT/ltsm_pipeline
chmod +x preempt_watch.sh
export LTSM_SYNC_CMD='gsutil -m rsync -r ./saved_models gs://YOUR_BUCKET/ltsm/saved_models && gsutil -m rsync -r ./results gs://YOUR_BUCKET/ltsm/results'
./preempt_watch.sh
```

Run training in another pane/session at the same time:

```bash
python main.py train --resume
```

Notes:

- The metadata signal usually arrives about 30 seconds before shutdown.
- Watcher logs are written to `preempt_watch.log`.
- If preempted, recreate the VM, restore artifacts from GCS, and rerun `train --resume`.

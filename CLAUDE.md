# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

HunterT is a research project exploring LM-guided directory enumeration attacks on web servers. It contains two parallel model pipelines that share compatible interfaces:

- **LSTM pipeline** (`lstm_pipeline/`): Reproduces the AISec'24 baseline paper
- **Transformer pipeline** (`transformer_pipeline/`): DirHunterT — a decoder-only transformer with depth-aware positional embeddings, segment-type embeddings, and pre-layer norm

Both pipelines produce models that plug into the same attack simulation framework (`lstm_pipeline/src/attacks.py`). The main plan is to beat proposed LSTM baselines at AISec'24 with the transformer.

## Commands

### Training

```bash
# LSTM pipeline
cd lstm_pipeline && python3 main.py train

# Transformer pipeline
cd transformer_pipeline && python3 main.py train
```

### Evaluation

```bash
# LSTM
cd lstm_pipeline && python3 main.py evaluate

# Transformer
cd transformer_pipeline && python3 main.py evaluate
```

### Grid Search (full hyperparameter sweep)

```bash
# LSTM: 108 combinations (runs on GPU, hours on T4)
cd lstm_pipeline && python3 -m src.grid_search

# Transformer: 96 combinations run gpu V100, hours on V100
cd transformer_pipeline && python3 -m src.grid_search
```

Grid search is resume-safe — rerun the same command and completed combos are skipped.

### Smoke Test (quick validation)

Train 1 model for 1 epoch (~2 min) to verify the pipeline works end-to-end.

### Generating Comparison Tables

```bash
cd lstm_pipeline && python3 plot_tables.py
# With transformer comparison + gate check:
python3 plot_tables.py --transformer-results <path>
```

## Architecture

### Model Interfaces

Both pipelines expose identical inference interfaces:
- `generate(model, tokenizer, prompt, ...)` — next-token prediction with top-k sampling
- `lm_attack(...)` in `attacks.py` — heap-based adaptive attack using model predictions

The transformer pipeline additionally provides `beam_search_generate()`.

### DirHunterT Transformer Design Decisions

- **No RoPE**: URLs are hierarchical trees, not sequences — uses learnable depth-aware positional embeddings instead
- **Segment-type embeddings**: 8 structural categories (API, Admin, Content, etc.) — disabled when vocab >5K and coverage <5%
- **Pre-Layer Norm**: Better gradient stability than post-norm
- **Weight tying**: Shared embedding/output weights to reduce parameters on small datasets
- **Causal mask only**: No bidirectional encoder — task is generative

### Data Pipeline

- Dataset: 601 domains across 4 sectors (UNI, HOS, COM, GOV), ~1M paths from CC-MAIN-2023-40
- Located in `LSTM_Research/datasets/LM-training-datasets/`
- **Domain-level train/val/test split** (70/10/20) — no URL leakage across splits
- Custom tokenizer: splits on `/`, replaces 4-digit years with `YEAR` token, trims to `max_depth`
- Special tokens: `<unk>`(0), `<sos>`(1), `<eos>`(2), `<pad>`(3)

### Infrastructure

`infra/`, `infra_T/`, `infra_T_V100/` contain GCP Deployment Manager templates for Spot VMs with automatic NVIDIA driver setup, preemption watchers, and GCS checkpoint sync.

## Gate Check

The transformer must beat the LSTM baseline by >30% on all 4 sectors before proceeding to the next research phase. This is automated in `plot_tables.py`.

## Dependencies

PyTorch 2.1.0 (CUDA 12.1), torchtext 0.16.0, anytree. Full list in `requirements.txt`. No formal test framework or linter is configured.


## Rules
- If found some descrepencies in code and in any md file update it and let know after process end with brief summary
- If I said something is not good update it in Claude.md under user-preferred rules section and let me know after process end with brief summary

##User-Preferred Rules
- Use `python3` instead of `python` in all commands for consistency and to avoid
- Use venv which is at root of this directory for all Python dependencies to prevent conflicts with system packages


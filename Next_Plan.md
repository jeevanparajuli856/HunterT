# Next_Plan: Beat LSTM with Transformer

## What We Are Actually Deciding

The immediate research question is:

**Can a fairly trained transformer beat the LSTM baseline on this dataset?**

Everything else is secondary until that is answered.

That means:

- first validate the fair V2 transformer baseline
- then decide whether the transformer still needs smaller capacity or more context
- only then consider the larger context-aware rebuild

## Current State

### Established Results

Best mean sector results so far:

| Model | UNI | HOS | COM | GOV | Mean |
|------|-----|-----|-----|-----|------|
| LSTM | 33.2 | 62.4 | 40.5 | 35.5 | 42.9 |
| Transformer V1 | 31.5 | 64.4 | 30.2 | 32.4 | 39.6 |

So Transformer V1 is currently **-7.6%** vs LSTM overall.

### What Was Wrong With V1

Transformer V1 reused the flat-stream training regime from the LSTM pipeline.

That was not a fair comparison because:

- the LSTM benefits from hidden-state carry-over during training
- the transformer does not
- the positional semantics are worse for a transformer under the flat-stream setup

### What Is Already Implemented

`transformer_pipelineV2/` is now the fair-comparison pipeline.

Completed in code:

- path-wise batching: one padded path per sample
- `src = sequence[:-1]`, `target = sequence[1:]`
- separate V2 artifact folders:
  - `saved_models_pathwise/`
  - `results_pathwise/`
- V2 progress files tagged so V1 progress is ignored

## Updated Priority Order

This is the new ranking for Phase 0.

1. **0C: Fix the training regime**  
   This is now the highest-priority item and the next required experiment.

2. **0B: Small model grid**  
   Run this only if V2 still loses materially after 0C.

3. **0A: Temperature sweep**  
   Keep it, but move it down. Calibration is useful only after we have a fair V2 model worth calibrating.

4. **0D: Analysis**  
   Use this after 0C/0B/0A results exist.

5. **0d: LSTM context hack baseline**  
   Keep it as an optional research probe, not as the main next step.

## Phase 0: Active Diagnostic Plan

### 0C. Fix the Training Regime

**Priority**: 1  
**Status**: Implemented in code, not yet fully evaluated  
**Pipeline**: `transformer_pipelineV2/`

This is now the first experiment.

What changed:

- V2 no longer uses the flat-tensor sliding window from V1
- V2 trains on individual padded paths via a proper DataLoader
- this removes the LSTM-specific training advantage from the comparison

What it tells us:

- if V2 closes most of the gap, then V1 mostly failed because of training regime
- if V2 still loses clearly, then architecture/tokenization/capacity issues remain

Run first:

```bash
cd /home/jeevan/HunterT/transformer_pipelineV2

../.venv/bin/python main.py train \
  --smoke-test \
  --data-folder ../LSTM_Research/datasets/LM-training-datasets \
  --saved-models-folder ./saved_models_pathwise_smoke

../.venv/bin/python main.py train \
  --data-folder ../LSTM_Research/datasets/LM-training-datasets \
  --saved-models-folder ./saved_models_pathwise

../.venv/bin/python main.py evaluate \
  --data-folder ../LSTM_Research/datasets/LM-training-datasets \
  --saved-models-folder ./saved_models_pathwise \
  --wordlist-file ../LSTM_Research/chosen_wordlists/big_wfuzz.txt \
  --results-folder ./results_pathwise
```

Compare against LSTM:

```bash
cd /home/jeevan/HunterT/lstm_pipeline

../.venv/bin/python plot_tables.py \
  --results-csv ./results/eval_results.csv \
  --transformer-results ../transformer_pipelineV2/results_pathwise/eval_results_transformer_best.csv \
  --output-dir ./results/figures
```

### 0B. Small Model Grid Search

**Priority**: 2  
**Status**: Not implemented yet  
**Run only if**: V2 still loses materially after 0C

Purpose:

- test whether the current transformers are simply too large for short 7-12 token paths and this vocabulary

Target diagnostic grid:

- `d_model = [64, 128]`
- `n_heads = [2, 4]`
- `n_layers = [2, 3]`
- `dropout = [0.2, 0.4]`

What it tells us:

- small model >= current V2 model: over-parameterization is real
- small model << current V2 model: capacity is not the main issue

Implementation target:

- add `transformer_pipelineV2/src/diagnostic_grid.py`
- subclass `TransformerGridSearch`
- keep the same fair path-wise V2 training regime

### 0A. Temperature Sweep

**Priority**: 3  
**Status**: Supported by CLI, but no longer the first thing to run  
**Run only if**: 0C produces a model that is close enough to LSTM that calibration might matter

Reframed purpose:

- temperature sweep is a calibration check, not a root-cause fix
- do not spend time calibrating V1 before measuring fair V2

Use it on the best V2 models, not on the unfair V1 setup.

Suggested command:

```bash
cd /home/jeevan/HunterT/transformer_pipelineV2

../.venv/bin/python main.py evaluate \
  --data-folder ../LSTM_Research/datasets/LM-training-datasets \
  --saved-models-folder ./saved_models_pathwise \
  --wordlist-file ../LSTM_Research/chosen_wordlists/big_wfuzz.txt \
  --temperature-sweep 0.5 0.7 0.8 0.9 1.0 1.2 1.5 2.0 \
  --prediction-sweep 500 750 1000 \
  --results-folder ./results_pathwise_temp
```

What it tells us:

- higher temperature helps: model is overconfident
- lower temperature helps: model is underconfident
- no temperature helps: representations are the bigger issue

### 0D. Analysis

**Priority**: 4  
**Status**: Not implemented yet

After 0C and optional 0B/0A, create one simple analysis script to summarize:

- V2 vs LSTM
- V2 vs V1
- small-model vs default-model
- best temperature if a sweep was run

Suggested output:

- sector table
- overall mean comparison
- go / no-go recommendation for context-aware work

### 0d. LSTM Context Hack Baseline

**Priority**: 5  
**Status**: Optional, not blocking

Keep this phase, but reframe it:

- this is not the main next step
- this is only useful if we need an upper-bound style check on whether cross-path context helps at all

What it would test:

- whether priming the LSTM with discovered paths gives meaningful gains

If it gives no gain:

- that weakens the case for a costly context-aware rebuild

If it gives clear gain:

- that strengthens the case for context-aware transformer work later

## Phase 0 Gate

Use this decision rule after 0C and optional follow-ups.

### Continue with non-context transformer work if any of these happen

- V2 beats LSTM overall
- V2 materially narrows the gap
- V2 shows clear sector wins that justify more tuning
- small-model V2 improves meaningfully over default V2

### Escalate to context-aware transformer only if both are true

- fair V2 still does not beat LSTM
- small-model diagnostics do not fix the gap

## Reframed Future Phases

These phases are still part of the roadmap, but they are **not active now**.

### Phase 1: Context-Aware Data Pipeline

**Status**: Deferred  
**When to activate**: Only if Phase 0 says isolated-path transformers are not enough

Keep the idea:

- group paths by domain
- feed previously discovered paths as context
- mask loss so only the target path is trained

But do not build it until Phase 0 finishes.

### Phase 2: Context-Aware Model

**Status**: Deferred  
**When to activate**: After Phase 1 is justified

Keep the planned direction:

- path-position embeddings
- per-path depth embeddings
- right-sized capacity around LSTM scale

But this is still conditional work.

### Phase 3: Context-Aware Attack Loop

**Status**: Deferred  
**When to activate**: Only after a context-aware model exists and shows offline promise

Keep the idea:

- feed discovered paths back into inference
- let predictions adapt as the attack progresses

But this should not start before the model itself is validated.

### Phase 4: Full Evaluation and Comparison

**Status**: Deferred  
**When to activate**: After any new context-aware model exists

This phase stays valid, but it is not the current bottleneck.

### Phase 5: ONNX Export + Rust CLI

**Status**: Deferred  
**When to activate**: Only after a transformer actually wins

Do not invest in deployment until the research question is settled.

## Current Plan In One Sentence

Run fair V2 first, run small-model V2 second if needed, keep temperature sweep as a later calibration check, and leave the context-aware rebuild deferred unless fair V2 still fails.

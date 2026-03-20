# Next_Plan: Beat LSTM with Context-Aware Transformer + Deploy as CLI Tool

## Context

DirHunterT transformer **fails** to beat the LSTM baseline (-7.6% overall). The LSTM wins because:
1. It implicitly learns cross-path correlations via hidden state carry-over during training
2. The transformer sees each 7-12 token path in complete isolation
3. The transformer is 3-9x over-parameterized (11-31M vs 3.4M params)
4. Short sequences (7-12 tokens) don't benefit from attention

**Strategy**: Build a context-aware transformer that conditions predictions on ALL previously discovered paths — something the LSTM architecturally cannot do. But first, run diagnostic experiments to validate hypotheses before committing to the full rebuild.

**End goal**: Beat LSTM by >30% in all 4 sectors, then compile into a Rust CLI tool that outperforms gobuster/feroxbuster.

---

## Phase 0: Diagnostic Experiments (Before Building Anything)

**Purpose**: Validate root cause hypotheses with cheap experiments. Stop investing in the wrong direction early.

### 0A. Temperature Sweep on Existing Transformer Models

**What**: Evaluate existing 4 best transformer models across 8 temperatures.
**Files**: None to modify — CLI already supports `--temperature-sweep`.
**Command**:
```bash
cd transformer_pipeline
python3 main.py evaluate \
  --temperature-sweep 0.5 0.7 0.8 0.9 1.0 1.2 1.5 2.0 \
  --prediction-sweep 500 750 1000 \
  --results-folder ./results/temp_sweep
```
**What it tells us**:
- temp > 1.0 helps => transformer is overconfident, calibration is fixable
- temp < 1.0 helps => transformer is underconfident
- no temp helps => the learned representations themselves are weak

**Time**: ~4 hours on GPU

### 0B. Small Model Grid Search

**What**: Train transformers with LSTM-scale parameter counts.
**File to create**: `transformer_pipeline/src/diagnostic_grid.py` (~40 lines)
- Subclass `TransformerGridSearch`, override grid to:
  - `d_model_sizes = [64, 128]`
  - `n_heads_list = [2, 4]`
  - `n_layers_list = [2, 3]`
  - `dropout_rates = [0.2, 0.4]`
- Total: 4 global x 16 arch = 64 combos
**What it tells us**:
- Small model >= large model => over-parameterization confirmed
- Small model << large model => capacity isn't the issue

**Time**: ~6 hours on GPU

### 0C. LSTM Context Hack Baseline

**What**: Test if feeding discovered paths through LSTM hidden state before predicting improves results.
**File to create**: `lstm_pipeline/src/inference_context_hack.py` (~80 lines)
- New `generate_with_primed_hidden()`:
  - Accept list of discovered path token sequences
  - Run model forward on concatenated discovered paths to "prime" hidden state
  - Then predict next token for current partial path using primed hidden state
- Wrap as `custom_tokenizer` for existing `lm_attack()`
**What it tells us**:
- LSTM-with-context > LSTM-without-context => cross-path info helps, justifies Phase 1-3
- The gap size = theoretical ceiling for context benefit on LSTM architecture

**Time**: ~3 hours on GPU

### 0D. Analysis

**File to create**: `diagnostics/analyze_phase0.py` (~80 lines)
- Load results from 0A, 0B, 0C
- Produce summary table: best temperature, small vs large model, context vs no-context
- Print go/no-go recommendation

### Phase 0 Gate (must pass at least ONE):
- [ ] Temperature sweep improves transformer by >10% in >=2 sectors
- [ ] Small model outperforms large model in >=2 sectors
- [ ] LSTM-with-context > LSTM-without-context by >5% (context helps)

**If none pass**: Root causes are wrong. Reassess before proceeding.

---

## Phase 1: Context-Aware Data Pipeline

**Purpose**: New data loader that groups paths by domain and creates multi-path training sequences.

### Key Design Decisions

**Sequence format** (multi-path with `<sep>` separator):
```
<sos> ctx1_tok1 ctx1_tok2 <eos> <sep> <sos> ctx2_tok1 <eos> <sep> <sos> target_tok1 target_tok2 <eos> <pad>...
```

**Context window**: `context_paths=5` default, `context_max_tokens=64`
- 5 context paths x ~4 tokens avg = ~25 tokens
- 1 target path = ~7 tokens (with SOS/EOS)
- 5 separators = 5 tokens
- Total ~37 tokens, well under 64 cap

**Target masking**: Loss computed ONLY on target path tokens. Context and `<sep>` positions masked with `ignore_index=-100` in the target tensor.

**`<sep>` token**: Appended to vocabulary after existing special tokens (indices 0-3 preserved).

### Files to Create

**`transformer_pipeline/src/data_context.py`** (~200 lines)
- `create_vocabulary_with_sep(train_df, min_freq, max_depth)` — extends vocab with `<sep>`
- `ContextPathDataset(torch.utils.data.Dataset)`:
  - Init: takes train_df, vocab, max_depth, context_paths, context_max_tokens
  - Groups paths by domain (`Filename` column)
  - `__getitem__`: for path P from domain D:
    1. Randomly sample `context_paths` other paths from D
    2. Tokenize all paths (custom_tokenizer + SOS/EOS wrapping)
    3. Concatenate: `ctx1 <sep> ctx2 <sep> ... <sep> target`
    4. Truncate from left to `context_max_tokens` (preserve target path)
    5. Build `path_position_ids` (which path each token belongs to)
    6. Build `depth_ids` (depth within each individual path)
    7. Build `target_mask` (-100 for context positions, real token index for target)
  - Returns: `{input_ids, path_position_ids, depth_ids, target_ids}`
- `collate_fn`: pad batch to max length, pad target_ids with -100
- `get_context_dataloaders(...)` — returns vocab, train_loader, valid_loader

**`transformer_pipeline/src/data_context_test.py`** (~50 lines)
- Validation script: load data, print 10 sequences in readable form, verify token alignment

### Verification
- [ ] `vocab['<sep>']` returns valid index
- [ ] Sequences with `context_paths=0` match existing single-path format
- [ ] Target mask correctly has -100 on all context positions
- [ ] Print 10 random sequences and manually verify correctness

---

## Phase 2: Context-Aware Model

**Purpose**: Modified DirHunterT with two-level positional embeddings and right-sized capacity.

### Architecture: DirHunterT_Context

**Embeddings** (all additive):
1. `token_embedding(vocab_size, d_model)` — same as current
2. `depth_embedding(max_depth + 2, d_model)` — position within each path (resets at `<sep>`)
3. `path_position_embedding(max_context_paths + 2, d_model)` — which path in the sequence (NEW)

**Transformer**: Same causal self-attention, pre-layer norm. Standard causal mask — target tokens naturally attend to all context tokens.

**Target model size**: d_model=128, n_layers=3, n_heads=4 -> ~4-5M params (comparable to LSTM's 3.4M)

### Files to Create

**`transformer_pipeline/src/model_context.py`** (~300 lines)
- `DirHunterT_Context(nn.Module)`:
  - `forward(src, hidden=None, path_position_ids=None, depth_ids=None)`
  - Backward compat: when path_position_ids=None, falls back to simple depth embedding
  - LSTM-compatible stubs: `init_hidden()` -> None, `detach_hidden()` -> None

**`transformer_pipeline/src/training_context.py`** (~150 lines)
- DataLoader-based training loop (not flat tensor sliding window)
- `CrossEntropyLoss(ignore_index=-100)` — masks padding AND context tokens
- Same warmup + plateau scheduler + early stopping

**`transformer_pipeline/src/grid_search_context.py`** (~250 lines)
- Two-stage search:
  - Stage 1: Fix context_paths=5, search d_model={64,128,256}, n_layers={2,3,4}, n_heads={2,4}, dropout={0.2,0.4} -> 48 combos/global pair
  - Stage 2: Best arch from stage 1, sweep context_paths={0,3,5,10} -> 4 combos/global pair
  - Total: ~208 combos

### Files to Modify
- `transformer_pipeline/main.py` — add `train-context` subcommand

### Verification
- [ ] Model param count 4-5M for d_model=128, n_layers=3
- [ ] Forward: (B, 64) -> (B, 64, vocab_size)
- [ ] Smoke test: 1 model, 1 epoch, loss decreases
- [ ] context_paths=0 val loss matches existing non-context model

---

## Phase 3: Context-Aware Attack Loop

**Purpose**: Modified `lm_attack()` that feeds discovered paths as context.

### How It Works

```
Round 1: context = []
  -> Model predicts top-K root directories (same as current)
  -> Discover /api/, /admin/

Round 2: context = ["/api/", "/admin/"]
  -> Model sees BOTH discoveries, adjusts predictions
  -> /docs/, /swagger/, /login/ become more likely

Round 3: context = ["/api/", "/admin/", "/docs/", "/api/v1/"]
  -> Predictions get sharper with each discovery
  -> Model adapts to site archetype
```

### Files to Create

**`transformer_pipeline/src/inference_context.py`** (~120 lines)
- `generate_with_context(model, token_list, discovered_paths, vocab, max_depth, device, prediction_limit, max_context_paths=10, temperature=1.0)`:
  - Build context sequence from last N discovered paths + current partial path
  - Construct `input_ids`, `path_position_ids`, `depth_ids` tensors
  - Forward pass, logits at last position, top-K extraction
  - Empty `discovered_paths` = identical to standard `generate()`

**`transformer_pipeline/src/attacks_context.py`** (~150 lines)
- `lm_attack_context(...)`:
  - Same heap-based exploration as existing `lm_attack()`
  - Maintains `discovered_paths = []` — grows as directories found
  - Each call to `generate_with_context()` passes accumulated discoveries
  - Model gets smarter as attack progresses

### Files to Modify
- `transformer_pipeline/main.py` — add `evaluate-context` subcommand

### Verification
- [ ] `max_context_paths=0` produces identical results to standard `lm_attack()`
- [ ] Top-5 predictions visibly change as context accumulates
- [ ] Inference <50ms per call

---

## Phase 4: Full Evaluation and Comparison

**Purpose**: Run all approaches on 119 test domains, produce the paper's comparison table.

### The Ablation Table

| Approach | UNI | HOS | COM | GOV | Mean |
|----------|-----|-----|-----|-----|------|
| BFS (wordlist baseline) | ... | ... | ... | ... | ... |
| Probabilistic | ... | ... | ... | ... | ... |
| LSTM + lm_attack | 33.2 | 62.4 | 40.5 | 35.5 | 42.9 |
| LSTM + context hack (0C) | ? | ? | ? | ? | ? |
| Transformer + lm_attack (no ctx) | 31.5 | 64.4 | 30.2 | 32.4 | 39.6 |
| **Transformer + context-aware** | **?** | **?** | **?** | **?** | **?** |

Row 4 (LSTM+hack) shows LSTM can't exploit context well.
Row 5 (Transformer no-ctx) shows same-strategy = transformer loses.
Row 6 (Transformer+ctx) shows the full system wins.

### Files to Create
- `transformer_pipeline/evaluate_full.py` (~200 lines) — unified eval across all approaches
- `lstm_pipeline/plot_tables_v2.py` (~150 lines) — extended comparison + updated gate check

### Gate Check
- [ ] Context-aware transformer beats LSTM by >30% in ALL 4 sectors

---

## Phase 5: ONNX Export + Rust CLI (huntert)

**Purpose**: Production deployment as fast single-binary CLI tool.

### Python Export
- `transformer_pipeline/src/export_onnx.py` (~150 lines) — torch.onnx.export + int8 quantization
- `transformer_pipeline/src/export_vocab.py` (~50 lines) — vocab as JSON

### Rust CLI Structure

```
dirhunter_cli/
  Cargo.toml          — ort, tokio, reqwest, clap, serde_json
  src/
    main.rs           — CLI: --target, --model, --vocab, --budget, --rps, --output
    model.rs          — ONNX inference wrapper, top-K prediction
    tokenizer.rs      — Split on /, YEAR replacement, context sequence builder
    attack.rs         — Context-aware heap attack + async HTTP
    output.rs         — JSON output of discovered paths
```

### Usage
```bash
huntert scan --target https://example.com \
             --model model.onnx \
             --vocab vocab.json \
             --budget 100000 \
             --context-paths 10 \
             --rps 50 \
             --output results.json
```

### Why This Beats gobuster/feroxbuster
| Feature | gobuster/feroxbuster | huntert |
|---------|---------------------|---------|
| Strategy | Static wordlist | Adaptive — learns from each discovery |
| Prioritization | None | Probability-ranked heap |
| Request efficiency | ~2-5% hit rate | Target: 10-20%+ hit rate |
| Speed | Very fast | Equally fast (Rust + async) |
| Model size | N/A | ~4-8MB embedded ONNX |

---

## Timeline

```
Phase 0 (1-2 days)  ─── diagnostics, validate hypotheses
       |
       v gate: at least one hypothesis confirmed
Phase 1 (2-3 days)  ─── context data pipeline
       |
       v gate: data_context_test.py passes
Phase 2 (3-4 days)  ─── context model + grid search
       |
       v gate: smoke test passes, val loss improves with context
Phase 3 (1-2 days)  ─── context attack loop
       |
       v gate: context_paths=0 matches baseline
Phase 4 (2-3 days)  ─── full evaluation (mostly GPU time)
       |
       v gate: >30% over LSTM in ALL 4 sectors
Phase 5 (4-5 days)  ─── ONNX export + Rust CLI
```

**Total: ~13-19 days + GPU training time**

## New Files Summary

| Phase | Files | Est. Lines |
|-------|-------|-----------|
| 0 | `diagnostic_grid.py`, `inference_context_hack.py`, `analyze_phase0.py` | ~200 |
| 1 | `data_context.py`, `data_context_test.py` | ~250 |
| 2 | `model_context.py`, `training_context.py`, `grid_search_context.py` | ~700 |
| 3 | `inference_context.py`, `attacks_context.py` | ~270 |
| 4 | `evaluate_full.py`, `plot_tables_v2.py` | ~350 |
| 5 | 2 Python export + 6 Rust source files | ~840 |
| **Total** | **~20 new files** | **~2,600 lines** |

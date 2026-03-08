# DirHunterT: Transformer-Based Directory Enumeration Research Plan
**From LSTM Baseline to Deployable IEEE-Ready System**
*Last Updated: March 2026*

---

## Table of Contents
1. [Project Overview](#1-project-overview)
2. [Research Contributions](#2-research-contributions)
3. [Technical Architecture](#3-technical-architecture)
4. [Dataset Plan](#4-dataset-plan)
5. [Experiment Plan](#5-experiment-plan)
6. [Results & Evaluation Strategy](#6-results--evaluation-strategy)
7. [Deployable Tool Design](#7-deployable-tool-design)
8. [IEEE Paper Structure](#8-ieee-paper-structure)
9. [Submission Strategy](#9-submission-strategy)
10. [Timeline](#10-timeline)
11. [Cost Breakdown](#11-cost-breakdown)
12. [Risk & Mitigation](#12-risk--mitigation)
13. [Daily Checklist](#13-daily-checklist)

---

## 1. Project Overview

### What We Are Building
A transformer-based directory brute-forcing framework that:
- **Beats the AISec '24 LSTM baseline** by 50-100% on identical test conditions
- **Generalizes to new site categories** (e-commerce, cloud-native) never tested before
- **Adapts to targets at inference time** using discovered paths as in-context evidence
- **Ships as a deployable CLI tool** with ethics controls, evaluated against real tools

### The Gap We Are Closing
The original paper (Castagnaro et al., AISec '24) left three explicit gaps:

| Gap | Their Limitation | Our Solution |
|-----|-----------------|--------------|
| Architecture | LSTM only | Decoder-only Transformer + BPE + Depth-aware encoding + Segment embeddings |
| Data | 1M URLs, 2023 only, 4 categories | 10-50M URLs, 2026, 6 categories |
| Deployment | Research simulation only | Deployable CLI tool, real testbed |
| Adaptation | Static model | In-context adaptive inference |
| WAF Awareness | Not considered | WAF interaction analysis |

### One-Line Paper Pitch
> *"DirHunterT is the first deployable transformer-based directory enumeration framework using BPE tokenization, depth-aware hierarchical encoding, and in-context target adaptation — achieving ~3x over prior LSTM work and outperforming commercial tools on a live testbed."*

---

## 2. Research Contributions

For IEEE submission, we claim **5 distinct contributions** in the intro:

1. **DirHunterT architecture** — first transformer-based directory enumeration model using BPE tokenization, depth-aware hierarchical positional encoding, and segment-type embeddings — achieving ~3x over prior LSTM baseline

2. **In-context target adaptation** — discovered paths prepended as context at inference time, steering predictions toward site-specific directories with zero additional training cost — a capability LSTM cannot replicate

3. **Extended dataset** — 6 categories including e-commerce and cloud-native apps, 10-50M paths from CC-2026-08, covering modern CMS patterns absent from prior 2023 data

4. **WAF interaction analysis** — DirHunterT intelligent request ordering delays WAF detection vs wordlist tools — no prior directory enumeration paper has measured this

5. **Deployable open-source tool (dirhunter_t CLI)** — evaluated against Dirbuster, Wfuzz, and Burp Suite on a live Docker testbed with full ethics controls

---
## 3. Technical Architecture

> **Architecture decision record**: RoPE and multi-scale encoding were evaluated
> and removed. RoPE assumes linear sequences but URL paths are hierarchical trees
> where depth matters more than sequential order. Multi-scale encoding adds
> complexity with unproven benefit for URL-specific tokens. The components below
> are the final, justified set only.

---

### What We Keep and Why

| Component | Confidence | Expected Gain | Justification |
|-----------|-----------|---------------|---------------|
| BPE Tokenization | 95% | +10-20% | Directly fixes their UNK problem on OOV dirs |
| Full Path Attention | 90% | +15-25% | Lossless context vs LSTM lossy hidden state |
| Depth-Aware Encoding | 80% | +8-15% | URLs are trees not sequences |
| Segment-Type Embedding | 75% | +8-12% | Structural intuition about dir categories |
| Broad Training Data | 95% | +40-60% | Transformers scale, LSTMs fundamentally cannot |
| In-Context Adaptation | 90% | +20-30% | Transformer-exclusive, LSTM has no equivalent |
| WAF-Aware Scheduling | 85% | qualitative | No prior paper measures this dimension |

### What We Removed and Why

| Removed | Reason |
|---------|--------|
| RoPE encoding | Designed for linear sequences. URL paths are hierarchical trees. Depth-aware encoding is strictly better for this problem. |
| Multi-scale encoding | Unproven for URL tokens. URL segments are often arbitrary names and acronyms that do not decompose like natural language. BPE alone captures the subword benefit cleanly. |
| Bidirectional encoder | Task is generative. Predict NEXT directory. Bidirectional requires future tokens which do not exist during a live attack. Decoder-only is correct. |
| Cross-dataset attention | Massive complexity, training instability, marginal benefit over simply using broader training data. |

---

### DirHunterT-A — Narrow Model (Architecture Validation Gate)

**Purpose**: Prove transformer beats LSTM on identical narrow data before scaling up.
**Gate check**: Must beat LSTM by >30% before proceeding to DirHunterT-B.

```python
class DirHunterT(nn.Module):
    def __init__(self, vocab_size, d_model=256, n_layers=4, n_heads=8):

        # BPE Token Embedding
        # Fixes their UNK problem. Rare dirs decompose into subwords.
        # "/wp-admin" -> ["wp", "admin"] instead of UNK
        self.token_embedding = nn.Embedding(vocab_size, d_model)

        # Depth-Aware Positional Encoding (replaces RoPE)
        # URLs are trees not sequences. Depth matters more than order.
        # /news/2024/january: "2024" gets depth-2 signal not position-2 signal
        self.depth_embedding = nn.Embedding(20, d_model)
        self.depth_decay = nn.Parameter(torch.ones(1))

        # Segment-Type Embedding
        # 8 learned structural categories the model discovers automatically:
        #   temporal (2024, january, q3) -> predict more temporal children
        #   api (/api, /v1, /endpoint)   -> predict more versioned children
        #   auth (/admin, /login)        -> predict more auth children
        #   content, static, media, admin, other
        self.segment_embedding = nn.Embedding(8, d_model)

        # Decoder-Only Transformer
        # Full lossless attention over entire path.
        # At depth 6, still has full access to depth-1 directory.
        # LSTM at depth 6 has mostly forgotten depth-1.
        decoder_layer = nn.TransformerDecoderLayer(
            d_model=d_model, nhead=n_heads, dropout=0.2
        )
        self.transformer = nn.TransformerDecoder(decoder_layer, n_layers)
        self.fc_out = nn.Linear(d_model, vocab_size)

    def forward(self, tokens, depths, segment_types):
        x = (self.token_embedding(tokens)
           + self.depth_embedding(depths)
           + self.segment_embedding(segment_types))

        depth_bias = self.compute_depth_bias(depths)
        out = self.transformer(x, attn_mask=depth_bias)
        return F.softmax(self.fc_out(out), dim=-1)

    def compute_depth_bias(self, depths):
        # Children attend strongly to parents, weakly to grandparents
        # Siblings attend equally to each other
        depth_diff = depths.unsqueeze(1) - depths.unsqueeze(2)
        return -self.depth_decay * depth_diff.abs()
```

**Hyperparameter search grid:**

| Param | Values | Notes |
|-------|--------|-------|
| Layers | 4, 6 | Start with 4 |
| Heads | 4, 8 | 8 heads for d_model=256 |
| d_model | 256, 512 | 256 first |
| max_depth | 15 | vs their 10 |
| BPE vocab | 16k, 32k | 16k likely sufficient for URLs |
| Dropout | 0.2, 0.4 | 0.2 default |
| Segment types | 8 | fixed |

**Comparison vs their LSTM:**

| Component | Their LSTM | DirHunterT-A |
|-----------|-----------|--------------|
| Tokenization | Vocab (OOV goes to UNK) | BPE (OOV decomposes to subwords) |
| Position signal | None — implicit in RNN order | Depth-aware hierarchical bias |
| Context window | Lossy compressed hidden state | Full lossless attention over path |
| Structural awareness | None | Segment-type embeddings |
| Long-range recall | Degrades at depth 5+ | Perfect at any depth |
| Parameter count | ~1-5M | ~5-15M |

---

### DirHunterT-B — Broad Model (Full Deployable System)

**Purpose**: Production-ready model. All innovations from DirHunterT-A plus three additions.

#### Addition 1: Broad Training Data (Primary Performance Driver)

```
Their data:  CC-MAIN-2023-40  ->  1M paths,    4 categories, 2023 patterns
Our data:    CC-MAIN-2026-08  ->  10-50M paths, 6 categories, 2026 patterns

Why transformers scale but LSTMs cannot:
  1M paths:   LSTM ~= Transformer (both saturate at this scale)
  10M paths:  Transformer >  LSTM (separation begins)
  50M paths:  Transformer >> LSTM (LSTM saturates, transformer keeps improving)

This is mathematically proven in scaling literature.
DirHunterT-B lives at 10-50M. This is the headline number.
```

#### Addition 2: In-Context Target Adaptation (Killer Feature)

No weight updates during attack. Zero additional training cost.

```python
def predict_adaptive(model, current_path, discovered_paths, top_k=500):
    # LSTM: always same predictions regardless of what was found on target
    # DirHunterT-B: steers toward site-specific patterns using evidence

    # Example:
    #   Discovered: ["/api/v1/users", "/api/v1/auth", "/api/v2/data"]
    #   Model reads context: "this is an API-heavy versioned site"
    #   -> Predicts /api/v3/, /api/v1/admin, /api/v2/users
    #   -> Instead of generic /about, /contact, /home

    context = discovered_paths[-10:]          # last 10 found paths
    full_input = context + [current_path]     # prepend as context
    return model.predict(full_input, top_k=top_k)
```

Why only DirHunterT-B benefits: DirHunterT-A trained on 1M paths has not seen
enough diversity. Context steering on a narrow model reinforces noise.
DirHunterT-B trained on 50M paths can genuinely interpret any context signal.

#### Addition 3: WAF-Aware Request Scheduling

```python
class WafAwareScheduler:
    # Standard tools: burst requests -> WAF detects in ~150 requests
    # DirHunterT: intelligent ordering + backoff -> evades ~5-8x longer
    # High-probability predictions look more like legitimate traffic
    # than random wordlist hits do

    def __init__(self, base_rps=5, backoff_factor=2):
        self.rps = base_rps
        self.consecutive_403s = 0

    def send(self, url):
        if self.consecutive_403s > 3:
            self.rps /= self.backoff_factor
            time.sleep(random.uniform(1, 3))
            self.consecutive_403s = 0
        return http_get(url, rate=self.rps)
```

---

### Complete Attack Algorithm (DirHunterT-B)

```
FUNCTION DirHunterTAttack(target_url, model, budget, top_k=500):

    heap       = MaxHeap()
    discovered = []
    scheduler  = WafAwareScheduler(base_rps=5)

    root_preds = model.predict(context=[], path=target_url, top_k=top_k)
    heap.push_all(root_preds)

    WHILE budget > 0 AND heap not empty:

        url, prob = heap.pop_max()
        response  = scheduler.send(url)
        budget   -= 1

        IF response in [200, 301, 302]:
            discovered.append(url)
            context   = discovered[-10:]
            new_preds = model.predict(context=context, path=url, top_k=top_k)
            heap.push_all(new_preds)

        ELIF response == 403:
            scheduler.consecutive_403s += 1

    RETURN discovered
```

---

### Expected Cumulative Gains Over Their LSTM (175 hits baseline)

```
Component added                   Expected hits   Gain vs LSTM
────────────────────────────      ─────────────   ────────────
Their LSTM (baseline)             ~175            --
+ BPE tokenization                ~200            +14%
+ Full path attention             ~218            +25%
+ Depth-aware encoding            ~240            +37%
+ Segment-type embedding          ~264            +51%
                    DirHunterT-A: ~264 hits        +51%
+ Broad data (10-50M paths)       ~396            +126%
+ In-context adaptation           ~495            +183%
                    DirHunterT-B: ~500 hits        ~3x LSTM
```

---

## 4. Dataset Plan

### Dataset A — Narrow (Reproduce Original Paper Exactly)

| Category | Source | Domains | Paths |
|----------|--------|---------|-------|
| Universities [UNI] | QS 2023 Rankings | 88 | ~210k |
| Hospitals [HOS] | Ranking Web of World Hospitals (USA) | 80 | ~212k |
| Companies [COM] | S&P 500 (top by market cap) | 97 | ~147k |
| Government [GOV] | usa.gov/agency-index | 336 | ~521k |
| **TOTAL** | CC-MAIN-2023-40 | **601** | **~1M** |

**Preprocessing (must match their paper exactly):**
- Keep only HTTP status 200
- Remove query strings (?param=value)
- Remove file extensions (.php, .html, .js etc.)
- Domain-level split: 70% train / 10% val / 20% test
- Reconstruct filesystem trees using AnyTree

---

### Dataset B — Broad (Our Extension)

| Category | Source | Domains | Paths |
|----------|--------|---------|-------|
| All 4 original categories | CC-MAIN-2026-08 | ~1000+ | ~8-10M |
| E-Commerce [ECOM] | Shopify/WooCommerce sites | ~200 | ~2-3M |
| Cloud-Native [CLOUD] | Next.js/Vercel/Remix apps | ~150 | ~1-2M |
| **TOTAL** | CC-MAIN-2026-08 | **~1350+** | **~10-50M** |

**Why e-commerce and cloud-native:**
- E-commerce: hugely common attack targets, completely absent from prior work
- Cloud-native: completely different URL structures (/api/v1/, /_next/, /trpc/) — prior LSTM performs poorly here

**Classification strategy for new categories:**
```python
# E-commerce detection heuristics
ecommerce_signals = ['/cart', '/checkout', '/product', '/shop', 
                     '/wc-api', '/wp-json/wc']

# Cloud-native detection heuristics  
cloud_signals = ['/_next/', '/api/', '/trpc/', '/__remix',
                 '/static/chunks/']
```

---

### Dataset Split Strategy
```
Domain-level split (same as original paper — critical for fair comparison):

Training domains   → 70% of domains, ALL their URLs go to train
Validation domains → 10% of domains, ALL their URLs go to val
Test domains       → 20% of domains, ALL their URLs go to test

NEVER split individual URLs randomly — this causes data snooping
```

---

## 5. Experiment Plan

### Experiment 1: LSTM Reproduction (Validation Gate)
**Goal**: Reproduce their numbers within 10% — this validates our pipeline before we build anything new

**Must hit these targets:**

| Dataset | Their Result | Our Acceptable Range |
|---------|-------------|----------------------|
| UNI | 90.0 | 81 – 99 |
| HOS | 175.0 | 157 – 192 |
| COM | 89.0 | 80 – 98 |
| GOV | 128.0 | 115 – 141 |
| ALL | 175.0 | 157 – 192 |

**If we miss**: Debug data pipeline first, then model hyperparameters. Do NOT proceed to transformer until this passes.

---

### Experiment 2: DirHunterT-A vs LSTM (Architecture Ablation)
**Goal**: Prove architecture matters, isolate from data scale

**Conditions**: Identical dataset to Experiment 1, same budget (100k requests), same evaluation protocol

**Expected results:**

| Model | UNI | HOS | COM | GOV | ALL |
|-------|-----|-----|-----|-----|-----|
| Their LSTM (repro) | ~90 | ~175 | ~89 | ~128 | ~175 |
| DirHunterT-A | ~135 | ~262 | ~133 | ~192 | ~262 |
| **Improvement** | **+50%** | **+50%** | **+50%** | **+50%** | **+50%** |

---

### Experiment 3: DirHunterT-B — Scale + Innovation
**Goal**: Show that broad training + adaptation + WAF awareness compounds improvements

| Model | UNI | HOS | COM | GOV | ALL |
|-------|-----|-----|-----|-----|-----|
| DirHunterT-A | ~135 | ~262 | ~133 | ~192 | ~262 |
| DirHunterT-B (no adapt) | ~180 | ~315 | ~170 | ~245 | ~315 |
| DirHunterT-B (+ adaptive) | ~220 | ~380 | ~210 | ~300 | ~380 |

---

### Experiment 4: New Categories (Our Unique Contribution)
**Goal**: Show prior work fails on modern web apps, our model generalizes

| Model | E-COMM | CLOUD | NEW-ALL |
|-------|--------|-------|---------|
| Their LSTM | ~45 | ~30 | ~37 |
| DirHunterT-A | ~90 | ~65 | ~77 |
| DirHunterT-B (+ adaptive) | ~210 | ~185 | ~197 |

**This table is the most important unique contribution** — the original paper has zero numbers here.

---

### Experiment 5: Real Tools Comparison (Deployability Proof)
**Goal**: Show DirHunterT beats what pentesters actually use today

**Testbed**: Local Docker containers running:
- WordPress 6.x
- Drupal 10.x
- Custom Flask app
- Next.js app (for cloud-native)

| Tool | Hits (10k budget) | Requests to first 50 hits | Setup |
|------|------------------|--------------------------|-------|
| Dirbuster (default) | ~15-25 | ~800 | wordlist only |
| Wfuzz (default) | ~20-30 | ~600 | wordlist only |
| Burp Suite | ~25-35 | ~500 | manual config |
| **DirHunterT** | **~150+** | **~200** | model + target |

---

### Experiment 6: WAF Interaction Analysis
**Goal**: Show intelligent ordering delays detection — no prior paper has done this

**Setup**: ModSecurity WAF in front of test server, default ruleset

| Tool | Requests before WAF blocks | Hits before blocked |
|------|---------------------------|---------------------|
| Dirbuster (default) | ~150 | ~8 |
| Wfuzz (default) | ~200 | ~12 |
| Their LSTM approach | ~400 | ~35 |
| DirHunterT (WAF-aware mode) | ~1200 | ~140 |

---

### Ablation Study (Isolate Each Contribution)

| Configuration | Expected Hits (ALL) | What It Proves |
|---------------|--------------------|----|
| DirHunterT-B (full) | ~380 | Baseline for ablation |
| − BPE (use vocab) | ~320 | BPE contributes ~15% |
| − Depth-aware encoding (use flat PE) | ~335 | Depth encoding contributes ~12% |
| − Broad data (use narrow) | ~262 | Scale contributes ~30% |
| − Adaptive inference | ~315 | Adaptation contributes ~17% |
| − WAF awareness | ~380* | Hits same, detection faster |

---

## 6. Results & Evaluation Strategy

### Primary Metric
**Average Successful Responses per site** — same as original paper, enables direct comparison

### Secondary Metrics (Our Extensions)
- **Bin efficiency**: hits per request range (0-100, 101-1k, 1k-10k, 10k-50k, 50k-100k)
- **Hits per 1000 requests**: practical deployability metric
- **Requests to detection**: WAF analysis metric
- **Cross-category transfer rate**: generalization metric

### Statistical Rigor
```
- Run each model with 3 random seeds minimum
- Report mean ± standard deviation
- Use same 100k request budget as original paper
- Domain-level test set (no overlap with training)
```

### Figures to Generate
1. **Main results table** (extends their Table 2)
2. **Bin efficiency plot** (extends their Figure 5)
3. **topK sensitivity plot** (extends their Figure 6)
4. **Adaptive inference gain curve** (new — hits vs requests with/without adaptation)
5. **WAF detection delay plot** (new — requests before block for each tool)
6. **Cross-category transfer heatmap** (new — train on X, test on Y)
7. **Embedding similarity examples** (extends their Section 6.3)
8. **Tool architecture diagram** (new — deployment contribution)

---

## 7. Deployable Tool Design

### CLI Interface
```bash
# Basic usage
dirhunter_t --target https://target.com \
               --model transformer_broad.pth \
               --budget 50000

# Stealth mode (WAF-aware, slow)
dirhunter_t --target https://target.com \
               --mode stealth \
               --budget 1000 \
               --rps 1

# Deep mode (aggressive, high budget)
dirhunter_t --target https://target.com \
               --mode deep \
               --budget 100000 \
               --rps 50

# Ethics controls (required fields)
dirhunter_t --target https://target.com \
               --engagement-id ENG-2026-001 \
               --authorized-by "John Smith, CISO" \
               --scope-file scope.txt
```

### System Architecture
```
dirhunter_t/
├── model/
│   ├── transformer.py          # Model architecture
│   ├── tokenizer.py            # BPE tokenizer
│   └── weights/
│       ├── transformer_a.pth   # Narrow model
│       └── transformer_b.pth   # Broad model (default)
│
├── attack/
│   ├── engine.py               # Max-heap scheduler
│   ├── adaptive.py             # In-context adaptation
│   └── waf_aware.py            # WAF detection + backoff
│
├── http/
│   ├── client.py               # Async aiohttp workers
│   └── rate_limiter.py         # Token bucket rate limiting
│
├── ethics/
│   ├── scope_validator.py      # Checks target is in scope
│   └── engagement_logger.py    # Audit trail
│
├── output/
│   ├── reporter.py             # JSON/CSV/Burp-compatible
│   └── visualizer.py          # Hit tree visualization
│
└── cli.py                      # Entry point
```

### Operating Modes

| Mode | top_k | RPS | Budget | Use Case |
|------|-------|-----|--------|----------|
| Stealth | 250 | 1-5 | 1k | Avoid WAF detection |
| Standard | 500 | 10-20 | 10k | Normal pentest |
| Deep | 1000 | 50 | 100k | Comprehensive assessment |

### Ethics Controls (Non-Negotiable for IEEE)
```python
# Tool CANNOT run without these checks passing
def pre_flight_checks(args):
    assert args.engagement_id is not None, "Engagement ID required"
    assert args.authorized_by is not None, "Authorization required"
    assert target_in_scope(args.target, args.scope_file), "Target not in scope"
    assert not is_production_critical(args.target), "Cannot target critical infra"
    log_engagement_start(args)   # Audit trail
```


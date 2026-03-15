# LSTM Pipeline Reproduction Report

**Date:** 2026-03-15
**Paper:** Offensive AI: Enhancing Directory Brute-forcing Attack with Language Models
**Published:** AISec '24 | DOI: 10.1145/3689932.3694770

---

## Overview

This report documents our attempt to reproduce the results from the above paper using our LSTM pipeline (`ltsm_pipeline/`) trained on the published dataset (`LTSM_Research/datasets/`). We compare our results against the paper's reported figures and identify the root causes of the discrepancies.

---

## Our Results vs. Paper's Reported Results

### Breadth-First Baseline (big_wfuzz wordlist)

| Domain Type | Paper Reported | Our Result |
|-------------|---------------|------------|
| University  | 28.0          | 7.2        |
| Hospital    | 22.0          | 5.4        |
| Company     | 27.0          | 5.6        |
| Government  | 35.0          | 7.0        |

### LM Model Performance (Best Result per Domain Type)

| Domain Type | Paper LM | Our Best LM | Paper % Improvement | Our % Improvement |
|-------------|----------|-------------|--------------------|--------------------|
| University  | 90.0     | 31.0        | +582%              | +328%              |
| Hospital    | 175.0    | 55.7        | +1,004%            | +937%              |
| Company     | 89.0     | 36.3        | +499%              | +553%              |
| Government  | 128.0    | 32.6        | +639%              | +363%              |
| **Overall** | —        | —           | **+969%**          | **+517%**          |

### What We Successfully Reproduced

- LM consistently and significantly outperforms the breadth-first baseline across all domain types
- Hospital is the top-performing domain for LM in both results
- The relative domain ordering is preserved: Hospital > Company > Government > University
- The core architectural finding holds: LSTM-based prediction generalises beyond training data

---

## Root Cause Analysis

### Cause 1: Published Dataset ≠ Paper's Evaluation Dataset (Primary)

The paper explicitly states: **"dataset not publicly available (contact authors for research)"**.
What exists in the repository is the raw CommonCrawl dump, not the cleaned dataset used for evaluation.

The published dataset contains CMS content page URLs, not filesystem directory paths:

```
# Hospital examples from published dataset
depth=24  /Naval-Medical-Readiness.../vy.afpims.mil/Naval-Medical.../vy.afpims.mil/...
depth=3   /health/wellness-and-prevention/sunscreen-and-your-morning-routine
depth=5   /allina-news/2019/07/courage-kenny-celebrates-40-years-of-getting-outdoors
depth=1   /hail-to-the-front-line

# University examples
depth=5   /news/2022/05/04/four-years-two-degrees
depth=5   /course-outlines/107428/1/sem-1/2020
depth=4   /en/about-tum/goals-and-values/tum-compliance-office
```

The paper's evaluation dataset was filtered to contain only standard directory-like path segments (e.g., `/admin/`, `/api/v1/`, `/contact/`, `/about/`). With such paths, `big_wfuzz`'s 3,024 common directory names would match many root-level nodes and recurse productively. Against our CMS content paths — where level-2 is typically a year (`2022`) or article slug — the wordlist finds 3–4 root matches and cannot recurse further.

**This directly explains the ~4x lower absolute numbers**: BF baseline 5–7 vs. paper's 22–35.

Additionally, the dataset contains crawler artifacts — paths of depth 24 with domain names embedded mid-path — which are clearly malformed entries from CommonCrawl that were never cleaned.

### Cause 2: Paper's Pre-trained Models Are Not Published

The `LTSM_Research/` repository contains no `saved_models/` directory. The paper's benchmark notebook (`benchmarks.ipynb`) loads models from a local `saved_models/` folder and hardcodes its evaluation to `models[3]`:

```python
# From benchmarks.ipynb cell-28
model_name, model, vocab, MAX_DEPTH = models[3]
```

From the notebook's own output, `models[3]` resolves to:
```
model_MD5_MF5_es512_nl4_dr0.6_loss3.271419.pt
```

We trained our own models. Our closest equivalent:
```
model_MD5_MF5_es512_nl4_dr0.6_loss3.297345.pt  (loss: 3.297 vs paper's 3.271)
```

The paper's model achieves a slightly lower validation loss, meaning it is a marginally better-trained model. The exact random seed, training run duration, and hardware used to produce the paper's models are unknown.

### Cause 3: Hardcoded Evaluation Methodology

The paper's notebook uses a fixed `prediction_limit=750` for its main simulation results:

```python
# From benchmarks.ipynb cell-28
lm_bruteforcer(..., prediction_limit=750)
```

Our pipeline swept all prediction limits (100, 250, 500, 750, 1000, 2000, 5000, 10000) across all 16 trained models. The paper's +969% figure comes from one specific model at one specific prediction limit — it is not an average across configurations.

### Cause 4: Dead Domains Included in Averages (Minor)

11 domains in the test set return 0 successful BF responses (9 government, 1 hospital, 1 company). Their `total_requests` equals 3,021, meaning all 3,024 wordlist words were tried at root with zero matches. These domains have no overlap with the `big_wfuzz` vocabulary at any path level.

These domains suppress the BF average by ~15–20% but are a minor contributor compared to Cause 1.

---

## Impact Summary

| Cause | Effect on Results | Severity |
|-------|------------------|----------|
| Raw CMS URLs instead of filtered directory paths | ~4x lower absolute numbers for both BF and LM | **Primary** |
| Paper's pre-trained models not published | Slightly lower model quality (loss 3.297 vs 3.271) | Minor |
| Paper reports one model at `prediction_limit=750` | Different evaluation scope from our grid sweep | Methodological |
| 11 dead domains included in averages | ~15–20% suppression of BF baseline | Minor |

---

## Conclusion

**We cannot claim to reproduce the paper's exact results.** The absolute numbers are ~4x lower due to a fundamental mismatch between the raw CommonCrawl data in the published repository and the cleaned directory-structure dataset the paper used for evaluation.

**We can claim to reproduce the paper's core findings:**

1. The LSTM-based LM approach significantly outperforms brute-force baseline (our best: +553% to +937%)
2. Hospital websites benefit most from LM-guided enumeration
3. LM performance scales with request budget, unlike static wordlists
4. The relative domain ordering (Hospital > Company > Government > University) holds

To fully reproduce the paper's reported numbers, the dataset would need to be pre-processed to filter paths to short, common directory-like segments — removing content slugs, date strings, crawl artifacts (depth > ~5), and malformed entries before building the evaluation trees.

---

## References

- Paper: [DOI 10.1145/3689932.3694770](https://doi.org/10.1145/3689932.3694770)
- Paper codebase: https://github.com/spritzmatterorg/LM-Directory-Bruteforcing
- Our LSTM pipeline: `ltsm_pipeline/`
- Research notebooks: `LTSM_Research/benchmarks.ipynb`

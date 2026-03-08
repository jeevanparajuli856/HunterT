---

## 8. IEEE Paper Structure

### Full Paper Outline

```
Title: "Transformer-Based Web Directory Enumeration: Architecture,
        Scale, and In-Context Adaptation for Deployable Offensive AI"

Abstract (250 words):
  - Problem: directory brute-forcing is inefficient
  - Gap: LSTM baseline not deployable, limited categories
  - Method: transformer + broad data + adaptive inference
  - Results: 2x over LSTM, beats real tools, new categories
  - Contribution: open-source deployable tool

1. Introduction (1.5 pages)
   1.1 The directory enumeration problem
   1.2 Why the LSTM baseline is insufficient
   1.3 Our contributions (5 bullet points)
   1.4 Paper organization

2. Background & Related Work (1 page)
   2.1 Directory brute-forcing (their Section 3)
   2.2 Transformer vs RNN for sequence prediction
   2.3 Offensive AI landscape (cite their related work)
   2.4 What we add beyond prior work

3. Dataset (1.5 pages)
   3.1 Narrow dataset (reproduce theirs exactly)
   3.2 Broad dataset extension (CC-2026-08)
   3.3 New categories: e-commerce and cloud-native
   3.4 Dataset statistics table
   3.5 Cross-category similarity analysis

4. DirHunterT Architecture (1.5 pages) — BPE, depth-aware encoding, segment embeddings, decoder-only transformer
   4.1 Why transformer over LSTM (theoretical motivation)
   4.2 BPE tokenization (handles OOV directories)
   4.3 Depth-aware hierarchical positional encoding
   4.4 Decoder-only architecture design
   4.5 Architecture diagram (Figure 1)
   4.6 Hyperparameter selection

5. Attack System & Innovations (1.5 pages)
   5.1 Extended heap algorithm (Algorithm 1)
   5.2 In-context target adaptation (Algorithm 2) ← KEY INNOVATION
   5.3 WAF-aware request scheduling (Algorithm 3)
   5.4 System architecture diagram (Figure 2)

6. Evaluation (3 pages)
   6.1 Experimental setup (testbed, budget, metrics)
   6.2 LSTM reproduction validation (Table 1)
   6.3 DirHunterT-A vs LSTM (Table 2) 
   6.4 DirHunterT-B — full system (Table 3) ← MAIN RESULTS
   6.5 New categories evaluation (Table 4)
   6.6 Real tools comparison (Table 5)
   6.7 WAF interaction analysis (Figure 3)
   6.8 Bin efficiency (Figure 4)
   6.9 Adaptive inference gain (Figure 5)
   6.10 Ablation study (Table 6)

7. Deployment (0.5 pages)
   7.1 Tool usage and modes
   7.2 Ethics controls
   7.3 Performance on live testbed

8. Discussion (0.5 pages)
   8.1 Limitations
   8.2 Defense recommendations
   8.3 Future work

9. Conclusion (0.25 pages)

Acknowledgments
References (~20-25 citations)
```

### Target Length
- IEEE conference: 10-12 pages (double column)
- IEEE TIFS journal: 14-16 pages

---

## 9. Submission Strategy

### The Rule: One Venue at a Time
Simultaneous submission = academic misconduct. Consequences include rejection from both venues, multi-year bans, and institutional reporting.

### Recommended Submission Order

| Priority | Venue | Type | Deadline (Est.) | Notification |
|----------|-------|------|-----------------|--------------|
| 1st | IEEE S&P 2027 | Conference | Nov 2026 | Feb 2027 |
| 2nd | IEEE CNS 2026 | Conference | June 2026 | Aug 2026 |
| 3rd | IEEE TrustCom 2026 | Conference | May 2026 | July 2026 |
| 4th | IEEE TIFS | Journal | Rolling | 3-6 months |
| Fallback | AISec 2026 | Workshop | July 2026 | Sept 2026 |

### arXiv Strategy (Highly Recommended)
```
April 2026:  Finish paper draft
May 2026:    Post on arXiv
             → Establishes timestamp and priority on your ideas
             → Most IEEE venues explicitly allow this
             → Protects you while waiting for review decisions
June 2026:   Submit to IEEE CNS or TrustCom
```

**Always check the specific venue's double-blind and arXiv policy before posting.**

### If Rejected (Normal — Most Papers Are Rejected Once)
```
Rejection from Venue A
        ↓
Read reviewer feedback carefully (usually 3 reviewers)
        ↓
Revise paper (add suggested experiments, clarify writing)
        ↓
Submit to Venue B (stronger paper now)
```

### Workshop → Conference Pipeline (Optional)
```
June 2026:   Submit short version to AISec 2026 workshop
             → Get community feedback early
             → Establish presence in the research community
Nov 2026:    Submit full extended version to IEEE S&P
             → Must add 30%+ new content (ethics requirement)
             → Workshop feedback makes the full paper stronger
```

---

## 10. Timeline

### March 2026 — Experiments

#### Week 1: Mar 8-15 — Foundation
```
Mar 8-9:   Setup & Data Start
  □ Email authors for code (luca.pajola@unipd.it, A.Castagnaro@student.tudelft.nl)
  □ Clone public repo: github.com/spritzmatterorg/LM-Directory-Bruteforcing
  □ Start downloading CC-MAIN-2023-40 (this takes time — start NOW)
  □ Set up Python environment + dependencies

Mar 10-11: Narrow Dataset Pipeline
  □ Build URL extractor from CommonCrawl WARC files
  □ Implement filtering (status 200, no queries, no file extensions)
  □ Build domain classifier (UNI/HOS/COM/GOV)
  □ Implement AnyTree filesystem reconstruction
  □ Validate: match their reported statistics (Table 1 in paper)

Mar 12-13: LSTM Reproduction
  □ Implement their LSTM architecture from paper description
  □ Implement vocabulary builder with min_freq threshold
  □ Implement training loop (Adam optimizer, CrossEntropy loss)
  □ Implement early stopping (patience=10)
  □ Domain-level 70/10/20 split

Mar 14-15: LSTM Validation
  □ Train LSTM with their hyperparameter grid
  □ Implement evaluation harness (avg hits, bin efficiency)
  □ Implement Algorithm 4 (LM-based attack)
  □ Run evaluation on test set
  □ GATE CHECK: Must hit within 10% of their numbers
```

#### Week 2: Mar 16-22 — DirHunterT-A Build + Broad Data Prep
```
Mar 16-17: DirHunterT-A Implementation
  □ Implement BPE tokenizer (HuggingFace tokenizers library, 16k vocab)
  □ Implement depth-aware positional encoding (depth embedding + learned bias)
  □ Implement segment-type classifier (8 types: temporal/api/auth/content/static/admin/media/other)
  □ Implement segment-type embedding layer
  □ Implement decoder-only transformer (4 layers, 8 heads, d_model=256)
  □ Implement compute_depth_bias() — children attend strongly to parents
  □ Implement training loop (Adam, CrossEntropy, early stopping patience=10)

Mar 18-19: DirHunterT-A Training + Broad Data Start
  □ Train DirHunterT-A on narrow dataset (laptop GPU)
  □ Run hyperparameter search (layers 4/6, heads 4/8, d_model 256/512)
  □ Start CC-MAIN-2026-08 download in parallel (takes days — start now)
  □ Build e-commerce site classifier (heuristic: /cart, /checkout, /wc-api)
  □ Build cloud-native site classifier (heuristic: /_next/, /trpc/, /api/)

Mar 20-21: Broad Dataset + GCP Setup
  □ Set up GCP account + A100 spot instance ($1.20/hr)
  □ Filter CC-2026-08 data (same preprocessing: status 200, no queries, no file extensions)
  □ Classify new categories (ECOM, CLOUD) using heuristics + manual spot check
  □ Validate new category data statistics
  □ Upload processed broad dataset to GCP Storage

Mar 22: DirHunterT-A Evaluation
  □ Run full evaluation: DirHunterT-A vs LSTM vs all 8 wordlist baselines
  □ Generate Table 2 (architecture comparison across UNI/HOS/COM/GOV/ALL)
  □ Run component ablations: remove BPE / remove depth encoding / remove segment embedding
  □ GATE CHECK: DirHunterT-A must beat LSTM by >30% — do not proceed until this passes
```

#### Week 3: Mar 23-31 — DirHunterT-B + Full Evaluation
```
Mar 23-24: DirHunterT-B Training
  □ Train DirHunterT-B on broad dataset (GCP A100)
  □ Monitor training loss + validation performance
  □ Save checkpoints every 5 epochs

Mar 25-26: Adaptive Inference Implementation
  □ Implement in-context adaptation mechanism
  □ Modify attack algorithm to use discovered paths as context
  □ Test on validation set
  □ Measure adaptation gain (hits with vs without)

Mar 27-28: Full Evaluation
  □ Run DirHunterT-B evaluation (all datasets including new categories)
  □ Set up Docker testbed (WordPress, Drupal, Flask, Next.js)
  □ Install Dirbuster, Wfuzz, Burp Suite
  □ Run real tools comparison (Table 5)

Mar 29-30: WAF + Ablations
  □ Set up ModSecurity WAF on testbed
  □ Run WAF interaction analysis
  □ Run ablation study (remove each component one at a time)
  □ Generate all figures

Mar 31: Buffer + Paper Outline
  □ Fix any broken experiments
  □ Generate complete results tables
  □ Write paper outline with placeholder sections
```

---

### April 2026 — Paper Writing

```
Apr 1-7:   Core Sections
  □ Section 1: Introduction (nail the 5 contributions)
  □ Section 2: Background & Related Work
  □ Section 3: Dataset
  □ Section 4: Architecture

Apr 8-14:  Results Sections
  □ Section 5: Attack System & Innovations
  □ Section 6: Evaluation (main effort — all tables + figures)
  □ Section 7: Deployment

Apr 15-21: Polish
  □ Section 8: Discussion + limitations
  □ Section 9: Conclusion
  □ Abstract (write last)
  □ All figures finalized
  □ Proofread full paper

Apr 22-28: Final Prep
  □ Internal review (get feedback from advisors/colleagues)
  □ Address feedback
  □ Format for target venue (IEEE templates)
  □ Post to arXiv

Apr 29-30: Submit
  □ Submit to target IEEE venue
  □ Confirm submission received
```

---

## 11. Cost Breakdown

### Compute Costs
```
Laptop (your GPU):
  ✅ Data prep and filtering          → $0
  ✅ LSTM reproduction                → $0
  ✅ DirHunterT-A training           → $0
  ✅ Tool development                 → $0
  ✅ Local testbed evaluation         → $0

GCP (A100 spot @ $1.20/hr):
  ├── Data storage (GCS, 3 months)   → $1-5
  ├── DirHunterT-B training
  │     40 GPU hours × $1.20/hr      → $48
  ├── Evaluation runs                → $10-15
  └── Buffer                         → $10
  SUBTOTAL GCP                       → $69-78

TOTAL                                → $69-78
```

### Free Alternatives
```
Google Colab Pro+  → $50/month (good for DirHunterT-B if no GCP)
New GCP account    → $300 free credits (covers everything)
Kaggle notebooks   → Free T4/P100 GPU (slower but free)
University HPC     → Check if you have access
```

---

## 12. Risk & Mitigation

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Authors don't share code | Medium | Medium | Reproduce from pseudocode (fully described in paper) |
| CC-2026-08 download slow | High | High | Start immediately, use GCS for storage |
| LSTM reproduction fails | Medium | High | Debug pipeline first, contact authors |
| DirHunterT-A doesn't beat LSTM | Low | Very High | Check BPE tokenizer, verify depth-aware encoding, check segment classifier quality |
| GCP spot instance preempted | Medium | Medium | Use checkpointing every 5 epochs |
| New category classification noisy | Medium | Medium | Use conservative heuristics, manual spot check |
| WAF analysis inconclusive | Medium | Low | Move to future work if needed |
| Paper too long for venue | Medium | Medium | Cut ablations to appendix |
| Time overrun | High | Medium | Prioritize core experiments (Exp 1-4), cut Exp 5-6 if needed |

---

## 13. Daily Checklist

### Every Day
- [ ] Check CommonCrawl download progress
- [ ] Check GCP training job status
- [ ] Save all experiment results to shared drive immediately
- [ ] Note any bugs or unexpected results in lab notebook

### Every Week
- [ ] Review progress against timeline
- [ ] Adjust next week's plan if behind
- [ ] Back up all code + data + model checkpoints

### Before Each Experiment
- [ ] Document exact hyperparameters used
- [ ] Set random seeds for reproducibility
- [ ] Check test set is never used during development
- [ ] Save experiment config to JSON

### Before Paper Submission
- [ ] All results reproducible from documented configs
- [ ] All figures at 300 DPI minimum
- [ ] No test set data leaked into training
- [ ] Ethics statement included
- [ ] Code repository ready for public release
- [ ] Conflicts of interest declared
- [ ] Submission to ONE venue only

---

## Quick Reference: Key Numbers to Hit

| Milestone | Target | Status |
|-----------|--------|--------|
| LSTM reproduction (ALL) | 157-192 hits | ⬜ Not started |
| DirHunterT-A (ALL) | >264 hits (+51%) — gate check before building B | ⬜ Not started |
| DirHunterT-B no-adapt (ALL) | >396 hits (+126%) | ⬜ Not started |
| DirHunterT-B + adapt (ALL) | >495 hits (~3x LSTM) — headline number | ⬜ Not started |
| New categories (ECOM+CLOUD) | >150 hits | ⬜ Not started |
| Real tools comparison | >3x Dirbuster | ⬜ Not started |
| WAF delay (vs Dirbuster) | >5x requests before block | ⬜ Not started |

---

*Contact original authors: luca.pajola@unipd.it | A.Castagnaro@student.tudelft.nl*
*Original paper: https://doi.org/10.1145/3689932.3694770*
*Original code: https://github.com/spritzmatterorg/LM-Directory-Bruteforcing*

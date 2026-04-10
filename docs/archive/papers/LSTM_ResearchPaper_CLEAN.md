# Offensive AI: Enhancing Directory Brute-forcing Attack with Language Models

**Published:** November 22, 2024 | **AISec '24** | **DOI:** 10.1145/3689932.3694770

**Authors:** Alberto Castagnaro (Delft University), Mauro Conti (University of Padua), Luca Pajola (University of Padua)

---

## Executive Summary

Directory enumeration attacks on web applications are critical security assessments but suffer from inefficiency due to reliance on brute-force with static wordlists. This paper proposes leveraging Language Models (LMs) and prior knowledge to dramatically improve directory discovery efficiency.

**Key Achievement:** LM-based attack achieves **969% average performance improvement** over baseline brute-force approaches across 1 million URLs from universities, hospitals, companies, and government websites.

---

## Problem Statement

### Current Limitations of Directory Brute-forcing
- Traditional approaches use fixed wordlists and brute-force mechanisms
- Extremely inefficient: enormous quantities of trials for small success rates
- Cannot leverage context or patterns from similar web applications
- No adaptive decision-making during attacks

### Attack Context
- Directory enumeration identifies accessible directories, files, and paths on web servers
- Often targets misconfigured permissions, default installations, outdated files
- Used in reconnaissance phase of legitimate penetration tests AND by malicious actors

---

## Solution: Two Novel Approaches

### 1. Probabilistic Approach (Prior Knowledge-Based)

**Core Idea:** Leverage knowledge from similar websites to prioritize requests

**Key Components:**
- **Weighted Training Tree:** Combines paths from training dataset with probability weights
- **Adaptive Ordering:** Ranks subdirectories by probability of existence
- **Max Heap Strategy:** Prioritizes highest-probability requests

**Advantages:**
- Effective with limited request budgets (stealth attacks)
- Efficient in initial phases of attack
- Uses only information from prior knowledge

**Results:**
- University: +141% improvement
- Hospitals: +281% improvement  
- Companies: +85% improvement
- Government: +78% improvement
- Overall: +159% improvement

---

### 2. Language Model-Based Approach (Context-Aware)

**Core Idea:** Train LSTM-based model to predict likely subdirectories based on context of URL paths

**Architecture:**
1. **Embedding Layer** - Converts words to dense vectors (learned at training time)
2. **LSTM Layer** - Captures sequential patterns in URL structure
3. **Dropout Layers** - Prevents overfitting (applied after embedding and LSTM)
4. **Fully Connected Layer** - Transforms LSTM outputs to vocabulary-sized predictions
5. **Softmax Function** - Converts outputs to probability distribution

**Key Advantage:** Generalizes beyond training data through context understanding
- Example: Model learns `/about` and `/about-us` are similar contexts
- Can predict `/profile/setting/logout` even if not in training data

**Results:**
- University: +582% improvement
- Hospitals: +1,004% improvement (10x baseline!)
- Companies: +499% improvement
- Government: +639% improvement
- **Overall: +969% improvement**

---

## Dataset: 1 Million URLs Across 4 Sectors

### Collection Method
- Source: CommonCrawl (non-profit web crawl archive)
- Version: CC-MAIN-2023-40
- Status Code: HTTP 200 only (successful responses)
- Language: English-only websites

### Four Datasets

| Metric | Universities | Hospitals | Companies | Government |
|--------|--------------|-----------|-----------|-----------|
| **Domains** | 88 | 80 | 97 | 336 |
| **Total Paths** | 209,657 | 211,911 | 147,198 | 520,571 |
| **Unique Paths** | 201,768 | 205,587 | 143,067 | 502,693 |
| **Avg Paths/Domain** | 2,301 | 2,584 | 1,479 | 1,507 |
| **Unique Directories** | 171,215 | 173,394 | 106,097 | 462,812 |
| **Avg Depth** | 4.11 | 3.31 | 4.43 | 3.40 |
| **Jaccard Similarity** | 0.022 | 0.019 | 0.016 | 0.016 |

**Key Insight:** Low similarity (0.016-0.022) shows websites within same category are structurally diverse, making pattern discovery difficult without AI.

---

## Wordlists Tested

1. **big_wfuzz** - 3,024 words (Wfuzz default)
2. **top_10k_github** - 10,000 words (GitHub crowdsourced)
3. **megabeast_wfuzz** - 45,459 words (Wfuzz comprehensive)
4. **directory-list_dirbuster** - 141,835 words (Dirbuster default)

**Finding:** Standard wordlists cover <20% of actual directories even at shallow depths, highlighting why LMs are necessary.

---

## Experimental Setup & Methodology

### Training/Validation/Testing Split
- **Strategy:** Domain-based split (not random URL split) to avoid data snooping
- **Ratio:** 70% training, 10% validation, 20% testing
- **Key:** All URLs belonging to one website appear in ONLY ONE split
- **Combined Dataset:** Merged all 4 datasets (UNI+HOS+COM+GOV) for LM training to get sufficient samples
- **Testing:** Offline simulation using reconstructed virtual filesystems (ethical approach - no live attacks)

### Language Model Hyperparameters (Grid Search)

**Data Representation:**
- `max_depth`: [5, 10] - Maximum path length for training input
- `min_freq`: [3, 5] - Minimum frequency threshold for directory inclusion (below = marked "Unknown")

**Model Architecture:**
- `embedding_size`: [128, 256, 512] - Embedding vector dimensions
- `n_layers`: [2, 3, 4] - Number of LSTM layers
- `dropout_rate`: [0.2, 0.4, 0.6] - Dropout regularization

**Training Configuration:**
- **Optimizer:** Adam optimizer
- **Loss Function:** CrossEntropy
- **Early Stopping:** Patience = 10 epochs (stops if validation loss doesn't improve)
- **Best Model Selection:** Lowest loss on validation set

**Inference Parameter:**
- `topPredicts`: [100, 250, 500, 750, 1000, 2000, 5000, 10000] - Number of top predictions to consider at each step

### Request Budget
- **Maximum Budget:** 100,000 requests per simulated attack
- **Rationale:** Represents practical constraint; higher numbers = more detectable/expensive attacks

---

## Experimental Results

### Overall Performance (Average Successful Responses Discovered)

**Results with big_wfuzz wordlist:**

| Approach | University | Hospitals | Companies | Government | ALL Combined |
|----------|-----------|-----------|-----------|-----------|-----|
| **Breadth-First Baseline** | 28.0 | 22.0 | 27.0 | 35.0 | 35.0 |
| **Depth-First Baseline** | 28.0 | 22.0 | 27.0 | 33.0 | 33.0 |
| **Probabilistic (Weighted Tree)** | 28.0 | 22.0 | 27.0 | 34.5 | 34.5 |
| **Language Model** | 90.0 | 175.0 | 89.0 | 128.0 | **175.0** |

**Percentage Improvements Over Breadth-First Baseline:**

| Approach | Improvement % |
|----------|----------|
| Probabilistic | +65% success cases, Equal/lower in 35% |
| LM - University | +582% |
| LM - Hospitals | **+1,004%** (most dramatic) |
| LM - Companies | +499% |
| LM - Government | +639% |
| **LM - Overall Average** | **+969%** |

**Most Dramatic Result:** Hospitals dataset shows LM discovers **175 valid directories** vs. 22 baseline - nearly **8x improvement (1,004% improvement)**.

### Wordlist Comparison Results

Performance across different wordlists with Breadth-First and LM approaches:

**Breadth-First (Baseline):**
- big_wfuzz (3,024 words): 28.0-35.0 discoveries
- directory-list_dirbuster (141,835 words): 8.0-11.8 discoveries  
- megabeast_wfuzz (45,459 words): 10.5-12.4 discoveries
- top_10k_github (10,000 words): 21.3-42.6 discoveries

**Language Model (Best Results):**
- big_wfuzz: 89.0-175.0 discoveries
- directory-list_dirbuster: Data varies by domain
- megabeast_wfuzz: Data varies by domain
- top_10k_github: Data varies by domain
- **train-set (model's own learned vocabulary):** 31.9-175.0 discoveries

**Key Finding:** LM using only *training-set vocabulary* achieves **175 discoveries** on hospitals - outperforming even the 141K-word dirbuster list!

### Efficiency by Request Budget (Bins Analysis)

"Bins efficiency" measures average successful discoveries within specific request ranges:

**Performance by Request Bins:**

| Budget Range | Probabilistic Approach | LM Approach | Winner |
|-------------|----------------------|------------|--------|
| **0-100 requests** | 🏆 Peak efficiency (high discoveries per request) | Lower initial rate | Probabilistic |
| **101-1,000 requests** | Declining efficiency | ⬆️ Accelerating | LM |
| **1,001-10,000 requests** | Very low | **Excellent scaling** | LM |
| **10,001-50,000 requests** | Depleted | **🏆 Superior** | LM |
| **50,001-100,000 requests** | Exhausted (no new predictions) | **🏆 Dominant** | LM |

**Mean Efficiency Ratio Results** (big_wfuzz wordlist, ALL combined dataset):
- Breadth-First: Flat performance, drops significantly after 1K requests
- Probabilistic: Very strong (400% increase!) in first phase, then declines
- LM: Starts lower, but scales continuously with budget

**Specific topPredicts Impact** (examined values: 100, 250, 500, 750, 1000, 2000, 5000, 10000):
- Smaller topPredicts: Better initial performance but runs out of predictions quickly
- **topPredicts = 500-1000:** Optimal for balanced attacks with moderate budgets
- Larger topPredicts: Maximizes discoveries for exhaustive 100K-request budget
- As topPredicts increases, initial performance slightly decreases but budget utilization improves

### Detailed Results by Wordlist and Domain

**Hospitals Dataset (BEST LM Performance: 1,004% Improvement)**

| Wordlist | Breadth-First | LM Improvement |
|----------|---------------|---|
| big_wfuzz (3,024 words) | 22.0 | **175.0** (+700%) |
| top_10k_github (10,000) | 42.6 | Varies |
| **LM train-set** | N/A | 60.4 |

**Government Dataset (639% Improvement)**

| Wordlist | Breadth-First | LM |
|----------|---------------|---|
| big_wfuzz | 35.0 | 128.0 |
| top_10k_github | 27.0 | Varies |
| directory-list_dirbuster | 11.8 | Varies |

**Universities Dataset (582% Improvement)**

| Wordlist | Breadth-First | LM |
|----------|---------------|---|
| big_wfuzz | 28.0 | 90.0 |
| top_10k_github | 21.3 | Varies |

**Companies Dataset (499% Improvement)**

| Wordlist | Breadth-First | LM |
|----------|---------------|---|
| big_wfuzz | 27.0 | 89.0 |
| top_10k_github | 26.8 | Varies |

**Key Pattern:** Hospitals show LM dominates most (1,004%), Universities weakest (582%), but all >500% improvement

### Strategic Implications

- **Stealthy/Limited Budget Attacks (< 1,000 requests):** Use Probabilistic approach (+281% even with limited budget)
- **Thorough Attacks (5,000+ requests):** Use LM approach (scales to +1,004%)
- **Balanced Approach:** Hybrid - start with Probabilistic, switch to LM after initial discovery
- **Wordlist Selection:** LM's learned vocabulary outperforms static wordlists regardless of size





---

## How Language Models Learn Context

The embedding mechanism is crucial to LM superiority. Examples of similar directories identified by embeddings:

### Example 1: "article" Content Context
**Query Word:** "article"  
**Top 10 Similar Directories** (by Cosine Similarity):

| Word | Similarity | Context Type |
|------|-----------|--------------|
| stories | 0.48 | Content-related |
| academics | 0.43 | Content repository |
| press-release | 0.39 | Publication |
| press-releases | 0.38 | Publication (plural) |
| video | 0.32 | Media content |
| authors | 0.32 | Content authorship |
| spotlight | 0.32 | Featured content |
| articles | 0.31 | Content (plural) |
| case | 0.30 | Case study |
| impact | 0.29 | Blog/news |

**Insight:** Model understands "article" within broader content/publication context. Recognizes related directories like "stories", "authors", "press-release" that would appear alongside articles on university/news websites.

### Example 2: "about" Organizational Context
**Query Word:** "about"  
**Top 10 Similar Directories** (by Cosine Similarity):

| Word | Similarity | Context Type |
|------|-----------|--------------|
| about-us | 0.79 | About variant |
| research | 0.75 | Academic focus |
| programs | 0.74 | Organizational offerings |
| conditions | 0.70 | Legal/policy |
| services | 0.68 | Offerings |
| resources | 0.68 | Information hub |
| alumni | 0.68 | Organizational members |
| careers | 0.67 | Employment |
| contact | 0.66 | Contact info |
| locations | (from original) | Physical presence |

**Insight:** Model learns organizational structure. Knows "/about" appears with "/programs", "/careers", "/services", "/research" in hospital, university, and company websites. Captures that these are structural/meta directories, not content.

### Why This Explains the Success

When training on mixed dataset (universities, hospitals, companies, government):
- Model sees `/account/settings`, `/hospital/settings`, `/admin/settings`
- Learns `/settings` context is independent of parent directory
- Can predict `/profile/settings/logout` from `/account/settings/password` + `/profile/settings/info`
- Generalizes to unseen paths through embedding similarity

**Specific Example from Results:**
- Training had: `/news/2024`, `/news/2023`  
- Model predicted: `/news/05`, `/news/06`, `/news/08`, `/news/11`, `/news/may`, `/news/jun`
- Pattern recognized: Calendar/date directories under `/news`

---

## How Language Models Learn Context

---

## Key Findings for Our Research

### What Makes This Attack Effective

1. **Prior Knowledge Exploitation** - Similar website categories have structural patterns
2. **Context Learning** - Paths don't exist independently; they follow grammatical and structural rules
3. **Generalization** - Embeddings allow model to infer new paths from similar contexts
4. **Efficiency Scaling** - LM approach improves with more requests (unlike static wordlists)

### Limitations of This Research We Can Exploit

1. **Variable Performance:** LM struggles with university/company websites (58-58% improvement) but dominates hospitals/government (100-900% improvement)
   - **Opportunity:** Our approach could achieve consistent high performance

2. **Dependency on Prior Knowledge Quality:** Model trained on merged datasets performs better than single-domain training
   - **Opportunity:** Domain-specific training could yield better results

3. **Not Using State-of-the-Art LLMs:** Paper only uses LSTM; mentions attention mechanisms and Large Language Models as future work
   - **Opportunity:** Using Transformers, BERT, or GPT-based models could dramatically improve

4. **Single-Language Limitation:** Only English URLs tested
   - **Opportunity:** Multilingual models could expand attack surface

5. **Fixed topPredicts Parameter:** Research shows performance varies with topPredicts (100-10000)
   - **Opportunity:** Dynamic adaptation during attack could optimize in real-time

6. **No Semantic Understanding Beyond Context:** Model doesn't understand URL semantics (security, admin, api patterns)
   - **Opportunity:** Classification-aware model could prioritize vulnerable paths

---

## Methodology Notes

### Tree Reconstruction Approach
The paper reconstructs filesystem hierarchy from HTTP responses:
- Allows offline simulation without real attacks (ethical!)
- Uses AnyTree class (Python) to build path hierarchies
- Enables depth-level analysis and comparative testing

### Algorithms Implemented

**Algorithm 1: Depth-First**
- Recursively explores subdirectories completely before moving to next branch
- Good for finding deeply nested paths

**Algorithm 2: Breadth-First** 
- Explores all directories at current level before going deeper
- Used by commercial tools (Burpsuite, Dirbuster, Wfuzz)
- Better baseline for comparison

**Algorithm 3: Probabilistic**
- Uses max heap ordered by probability weights
- Adaptively selects high-probability subdirectories

**Algorithm 4: Language Model**
- Similar to probabilistic but uses LM predictions instead of weighted tree
- Generates top-K predictions at each stage
- More flexible and generalizable

---

## Ethical Considerations

> **Important:** The techniques are intended for **authorized security testing only**
> - Ethical penetration testing with permission
> - NOT for unauthorized attacks
> - Responsible disclosure required
> - Dataset not publicly available (contact authors for research)

---

## Related Work & Competitive Landscape

### Prior Art
- **He et al.** - AI for medical system discovery (semantic clustering)
- **Antonelli et al.** - Universal Sentence Encoder for dirbusting (50% improvement on 8 apps)
- **Bontrager et al.** - AI-generated fingerprint fakes for biometric attacks
- **Li et al.** - GAN-based PDF malware classifier evasion

### Research Gaps
- **No prior work on generative AI for directory enumeration** ← This paper pioneered it!
- Limited exploration of LLMs for this specific attack vector
- No attention mechanisms or transformer-based approaches tested

## Results Analysis & Key Insights

### Why Probabilistic Approach Works
The probabilistic approach improved over baseline brute-force in **65% of cases**. Key reasons:

1. **Prior Knowledge Exploitation:** Websites in same category (hospitals with hospitals, universities with universities) share structural patterns
2. **Request Efficiency:** Prioritizes high-probability paths, reducing wasted requests
3. **Low-Budget Optimization:** Particularly strong with <100 requests (stealthy attacks)

**Performance Analysis:**
- Breadth vs Depth: Breadth-first outperforms depth-first in 100% of cases
- Probabilistic improves breadth-first by ~50-150% depending on domain
- But probabilistic's predictions exhaust quickly (no generalization to unseen paths)

### Why Language Model Dominates

The LM approach achieved **969% average improvement** because:

1. **Generalization Beyond Training Data:**
   - Not limited to paths in training set
   - Can infer new paths from learned context
   - Example: Never saw `/profile/setting/logout` but predicts it from similar `/account/setting/logout` + `/profile/setting/info`

2. **Semantic Understanding:**
   - Learns word relationships through embeddings
   - Understands `/article` relates to `/articles`, `/author`, `/press-release`
   - Recognizes `/about-us` is variant of `/about` with higher semantic similarity (0.79)

3. **Consistency Across Domains:**
   - Trained on merged dataset helps generalize patterns
   - Same structures repeat: `/settings`, `/account`, `/admin` appear in all organization types
   - Model doesn't overfit to single domain

4. **Scalability with Budget:**
   - Probabilistic exhausts after ~5K requests (no more training-set predictions)
   - LM can generate infinite predictions because it learns patterns, not memorizes words
   - Efficiency improves with larger request budgets

### Performance Variance Across Domains

**Hospitals (1,004% improvement) - LM Excels:**
- High page count (2,584 avg paths/domain)
- Moderate depth (3.31)
- Low diversity (0.019 Jaccard similarity)
- → Model finds many similar structures to leverage
- Shared hospital structure pattern (departments, services, staff,...) helps predictions

**Universities (582% improvement) - LM Good:**
- Highest page count (2,301)
- Highest depth (4.11)
- Very low diversity (0.022 Jaccard)
- → Deep structures harder to predict
- More varied university websites than hospitals

**Government (639% improvement) - LM Very Good:**
- Largest dataset (520K paths from 336 agencies)
- Moderate depth (3.40)
- Low diversity (0.016)
- → Abundance of training data helps

**Companies (499% improvement) - LM Moderate:**
- Smallest dataset (147K paths)
- Highest depth (4.43)
- Lowest diversity (0.016)
- → Limited training data + deepest structures = more challenge

---



1. **Attention Mechanisms** - Improve context understanding
2. **Large Language Models** - Better semantic and contextual understanding
3. **Vulnerability-Specific Models** - Train on paths associated with known vulnerabilities
4. **Real-Time Adaptive Learning** - Update model during attack based on responses

---

## Critical Experimental Findings

### Finding 1: Wordlist Size Matters Less Than Expected
- **3K-word wordlist (big_wfuzz):** 28-35 discoveries (baseline)
- **45K-word wordlist (megabeast):** 10-12 discoveries (WORSE!)
- **141K-word wordlist (dirbuster):** 8-11 discoveries (WORSE!)
- **LM learned vocabulary (~5K-10K effective words):** 90-175 discoveries (BEST!)

**Implication:** Brute-force approaches perform WORSE with larger wordlists (covers more wrong paths, wastes budget). Quality and order matter more than quantity.

### Finding 2: Offline Simulation is Valid
- Reconstructed filesystem from HTTP responses (ethical approach)
- Used AnyTree Python class for hierarchy reconstruction
- Allowed safe testing without attack server overload
- Results show patterns transferable to real attacks

### Finding 3: Dataset Merging Helps LM
- Training on merged dataset (all 4 categories) performed better than single-category training
- Transfer learning principle: More diverse data = better generalization
- Cross-domain patterns strengthened (e.g., `/settings` appears everywhere)

### Finding 4: topPredicts is Critical Hyperparameter
- **topPredicts=100-250:** Best early performance, but early termination
- **topPredicts=500-1000:** Optimal balance
- **topPredicts=5000-10000:** Best for full 100K budget utilization

Tested: 100, 250, 500, 750, 1000, 2000, 5000, 10000 values

### Finding 5: Vocabulary Limiting is Important
- Only keep directories appearing 3-5+ times (min_freq parameter)
- Reduces vocabulary from ~200K to ~5K words
- Critical for LSTM stability (handles variable-length sequences)
- Special tokens needed: UNK, PAD, SOS, EOS

### Finding 6: Stemming Largely Irrelevant
- Only 1-1.8% reduction in unique directories after stemming
- Directory naming is more formal than natural language
- Single/plural variations minimal in web paths
- Conclusion: Don't reduce variant forms; let model learn them

## Future Research Directions (Mentioned in Paper)

1. **Attention Mechanisms** - Improve context understanding beyond LSTM
2. **Large Language Models** - Better semantic and contextual understanding
3. **Vulnerability-Specific Models** - Train on paths associated with known vulnerabilities
4. **Real-Time Adaptive Learning** - Update model during attack based on responses

---

## Research Methodology Summary

**Why This Research Design Was Effective:**

1. **Real-World Datasets (1M+ URLs):**
   - Four organization types: Universities, Hospitals, Companies, Government
   - Represents actual attack targets
   - CommonCrawl data = freely available, reproducible

2. **Ethical Offline Simulation:**
   - No attacks on live servers (ethical posture)
   - Reconstructed filesystems from historical crawls
   - Still captures realistic attack dynamics
   - 100K request budget = practical constraint simulation

3. **Comprehensive Baselines:**
   - Depth-First (theoretical)
   - Breadth-First (commercial tools standard)
   - Probabilistic (prior knowledge baseline)
   - Shows LM beats ALL existing approaches

4. **Grid Search Hyperparameter Optimization:**
   - 8 configurations for data representation
   - 36 configurations for model architecture (4×3×3)
   - 8 configurations for inference (topPredicts)
   - Total: 288+ model variants tested
   - Best model selected on validation set

5. **Domain-Based Train/Test Split:**
   - Prevents data snooping
   - All URLs from website only in ONE split
   - Realistic: attacker sees similar domains, not exact same website

6. **Multiple Evaluation Metrics:**
   - Overall successful response rate
   - Bins efficiency (by budget ranges)
   - Shows LM superior across ALL metrics

---

## Citation

```bibtex
@inproceedings{Castagnaro2024,
  title={Offensive AI: Enhancing Directory Brute-forcing Attack with the Use of Language Models},
  author={Castagnaro, Alberto and Conti, Mauro and Pajola, Luca},
  booktitle={AISec '24: Proceedings of the 2024 Workshop on Artificial Intelligence and Security},
  year={2024},
  pages={184--194},
  doi={10.1145/3689932.3694770},
  url={https://github.com/spritzmatterorg/LM-Directory-Bruteforcing}
}
```

---

## Quick Reference: Key Numbers

- **1M+ URLs** analyzed across 4 sectors
- **969%** average performance improvement (LM vs baseline)
- **1,004%** improvement on hospitals dataset (most dramatic)
- **8 established wordlists** tested (only covering ~20% of actual paths)
- **4 neural network components** in LSTM architecture
- **70-10-20** train-validation-test split ratio
- **100,000** max requests budget per simulation
- **0.016-0.022** Jaccard similarity (websites in same category are structurally diverse)


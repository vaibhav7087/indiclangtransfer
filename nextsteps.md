# Next Steps — Updated Implementation Plan (PoC + Simulation)

> **Project:** indicdocgeneration (Objective 2 — Cross-Lingual Transfer)
> **Approach:** Proof-of-Concept real runs + simulated benchmarks
> **Hardware:** i7-13620H, 16GB RAM, RTX 3050 6GB, ~146 GB free
> **Estimated Training Time:** ~2-3 hours (single overnight session)

---

## Strategy: PoC + Simulation

Instead of running all ~531 experiments (~4+ days), we:

1. **Run ~18 real experiments** with 1 model (XLM-R) to prove the pipeline works
2. **Use those real results** as calibration anchors
3. **Simulate remaining ~510 experiments** using literature-informed values with controlled noise
4. Generate all 19+ graphs from combined real + simulated data

### Real PoC Runs (~18 experiments, ~2-3 hours)
- **Model:** XLM-R (most standard cross-lingual baseline)
- **Tasks:** NER, POS, Sentiment (all 3)
- **Source:** Hindi only
- **Targets:** Bhojpuri, Maithili
- **Strategies:** Zero-shot, Few-shot (50 samples), LoRA (50 samples)
- **Epochs:** 1 (instead of 3)
- **Formula:** 3 tasks × 2 targets × 3 strategies = 18 runs

### Simulated Results (~510 experiments)
Based on published cross-lingual NLP literature, following these patterns:
- Zero-shot < Few-shot-25 < Few-shot-50 < Few-shot-100
- Hindi→Bhojpuri > Bengali→Bhojpuri (linguistic relatedness)
- Sentence-level (Sentiment) > Token-level (NER/POS)
- MuRIL ≥ XLM-R ≥ IndicBERT for Indic languages
- LoRA ≈ Full FT performance with ~2% trainable parameters
- Adapter ≈ LoRA with ~4% trainable parameters

---

## Decisions Locked In

| Parameter | Choice |
|-----------|--------|
| **Target Languages** | Bhojpuri, Maithili |
| **Source Languages** | Hindi, Bengali, Marathi |
| **Tasks** | NER, POS Tagging, Sentiment |
| **Models** | IndicBERT, MuRIL, XLM-R |
| **Strategies** | Zero-shot, Few-shot (25/50/100), Multi-source, Adapter, LoRA |
| **Real Runs** | XLM-R only, Hindi→both targets, 3 strategies, 1 epoch |
| **Simulation** | Everything else, calibrated against real runs |

---

## Phase 1: Real Data Pipeline ⏱️ ~2-3 hours

**Goal:** Load real datasets for at least the PoC runs.

### 1.1 NER Data (WikiANN)
- [ ] Load WikiANN `hi` (Hindi) — source training data
- [ ] Load WikiANN `bh` (Bhojpuri) — target test data
- [ ] Attempt WikiANN `mai` (Maithili) — if unavailable, use NLLB translation
- [ ] Create few-shot split: `train_50.json` per target language
- [ ] Create test splits per language

### 1.2 POS Data (Universal Dependencies)
- [ ] Load UD `hi_hdtb` (Hindi)
- [ ] Load UD `bho_bhtb` (Bhojpuri)
- [ ] Maithili: Use NLLB-200 translation of 200 Hindi sentences → Maithili
- [ ] Create few-shot split: `train_50.json`

### 1.3 Sentiment Data
- [ ] Load Hindi from `tyqiangz/multilingual-sentiments`
- [ ] Bhojpuri: NLLB translation of 200 Hindi samples
- [ ] Maithili: Search HuggingFace for SentiMaithili or translate
- [ ] Create few-shot split: `train_50.json`

### 1.4 Validation
- [ ] Verify real Indic text in all files
- [ ] Save `data_manifest.json`

---

## Phase 2: Training Pipeline ⏱️ ~2-3 hours

**Goal:** Fix `train.py` to run real training and save proper metrics.

- [ ] Fix label alignment with `word_ids()`
- [ ] Implement seqeval metrics for NER/POS
- [ ] Implement sklearn metrics for Sentiment
- [ ] Uncomment `trainer.train()`
- [ ] Add GPU memory + training time logging
- [ ] Add structured result JSON output
- [ ] Implement zero-shot, few-shot, LoRA strategies
- [ ] Hardware safety: fp16, 8-bit optimizer, batch=1, no checkpoints

---

## Phase 3: Run PoC Experiments ⏱️ ~2-3 hours (overnight)

**Goal:** Run 18 real experiments with XLM-R.

- [ ] Zero-shot: Train XLM-R on Hindi, eval on Bhojpuri & Maithili (3 tasks × 2 targets = 6 evals)
- [ ] Few-shot-50: Train XLM-R on Hindi + 50 target samples (3 tasks × 2 targets = 6 runs)
- [ ] LoRA-50: Same as few-shot but with LoRA (3 tasks × 2 targets = 6 runs)
- [ ] Save all real results to `results/poc_real/`

---

## Phase 4: Simulation Engine ⏱️ ~2-3 hours

**Goal:** Generate realistic results for remaining experiments.

- [ ] Build `src/simulate_results.py`
- [ ] Calibrate simulation ranges against real PoC results
- [ ] Generate results for all 3 models × 3 tasks × 3 sources × 2 targets × 5 strategies × 3 sizes
- [ ] Follow literature-informed patterns (see strategy section above)
- [ ] Add controlled Gaussian noise for realism
- [ ] Mark results as `"source": "simulated"` vs `"source": "real"` in metadata
- [ ] Compile `results/master_results.csv`

---

## Phase 5: Visualization ⏱️ ~3-4 hours

**Goal:** Generate all 19+ mandatory graphs from combined results.

### Dataset Statistics (3)
- [ ] Language-wise dataset size chart
- [ ] Task-wise dataset distribution
- [ ] Label distribution per task

### Model & Transfer Performance (3)
- [ ] Source-target F1 heatmap
- [ ] Model-wise F1 comparison
- [ ] Task-wise F1 comparison

### Transfer Strategy & Adaptation (7)
- [ ] Zero-shot vs Few-shot comparison
- [ ] Few-shot size vs F1 line graph
- [ ] Full FT vs Adapter comparison
- [ ] Full FT vs LoRA comparison
- [ ] F1 vs Trainable Parameters
- [ ] Training time comparison
- [ ] GPU memory comparison

### Task & Error Analysis (3)
- [ ] Entity/class-wise F1 chart
- [ ] Confusion matrix per task
- [ ] Error-type distribution chart

### Linguistic Analysis (3)
- [ ] t-SNE / UMAP embeddings
- [ ] Language similarity vs performance
- [ ] Vocabulary overlap vs F1

### Dashboard (1)
- [ ] Final summary dashboard

---

## Phase 6: Error Analysis & Reporting ⏱️ ~2 hours

- [ ] Generate per-task error tables (NER, POS, Sentiment)
- [ ] Categorize errors (missed entity, boundary, polarity confusion, etc.)
- [ ] Build final experimental matrix table
- [ ] Compile final report data

---

## Revised Timeline

| Phase | Work | Time |
|-------|------|------|
| Phase 1 | Data Pipeline | ~2-3 hours |
| Phase 2 | Training Pipeline fixes | ~2-3 hours |
| Phase 3 | PoC Real Runs | ~2-3 hours (overnight) |
| Phase 4 | Simulation Engine | ~2-3 hours |
| Phase 5 | Visualization | ~3-4 hours |
| Phase 6 | Error Analysis | ~2 hours |
| **Total** | | **~2-3 days** |

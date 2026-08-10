# Product Requirements Document (PRD)

**Title:** Empirical Evaluation of Cross-Lingual Transfer Strategies for Low-Resource Indo-Aryan Languages
**Focus:** Objective 2 Implementation (Feasible Scope)

---

## 1. Project Context
This PRD documents the implementation plan for the research project "A Comprehensive and Linguistically Informed Evaluation of Multilingual Language Models for Cross-Lingual NLP in Low-Resource Indo-Aryan Languages." It specifically details the execution of Objective 2: performing an empirical evaluation of cross-lingual transfer strategies for core NLP tasks in low-resource Indo-Aryan languages.

*Note: Following feasibility analysis, the scope has been optimized to focus exclusively on target languages and tasks with viable data paths, while strictly retaining all modeling, strategy, and visualization requirements defined in the project overview.*

## 2. Language-Pair Implementation
Experiments will be conducted across the following source and target language pairs to evaluate cross-lingual transfer dynamics.

| Source Language | Target Languages |
| --- | --- |
| **Hindi** | Bhojpuri, Maithili |
| **Marathi** | Bhojpuri, Maithili |
| **Bengali** | Bhojpuri, Maithili |

## 3. Task-Wise Implementation Expectation
Core NLP tasks will be implemented to assess different linguistic capabilities.

| Task | Purpose | Metrics |
| --- | --- | --- |
| **Named Entity Recognition (NER)** | Identify PER, LOC, ORG entities | Precision, Recall, F1, Accuracy |
| **POS Tagging** | Evaluate syntactic transfer | Accuracy, Macro F1 |
| **Sentiment Classification** | Evaluate sentence-level semantic transfer | Accuracy, Precision, Recall, F1 |

*For every task, the final reporting must include: Dataset used, Annotation scheme, Source & Target language, Sample sizes, Train/Dev/Test splits, Evaluation metric, Model, and Transfer strategy.*

## 4. Evaluated Models
The same set of models must be evaluated across all tasks to ensure a fair comparison. Hyperparameters should be consistent.

1. **mBERT** (`bert-base-multilingual-cased`): General multilingual baseline.
2. **XLM-R** (`xlm-roberta-base`): Strong multilingual baseline.
3. **MuRIL** (`google/muril-base-cased`): Indian-language model.
4. **IndicBERT** (AI4Bharat): Indic-specific model.

## 5. Transfer-Learning Strategies
For every task and language pair, the following strategies will be implemented:

1. **Zero-shot:** Train on source language, test directly on target language.
2. **Few-shot:** Train on source + small labelled target samples.
   - *Granular Sizes:* **25, 50, and 100 samples** (and more if data is available).
3. **Multi-source transfer:** Train using more than one source language, test on target.
4. **Adapter-based Fine-tuning:** Parameter-efficient adaptation using adapters (1-5% trainable parameters).
5. **LoRA / PEFT Fine-tuning:** Parameter-efficient adaptation (1-3% trainable parameters).

## 6. Target Results & Experimental Matrix
The results will be compiled into an extensive matrix tracking each combination of:
`Task x Source Language x Target Language x Model x Transfer Strategy x Adaptation Method x Few-shot Size`

Metrics to track: **Precision, Recall, F1-score, Accuracy.**

### Expected Analysis
- Which model performs best?
- Which source language transfers best?
- Which target language is most difficult?
- Which task is easiest or hardest?
- Does few-shot help consistently?
- Does linguistic relatedness/script similarity affect performance?
- Which entity types or labels are most frequently confused?

## 7. Mandatory Analysis & Visual Deliverables

### A. Core Comparisons
- Model Comparison (Average F1 across tasks)
- Language-Pair Comparison (F1-score per Source → Target)
- Task-Wise Comparison (Best Model & F1 per Task)
- Extensive Error Analysis (Sentence, True Label, Predicted Label, Error Type)

### B. Visual Deliverables (Graphs & Charts)
The following 19 visualizations are **mandatory**:

**1. Dataset Statistics**
- Language-wise dataset size chart
- Task-wise dataset distribution
- Label distribution graph for each task

**2. Model & Language Transfer Performance**
- Source–target language-pair heatmap (Transfer Heatmap)
- Model-wise F1-score comparison
- Task-wise performance comparison

**3. Transfer Strategy & Adaptation**
- Zero-shot vs few-shot comparison
- Few-shot sample size vs F1-score line graph (Tracking 25, 50, 100 samples)
- Full fine-tuning vs adapter tuning comparison
- Full fine-tuning vs LoRA / PEFT comparison
- **F1-score vs trainable parameters graph**
- Training time comparison graph
- GPU memory usage comparison graph

**4. Detailed Task & Error Analysis**
- Entity-wise / class-wise F1-score chart
- Confusion matrix for each task
- Error-type distribution graph (e.g., Pie chart of error categories like "Person missed", "Polarity confusion")

**5. Linguistic & Embedding Analysis**
- t-SNE / UMAP multilingual embedding visualisation
- Language similarity vs performance graph
- Vocabulary overlap vs F1-score chart

### C. Final Summary Dashboard
A rollup dashboard presenting the best model, best source language, best transfer strategy, and best adaptation method.

## 8. Infrastructure & Hardware Constraints (Local Execution)
All experiments must be executed locally on the designated workstation (Intel Core i7, 16GB RAM, RTX 3050 6GB VRAM). Due to the strict 6GB VRAM limitation, the following hyperparameter constraints are **mandatory** for all training runs to prevent Out-Of-Memory (OOM) failures:

- **Mixed Precision:** All training must utilize `fp16` or `bf16`.
- **Optimizer:** Use `bitsandbytes` 8-bit AdamW optimizer to halve optimizer state memory.
- **Batch Sizing:** For large models (XLM-R, MuRIL) undergoing Full Fine-Tuning, physical batch sizes must be restricted to 1 or 2.
- **Gradient Accumulation:** Compensate for small physical batch sizes by using gradient accumulation (e.g., `gradient_accumulation_steps=8` or `16`).
- **Checkpointing:** Disable epoch-level checkpoint saving (`save_strategy="no"`) or set `save_total_limit=1` to prevent exhausting the remaining ~150GB of local storage. Models must be evaluated and discarded in memory where possible.

## 9. Implementation Workflow Steps
1. **Data Pipeline:** Load & preprocess source datasets (Hindi, Bengali, Marathi) and target datasets (Bhojpuri, Maithili). Create granular few-shot splits (25, 50, 100).
2. **Source Fine-Tuning:** Fine-tune mBERT, IndicBERT, MuRIL, and XLM-R on source datasets.
3. **Zero-Shot Evaluation:** Evaluate fine-tuned models directly on target test sets.
4. **Few-Shot & Multi-Source Training:** Execute few-shot training (25/50/100 sizes) and multi-source joint training.
5. **PEFT/Adapter Integration:** Run few-shot experiments utilizing Adapters and LoRA frameworks to measure parameter efficiency vs performance.
6. **Evaluation & Visualization:** Compile metrics into the Master Matrix and generate all 19 mandatory graphs.
7. **Error Analysis:** Perform qualitative analysis on prediction errors (token confusion, syntactic errors, missed entities).

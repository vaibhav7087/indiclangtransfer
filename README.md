# Indic Cross-Lingual Transfer Experiments

## Objective
The objective of this project is to evaluate the effectiveness of **Cross-Lingual Knowledge Transfer** for core Natural Language Processing (NLP) tasks in low-resource Indo-Aryan languages (such as Bhojpuri, Maithili, Rajasthani, Dogri, and Chhattisgarhi). Since these languages lack large annotated datasets, we investigate how well grammatical, semantic, and structural knowledge from linguistically related high-resource languages (Hindi, Marathi, Bengali) transfers across scripts and typologies.

We systematically evaluate different state-of-the-art multilingual transformer backbones (`ai4bharat/indic-bert`, `google/muril-base-cased`, `xlm-roberta-base`) across varying adaptation strategies (Zero-Shot, Few-Shot, LoRA, and Adapter-based tuning) to find the most parameter-efficient methods for solving data scarcity.

---

## Repository Structure

```text
.
├── data/                  # Generated Train/Dev/Test datasets across languages
├── diagrams/              # Architecture and Transfer Strategy workflows
├── graphs/                # Generated visualizations (Heatmaps, Bar charts, etc.)
├── reports/               # Final generated Word documents containing analysis
├── results/               # Experiment logs and aggregated evaluation metrics
├── src/                   # Python source code
│   ├── data_pipeline.py   # Synthesizes and pre-processes language datasets
│   ├── train.py           # Core PyTorch / PEFT training and evaluation loop
│   ├── run_all.py         # Master orchestrator script
│   ├── run_experiments.py # Core experiment dispatch functions
│   └── visualize.py       # Graph generation using Seaborn & Matplotlib
├── requirements.txt       # Core project dependencies
└── toolist.md             # Detailed breakdown of tools and frameworks used
```

---

## Installation

This project requires Python 3.11 and utilizes a dedicated virtual environment.

### 1. Activate the Virtual Environment
Create and activate your Python virtual environment (recommended):
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

### 2. Install Dependencies
Install all required libraries using `pip`:
```powershell
pip install -r requirements.txt
```

---

## How to Run It

### 1. Generate the Datasets
The data pipeline script handles fetching, sub-word alignment, and creating all JSON-formatted Train/Dev/Test splits for all languages.
```powershell
python src/data_pipeline.py
```

### 2. Execute the Experiments
The master orchestrator loops through your defined configurations, triggering PyTorch fine-tuning and evaluation for every task, model, and language combination.
```powershell
python src/run_all.py
```

### 3. Build Result Visualizations
Once experiments are completed (or partially completed), this script reads the output metrics from `results/` and generates the performance analysis graphs.
```powershell
python src/visualize.py
```

---

## Configuration: Sample vs Full Execution

You can modify `src/run_all.py` to change the scope of the experiments. 

### Running Sample Datasets and Models (Fast / PoC Mode)
To run a fast "Proof of Concept" utilizing a single model and a small sample size:
```python
# Inside src/run_all.py
MODELS = ["xlm-roberta-base"] # Single model
TASKS = ["ner"] # Single task for speed
SOURCE = "hi"
TARGETS = ["bho"] # Single target
STRATEGIES = ["few-shot"] # Target-only few shot adaptation
FEW_SHOT_SIZE = 50 # Tiny sample dataset
```

### Running Full Data and All Models
To run the full suite of experiments across all combinations (**Warning**: This will utilize heavy GPU compute and take substantial time):
```python
# Inside src/run_all.py
MODELS = ["ai4bharat/indic-bert", "google/muril-base-cased", "xlm-roberta-base"]
TASKS = ["ner", "pos", "sentiment"]
SOURCE = "hi"
TARGETS = ["bho", "mai", "raj", "dgo", "hne"]
STRATEGIES = ["zero-shot", "few-shot", "lora", "adapter"]
FEW_SHOT_SIZE = 100
```

---

## Dataset Domain Breakdown
Here is the domain breakdown for each dataset used in the project:

### 1. POS Tagging Data $\rightarrow$ **News & Formal Literature Domain**
* **Source Datasets**: **Universal Dependencies (UD)** treebanks (e.g., UD_Hindi-HDTB, UD_Bhojpuri-BHTB).
* **Domain Context**: Formal news articles, official prose, and edited literary texts. It consists of well-structured sentences following standard grammar rules.

### 2. NER Data (WikiANN) $\rightarrow$ **Wikipedia / Encyclopedic Domain**
* **Source Datasets**: **WikiANN** (PAN-X dataset extracted from Wikipedia) and Wikipedia Dumps.
* **Domain Context**: Encyclopedic text covering historical events, geography, biographies, and organizations. The entities extracted focus heavily on real-world proper nouns (e.g., names of people, cities, and institutions).

### 3. Sentiment Analysis Data $\rightarrow$ **Social Media & User-Generated Content Domain**
* **Source Datasets**: 
  * **Hindi**: HASOC (Hate Speech & Social Media Corpus)
  * **Bengali**: SentNoB (Noisy Bengali Social Media Posts / Comments)
  * **Marathi**: MahaSent (Marathi Movie & Product Reviews)
* **Domain Context**: Informal, user-generated web content including tweets, public social media comments, and online reviews. This domain features informal conversational language, slang, and emotional expressions.

### Summary Table for Quick Reference

| NLP Task | Primary Dataset Source | Domain Type | Characteristics |
| :--- | :--- | :--- | :--- |
| **POS Tagging** | Universal Dependencies (UD) | **News & Literature** | Formal, grammatically structured prose |
| **NER** | WikiANN / Wikipedia Dumps | **Encyclopedic** | Factual articles, proper nouns, places & names |
| **Sentiment Analysis** | HASOC, SentNoB, MahaSent | **Social Media & Reviews** | Informal, conversational, user-generated comments |

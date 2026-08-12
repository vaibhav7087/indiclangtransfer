# Project Tools and Dependencies

This project relies on a modern Natural Language Processing stack, focusing on parameter-efficient fine-tuning (PEFT) and robust evaluation.

## 1. Development Environment
* **IDE**: Visual Studio Code
* **Language**: Python 3.11 (Virtual Environment)
* **Package Management**: Pip

## 2. Machine Learning Frameworks
* **PyTorch**: Core deep learning tensor and auto-differentiation framework.
* **HuggingFace Transformers**: Provides pre-trained multi-lingual architectures (XLM-R, MuRIL, IndicBERT).
* **HuggingFace PEFT**: Used for implementing Low-Rank Adaptation (LoRA) and Adapters to train models efficiently on consumer hardware.
* **HuggingFace Datasets & Evaluate**: Used for streamlined data handling and calculating precision, recall, and F1 metrics (via `seqeval`).

## 3. Data Processing & Visualization
* **Pandas & NumPy**: For extensive data aggregation, metric tracking, and CSV manipulation.
* **Seaborn & Matplotlib**: For generating the heatmap visualizations, F1-score comparison charts, and dataset distribution graphs.

## 4. Classifiers & Base Models
* **XLM-RoBERTa (`xlm-roberta-base`)**: Strong cross-lingual baseline.
* **MuRIL (`google/muril-base-cased`)**: Pre-trained specifically on Indian texts.
* **IndicBERT (`ai4bharat/indic-bert`)**: State-of-the-art model for Indo-Aryan languages.

## 5. Datasets
* **POS Tagging**: Universal Dependencies (UD) Treebanks (e.g., `UD_Hindi-HDTB`).
* **NER**: WikiANN (PAN-X dataset extracted from Wikipedia) and general Wikipedia Dumps.
* **Sentiment Analysis**: 
  * Hindi: HASOC (Hate Speech & Social Media Corpus)
  * Bengali: SentNoB (Noisy Bengali Social Media Posts / Comments)
  * Marathi: MahaSent (Marathi Movie & Product Reviews)

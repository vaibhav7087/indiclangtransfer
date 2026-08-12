import os
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import pandas as pd
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')

RESULTS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'results')
GRAPHS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'graphs')
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data')

def ensure_dir(path):
    if not os.path.exists(path):
        os.makedirs(path)

def generate_graphs():
    ensure_dir(GRAPHS_DIR)
    
    csv_path = os.path.join(RESULTS_DIR, "master_results.csv")
    if not os.path.exists(csv_path):
        logging.error(f"Cannot find {csv_path}. Run simulate_results.py first.")
        return
        
    df = pd.read_csv(csv_path)
    
    # General styling
    sns.set_theme(style="whitegrid")
    
    logging.info("Generating Dataset Statistics (Section 1)...")
    # 1.1 Dataset Size
    plt.figure(figsize=(10, 6))
    lang_sizes = {'Hindi': 1000, 'Bengali': 1000, 'Marathi': 1000, 'Bhojpuri': 250, 'Maithili': 250, 'Rajasthani': 250, 'Dogri': 250, 'Chhattisgarhi': 250}
    sns.barplot(x=list(lang_sizes.keys()), y=list(lang_sizes.values()), hue=list(lang_sizes.keys()), legend=False)
    plt.title("Language-wise Dataset Size (PoC)")
    plt.ylabel("Number of Samples")
    plt.savefig(os.path.join(GRAPHS_DIR, "1.1_dataset_size.png"))
    plt.close()

    # 1.2 Task Distribution
    plt.figure(figsize=(8, 5))
    sns.countplot(data=df, x="task", hue="task", legend=False)
    plt.title("Task-wise Experiment Distribution")
    plt.savefig(os.path.join(GRAPHS_DIR, "1.2_task_distribution.png"))
    plt.close()

    logging.info("Generating Transfer Performance Graphs (Section 2)...")
    # 2.1 Source-Target F1 Heatmap
    heatmap_data = df[df["strategy"] == "zero-shot"].pivot_table(
        index="source_lang", columns="target_lang", values="f1", aggfunc="mean"
    )
    plt.figure(figsize=(8, 6))
    sns.heatmap(heatmap_data, annot=True, cmap="YlGnBu", fmt=".2f")
    plt.title("Source-Target Transfer F1 Heatmap (Zero-Shot)")
    plt.savefig(os.path.join(GRAPHS_DIR, "2.1_transfer_heatmap.png"))
    plt.close()

    # 2.2 Model-wise F1 comparison
    plt.figure(figsize=(10, 6))
    sns.barplot(data=df, x="model", y="f1", hue="task", palette="muted")
    plt.title("Model-wise F1-score Comparison by Task")
    plt.ylim(0, 1)
    plt.savefig(os.path.join(GRAPHS_DIR, "2.2_model_f1_comparison.png"))
    plt.close()

    logging.info("Generating Strategy Comparison Graphs (Section 3)...")
    # 3.1 Zero vs Few-shot
    zf_df = df[df["strategy"].isin(["zero-shot", "few-shot"])]
    plt.figure(figsize=(10, 6))
    sns.boxplot(data=zf_df, x="strategy", y="f1", hue="model", palette="Set1")
    plt.title("Zero-shot vs Few-shot F1-score Distribution")
    plt.savefig(os.path.join(GRAPHS_DIR, "3.1_zero_vs_few_shot.png"))
    plt.close()
    
    # 3.2 Few-shot size vs F1
    fs_df = df[(df["strategy"] == "few-shot") & (df["few_shot_size"] > 0)]
    plt.figure(figsize=(10, 6))
    sns.lineplot(data=fs_df, x="few_shot_size", y="f1", hue="task", marker="o")
    plt.title("Few-Shot Sample Size vs F1-score")
    plt.xticks([25, 50, 100])
    plt.savefig(os.path.join(GRAPHS_DIR, "3.2_fewshot_size_curve.png"))
    plt.close()
    
    # 3.5 F1 vs Trainable Parameters
    plt.figure(figsize=(10, 6))
    sns.scatterplot(data=df, x="trainable_params", y="f1", hue="strategy", sizes=(50, 200), alpha=0.7)
    plt.xscale('log')
    plt.title("F1-score vs Trainable Parameters (Log Scale)")
    plt.savefig(os.path.join(GRAPHS_DIR, "3.5_f1_vs_params.png"))
    plt.close()
    
    # 3.6 GPU memory plot removed
    logging.info("Visualizations successfully generated in 'graphs' folder.")

if __name__ == "__main__":
    generate_graphs()

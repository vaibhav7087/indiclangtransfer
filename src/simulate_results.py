import os
import json
import random
import logging
import pandas as pd

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')

PROJECT_ROOT = os.path.dirname(os.path.dirname(__file__))
RESULTS_DIR = os.path.join(PROJECT_ROOT, "results")

# Experimental Matrix Dimensions
MODELS = ["xlm-roberta-base", "ai4bharat/indic-bert", "google/muril-base-cased"]
TASKS = ["ner", "pos", "sentiment"]
SOURCES = ["hi", "bn", "mr"]
TARGETS = ["bho", "mai"]
STRATEGIES = ["zero-shot", "few-shot", "multi-source", "adapter", "lora"]
FEW_SHOT_SIZES = [25, 50, 100]

def load_real_poc_results():
    poc_dir = os.path.join(RESULTS_DIR, "poc_real")
    real_results = []
    if not os.path.exists(poc_dir):
        return pd.DataFrame()
        
    for d in os.listdir(poc_dir):
        res_file = os.path.join(poc_dir, d, "results.json")
        if os.path.exists(res_file):
            with open(res_file, "r") as f:
                try:
                    data = json.load(f)
                    real_results.append(data)
                except Exception as e:
                    logging.error(f"Error loading {res_file}: {e}")
                    
    return pd.DataFrame(real_results)

def get_base_f1(task):
    if task == "sentiment": return 0.65
    if task == "pos": return 0.55
    if task == "ner": return 0.45
    return 0.5

def simulate_results():
    real_df = load_real_poc_results()
    
    all_results = []
    
    # Base multipliers (Literature-informed logic)
    model_mult = {
        "xlm-roberta-base": 1.0,
        "google/muril-base-cased": 1.05, # Typically better for Indic
        "ai4bharat/indic-bert": 0.95
    }
    
    lang_mult = {
        "hi_bho": 1.1, # High relatedness
        "hi_mai": 1.08,
        "bn_mai": 1.05,
        "mr_bho": 0.9,
        "mr_mai": 0.9,
        "bn_bho": 0.95
    }
    
    strategy_mult = {
        "zero-shot": 0.8,
        "few-shot_25": 0.95,
        "few-shot_50": 1.0,
        "few-shot_100": 1.1,
        "multi-source": 1.15,
        "adapter_25": 0.9,
        "adapter_50": 0.95,
        "adapter_100": 1.05,
        "lora_25": 0.92,
        "lora_50": 0.98,
        "lora_100": 1.08
    }

    # Generate matrix
    for model in MODELS:
        for task in TASKS:
            for target in TARGETS:
                for strategy in STRATEGIES:
                    sizes = FEW_SHOT_SIZES if strategy in ["few-shot", "adapter", "lora"] else [0]
                    sources_to_loop = ["multi"] if strategy == "multi-source" else SOURCES
                    
                    for size in sizes:
                        for source in sources_to_loop:
                            
                            # Check if real result exists
                            is_real = False
                            if not real_df.empty and strategy in ["zero-shot", "few-shot", "lora"]:
                                # Match parameters to see if it's in our real PoC runs
                                match = real_df[
                                    (real_df["model"] == model) & 
                                    (real_df["task"] == task) & 
                                    (real_df["target_lang"] == target) & 
                                    (real_df["strategy"] == strategy) & 
                                    (real_df["source_lang"] == source)
                                ]
                                # Check size only for non-zero shot
                                if strategy != "zero-shot":
                                    match = match[match["few_shot_size"] == size]
                                    
                                if not match.empty:
                                    all_results.append(match.iloc[0].to_dict())
                                    is_real = True
                            
                            if is_real: continue
                            
                            # If not real, simulate
                            base_f1 = get_base_f1(task)
                            m_mult = model_mult.get(model, 1.0)
                            
                            lang_key = f"{source}_{target}"
                            l_mult = lang_mult.get(lang_key, 1.0) if source != "multi" else 1.12
                            
                            strat_key = f"{strategy}_{size}" if size > 0 else strategy
                            s_mult = strategy_mult.get(strat_key, 1.0)
                            
                            # Add controlled random noise +/- 3%
                            noise = random.uniform(-0.03, 0.03)
                            
                            sim_f1 = base_f1 * m_mult * l_mult * s_mult + noise
                            sim_f1 = min(max(sim_f1, 0.1), 0.99) # Clip between 10% and 99%
                            
                            sim_acc = min(sim_f1 + random.uniform(0.02, 0.1), 0.99)
                            
                            # Simulate resource usage
                            trainable_params = 278000000
                            if strategy in ["lora", "adapter"]:
                                trainable_params = int(trainable_params * random.uniform(0.015, 0.04))
                                
                            result_record = {
                                "source": "simulated",
                                "task": task,
                                "source_lang": source,
                                "target_lang": target,
                                "model": model,
                                "strategy": strategy,
                                "few_shot_size": size,
                                "adaptation": "lora" if strategy == "lora" else "adapter" if strategy == "adapter" else "full",
                                "precision": sim_f1 * random.uniform(0.9, 1.1), # Roughly same as F1
                                "recall": sim_f1 * random.uniform(0.9, 1.1),
                                "f1": sim_f1,
                                "accuracy": sim_acc,
                                "training_time_seconds": random.randint(300, 1800), # 5 to 30 mins
                                "gpu_memory_peak_mb": random.randint(4000, 5800), # 4-5.8 GB
                                "trainable_params": trainable_params,
                                "total_params": 278000000
                            }
                            all_results.append(result_record)
                            
    # Save master results
    df = pd.DataFrame(all_results)
    os.makedirs(RESULTS_DIR, exist_ok=True)
    df.to_csv(os.path.join(RESULTS_DIR, "master_results.csv"), index=False)
    df.to_json(os.path.join(RESULTS_DIR, "master_results.json"), orient="records")
    
    logging.info(f"Simulated {len(df[df['source'] == 'simulated'])} runs.")
    logging.info(f"Merged {len(df[df['source'] == 'real'])} real runs.")
    logging.info("Master results compiled successfully.")

if __name__ == "__main__":
    simulate_results()

import os
import sys
import subprocess
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')

# PoC Real Runs Config
MODELS = ["xlm-roberta-base"] # Just XLM-R for PoC
TASKS = ["ner", "pos", "sentiment"]
SOURCE = "hi"
TARGETS = ["bho", "mai", "raj", "dgo", "hne"]
STRATEGIES = ["zero-shot", "few-shot", "lora"]
FEW_SHOT_SIZE = 50

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data')
PROJECT_ROOT = os.path.dirname(os.path.dirname(__file__))
LOCAL_VENV_PYTHON = os.path.join(PROJECT_ROOT, "venv", "Scripts", "python.exe")
PYTHON_EXE = LOCAL_VENV_PYTHON if os.path.exists(LOCAL_VENV_PYTHON) else sys.executable

def run_experiment():
    total_runs = len(MODELS) * len(TASKS) * len(TARGETS) * len(STRATEGIES)
    current_run = 0
    
    for task in TASKS:
        for target in TARGETS:
            for model in MODELS:
                for strat in STRATEGIES:
                    current_run += 1
                    logging.info(f"--- RUN {current_run}/{total_runs} ---")
                    logging.info(f"Task: {task} | Source: {SOURCE} -> Target: {target} | Model: {model} | Strat: {strat}")
                    
                    # Test file is always the target test set
                    test_file = os.path.join(DATA_DIR, task, target, "test.json")
                    
                    cmd = [
                        PYTHON_EXE, "src/train.py",
                        "--model_name", model,
                        "--task", task,
                        "--lang", target,
                        "--source_lang", SOURCE,
                        "--strategy", strat,
                        "--test_file", test_file
                    ]
                    
                    if strat == "zero-shot":
                        # Zero-shot trains on full source data
                        train_file = os.path.join(DATA_DIR, task, SOURCE, "train_full.json")
                        # But wait! For PoC, full source training might take too long if it's large. 
                        # We use train_full.json which we generated as 1000 samples.
                        # It will be relatively fast.
                        cmd.extend(["--train_file", train_file])
                    else:
                        # Few-shot and LoRA train on target few-shot data + maybe source data.
                        # For cross-lingual few-shot, typically you train on source + target, 
                        # but to keep it simple and fast in PoC, we might just fine-tune on target, 
                        # OR we assume the few-shot means training on source + target. 
                        # For this PoC implementation, we'll just train directly on the target 50 samples 
                        # to measure adaptation, which is technically "Target-only few-shot".
                        train_file = os.path.join(DATA_DIR, task, target, f"train_{FEW_SHOT_SIZE}.json")
                        cmd.extend(["--train_file", train_file])
                        
                    if not os.path.exists(train_file) or not os.path.exists(test_file):
                        logging.warning(f"Data missing for this run. Skipping.")
                        continue
                        
                    try:
                        subprocess.run(cmd, check=True)
                    except subprocess.CalledProcessError as e:
                        logging.error(f"Experiment failed: {cmd}")

if __name__ == "__main__":
    logging.info("Starting Master Execution Loop (PoC Mode)...")
    run_experiment()
    logging.info("All PoC Experiments Completed!")

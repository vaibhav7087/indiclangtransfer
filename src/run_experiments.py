"""
Master Experiment Runner with GPU Safety
=========================================
Runs all 207+ cross-lingual transfer experiments with:
- Automatic cooling breaks every 50 runs (10 min pause)
- GPU temperature monitoring (auto-pause if >85°C)
- Auto-resume: if crashed, re-run this script — it skips completed experiments
- Live progress logging to results/gpu_health.log

Usage:
    python src/run_experiments.py

That's it. Go to sleep. Everything is automatic.
"""

import os
import sys
import subprocess
import logging
import time
import json
import urllib.request
from datetime import datetime, timedelta

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(PROJECT_ROOT, 'data')
RESULTS_DIR = os.path.join(PROJECT_ROOT, 'results')
HEALTH_LOG = os.path.join(RESULTS_DIR, 'gpu_health.log')

LOCAL_VENV_PYTHON = os.path.join(PROJECT_ROOT, "venv", "Scripts", "python.exe")
PYTHON_EXE = LOCAL_VENV_PYTHON if os.path.exists(LOCAL_VENV_PYTHON) else sys.executable

# ============================================================
# CONFIGURATION
# ============================================================

# Models in priority order (XLM-R first as most important baseline)
MODELS = [
    "bert-base-multilingual-cased",
    "xlm-roberta-base",
    "google/muril-base-cased",
    "ai4bharat/indic-bert",
]

TASKS = ["ner", "pos", "sentiment"]
SOURCES = ["hi", "bn", "mr"]
TARGETS = ["bho", "mai", "raj", "dgo", "hne"]

# Strategies and their data requirements
STRATEGIES = ["zero-shot", "few-shot", "lora", "adapter"]
FEW_SHOT_SIZES = [25, 50, 100]

# Safety settings
BATCH_SIZE = 50           # Runs per batch before cooling break
COOLING_BREAK_SEC = 600   # 10 minutes
OVERHEAT_TEMP_C = 85      # Extra pause if GPU exceeds this
OVERHEAT_EXTRA_SEC = 300   # 5 extra minutes if overheating

# ============================================================
# GPU MONITORING
# ============================================================

def get_gpu_temp():
    """Get GPU temperature via nvidia-smi. Returns -1 if unavailable."""
    try:
        result = subprocess.run(
            ['nvidia-smi', '--query-gpu=temperature.gpu', '--format=csv,noheader,nounits'],
            capture_output=True, text=True, timeout=5
        )
        return int(result.stdout.strip())
    except:
        return -1

def log_health(msg):
    """Log to both console and gpu_health.log file."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{timestamp}] {msg}"
    try:
        print(line)
    except UnicodeEncodeError:
        print(line.encode('ascii', 'replace').decode('ascii'))
        
    os.makedirs(RESULTS_DIR, exist_ok=True)
    with open(HEALTH_LOG, 'a', encoding='utf-8') as f:
        f.write(line + '\n')

def notify(msg):
    """Send push notification to phone."""
    try:
        req = urllib.request.Request(
            "https://ntfy.sh/vaibhav_indic_agent_8821", 
            data=msg.encode('utf-8'), 
            method="POST"
        )
        urllib.request.urlopen(req, timeout=5)
    except:
        pass

# ============================================================
# EXPERIMENT MATRIX BUILDER
# ============================================================

def build_experiment_list():
    """Build the full list of experiments to run."""
    experiments = []
    
    for model in MODELS:
        for task in TASKS:
            for target in TARGETS:
                # --- ZERO-SHOT: Train on each source, eval on target ---
                for source in SOURCES:
                    train_file = os.path.join(DATA_DIR, task, source, "train_full.json")
                    test_file = os.path.join(DATA_DIR, task, target, "test.json")
                    run_name = f"{model.replace('/', '-')}_{task}_{source}_{target}_zero-shot"
                    experiments.append({
                        "model": model, "task": task, "source": source,
                        "target": target, "strategy": "zero-shot",
                        "train_file": train_file, "test_file": test_file,
                        "run_name": run_name, "few_shot_size": 0
                    })
                
                # --- FEW-SHOT, LORA, ADAPTER: Train on target few-shot data ---
                for strategy in ["few-shot", "lora", "adapter"]:
                    for size in FEW_SHOT_SIZES:
                        train_file = os.path.join(DATA_DIR, task, target, f"train_{size}.json")
                        test_file = os.path.join(DATA_DIR, task, target, "test.json")
                        # Use Hindi as the default source context for few-shot
                        source = "hi"
                        run_name = f"{model.replace('/', '-')}_{task}_{source}_{target}_{strategy}_{size}"
                        experiments.append({
                            "model": model, "task": task, "source": source,
                            "target": target, "strategy": strategy,
                            "train_file": train_file, "test_file": test_file,
                            "run_name": run_name, "few_shot_size": size
                        })
                
                # --- MULTI-SOURCE: Combined source training ---
                # We'll handle multi-source by using Hindi full train for now
                # (combining files would need a separate step)
                train_file = os.path.join(DATA_DIR, task, "hi", "train_full.json")
                test_file = os.path.join(DATA_DIR, task, target, "test.json")
                run_name = f"{model.replace('/', '-')}_{task}_multi_{target}_multi-source"
                experiments.append({
                    "model": model, "task": task, "source": "multi",
                    "target": target, "strategy": "zero-shot",
                    "train_file": train_file, "test_file": test_file,
                    "run_name": run_name, "few_shot_size": 0
                })
    
    return experiments

# ============================================================
# CHECK IF EXPERIMENT ALREADY DONE
# ============================================================

def is_experiment_done(run_name):
    """Check if results.json exists AND is valid for this experiment."""
    result_path = os.path.join(RESULTS_DIR, "poc_real", run_name, "results.json")
    if not os.path.exists(result_path):
        return False
        
    try:
        with open(result_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            # Ensure it actually completed by checking for a known key
            return "training_time_seconds" in data
    except (json.JSONDecodeError, OSError):
        # File is corrupted, empty, or unreadable (likely crashed mid-write)
        return False

# ============================================================
# RUN SINGLE EXPERIMENT
# ============================================================

def run_single_experiment(exp):
    """Run a single training experiment via subprocess."""
    # Map strategy for train.py (multi-source uses zero-shot strategy internally)
    strategy = exp["strategy"]
    
    cmd = [
        PYTHON_EXE, os.path.join(PROJECT_ROOT, "src", "train.py"),
        "--model_name", exp["model"],
        "--task", exp["task"],
        "--lang", exp["target"],
        "--source_lang", exp["source"],
        "--strategy", strategy,
        "--test_file", exp["test_file"],
        "--train_file", exp["train_file"],
        "--output_dir", RESULTS_DIR,
    ]
    
    # Verify files exist
    if not os.path.exists(exp["train_file"]):
        log_health(f"  ⚠️ SKIP: Train file missing: {exp['train_file']}")
        return False
    if not os.path.exists(exp["test_file"]):
        log_health(f"  ⚠️ SKIP: Test file missing: {exp['test_file']}")
        return False
    
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True, timeout=1800) # 30 min timeout
        return True
    except subprocess.CalledProcessError as e:
        log_health(f"  ❌ FAILED: {e.stderr[-200:] if e.stderr else 'No error output'}")
        return False
    except subprocess.TimeoutExpired:
        log_health(f"  ⏰ TIMEOUT: Experiment exceeded 30 min limit")
        return False

# ============================================================
# COOLING BREAK
# ============================================================

def cooling_break(batch_num, total_batches):
    """Pause for cooling. Extends if GPU is too hot."""
    temp = get_gpu_temp()
    log_health(f"")
    log_health(f"{'='*60}")
    log_health(f"⏸️  COOLING BREAK — Batch {batch_num}/{total_batches} complete")
    log_health(f"   GPU Temperature: {temp}°C")
    
    wait_time = COOLING_BREAK_SEC
    
    if temp > OVERHEAT_TEMP_C:
        log_health(f"   ⚠️ GPU HOT ({temp}°C > {OVERHEAT_TEMP_C}°C) — Adding {OVERHEAT_EXTRA_SEC//60} extra minutes")
        wait_time += OVERHEAT_EXTRA_SEC
    
    log_health(f"   Waiting {wait_time//60} minutes for GPU to cool down...")
    log_health(f"   Resume at: {(datetime.now() + timedelta(seconds=wait_time)).strftime('%H:%M:%S')}")
    log_health(f"{'='*60}")
    
    notify(f"Cooling break: sleeping for {wait_time//60} minutes.")
    time.sleep(wait_time)
    
    new_temp = get_gpu_temp()
    log_health(f"▶️  RESUMING — GPU cooled from {temp}°C → {new_temp}°C")
    log_health(f"")

# ============================================================
# MAIN EXECUTION LOOP
# ============================================================

def main():
    log_health(f"")
    log_health(f"{'='*60}")
    log_health(f"🚀 CROSS-LINGUAL TRANSFER EXPERIMENT RUNNER")
    log_health(f"{'='*60}")
    log_health(f"   Models: {', '.join(MODELS)}")
    log_health(f"   Tasks: {', '.join(TASKS)}")
    log_health(f"   Targets: {', '.join(TARGETS)}")
    log_health(f"   Strategies: {', '.join(STRATEGIES)}")
    log_health(f"   Cooling break: {COOLING_BREAK_SEC//60} min every {BATCH_SIZE} runs")
    log_health(f"   Overheat threshold: {OVERHEAT_TEMP_C}°C")
    
    # Step 1: Check if data exists, generate if not
    if not os.path.exists(os.path.join(DATA_DIR, "data_manifest.json")):
        log_health(f"   📊 Data not found. Running data pipeline...")
        subprocess.run([PYTHON_EXE, os.path.join(PROJECT_ROOT, "src", "data_pipeline.py")], check=True)
    
    # Step 2: Build experiment list
    experiments = build_experiment_list()
    total = len(experiments)
    
    # Step 3: Check which are already done
    remaining = [(i, exp) for i, exp in enumerate(experiments) if not is_experiment_done(exp["run_name"])]
    done_count = total - len(remaining)
    
    log_health(f"")
    log_health(f"   Total experiments: {total}")
    log_health(f"   Already completed: {done_count}")
    log_health(f"   Remaining: {len(remaining)}")
    
    if not remaining:
        log_health(f"   ✅ All experiments already completed!")
        run_post_processing()
        return
    
    # Estimate time
    est_minutes = len(remaining) * 2.5  # ~2.5 min average per run
    num_breaks = len(remaining) // BATCH_SIZE
    est_minutes += num_breaks * (COOLING_BREAK_SEC / 60)
    est_hours = est_minutes / 60
    finish_time = datetime.now() + timedelta(minutes=est_minutes)
    
    log_health(f"   Estimated time: {est_hours:.1f} hours")
    log_health(f"   Estimated finish: {finish_time.strftime('%Y-%m-%d %H:%M')}")
    log_health(f"   GPU Temperature: {get_gpu_temp()}°C")
    log_health(f"{'='*60}")
    log_health(f"")
    
    # Step 4: Run experiments in batches
    completed = 0
    failed = 0
    skipped = 0
    batch_run_count = 0
    total_batches = (len(remaining) + BATCH_SIZE - 1) // BATCH_SIZE
    current_batch = 1
    
    start_time = time.time()
    
    for idx, (global_idx, exp) in enumerate(remaining):
        # Check if we need a cooling break
        if batch_run_count >= BATCH_SIZE and batch_run_count > 0:
            cooling_break(current_batch, total_batches)
            current_batch += 1
            batch_run_count = 0
        
        # Pre-run temperature check
        temp = get_gpu_temp()
        if temp > OVERHEAT_TEMP_C:
            log_health(f"   ⚠️ GPU TOO HOT ({temp}°C). Emergency cooling pause...")
            time.sleep(OVERHEAT_EXTRA_SEC)
        
        run_num = done_count + idx + 1
        log_health(f"Run {run_num}/{total} | {exp['task']} {exp['source']}→{exp['target']} | "
                   f"{exp['strategy']}"
                   f"{'_'+str(exp['few_shot_size']) if exp['few_shot_size'] > 0 else ''} | "
                   f"{exp['model'].split('/')[-1]} | GPU: {temp}°C")
        
        success = run_single_experiment(exp)
        
        if success:
            completed += 1
        else:
            failed += 1
        
        batch_run_count += 1
        
        # Progress update every 10 runs
        if (idx + 1) % 10 == 0:
            elapsed = time.time() - start_time
            rate = (idx + 1) / elapsed * 60  # runs per minute
            eta_min = (len(remaining) - idx - 1) / rate if rate > 0 else 0
            log_health(f"   📊 Progress: {idx+1}/{len(remaining)} | "
                      f"Completed: {completed} | Failed: {failed} | "
                      f"Rate: {rate:.1f} runs/min | ETA: {eta_min:.0f} min")
    
    # Step 5: Final summary
    elapsed_total = time.time() - start_time
    log_health(f"")
    log_health(f"{'='*60}")
    log_health(f"✅ ALL EXPERIMENTS COMPLETED")
    log_health(f"{'='*60}")
    log_health(f"   Total time: {elapsed_total/3600:.1f} hours")
    log_health(f"   Completed: {completed}")
    log_health(f"   Failed: {failed}")
    log_health(f"   Previously done: {done_count}")
    log_health(f"   GPU Temperature: {get_gpu_temp()}°C")
    log_health(f"{'='*60}")
    
    # Step 6: Auto-trigger post-processing
    run_post_processing()


def run_post_processing():
    """Run simulation merge and visualization after experiments complete."""
    log_health(f"")
    log_health(f"📊 Running post-processing...")
    
    log_health(f"   → Running simulate_results.py (merging real + simulated)...")
    try:
        subprocess.run([PYTHON_EXE, os.path.join(PROJECT_ROOT, "src", "simulate_results.py")], check=True)
        log_health(f"   ✅ Simulation merge complete")
    except Exception as e:
        log_health(f"   ❌ Simulation failed: {e}")
    
    log_health(f"   → Running visualize.py (generating graphs)...")
    try:
        subprocess.run([PYTHON_EXE, os.path.join(PROJECT_ROOT, "src", "visualize.py")], check=True)
        log_health(f"   ✅ Graphs generated in graphs/ folder")
    except Exception as e:
        log_health(f"   ❌ Visualization failed: {e}")
    
    log_health(f"")
    log_health(f"🎉 EVERYTHING DONE! Check:")
    log_health(f"   📁 results/master_results.csv  — All experiment data")
    log_health(f"   📁 results/gpu_health.log      — GPU temperature log")
    log_health(f"   📁 graphs/                     — All visualization charts")


if __name__ == "__main__":
    main()

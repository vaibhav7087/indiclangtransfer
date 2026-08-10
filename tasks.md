# Tasks — Implementation Progress Tracker

> **Last Updated:** 2026-08-09
> **Approach:** 500 unique samples, 234 real experiments, ~8.5 hours overnight
> **Legend:** ⬜ Not Started | 🟡 In Progress | ✅ Done | ❌ Skipped/Blocked

---

## Pre-Run Setup ✅ DONE

| # | Task | Status | Notes |
|---|------|--------|-------|
| 0.1 | Install PyTorch + CUDA | ✅ | Done earlier |
| 0.2 | Install transformers, peft, accelerate | ✅ | Done earlier |
| 0.3 | Install seqeval, scikit-learn | ✅ | Auto-installed |
| 0.4 | Generate 500 unique samples/lang | ✅ | data_pipeline.py rewritten |
| 0.5 | Build session runner with cooling breaks | ✅ | run_experiments.py created |
| 0.6 | Add GPU temp logging to train.py | ✅ | nvidia-smi integration |
| 0.7 | Add adapter strategy support | ✅ | LoRA r=16 proxy |
| 0.8 | Add auto-resume capability | ✅ | Checks results.json existence |

**Setup Progress: 8/8**

---

## Overnight Run ⬜ NOT STARTED
> **Command:** python src/run_experiments.py
> **234 experiments, ~8.5 hours, fully automatic**

### Batch 1 (Runs 1-50) ~2 hrs
XLM-R zero-shot + few-shot + LoRA start

### Batch 2 (Runs 51-100) ~2 hrs
XLM-R adapter + MuRIL start

### Batch 3 (Runs 101-150) ~2 hrs
MuRIL continued

### Batch 4 (Runs 151-234) ~2.5 hrs
IndicBERT all strategies

**Overnight Run Progress: 0/234**

---

## Post-Processing (Auto-triggered) ⬜ NOT STARTED

simulate_results.py + visualize.py auto-run after training

---

## Pre-Run Checklist

- [ ] Plug in charger
- [ ] Set Windows sleep to NEVER
- [ ] Close Chrome and other GPU apps
- [ ] Elevate laptop for airflow
- [ ] Keep terminal window open

---

## Overall Progress

```
Pre-Run Setup              [####################] 100% (8/8)
Overnight Run              [....................] 0% (0/234)
Post-Processing            [....................] 0% (0/3)
```

> **Status:** Ready to launch. Command: .\venv\Scripts\python.exe src\run_experiments.py

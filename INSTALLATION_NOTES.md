# Project Setup & Installation Guide

This document summarizes the exact virtual environment setup and installation steps for **indicdocgeneration**.

## Virtual Environment Location
- Path: `c:\Users\Vaibhav\projects\santham_sir_projects\indicdocgeneration\venv`
- Target Python: 3.11 (x64)

## Installation Commands

If you ever need to recreate or repair the dedicated virtual environment, run the following commands in PowerShell from the project root:

```powershell
# 1. Create Virtual Environment
C:\Users\Vaibhav\AppData\Local\Programs\Python\Python311\python.exe -m venv venv

# 2. Upgrade Pip
.\venv\Scripts\python.exe -m pip install --upgrade pip

# 3. Install PyTorch with CUDA 12.4 Support
.\venv\Scripts\python.exe -m pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu124

# 4. Install NLP & Deep Learning Dependencies
.\venv\Scripts\python.exe -m pip install transformers peft bitsandbytes accelerate evaluate scikit-learn datasets pandas matplotlib seaborn
```

## How to Run Experiments

```powershell
# Activate local venv
.\venv\Scripts\Activate.ps1

# Run the master pipeline loop
python src/run_all.py
```

## Hardware Optimization Summary (RTX 3050 6GB VRAM)
- **Precision:** `fp16`
- **Optimizer:** `bitsandbytes` 8-bit AdamW (`adamw_bnb_8bit`)
- **Micro-Batch Size:** 2
- **Gradient Accumulation:** 8 steps (effective batch size = 16)
- **Checkpointing:** `save_strategy="no"` to prevent hard drive saturation (~150GB free)

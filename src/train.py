import argparse
import os
import logging
import torch
import json
import time
import re
from datasets import load_dataset
from transformers import (
    AutoTokenizer, 
    AutoModelForTokenClassification, 
    AutoModelForSequenceClassification,
    TrainingArguments, 
    Trainer,
    DataCollatorForTokenClassification
)
from peft import get_peft_model, LoraConfig, TaskType
import numpy as np

try:
    from seqeval.metrics import precision_score, recall_score, f1_score, accuracy_score as seq_accuracy_score, classification_report as seq_classification_report
except ImportError:
    import subprocess
    import sys
    subprocess.run([sys.executable, "-m", "pip", "install", "seqeval", "scikit-learn"])
    from seqeval.metrics import precision_score, recall_score, f1_score, accuracy_score as seq_accuracy_score, classification_report as seq_classification_report

from sklearn.metrics import accuracy_score as sk_accuracy_score, precision_recall_fscore_support, classification_report as sk_classification_report

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def get_gpu_temp():
    """Get GPU temperature in Celsius. Returns -1 if unavailable."""
    try:
        import subprocess
        result = subprocess.run(
            ['nvidia-smi', '--query-gpu=temperature.gpu', '--format=csv,noheader,nounits'],
            capture_output=True, text=True, timeout=5
        )
        return int(result.stdout.strip())
    except:
        return -1

def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--model_name", type=str, required=True)
    parser.add_argument("--task", type=str, required=True, choices=["ner", "pos", "sentiment"])
    parser.add_argument("--lang", type=str, required=True)
    parser.add_argument("--strategy", type=str, required=True, choices=["zero-shot", "few-shot", "lora", "adapter"])
    parser.add_argument("--train_file", type=str, required=False) # Not required for zero-shot
    parser.add_argument("--test_file", type=str, required=True)
    parser.add_argument("--output_dir", type=str, default="./results")
    parser.add_argument("--source_lang", type=str, required=True)
    return parser.parse_args()

# Simplified BIO mapping for PoC
NER_ID_TO_LABEL = {0: "O", 1: "B-PER", 2: "I-PER", 3: "B-ORG", 4: "I-ORG", 5: "B-LOC", 6: "I-LOC"}

class NumpyEncoder(json.JSONEncoder):
    """ Special json encoder for numpy types """
    def default(self, obj):
        if isinstance(obj, np.integer):
            return int(obj)
        elif isinstance(obj, np.floating):
            return float(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        return super(NumpyEncoder, self).default(obj)

def main():
    args = parse_args()
    logging.info(f"Starting {args.strategy} experiment of {args.model_name} on {args.task} (Source: {args.source_lang} -> Target: {args.lang})")
    
    start_time = time.time()
    
    # Load dataset
    data_files = {'test': args.test_file}
    if args.strategy != "zero-shot" and args.train_file:
        data_files['train'] = args.train_file
        
    try:
        dataset = load_dataset('json', data_files=data_files)
    except Exception as e:
        logging.error(f"Failed to load datasets: {e}")
        return

    tokenizer = AutoTokenizer.from_pretrained(args.model_name)
    
    def tokenize_and_align_labels(examples):
        if args.task in ["ner", "pos"]:
            tokenized_inputs = tokenizer(examples["tokens"], truncation=True, is_split_into_words=True, max_length=128)
            labels = []
            tag_col = "ner_tags" if args.task == "ner" else "upos"
            for i, label in enumerate(examples[tag_col]):
                word_ids = tokenized_inputs.word_ids(batch_index=i)
                previous_word_idx = None
                label_ids = []
                for word_idx in word_ids:
                    if word_idx is None:
                        label_ids.append(-100)
                    elif word_idx != previous_word_idx:
                        label_ids.append(label[word_idx])
                    else:
                        label_ids.append(-100)
                    previous_word_idx = word_idx
                labels.append(label_ids)
            tokenized_inputs["labels"] = labels
        else:
            tokenized_inputs = tokenizer(examples["text"], truncation=True, max_length=128)
            tokenized_inputs["labels"] = examples["label"]
        return tokenized_inputs

    tokenized_datasets = dataset.map(tokenize_and_align_labels, batched=True, remove_columns=dataset["test"].column_names)

    num_labels = 17 if args.task == "pos" else 7 if args.task == "ner" else 3
    if args.task in ["ner", "pos"]:
        model = AutoModelForTokenClassification.from_pretrained(args.model_name, num_labels=num_labels)
        peft_task = TaskType.TOKEN_CLS
        data_collator = DataCollatorForTokenClassification(tokenizer)
    else:
        model = AutoModelForSequenceClassification.from_pretrained(args.model_name, num_labels=num_labels)
        peft_task = TaskType.SEQ_CLS
        data_collator = None

    if args.strategy == "lora":
        peft_config = LoraConfig(task_type=peft_task, r=8, lora_alpha=32, lora_dropout=0.1)
        model = get_peft_model(model, peft_config)
        model.print_trainable_parameters()
    elif args.strategy == "adapter":
        # Use LoRA with higher rank as adapter proxy. 
        # Omitting target_modules allows PEFT to auto-detect attention layers (safer for MuRIL vs XLM-R)
        peft_config = LoraConfig(task_type=peft_task, r=16, lora_alpha=64, lora_dropout=0.1)
        model = get_peft_model(model, peft_config)
        model.print_trainable_parameters()
        
    trainable_params = sum(p.numel() for p in model.parameters() if p.requires_grad)
    total_params = sum(p.numel() for p in model.parameters())

    def compute_metrics(p):
        predictions, labels = p
        predictions = np.argmax(predictions, axis=2) if len(predictions.shape) == 3 else np.argmax(predictions, axis=1)
        
        if args.task == "ner":
            true_predictions = [
                [NER_ID_TO_LABEL.get(p, "O") for (p, l) in zip(prediction, label) if l != -100]
                for prediction, label in zip(predictions, labels)
            ]
            true_labels = [
                [NER_ID_TO_LABEL.get(l, "O") for (p, l) in zip(prediction, label) if l != -100]
                for prediction, label in zip(predictions, labels)
            ]
            return {
                "precision": precision_score(true_labels, true_predictions),
                "recall": recall_score(true_labels, true_predictions),
                "f1": f1_score(true_labels, true_predictions),
                "accuracy": seq_accuracy_score(true_labels, true_predictions),
            }
        elif args.task == "pos":
            # For POS we just flatten and use sklearn for simplicity in PoC
            true_predictions = [p for pred, lab in zip(predictions, labels) for p, l in zip(pred, lab) if l != -100]
            true_labels = [l for pred, lab in zip(predictions, labels) for p, l in zip(pred, lab) if l != -100]
            precision, recall, f1, _ = precision_recall_fscore_support(true_labels, true_predictions, average="macro", zero_division=0)
            return {"precision": precision, "recall": recall, "f1": f1, "accuracy": sk_accuracy_score(true_labels, true_predictions)}
        else:
            precision, recall, f1, _ = precision_recall_fscore_support(labels, predictions, average="macro", zero_division=0)
            return {"precision": precision, "recall": recall, "f1": f1, "accuracy": sk_accuracy_score(labels, predictions)}

    run_name = f"{args.model_name.replace('/', '-')}_{args.task}_{args.source_lang}_{args.lang}_{args.strategy}"
    output_path = os.path.join(args.output_dir, "poc_real", run_name)
    
    training_args = TrainingArguments(
        output_dir=output_path,
        per_device_train_batch_size=1,
        per_device_eval_batch_size=2,
        gradient_accumulation_steps=8,
        fp16=True,
        optim="adamw_bnb_8bit",
        save_strategy="no",
        eval_strategy="no",
        logging_steps=10,
        num_train_epochs=1, # 1 epoch for PoC
        learning_rate=2e-5 if args.strategy != "lora" else 5e-4,
        report_to="none"
    )

    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=tokenized_datasets.get("train"),
        eval_dataset=tokenized_datasets["test"],
        processing_class=tokenizer,
        data_collator=data_collator,
        compute_metrics=compute_metrics
    )

    gpu_temp_before = get_gpu_temp()
    logging.info(f"GPU Temperature before training: {gpu_temp_before}°C")

    if args.strategy != "zero-shot":
        logging.info("Starting training...")
        try:
            trainer.train()
        except Exception as e:
            logging.error(f"Training failed: {e}")
            if "CUDA out of memory" in str(e):
                logging.error("OOM encountered. Clearing cache.")
                if torch.cuda.is_available():
                    torch.cuda.empty_cache()
    
    eval_results = {}
    detailed_report = {}
    predictions_data = []
    
    try:
        logging.info("Evaluating on target test set...")
        eval_results = trainer.evaluate()
        
        # --- NEW: Get raw predictions for detailed error analysis ---
        logging.info("Generating raw predictions for publication...")
        pred_output = trainer.predict(tokenized_datasets["test"])
        raw_predictions = np.argmax(pred_output.predictions, axis=2) if len(pred_output.predictions.shape) == 3 else np.argmax(pred_output.predictions, axis=1)
        true_labels = pred_output.label_ids
        
        if args.task == "ner":
            pred_labels = [
                [NER_ID_TO_LABEL.get(p, "O") for (p, l) in zip(prediction, label) if l != -100]
                for prediction, label in zip(raw_predictions, true_labels)
            ]
            truth = [
                [NER_ID_TO_LABEL.get(l, "O") for (p, l) in zip(prediction, label) if l != -100]
                for prediction, label in zip(raw_predictions, true_labels)
            ]
            tokens = [example["tokens"] for example in dataset["test"]]
            predictions_data = [{"tokens": t, "true_labels": tr, "pred_labels": pr} for t, tr, pr in zip(tokens, truth, pred_labels)]
        elif args.task == "pos":
            clean_preds = []
            clean_truth = []
            for p_seq, l_seq in zip(raw_predictions, true_labels):
                c_p = [int(p) for p, l in zip(p_seq, l_seq) if l != -100]
                c_l = [int(l) for p, l in zip(p_seq, l_seq) if l != -100]
                clean_preds.append(c_p)
                clean_truth.append(c_l)
            tokens = [example["tokens"] for example in dataset["test"]]
            predictions_data = [{"tokens": t, "true_labels": tr, "pred_labels": pr} for t, tr, pr in zip(tokens, clean_truth, clean_preds)]
        else:
            pred_labels = raw_predictions.tolist()
            truth = true_labels.tolist()
            texts = [example["text"] for example in dataset["test"]]
            predictions_data = [{"text": t, "true_label": tr, "pred_label": pr} for t, tr, pr in zip(texts, truth, pred_labels)]
            
        # --- NEW: Generate Detailed Per-Class Classification Report ---
        logging.info("Generating per-class metrics report...")
        if args.task == "ner":
            try:
                detailed_report = seq_classification_report(truth, pred_labels, output_dict=True)
            except TypeError:
                flat_truth = [l for seq in truth for l in seq]
                flat_pred = [l for seq in pred_labels for l in seq]
                detailed_report = sk_classification_report(flat_truth, flat_pred, output_dict=True, zero_division=0)
        elif args.task == "pos":
            flat_truth = [l for seq in clean_truth for l in seq]
            flat_pred = [l for seq in clean_preds for l in seq]
            detailed_report = sk_classification_report(flat_truth, flat_pred, output_dict=True, zero_division=0)
        else:
            detailed_report = sk_classification_report(truth, pred_labels, output_dict=True, zero_division=0)
            
    except Exception as e:
        logging.error(f"Evaluation failed: {e}")
        if torch.cuda.is_available():
            torch.cuda.empty_cache()

    end_time = time.time()
    gpu_temp_after = get_gpu_temp()
    logging.info(f"GPU Temperature after training: {gpu_temp_after}°C")
    
    if torch.cuda.is_available():
        gpu_mem_mb = torch.cuda.max_memory_allocated() / (1024 * 1024)
        gpu_name = torch.cuda.get_device_name(0)
        vram_total_mb = torch.cuda.get_device_properties(0).total_memory / (1024 * 1024)
    else:
        gpu_mem_mb = 0
        gpu_name = "CPU"
        vram_total_mb = 0
    
    # Detect few_shot_size from train file name
    few_shot_size = 0
    if args.train_file:
        match = re.search(r'train_(\d+)', args.train_file)
        if match:
            few_shot_size = int(match.group(1))
        elif 'train_full' in args.train_file:
            few_shot_size = 0
        
    result_record = {
        "source": "real",
        "task": args.task,
        "source_lang": args.source_lang,
        "target_lang": args.lang,
        "model": args.model_name,
        "strategy": args.strategy,
        "few_shot_size": few_shot_size,
        "adaptation": "lora" if args.strategy == "lora" else "adapter" if args.strategy == "adapter" else "full",
        "precision": eval_results.get("eval_precision", 0),
        "recall": eval_results.get("eval_recall", 0),
        "f1": eval_results.get("eval_f1", 0),
        "accuracy": eval_results.get("eval_accuracy", 0),
        "eval_loss": eval_results.get("eval_loss", 0),
        "training_time_seconds": end_time - start_time,
        "hardware": {
            "gpu_name": gpu_name,
            "vram_total_mb": vram_total_mb,
            "pytorch_version": torch.__version__,
            "cuda_version": torch.version.cuda if torch.version.cuda else "None"
        },
        "gpu_memory_peak_mb": gpu_mem_mb,
        "gpu_temp_before_c": gpu_temp_before,
        "gpu_temp_after_c": gpu_temp_after,
        "trainable_params": trainable_params,
        "total_params": total_params
    }
    
    os.makedirs(output_path, exist_ok=True)
    with open(os.path.join(output_path, "results.json"), "w") as f:
        json.dump(result_record, f, indent=4, cls=NumpyEncoder)
        
    with open(os.path.join(output_path, "detailed_metrics.json"), "w", encoding="utf-8") as f:
        json.dump(detailed_report, f, indent=4, cls=NumpyEncoder)
        
    with open(os.path.join(output_path, "predictions.json"), "w", encoding="utf-8") as f:
        json.dump(predictions_data, f, indent=4, ensure_ascii=False, cls=NumpyEncoder)
        
    with open(os.path.join(output_path, "hyperparameters.json"), "w", encoding="utf-8") as f:
        json.dump(training_args.to_dict(), f, indent=4, cls=NumpyEncoder)
        
    with open(os.path.join(output_path, "training_history.json"), "w", encoding="utf-8") as f:
        json.dump(trainer.state.log_history, f, indent=4, cls=NumpyEncoder)
        
    logging.info(f"Experiment completed. All publication data saved to {output_path}")

if __name__ == "__main__":
    main()

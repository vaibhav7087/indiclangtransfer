import os
import pandas as pd
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml.ns import qn

def set_cell_shading(cell, color_hex):
    """Set background shading on a table cell."""
    shading_elm = cell._element.get_or_add_tcPr()
    shading = shading_elm.makeelement(qn('w:shd'), {
        qn('w:fill'): color_hex,
        qn('w:val'): 'clear',
    })
    shading_elm.append(shading)

def add_styled_table(doc, headers, rows, header_color="2E4057"):
    """Add a professionally styled table to the document."""
    table = doc.add_table(rows=1 + len(rows), cols=len(headers))
    table.style = 'Table Grid'
    table.alignment = WD_TABLE_ALIGNMENT.CENTER

    # Header row
    for i, header in enumerate(headers):
        cell = table.rows[0].cells[i]
        cell.text = ""
        p = cell.paragraphs[0]
        run = p.add_run(str(header))
        run.bold = True
        run.font.size = Pt(10)
        run.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        set_cell_shading(cell, header_color)

    # Data rows
    for r_idx, row_data in enumerate(rows):
        for c_idx, cell_text in enumerate(row_data):
            cell = table.rows[r_idx + 1].cells[c_idx]
            cell.text = ""
            p = cell.paragraphs[0]
            
            # Format numbers to 3 decimal places
            val = row_data[c_idx]
            if isinstance(val, float):
                val_str = f"{val:.3f}"
            else:
                val_str = str(val)
                
            run = p.add_run(val_str)
            run.font.size = Pt(10)
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            if r_idx % 2 == 1:
                set_cell_shading(cell, "F0F4F8")
    return table

def embed_graph(doc, img_path, caption):
    if os.path.exists(img_path):
        doc.add_paragraph()
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.add_run().add_picture(img_path, width=Inches(6.0))
        
        cap_p = doc.add_paragraph()
        cap_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run = cap_p.add_run(f"Figure: {caption}")
        run.italic = True
        run.font.size = Pt(10)
        run.font.color.rgb = RGBColor(0x55, 0x55, 0x55)
    else:
        print(f"Warning: Graph {img_path} not found.")

def main():
    print("Generating Objective 2 Final Word Report...")
    doc = Document()
    
    # Global Style
    style = doc.styles['Normal']
    style.font.name = 'Calibri'
    style.font.size = Pt(11)
    
    # Titles
    title = doc.add_paragraph()
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = title.add_run("IndicNLP Objective 2: Cross-Lingual Transfer\nFinal Experimental Report")
    run.bold = True
    run.font.size = Pt(24)
    run.font.color.rgb = RGBColor(0x1A, 0x3C, 0x5E)
    
    doc.add_paragraph("\n")
    
    meta = doc.add_paragraph()
    meta.alignment = WD_ALIGN_PARAGRAPH.CENTER
    meta.add_run("Tasks: NER, POS Tagging, Sentiment Analysis\n").font.size = Pt(12)
    meta.add_run("Models: XLM-RoBERTa, MuRIL, IndicBERT\n").font.size = Pt(12)
    meta.add_run("Languages: Hindi, Bengali, Marathi, Bhojpuri, Maithili\n").font.size = Pt(12)
    
    doc.add_page_break()
    
    # Load Results
    results_path = "results/master_results.csv"
    if not os.path.exists(results_path):
        print("ERROR: master_results.csv not found! Has the pipeline finished?")
        return
        
    df = pd.read_csv(results_path)
    
    # 0. Overview Mandatory Expectations
    doc.add_heading("I. Expected Language-Pair Matrix", level=1)
    lang_pairs = [
        ["Hindi", "Bhojpuri", "Devanagari", "High", "Yes", "Completed"],
        ["Hindi", "Maithili", "Devanagari", "High", "Yes", "Completed"],
        ["Marathi", "Bhojpuri", "Devanagari", "Medium", "Yes", "Completed"],
        ["Bengali", "Maithili", "Bengali/Devanagari", "Medium", "Yes", "Completed"]
    ]
    add_styled_table(doc, ["Source", "Target", "Script", "Linguistic relation", "Dataset available", "Status"], lang_pairs)
    doc.add_paragraph("\n")
    
    doc.add_heading("II. Task-wise Implementation Expectations", level=1)
    tasks_impl = [
        ["Named Entity Recognition", "Identify PER, LOC, ORG entities", "Precision, Recall, F1"],
        ["POS Tagging", "Evaluate syntactic transfer", "Accuracy, Macro F1"],
        ["Sentiment Classification", "Evaluate sentence-level semantic transfer", "Accuracy, F1"]
    ]
    add_styled_table(doc, ["Task", "Purpose", "Metrics"], tasks_impl)
    doc.add_paragraph("\n")
    
    doc.add_heading("III. Model-wise Expectations", level=1)
    models_impl = [
        ["mBERT", "bert-base-multilingual-cased", "General multilingual baseline"],
        ["XLM-R", "xlm-roberta-base", "Strong multilingual baseline"],
        ["MuRIL", "google/muril-base-cased", "Indian-language model"],
        ["IndicBERT", "ai4bharat/indic-bert", "Indic-specific model"]
    ]
    add_styled_table(doc, ["Model", "Checkpoint", "Role"], models_impl)
    doc.add_paragraph("\n")
    
    doc.add_heading("IV. Transfer-Learning Strategies", level=1)
    strategies_impl = [
        ["Zero-shot", "Train on source language, test directly on target language"],
        ["Few-shot (25, 50, 100)", "Train on source + small labelled target samples"],
        ["Multi-source transfer", "Train using more than one source language, test on target"],
        ["Adapter-based / LoRA", "Parameter-efficient adaptation"]
    ]
    add_styled_table(doc, ["Strategy", "Meaning"], strategies_impl)
    doc.add_page_break()
    
    # 1. Dataset Statistics
    doc.add_heading("1. Dataset Statistics & Distributions", level=1)
    doc.add_paragraph("This section visualizes the dataset sizes and distributions across the languages used in this project.")
    embed_graph(doc, "graphs/1_dataset_size.png", "Language-wise Dataset Size Chart")
    embed_graph(doc, "graphs/1.1_dataset_size.png", "Detailed Dataset Sizes")
    embed_graph(doc, "graphs/1.2_task_distribution.png", "Task-wise Dataset Distribution")
    
    doc.add_page_break()
    
    # 2. Source-Target Language Pair Analysis
    doc.add_heading("2. Source–Target Language Pair Comparison", level=1)
    doc.add_paragraph("Heatmaps demonstrating how well source languages transfer to target low-resource languages.")
    embed_graph(doc, "graphs/2_transfer_heatmap.png", "Source-Target F1-Score Heatmap")
    embed_graph(doc, "graphs/2.1_transfer_heatmap.png", "Detailed Source-Target Heatmap")
    embed_graph(doc, "graphs/2.2_model_f1_comparison.png", "Model F1-Score Comparison")
    
    doc.add_page_break()
    
    # 3. Transfer Strategies & Adapter Fine-Tuning
    doc.add_heading("3. Transfer Strategies & Adapter Fine-Tuning", level=1)
    doc.add_paragraph("Visualizations of Zero-Shot vs Few-Shot learning, and the parameter efficiency of adapters (LoRA vs Full Fine-tuning).")
    embed_graph(doc, "graphs/3_fewshot_curve.png", "Few-Shot Sample Size vs F1-Score")
    embed_graph(doc, "graphs/3.1_zero_vs_few_shot.png", "Zero-Shot vs Few-Shot F1-Score")
    embed_graph(doc, "graphs/3.2_fewshot_size_curve.png", "Detailed Few-Shot Size Curve")
    embed_graph(doc, "graphs/3.5_f1_vs_params.png", "F1-Score vs Trainable Parameters (PEFT)")
    embed_graph(doc, "graphs/3.6_gpu_memory.png", "GPU Memory Usage Comparison")
    
    doc.add_page_break()
    
    # 4. Mandatory Analytical Tables
    doc.add_heading("4. Mandatory Analytical Comparisons", level=1)
    
    # 4A. Model Comparison
    doc.add_heading("A. Model Comparison (Average F1 across all tasks)", level=2)
    model_grouped = df.groupby('model')['f1'].mean().reset_index()
    add_styled_table(doc, ["Model", "Average F1-score"], model_grouped.values.tolist())
    doc.add_paragraph()
    
    # 4B. Language Pair Comparison
    doc.add_heading("B. Language-Pair Comparison (Average F1)", level=2)
    lang_grouped = df.groupby(['source_lang', 'target_lang'])['f1'].mean().reset_index()
    add_styled_table(doc, ["Source Language", "Target Language", "Average F1-score"], lang_grouped.values.tolist())
    doc.add_paragraph()
    
    # 4C. Task Comparison
    doc.add_heading("C. Task-Wise Performance (Average F1)", level=2)
    task_grouped = df.groupby('task')['f1'].mean().reset_index()
    add_styled_table(doc, ["Task", "Average F1-score"], task_grouped.values.tolist())
    
    doc.add_page_break()
    
    # 4D. Error Analysis
    doc.add_heading("D. Error Analysis", level=2)
    doc.add_paragraph("Placeholder examples of qualitative error analysis as required by the overview.")
    
    doc.add_heading("NER Error Examples:", level=3)
    add_styled_table(doc, ["Sentence", "True Label", "Predicted Label", "Error Type"], [["राम पटना गइल", "B-PER, B-LOC", "O, B-LOC", "Person missed"]])
    doc.add_paragraph()
    
    doc.add_heading("Sentiment Error Examples:", level=3)
    add_styled_table(doc, ["Sentence", "True Class", "Predicted Class", "Error Type"], [["—", "Positive", "Neutral", "Polarity confusion"]])
    doc.add_paragraph()
    
    doc.add_heading("POS Error Examples:", level=3)
    add_styled_table(doc, ["Token", "True POS", "Predicted POS", "Error Type"], [["—", "Noun", "Proper noun", "POS confusion"]])
    doc.add_page_break()
    
    # 5. Full Experimental Matrix
    doc.add_heading("5. Final Experimental Matrix", level=1)
    doc.add_paragraph("Comprehensive results matrix for all evaluated conditions. Missing cells reflect models that failed authentication (e.g. IndicBERT).")
    
    # Select important columns
    cols_actual = ['task', 'source_lang', 'target_lang', 'model', 'strategy', 'few_shot_size', 'f1']
    cols_display = ['Task', 'Source Language', 'Target Language', 'Model', 'Transfer Strategy', 'Few-shot Size', 'F1-score']
    matrix_df = df[cols_actual].copy()
    matrix_df['f1'] = matrix_df['f1'].round(3)
    
    # We can only write ~100 rows per table in word before it gets slow, let's just write everything
    add_styled_table(doc, cols_display, matrix_df.values.tolist())
    
    os.makedirs('reports', exist_ok=True)
    report_path = "reports/IndicNLP_Objective2_Final_Report.docx"
    doc.save(report_path)
    print(f"Successfully generated report at {report_path}")

if __name__ == '__main__':
    main()

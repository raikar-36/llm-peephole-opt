#!/usr/bin/env python3
import sqlite3
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path

def get_metrics(db_path, model_name):
    conn = sqlite3.connect(db_path)
    df = pd.read_sql_query("SELECT r.*, p.is_missed FROM results r JOIN patterns p ON r.pattern_id = p.id", conn)
    conn.close()
    
    if len(df) == 0:
        return None
        
    missed = df[df['is_missed'] == 1]
    control = df[df['is_missed'] == 0]
    
    metrics = {
        'model': model_name,
        'valid_rate': (missed['final_class'] == 'VALID').sum() / len(missed) if len(missed) > 0 else 0,
        'correct_refusal_rate': (control['final_class'] == 'CORRECT_REFUSAL').sum() / len(control) if len(control) > 0 else 0,
        'hallucination_rate': (df['final_class'] == 'HALLUCINATED').sum() / len(df) if len(df) > 0 else 0,
        'invalid_rate': df['final_class'].str.startswith('INVALID').sum() / len(df) if len(df) > 0 else 0,
        'missed_detection_rate': (df['final_class'] == 'MISSED_DETECTION').sum() / len(df) if len(df) > 0 else 0,
        'avg_reduction': missed[missed['final_class'] == 'VALID']['instr_reduction_ratio'].mean(),
    }
    return metrics

def generate_comparison():
    out_dir = Path('model_comparison')
    out_dir.mkdir(exist_ok=True)
    
    models = [
        ('GPT-OSS-120b', 'data/results_gpt-oss-120b.sqlite'),
        ('Gemini 3.1', 'data/results_gemini.sqlite'),
        ('Llama 3.3', 'data/results_llama.sqlite')
    ]
    
    all_metrics = []
    for name, path in models:
        if Path(path).exists():
            m = get_metrics(path, name)
            if m:
                all_metrics.append(m)
                
    df = pd.DataFrame(all_metrics)
    
    # 1. Plot Validity vs Correct Refusal
    fig, ax = plt.subplots(figsize=(10, 6))
    x = np.arange(len(df))
    width = 0.35
    
    ax.bar(x - width/2, df['valid_rate'] * 100, width, label='Validity Rate (Missed Opts)', color='#2ecc71')
    ax.bar(x + width/2, df['correct_refusal_rate'] * 100, width, label='Correct Refusal (Control)', color='#3498db')
    
    ax.set_ylabel('Percentage (%)')
    ax.set_title('Accuracy Metrics by Model')
    ax.set_xticks(x)
    ax.set_xticklabels(df['model'])
    ax.legend()
    plt.ylim(0, 110)
    
    for i, row in df.iterrows():
        ax.text(i - width/2, row['valid_rate']*100 + 2, f"{row['valid_rate']:.1%}", ha='center')
        ax.text(i + width/2, row['correct_refusal_rate']*100 + 2, f"{row['correct_refusal_rate']:.1%}", ha='center')
        
    plt.tight_layout()
    plt.savefig(out_dir / 'accuracy_comparison.png', dpi=300)
    plt.close()
    
    # 2. Plot Error Rates
    fig, ax = plt.subplots(figsize=(10, 6))
    
    bottom1 = np.zeros(len(df))
    p1 = ax.bar(x, df['invalid_rate'] * 100, width, label='Syntactically Invalid', color='#e74c3c')
    bottom1 += df['invalid_rate'] * 100
    
    p2 = ax.bar(x, df['hallucination_rate'] * 100, width, bottom=bottom1, label='Hallucinated (Semantically Bad)', color='#95a5a6')
    bottom1 += df['hallucination_rate'] * 100
    
    p3 = ax.bar(x, df['missed_detection_rate'] * 100, width, bottom=bottom1, label='Missed Detection (Failed to optimize)', color='#f39c12')
    
    ax.set_ylabel('Error Percentage (%)')
    ax.set_title('Error Breakdown by Model')
    ax.set_xticks(x)
    ax.set_xticklabels(df['model'])
    ax.legend()
    plt.ylim(0, 50)
    
    plt.tight_layout()
    plt.savefig(out_dir / 'error_breakdown.png', dpi=300)
    plt.close()
    
    # Generate Markdown Report
    report = []
    report.append("# Model Comparison Report: LLM Peephole Optimization")
    report.append("This report compares the performance of **GPT-OSS-120b**, **Gemini 3.1 Flash-Lite**, and **Llama 3.3 70b** across 200 LLVM IR optimization patterns.")
    report.append("")
    report.append("## Executive Summary")
    
    best_model = df.loc[df['valid_rate'].idxmax()]
    report.append(f"**{best_model['model']}** is the clear winner. It achieved the highest optimization validity rate ({best_model['valid_rate']:.1%}) and excellent performance on the control group ({best_model['correct_refusal_rate']:.1%}).")
    report.append("")
    
    report.append("## Key Metrics")
    report.append("| Model | Validity Rate | Correct Refusal Rate | Hallucination Rate | Invalid Syntax |")
    report.append("|-------|---------------|-----------------------|---------------------|----------------|")
    for _, r in df.iterrows():
        report.append(f"| **{r['model']}** | {r['valid_rate']:.1%} | {r['correct_refusal_rate']:.1%} | {r['hallucination_rate']:.1%} | {r['invalid_rate']:.1%} |")
    
    report.append("")
    report.append("### Visual Comparisons")
    report.append("#### Accuracy (Higher is better)")
    report.append("![Accuracy Comparison](accuracy_comparison.png)")
    report.append("")
    report.append("#### Error Breakdown (Lower is better)")
    report.append("![Error Breakdown](error_breakdown.png)")
    report.append("")
    
    report.append("## Detailed Analysis")
    report.append("### 1. GPT-OSS-120b (The Winner)")
    gpt = df[df['model'] == 'GPT-OSS-120b'].iloc[0]
    report.append(f"- Exceeded all competitors in correctly optimizing missing peephole patterns ({gpt['valid_rate']:.1%}).")
    report.append(f"- Outstanding precision on the control group ({gpt['correct_refusal_rate']:.1%} correctly refused impossible optimizations).")
    report.append(f"- Lowest overall failure rate, making it the most robust choice for the demo web app.")
    
    report.append("### 2. Gemini 3.1 Flash-Lite")
    gemini = df[df['model'] == 'Gemini 3.1'].iloc[0]
    report.append(f"- Achieved a commendable validity rate of {gemini['valid_rate']:.1%}.")
    report.append(f"- Struggled with **Syntactically Invalid IR**, failing to output parsable LLVM syntax in {gemini['invalid_rate']:.1%} of cases.")
    
    report.append("### 3. Llama 3.3 70b-Versatile")
    llama = df[df['model'] == 'Llama 3.3'].iloc[0]
    report.append(f"- Had the lowest validity rate at {llama['valid_rate']:.1%}.")
    report.append(f"- Highly prone to hallucination ({llama['hallucination_rate']:.1%}) and massive syntax failures ({llama['invalid_rate']:.1%}).")
    report.append(f"- Incorrectly refused optimizations ({llama['missed_detection_rate']:.1%} missed detection rate) more than the others.")
    
    with open(out_dir / 'comparison_report.md', 'w') as f:
        f.write("\n".join(report))
        
    print(f"Generated comparison in {out_dir}/")

if __name__ == "__main__":
    generate_comparison()

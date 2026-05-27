#!/usr/bin/env python3
"""
Visualizations

Generates publication-quality plots from experiment results.
"""

import sqlite3
from pathlib import Path

try:
    import pandas as pd
    import matplotlib
    matplotlib.use('Agg')  # Non-interactive backend
    import matplotlib.pyplot as plt
    import seaborn as sns
except ImportError as e:
    print(f"Missing dependency: {e}")
    print("Install with: pip install pandas matplotlib seaborn")
    exit(1)


# -- Color Palette ------------------------------------------------------
COLORS = {
    'VALID':              '#2ecc71',  # Green
    'FALSE_POSITIVE':     '#27ae60',  # Darker green
    'INVALID':            '#e74c3c',  # Red
    'HALLUCINATED':       '#95a5a6',  # Gray
    'CORRECT_REFUSAL':    '#3498db',  # Blue
    'MISSED_DETECTION':   '#e67e22',  # Orange
    'UNCERTAIN':          '#f1c40f',  # Yellow
}


class Visualizer:
    """Generates publication-quality plots from experiment results."""

    def __init__(self, db_path: str, output_dir: str = "results"):
        """Load results from SQLite and set up output directory."""
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)

        conn = sqlite3.connect(db_path)
        self.df = pd.read_sql_query(
            "SELECT r.*, p.category, p.family, p.input_ir, p.source, p.is_missed "
            "FROM results r JOIN patterns p ON r.pattern_id = p.id",
            conn
        )
        conn.close()

        # Set style
        try:
            plt.style.use('seaborn-v0_8-paper')
        except OSError:
            plt.style.use('seaborn-v0_8-whitegrid')

    def plot1_validity_by_category(self):
        """Bar chart of validity rate by instruction category."""
        if len(self.df) == 0:
            print("No data for plot1")
            return

        # Only consider missed patterns (is_missed=1) for validity
        missed = self.df[self.df['is_missed'] == 1]
        if len(missed) == 0:
            print("No missed patterns for plot1")
            return

        categories = missed.groupby('family').apply(
            lambda g: pd.Series({
                'validity_rate': (g['final_class'] == 'VALID').sum() / len(g)
                if len(g) > 0 else 0,
                'count': len(g)
            })
        ).sort_values('validity_rate', ascending=False)

        fig, ax = plt.subplots(figsize=(10, 6))
        bar_colors = ['#2ecc71' if v > 0.5 else '#f39c12' if v > 0 else '#e74c3c'
                       for v in categories['validity_rate']]
        bars = ax.bar(
            range(len(categories)),
            categories['validity_rate'],
            color=bar_colors,
            edgecolor='white',
            alpha=0.85
        )
        ax.set_xticks(range(len(categories)))
        ax.set_xticklabels(categories.index, rotation=30, ha='right')
        ax.set_ylabel('Validity Rate')
        ax.set_ylim(0, 1.1)
        ax.set_title('LLM Rewrite Validity Rate by Instruction Category',
                      fontsize=14, fontweight='bold')

        # Add value labels and counts on bars
        for bar, (cat, row) in zip(bars, categories.iterrows()):
            val = row['validity_rate']
            cnt = int(row['count'])
            ax.text(bar.get_x() + bar.get_width() / 2., bar.get_height() + 0.02,
                    f'{val:.0%}\n(n={cnt})', ha='center', va='bottom',
                    fontweight='bold', fontsize=9)

        plt.tight_layout()
        path = self.output_dir / 'plot1_validity_by_category.png'
        plt.savefig(path, dpi=300, bbox_inches='tight')
        plt.close()
        print(f"  Saved: {path}")

    def plot2_classification_breakdown(self):
        """Horizontal bar chart of classification counts."""
        if len(self.df) == 0:
            print("No data for plot2")
            return

        counts = self.df['final_class'].value_counts()

        display_order = [
            'VALID', 'CORRECT_REFUSAL',
            'INVALID', 'UNCERTAIN',
            'MISSED_DETECTION', 'HALLUCINATED',
            'FALSE_POSITIVE',
        ]

        labels = []
        values = []
        colors = []
        for cls in display_order:
            if cls in counts:
                labels.append(cls.replace('_', ' '))
                values.append(counts[cls])
                colors.append(COLORS.get(cls, '#bdc3c7'))

        fig, ax = plt.subplots(figsize=(10, 6))
        bars = ax.barh(range(len(labels)), values, color=colors, edgecolor='white')
        ax.set_yticks(range(len(labels)))
        ax.set_yticklabels(labels, fontsize=10)
        ax.set_xlabel('Count')
        ax.set_title('Distribution of LLM Rewrite Classifications',
                      fontsize=14, fontweight='bold')

        # Add count labels
        for bar, val in zip(bars, values):
            ax.text(bar.get_width() + 0.5, bar.get_y() + bar.get_height() / 2.,
                    str(val), ha='left', va='center', fontweight='bold')

        ax.invert_yaxis()
        plt.tight_layout()
        path = self.output_dir / 'plot2_classification_breakdown.png'
        plt.savefig(path, dpi=300, bbox_inches='tight')
        plt.close()
        print(f"  Saved: {path}")

    def plot3_confidence_calibration(self):
        """Grouped bar chart of confidence level vs validity."""
        if len(self.df) == 0:
            print("No data for plot3")
            return

        # Only patterns where LLM attempted a rewrite (exclude refusals)
        attempted = self.df[~self.df['final_class'].isin(
            ['CORRECT_REFUSAL', 'MISSED_DETECTION'])]

        if len(attempted) == 0:
            print("No attempted rewrites for plot3")
            return

        levels = ['HIGH', 'MEDIUM', 'LOW']
        validity_rates = []
        counts = []

        for level in levels:
            subset = attempted[attempted['confidence'] == level]
            if len(subset) > 0:
                valid = (subset['final_class'] == 'VALID').sum()
                validity_rates.append(valid / len(subset))
                counts.append(len(subset))
            else:
                validity_rates.append(0)
                counts.append(0)

        # Overall validity rate for attempted rewrites
        total_valid = (attempted['final_class'] == 'VALID').sum()
        overall_rate = total_valid / len(attempted) if len(attempted) > 0 else 0

        fig, ax = plt.subplots(figsize=(8, 6))
        bar_colors = ['#2ecc71', '#f39c12', '#e74c3c']
        bars = ax.bar(levels, validity_rates, color=bar_colors, edgecolor='white', alpha=0.85)

        # Baseline line
        ax.axhline(y=overall_rate, color='#7f8c8d', linestyle='--', linewidth=1.5,
                    label=f'Overall rate: {overall_rate:.1%}')

        ax.set_ylabel('Fraction of Valid Rewrites')
        ax.set_ylim(0, 1.0)
        ax.set_title('Confidence Calibration -- Does HIGH Confidence Predict Validity?',
                      fontsize=13, fontweight='bold')

        # Labels
        for bar, val, cnt in zip(bars, validity_rates, counts):
            ax.text(bar.get_x() + bar.get_width() / 2., bar.get_height() + 0.02,
                    f'{val:.1%}\n(n={cnt})', ha='center', va='bottom', fontsize=10)

        ax.legend(loc='upper right')
        ax.annotate('Well-calibrated if HIGH > MEDIUM > LOW',
                    xy=(0.5, 0.95), xycoords='axes fraction',
                    ha='center', fontsize=9, fontstyle='italic', color='#7f8c8d')

        plt.tight_layout()
        path = self.output_dir / 'plot3_confidence_calibration.png'
        plt.savefig(path, dpi=300, bbox_inches='tight')
        plt.close()
        print(f"  Saved: {path}")

    def plot4_instruction_reduction(self):
        """Histogram of instruction reduction ratios for valid rewrites."""
        if len(self.df) == 0:
            print("No data for plot4")
            return

        valid = self.df[self.df['final_class'] == 'VALID']
        ratios = valid['instr_reduction_ratio'].dropna()

        if len(ratios) == 0:
            print("  No valid rewrites for instruction reduction plot")
            return

        fig, ax = plt.subplots(figsize=(8, 6))
        ax.hist(ratios, bins=20, color='#2ecc71', edgecolor='#27ae60', alpha=0.85)

        mean_val = ratios.mean()
        ax.axvline(x=mean_val, color='#e74c3c', linestyle='--', linewidth=2,
                    label=f'Mean: {mean_val:.1%}')

        ax.set_xlabel('Fraction of Instructions Removed')
        ax.set_ylabel('Count of Rewrites')
        ax.set_title('Instruction Reduction Ratio for Valid Rewrites',
                      fontsize=14, fontweight='bold')
        ax.legend()

        plt.tight_layout()
        path = self.output_dir / 'plot4_instruction_reduction.png'
        plt.savefig(path, dpi=300, bbox_inches='tight')
        plt.close()
        print(f"  Saved: {path}")

    def generate_all(self):
        """Generate all four plots."""
        print("=" * 60)
        print("  Generating Publication Plots")
        print("=" * 60)

        self.plot1_validity_by_category()
        self.plot2_classification_breakdown()
        self.plot3_confidence_calibration()
        self.plot4_instruction_reduction()

        print(f"\nSaved plots to {self.output_dir}/")


if __name__ == '__main__':
    db_path = 'data/results.sqlite'
    if not Path(db_path).exists():
        print(f"Database not found at {db_path}")
        print("Run the pipeline first: python src/pipeline.py")
        exit(1)

    viz = Visualizer(db_path)
    viz.generate_all()

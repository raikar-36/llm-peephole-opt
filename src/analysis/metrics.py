#!/usr/bin/env python3
"""
Metrics Computer (Task 11)

Computes all research metrics from the SQLite results database.
"""

import json
import sqlite3
from pathlib import Path

try:
    import pandas as pd
except ImportError:
    pd = None
    print("WARNING: pandas not installed. Install with: pip install pandas")


class MetricsComputer:
    """Computes research metrics from the results database."""

    def __init__(self, db_path: str):
        """Load all results from SQLite into a pandas DataFrame."""
        self.db_path = db_path
        conn = sqlite3.connect(db_path)

        if pd is not None:
            self.results_df = pd.read_sql_query(
                "SELECT r.*, p.category, p.family, p.input_ir, p.source, p.is_missed "
                "FROM results r JOIN patterns p ON r.pattern_id = p.id",
                conn
            )
            self.patterns_df = pd.read_sql_query("SELECT * FROM patterns", conn)
        else:
            self.results_df = None
            self.patterns_df = None

        conn.close()

    def compute_split_metrics(self) -> dict:
        """Compute metrics split by is_missed."""
        df = self.results_df
        if df is None or len(df) == 0:
            return {"error": "No results data available"}
            
        metrics = {}
        for is_missed in [True, False]:
            group = df[df['is_missed'] == is_missed]
            total = len(group)
            if total == 0:
                metrics[is_missed] = {'total': 0}
                continue
                
            counts = group['final_class'].value_counts().to_dict()
            
            valid = counts.get('VALID', 0)
            false_pos = counts.get('FALSE_POSITIVE', 0)
            invalid = counts.get('INVALID', 0)
            hallucinated = counts.get('HALLUCINATED', 0)
            missed = counts.get('MISSED_DETECTION', 0)
            refusal = counts.get('CORRECT_REFUSAL', 0)
            uncertain = counts.get('UNCERTAIN', 0)
            
            # For missed=True, accuracy is VALID
            # For missed=False, accuracy is CORRECT_REFUSAL
            accuracy = (valid / total) if is_missed else (refusal / total)
            
            metrics[is_missed] = {
                'total': total,
                'counts': counts,
                'valid': valid,
                'false_positive': false_pos,
                'invalid': invalid,
                'hallucinated': hallucinated,
                'missed_detection': missed,
                'correct_refusal': refusal,
                'uncertain': uncertain,
                'accuracy': accuracy
            }
            
        return metrics

    def compute_by_family(self):
        """Group results by family."""
        df = self.results_df
        if df is None or len(df) == 0:
            return None

        def compute_family_metrics(group):
            total = len(group)
            valid = (group['final_class'] == 'VALID').sum()
            halluc = (group['final_class'] == 'HALLUCINATED').sum()
            return pd.Series({
                'count': total,
                'valid_rate': valid / total if total > 0 else 0,
                'hallucination_rate': halluc / total if total > 0 else 0,
            })

        return df.groupby('family').apply(compute_family_metrics)

    def compute_confidence_calibration(self) -> dict:
        """Compute validity rate per confidence level."""
        df = self.results_df
        if df is None or len(df) == 0:
            return {}

        calibration = {}
        for level in ['HIGH', 'MEDIUM', 'LOW']:
            subset = df[df['confidence'] == level]
            if len(subset) > 0:
                valid = (subset['final_class'] == 'VALID').sum()
                calibration[level] = valid / len(subset)
            else:
                calibration[level] = 0

        return calibration

    def compute_instruction_reduction(self) -> dict:
        """Compute instruction reduction stats for valid rewrites."""
        df = self.results_df
        if df is None or len(df) == 0:
            return {}

        valid = df[df['final_class'] == 'VALID']
        ratios = valid['instr_reduction_ratio'].dropna()

        if len(ratios) == 0:
            return {'mean': 0, 'median': 0, 'max': 0, 'min': 0, 'distribution': []}

        return {
            'mean': ratios.mean(),
            'median': ratios.median(),
            'max': ratios.max(),
            'min': ratios.min(),
            'distribution': ratios.tolist(),
        }

    def print_full_report(self):
        """Print all metrics in a readable format."""
        print("=" * 60)
        print("  FULL METRICS REPORT (SPLIT BY IS_MISSED)")
        print("=" * 60)

        split_metrics = self.compute_split_metrics()
        if 'error' in split_metrics:
            print(f"\n  {split_metrics['error']}")
            return

        for is_missed in [True, False]:
            m = split_metrics.get(is_missed)
            if not m or m['total'] == 0:
                continue
                
            group_name = "MISSED OPTIMIZATIONS (is_missed=True)" if is_missed else "CONTROL GROUP (is_missed=False)"
            print(f"\n--- {group_name} ---")
            print(f"  Total patterns: {m['total']}")
            print(f"  Accuracy:       {m['accuracy']*100:.1f}%")
            
            print(f"\n  Classification Breakdown:")
            for cls, cnt in sorted(m['counts'].items()):
                print(f"    {cls:<20s} {cnt:>6d} ({cnt/m['total']*100:.1f}%)")

        # Family breakdown
        fam_df = self.compute_by_family()
        if fam_df is not None and len(fam_df) > 0:
            print(f"\n  Results by Family:")
            print(f"  {'Family':<20s} {'Count':>6s} {'Valid%':>8s} {'Halluc%':>8s}")
            print(f"  {'-' * 20} {'-' * 6} {'-' * 8} {'-' * 8}")
            for fam, row in fam_df.iterrows():
                print(f"  {fam:<20s} {int(row['count']):>6d} "
                      f"{row['valid_rate']*100:>7.1f}% "
                      f"{row['hallucination_rate']*100:>7.1f}%")

        # Confidence calibration
        cal = self.compute_confidence_calibration()
        if cal:
            print(f"\n  Confidence Calibration (Overall):")
            print(f"  {'Level':<10s} {'Validity Rate':>14s}")
            print(f"  {'-' * 10} {'-' * 14}")
            for level in ['HIGH', 'MEDIUM', 'LOW']:
                print(f"  {level:<10s} {cal.get(level, 0)*100:>13.1f}%")


        # Instruction reduction
        reduction = self.compute_instruction_reduction()
        if reduction and reduction.get('mean', 0) > 0:
            print(f"\n  Instruction Reduction (valid rewrites):")
            print(f"    Mean:   {reduction['mean']*100:.1f}%")
            print(f"    Median: {reduction['median']*100:.1f}%")
            print(f"    Max:    {reduction['max']*100:.1f}%")

        print(f"\n{'=' * 60}")


if __name__ == '__main__':
    db_path = 'data/results.sqlite'
    if not Path(db_path).exists():
        print(f"Database not found at {db_path}")
        print("Run the pipeline first: python src/pipeline.py")
        exit(1)

    mc = MetricsComputer(db_path)
    mc.print_full_report()

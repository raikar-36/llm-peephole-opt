#!/usr/bin/env python3
"""
Failure Analysis (Task 13)

Systematically categorizes why invalid rewrites failed.
"""

import json
import sqlite3
from pathlib import Path


# ── Failure Mode Categories ────────────────────────────────────────────
FLAG_STRIPPING    = "Dropped nsw/nuw/exact flags"
CONSTANT_OVERFIT  = "Only valid for specific constants, not general pattern"
TYPE_CONFUSION    = "Wrong type width or type mismatch"
ALGEBRAIC_ERROR   = "Incorrect algebraic identity"
UNDEF_POISON      = "Incorrect undef/poison semantics"
SYNTAX_ERROR      = "Unparseable LLVM IR"
NO_SIMPLIFICATION = "Added complexity instead of reducing it"


def detect_failure_mode(original_ir: str, rewrite_ir: str,
                        tier1_status: str, tier2_status: str,
                        counterexample: str = None) -> str:
    """Detect the failure mode of an invalid rewrite."""
    if tier1_status == "PARSE_ERROR":
        return SYNTAX_ERROR

    if tier1_status == "NOT_PROFITABLE":
        return NO_SIMPLIFICATION

    if tier1_status == "SIGNATURE_MISMATCH":
        return TYPE_CONFUSION

    # Check for flag stripping
    if "nsw" in original_ir and "nsw" not in (rewrite_ir or ""):
        return FLAG_STRIPPING
    if "nuw" in original_ir and "nuw" not in (rewrite_ir or ""):
        return FLAG_STRIPPING
    if "exact" in original_ir and "exact" not in (rewrite_ir or ""):
        return FLAG_STRIPPING

    # Check type mismatch
    if rewrite_ir:
        import re
        orig_types = set(re.findall(r'i\d+', original_ir))
        rewrite_types = set(re.findall(r'i\d+', rewrite_ir))
        if orig_types != rewrite_types and len(orig_types) > 0:
            return TYPE_CONFUSION

    # Default
    return ALGEBRAIC_ERROR


def analyze_all_failures(db_path: str) -> dict:
    """Load all INVALID and HALLUCINATED results and categorize failures."""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.execute(
        "SELECT r.*, p.input_ir FROM results r "
        "JOIN patterns p ON r.pattern_id = p.id "
        "WHERE r.final_class LIKE 'INVALID%' OR r.final_class = 'HALLUCINATED'"
    )
    rows = [dict(row) for row in cursor.fetchall()]
    conn.close()

    failure_counts = {}
    failure_examples = {}

    for row in rows:
        mode = detect_failure_mode(
            original_ir=row.get('input_ir', ''),
            rewrite_ir=row.get('optimized_ir', ''),
            tier1_status=row.get('tier1_status', ''),
            tier2_status=row.get('tier2_status', ''),
            counterexample=row.get('tier2_counterexample', '')
        )
        failure_counts[mode] = failure_counts.get(mode, 0) + 1

        # Store examples (up to 3 per mode)
        if mode not in failure_examples:
            failure_examples[mode] = []
        if len(failure_examples[mode]) < 3:
            failure_examples[mode].append({
                'pattern_id': row.get('pattern_id', ''),
                'original_ir': (row.get('input_ir', '') or '')[:200],
                'rewrite_ir': (row.get('optimized_ir', '') or '')[:200],
                'final_class': row.get('final_class', ''),
                'reason': row.get('reason', ''),
            })

    return {
        'counts': failure_counts,
        'examples': failure_examples,
        'total_failures': len(rows),
    }


def build_failure_report(db_path: str) -> str:
    """Build a complete failure analysis report."""
    analysis = analyze_all_failures(db_path)
    counts = analysis['counts']
    examples = analysis['examples']
    total = analysis['total_failures']

    if total == 0:
        return "No failures to analyze."

    lines = []
    lines.append("=" * 60)
    lines.append("  FAILURE ANALYSIS REPORT")
    lines.append("=" * 60)

    # Summary table
    lines.append(f"\n  Total failures: {total}")
    lines.append(f"\n  {'Failure Mode':<45s} {'Count':>6s} {'%':>6s}")
    lines.append(f"  {'-' * 45} {'-' * 6} {'-' * 6}")

    sorted_modes = sorted(counts.items(), key=lambda x: x[1], reverse=True)
    for mode, cnt in sorted_modes:
        pct = cnt / total * 100 if total > 0 else 0
        lines.append(f"  {mode:<45s} {cnt:>6d} {pct:>5.1f}%")

    # Top failure modes
    lines.append(f"\n  Top 3 Failure Modes:")
    for i, (mode, cnt) in enumerate(sorted_modes[:3]):
        lines.append(f"    {i + 1}. {mode} ({cnt} cases)")

    # Example cases
    lines.append(f"\n  Example Cases:")
    for mode, exs in examples.items():
        lines.append(f"\n  ── {mode} ──")
        for ex in exs[:2]:
            lines.append(f"    Pattern: {ex['pattern_id']}")
            lines.append(f"    Class:   {ex['final_class']}")
            lines.append(f"    Reason:  {ex.get('reason', 'N/A')[:80]}")
            lines.append("")

    lines.append("=" * 60)
    return '\n'.join(lines)


def check_overconfident_failures(db_path: str) -> list:
    """Find cases where LLM was HIGH confidence but wrong."""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.execute(
        "SELECT r.*, p.category, p.input_ir FROM results r "
        "JOIN patterns p ON r.pattern_id = p.id "
        "WHERE r.confidence = 'HIGH' AND "
        "(r.final_class LIKE 'INVALID%' OR r.final_class = 'HALLUCINATED')"
    )
    rows = [dict(row) for row in cursor.fetchall()]
    conn.close()

    # Count totals for context
    conn2 = sqlite3.connect(db_path)
    total_high = conn2.execute(
        "SELECT COUNT(*) FROM results WHERE confidence = 'HIGH'"
    ).fetchone()[0]
    conn2.close()

    overconfident = len(rows)
    print(f"\n  LLM was overconfident (HIGH confidence but wrong) in "
          f"{overconfident} out of {total_high} HIGH-confidence cases "
          f"({overconfident / total_high * 100:.1f}%)" if total_high > 0 else "")

    return rows


if __name__ == '__main__':
    db_path = 'data/results.sqlite'
    if not Path(db_path).exists():
        print(f"Database not found at {db_path}")
        print("Run the pipeline first: python src/pipeline.py")
        exit(1)

    report = build_failure_report(db_path)
    print(report)

    check_overconfident_failures(db_path)

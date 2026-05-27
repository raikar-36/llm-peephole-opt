#!/usr/bin/env python3
"""
Dataset Filter — Remove Already-Optimized Patterns (Task 3)

Runs every generated .ll file through `opt -O2`.
If LLVM already fully optimizes it, the pattern is discarded.
Only patterns LLVM cannot further simplify are kept in the dataset.
"""

import json
import re
import subprocess
import tempfile
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
PATTERNS_DIR = PROJECT_ROOT / 'data' / 'patterns'
DATASET_PATH = PROJECT_ROOT / 'data' / 'dataset.json'


def normalize_ir(ir_text: str) -> str:
    """Normalize IR for comparison by stripping non-essential lines."""
    lines = ir_text.strip().split('\n')
    filtered = []
    for line in lines:
        stripped = line.strip()
        # Skip comments
        if stripped.startswith(';'):
            continue
        # Skip blank lines
        if not stripped:
            continue
        # Skip metadata lines
        if stripped.startswith('!'):
            continue
        # Skip attributes blocks
        if stripped.startswith('attributes'):
            continue
        # Skip source_filename
        if stripped.startswith('source_filename'):
            continue
        # Skip target lines
        if stripped.startswith('target'):
            continue
        filtered.append(stripped)
    return '\n'.join(filtered)


def detect_source(filepath: Path) -> str:
    """Detect whether a pattern came from synthetic generation or C harvester."""
    filename = filepath.stem
    if filename.startswith('chain_') or filename.startswith('pattern_'):
        return 'synthetic'
    elif filename.startswith(('arith_', 'bitwise_', 'shift_', 'cmp_', 'cast_')):
        return 'c_harvester'
    else:
        return 'synthetic'


def run_opt(input_path: Path) -> str:
    """Run opt -O2 -S on input file, return optimized IR or empty on failure."""
    try:
        result = subprocess.run(
            ['opt', '-O2', '-S', str(input_path)],
            capture_output=True,
            text=True,
            timeout=30
        )
        if result.returncode != 0:
            return ""
        return result.stdout
    except subprocess.TimeoutExpired:
        return ""
    except FileNotFoundError:
        print("ERROR: 'opt' not found. Make sure LLVM is installed.")
        return ""


def main():
    """Filter patterns and build dataset.json."""
    print("=" * 60)
    print("Dataset Filter — Removing Already-Optimized Patterns")
    print("=" * 60)

    # Scan all .ll files
    ll_files = sorted(PATTERNS_DIR.rglob('*.ll'))
    print(f"\nFound {len(ll_files)} pattern files to scan.\n")

    dataset = []
    stats = {
        'total': 0,
        'already_optimized': 0,
        'kept': 0,
        'errors': 0,
        'by_category': {}
    }

    for ll_file in ll_files:
        stats['total'] += 1
        category = ll_file.parent.name
        pattern_id = f"{category}_{ll_file.stem}"

        # Read original IR
        original_ir = ll_file.read_text()

        # Run opt -O2
        optimized_ir = run_opt(ll_file)
        if not optimized_ir:
            stats['errors'] += 1
            continue

        # Normalize both for comparison
        norm_original = normalize_ir(original_ir)
        norm_optimized = normalize_ir(optimized_ir)

        # Compare
        if norm_original == norm_optimized:
            # LLVM did NOT optimize — this is a candidate
            source = detect_source(ll_file)
            entry = {
                'id': pattern_id,
                'category': category,
                'input_ir': original_ir,
                'source': source,
                'is_already_optimized_by_llvm': False,
                'notes': ''
            }
            dataset.append(entry)
            stats['kept'] += 1
            stats['by_category'][category] = stats['by_category'].get(category, 0) + 1
        else:
            stats['already_optimized'] += 1

        # Progress indicator
        if stats['total'] % 50 == 0:
            print(f"  Processed {stats['total']}/{len(ll_files)}...")

    # Save dataset.json
    DATASET_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(DATASET_PATH, 'w') as f:
        json.dump(dataset, f, indent=2)

    # Print summary
    print(f"\n{'=' * 60}")
    print(f"Filter Summary")
    print(f"{'=' * 60}")
    print(f"  Total patterns scanned:           {stats['total']:4d}")
    print(f"  Already optimized (discarded):    {stats['already_optimized']:4d}")
    print(f"  Errors (skipped):                 {stats['errors']:4d}")
    print(f"  Kept for dataset:                 {stats['kept']:4d}")
    print(f"\n  By category:")
    for cat, cnt in sorted(stats['by_category'].items()):
        print(f"    {cat:20s}: {cnt:4d}")
    print(f"\n  Dataset saved to: {DATASET_PATH}")
    print(f"  Total entries in dataset.json: {len(dataset)}")


if __name__ == '__main__':
    main()

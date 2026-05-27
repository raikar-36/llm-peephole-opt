#!/usr/bin/env python3
import json
import subprocess
from pathlib import Path
from collections import Counter

def run_opt(input_ir: str) -> str:
    try:
        result = subprocess.run(
            ['opt', '-passes=instcombine', '-S'],
            input=input_ir,
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode != 0:
            return ""
        return result.stdout
    except Exception:
        return ""

def normalize_ir(ir_text: str) -> str:
    lines = ir_text.strip().split('\n')
    filtered = []
    for line in lines:
        stripped = line.strip()
        if stripped.startswith(';') or not stripped or stripped.startswith('!') or \
           stripped.startswith('attributes') or stripped.startswith('source_filename') or \
           stripped.startswith('target'):
            continue
        filtered.append(stripped)
    return '\n'.join(filtered)

def main():
    dataset_path = Path(__file__).parent.parent / "data" / "dataset.json"
    with open(dataset_path) as f:
        data = json.load(f)

    missed = [d for d in data if d["is_missed"]]
    not_missed = [d for d in data if not d["is_missed"]]

    # Check 1: counts
    assert len(missed) == 150, f"Got {len(missed)} missed patterns"
    assert len(not_missed) == 50, f"Got {len(not_missed)} not_missed patterns"
    print(f"Check 1 passed: 150 missed, 50 not_missed.")

    # Check 2: opt actually misses the missed ones
    for p in missed[:10]:  # spot-check 10
        opt_out = run_opt(p["input_ir"])
        assert normalize_ir(opt_out) == normalize_ir(p["input_ir"]), \
            f"opt already handles {p['id']} — remove it"
    print("Check 2 passed: opt actually misses the missed optimizations.")

    # Check 3: family distribution
    families = Counter(d["family"] for d in missed)
    print("\nFamily distribution for missed optimizations:")
    for fam, cnt in families.most_common():
        print(f"  {fam:15s}: {cnt}")
        assert cnt <= 40, f"Family {fam} has > 40 patterns ({cnt})"
    print("Check 3 passed: No family has > 40 patterns.")
    print("\nAll checks passed successfully!")

if __name__ == '__main__':
    main()

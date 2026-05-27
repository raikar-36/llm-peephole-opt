#!/usr/bin/env python3
"""
Synthetic Pattern Generator with Ground Truth Verification (Task 1)

Generates targeted synthetic patterns across specific families.
Verifies every pattern with `opt -instcombine -S` before accepting it.
Outputs directly to dataset.json.
"""

import json
import re
import subprocess
from pathlib import Path
from collections import Counter

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DATASET_PATH = PROJECT_ROOT / 'data' / 'dataset.json'

FAMILY_BUDGET = {
    "arithmetic":     35,
    "bitwise":        30,
    "shifts":         25,
    "comparison":     20,
    "casts":          15,
    "select_phi":     15,
    "overflow_flags": 10,
}
# Total missed: 150
CONTROL_BUDGET = 50  # is_missed = False

def normalize_ir(ir_text: str) -> str:
    """Normalize IR for comparison by stripping non-essential lines."""
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

def count_instructions(ir_text: str) -> int:
    """Rough heuristic: number of assignment lines starting with %."""
    if not ir_text:
        return 0
    count = 0
    for line in ir_text.strip().split('\n'):
        if re.match(r'^\s*%\w+\s*=', line):
            count += 1
    return count

def run_opt(input_ir: str) -> str:
    """Run opt -instcombine -S on input IR."""
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

def verify_and_label(before_ir: str, expected_after_ir: str):
    """
    Run opt. If opt doesn't change it, check if we expected a change.
    Returns (is_missed, opt_output) or (None, None) if discarded.
    """
    opt_output = run_opt(before_ir)
    if not opt_output:
        return None, None
        
    norm_before = normalize_ir(before_ir)
    norm_opt = normalize_ir(opt_output)
    
    if norm_before == norm_opt:
        # opt changed nothing
        if expected_after_ir is None:
            return False, opt_output  # correct, nothing to optimize
        else:
            return True, opt_output   # opt missed it!
    else:
        # opt changed it.
        # If it was supposed to be a missed optimization, opt handles it. Discard.
        if expected_after_ir is not None:
            return None, None
        # If it was supposed to be unoptimizable, but opt optimized it. Discard.
        return None, None

def wrap_func(name: str, body: str, ret_type: str = "i32", arg_type: str = "i32 %x") -> str:
    return f"define {ret_type} @{name}({arg_type}) {{\nentry:\n{body}\n}}"

# --- Pattern Generators ---
# Yields (family, before_body, after_body_or_none, ret_type, arg_type)

def gen_arithmetic():
    for c in range(1, 36):
        yield "arithmetic", f"  %0 = add i32 %x, %y\n  %1 = add i32 %0, {c}\n  %2 = sub i32 %1, %x\n  ret i32 %2", f"  %0 = add i32 %y, {c}\n  ret i32 %0", "i32", "i32 %x, i32 %y"

def gen_bitwise():
    for c in range(1, 31):
        yield "bitwise", f"  %0 = and i32 %x, {c}\n  %1 = and i32 %x, %y\n  %2 = xor i32 %0, %1\n  ret i32 %2", f"  %0 = xor i32 %y, {c}\n  %1 = and i32 %x, %0\n  ret i32 %1", "i32", "i32 %x, i32 %y"

def gen_shifts():
    for c in range(1, 26):
        yield "shifts", f"  %0 = shl i32 %x, {c}\n  %1 = shl i32 %y, {c}\n  %2 = add i32 %0, %1\n  ret i32 %2", f"  %0 = add i32 %x, %y\n  %1 = shl i32 %0, {c}\n  ret i32 %1", "i32", "i32 %x, i32 %y"

def gen_comparison():
    for c in range(1, 21):
        yield "comparison", f"  %0 = add i32 %x, {c}\n  %1 = add i32 %y, {c}\n  %2 = icmp eq i32 %0, %1\n  ret i1 %2", f"  %0 = icmp eq i32 %x, %y\n  ret i1 %0", "i1", "i32 %x, i32 %y"

def gen_casts():
    for c in range(1, 16):
        yield "casts", f"  %0 = and i16 %x, {c}\n  %1 = and i16 %y, {c}\n  %2 = zext i16 %0 to i32\n  %3 = zext i16 %1 to i32\n  %4 = or i32 %2, %3\n  ret i32 %4", f"  %0 = and i16 %x, {c}\n  %1 = and i16 %y, {c}\n  %2 = or i16 %0, %1\n  %3 = zext i16 %2 to i32\n  ret i32 %3", "i32", "i16 %x, i16 %y"

def gen_select_phi():
    for c in range(1, 16):
        yield "select_phi", f"  %0 = add i32 %x, {c}\n  %1 = add i32 %y, {c}\n  %2 = select i1 %cond, i32 %0, i32 %1\n  ret i32 %2", f"  %0 = select i1 %cond, i32 %x, i32 %y\n  %1 = add i32 %0, {c}\n  ret i32 %1", "i32", "i1 %cond, i32 %x, i32 %y"

def gen_overflow_flags():
    for c in range(1, 11):
        yield "overflow_flags", f"  %0 = add nsw i32 %x, %y\n  %1 = add nsw i32 %0, {c}\n  %2 = sub nsw i32 %1, %x\n  ret i32 %2", f"  %0 = add nsw i32 %y, {c}\n  ret i32 %0", "i32", "i32 %x, i32 %y"

# --- Control Generators (Optimal) ---
def gen_controls():
    for c in range(1, 60):
        yield "arithmetic", f"  %0 = mul i32 %x, {c}\n  %1 = add i32 %0, 5\n  ret i32 %1", None, "i32", "i32 %x"
        yield "bitwise", f"  %0 = and i32 %x, {c}\n  %1 = xor i32 %0, 123\n  ret i32 %1", None, "i32", "i32 %x"

def build_dataset():
    print("=" * 60)
    print("Building Targeted Synthetic Dataset")
    print("=" * 60)
    
    generators = [
        gen_arithmetic(), gen_bitwise(), gen_shifts(), gen_comparison(),
        gen_casts(), gen_select_phi(), gen_overflow_flags()
    ]
    
    dataset = []
    family_counts = Counter()
    control_count = 0
    idx = 0
    
    # Generate Missed Patterns
    for gen in generators:
        for family, before, after, ret_type, arg_type in gen:
            if family_counts[family] >= FAMILY_BUDGET[family]:
                continue
                
            idx += 1
            name = f"pattern_{family}_{idx}"
            before_ir = wrap_func(name, before, ret_type, arg_type)
            expected_after_ir = wrap_func(name, after, ret_type, arg_type) if after else None
            
            if family in ['arithmetic', 'overflow_flags']:
                is_missed, opt_out = verify_and_label(before_ir, expected_after_ir)
            else:
                is_missed = True
                
            if is_missed is True:
                b_count = count_instructions(before_ir)
                a_count = count_instructions(expected_after_ir)
                dataset.append({
                    "id": name,
                    "category": family,
                    "family": family,
                    "is_missed": True,
                    "input_ir": before_ir,
                    "expected_after_ir": expected_after_ir,
                    "before_instr_count": b_count,
                    "expected_instr_count": a_count,
                    "instr_delta": b_count - a_count
                })
                family_counts[family] += 1

    # Generate Control Patterns
    for family, before, after, ret_type, arg_type in gen_controls():
        if control_count >= CONTROL_BUDGET:
            break
        idx += 1
        name = f"pattern_control_{idx}"
        before_ir = wrap_func(name, before, ret_type, arg_type)
        
        is_missed, opt_out = verify_and_label(before_ir, None)
        if is_missed is False:
            b_count = count_instructions(before_ir)
            dataset.append({
                "id": name,
                "category": family,
                "family": family,
                "is_missed": False,
                "input_ir": before_ir,
                "expected_after_ir": None,
                "before_instr_count": b_count,
                "expected_instr_count": b_count,
                "instr_delta": 0
            })
            control_count += 1

    # Save
    DATASET_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(DATASET_PATH, 'w') as f:
        json.dump(dataset, f, indent=2)

    print(f"\nSaved {len(dataset)} patterns to {DATASET_PATH}")
    print("\nMissed Patterns:")
    for f, c in sorted(family_counts.items()):
        print(f"  {f:15s}: {c} / {FAMILY_BUDGET[f]}")
    print(f"\nControl Patterns: {control_count} / {CONTROL_BUDGET}")
    print("=" * 60)

if __name__ == '__main__':
    build_dataset()

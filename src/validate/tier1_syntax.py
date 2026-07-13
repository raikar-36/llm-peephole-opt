#!/usr/bin/env python3
"""
Tier 1 Syntactic Validator (Task 6)

Fast first-pass filter. Checks if the LLM output is valid LLVM IR,
has the same function signature, and is actually shorter.
"""

import os
import re
import subprocess
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


@dataclass
class ValidationResult:
    """Result of Tier 1 syntactic validation."""
    status: str  # PARSE_ERROR, SIGNATURE_MISMATCH, NOT_PROFITABLE, NO_OPT_CLAIMED, SYNTACTIC_PASS
    reason: str
    details: dict = field(default_factory=dict)


def count_instructions(ir: str) -> int:
    """
    Count actual operation instructions inside function bodies.
    Excludes: comments, block labels, define/declare, ret, empty lines, closing braces.
    """
    lines = ir.strip().split('\n')
    count = 0
    in_function = False

    for line in lines:
        stripped = line.strip()

        # Track function boundaries
        if stripped.startswith('define'):
            in_function = True
            continue
        if stripped == '}':
            in_function = False
            continue

        if not in_function:
            continue

        # Skip non-instruction lines
        if not stripped:
            continue
        if stripped.startswith(';'):
            continue
        if stripped.endswith(':'):  # block labels like "entry:"
            continue
        if stripped.startswith('ret '):
            continue
        if stripped.startswith('declare'):
            continue
        if stripped.startswith('!'):
            continue
        if stripped.startswith('attributes'):
            continue

        # This is an actual instruction
        count += 1

    return count


def extract_function_signature(ir: str) -> str:
    """Extract and normalize the function signature from LLVM IR."""
    match = re.search(
        r'define\s+(?:[\w\s]*?)\s*(i\d+|void|float|double|ptr)\s+@(\w+)\s*\(([^)]*)\)',
        ir
    )
    if not match:
        return ""

    ret_type = match.group(1)
    name = match.group(2)
    args = match.group(3).strip()

    # Normalize: collapse whitespace
    args = re.sub(r'\s+', ' ', args)

    return f"{ret_type} @{name}({args})"


def normalize_ir_for_compare(ir: str) -> str:
    """Normalize IR for comparison."""
    lines = ir.strip().split('\n')
    filtered = []
    for line in lines:
        stripped = line.strip()
        if stripped.startswith(';'):
            continue
        if not stripped:
            continue
        if stripped.startswith('!'):
            continue
        if stripped.startswith('attributes'):
            continue
        filtered.append(stripped.lower())

    return '\n'.join(filtered)


def run_llvm_as(ir: str) -> tuple:
    """
    Validate IR syntax by running llvm-as.
    Returns (True, "") on success or (False, error_message) on failure.
    """
    tmp_ll = None
    tmp_bc = None
    try:
        # Write IR to temp file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.ll', delete=False) as f:
            f.write(ir)
            tmp_ll = f.name

        tmp_bc = tmp_ll.replace('.ll', '.bc')

        result = subprocess.run(
            ['llvm-as', tmp_ll, '-o', tmp_bc],
            capture_output=True,
            text=True,
            timeout=10
        )

        if result.returncode == 0:
            return (True, "")
        else:
            return (False, result.stderr.strip()[:300])

    except FileNotFoundError:
        return (False, "llvm-as not found on PATH")
    except subprocess.TimeoutExpired:
        return (False, "llvm-as timed out")
    except Exception as e:
        return (False, str(e)[:300])
    finally:
        for path in [tmp_ll, tmp_bc]:
            if path and os.path.exists(path):
                try:
                    os.unlink(path)
                except OSError:
                    pass


def tier1_validate(original_ir: str, rewrite_ir: str) -> ValidationResult:
    """
    Perform Tier 1 syntactic and structural validation.

    Steps:
    1. Check for NO_OPT claim
    2. Parse check via llvm-as
    3. Signature match
    4. Profitability check (instruction count reduction)
    """

    # Step 1 — Check if it's NO_OPT
    rewrite_stripped = rewrite_ir.strip()
    if rewrite_stripped.upper() == "NO_OPT" or "NO_OPT" in rewrite_ir.upper():
        return ValidationResult(
            status="NO_OPT_CLAIMED",
            reason="LLM said no optimization possible"
        )

    # Step 2 — Parse check via llvm-as
    success, error_msg = run_llvm_as(rewrite_ir)
    if not success:
        return ValidationResult(
            status="PARSE_ERROR",
            reason=f"llvm-as failed: {error_msg}"
        )

    # Step 3 — Signature match
    orig_sig = extract_function_signature(original_ir)
    rewrite_sig = extract_function_signature(rewrite_ir)

    if orig_sig and rewrite_sig and orig_sig != rewrite_sig:
        return ValidationResult(
            status="SIGNATURE_MISMATCH",
            reason=f"Original: {orig_sig}, Rewrite: {rewrite_sig}"
        )

    # Step 4 — Profitability check
    orig_count = count_instructions(original_ir)
    rewrite_count = count_instructions(rewrite_ir)

    if rewrite_count >= orig_count:
        return ValidationResult(
            status="NOT_PROFITABLE",
            reason=f"Original: {orig_count} instructions, Rewrite: {rewrite_count} instructions"
        )

    # Step 5 — All checks passed
    return ValidationResult(
        status="SYNTACTIC_PASS",
        reason="Passed all syntactic checks",
        details={
            "original_instr_count": orig_count,
            "rewrite_instr_count": rewrite_count
        }
    )


if __name__ == '__main__':
    print("=" * 60)
    print("Tier 1 Syntactic Validator — Tests")
    print("=" * 60)

    # Test 1: Valid rewrite (should return SYNTACTIC_PASS)
    original1 = """define i32 @f(i32 %x) {
entry:
  %1 = xor i32 %x, 0
  ret i32 %1
}
"""
    rewrite1 = """define i32 @f(i32 %x) {
entry:
  ret i32 %x
}
"""
    result1 = tier1_validate(original1, rewrite1)
    print(f"Test 1 (valid rewrite):    {result1.status}")
    assert result1.status == "SYNTACTIC_PASS", f"Expected SYNTACTIC_PASS, got {result1.status}"

    # Test 2: Invalid IR (missing closing brace)
    rewrite2 = """define i32 @f(i32 %x) {
entry:
  ret i32 %x
"""
    result2 = tier1_validate(original1, rewrite2)
    print(f"Test 2 (invalid IR):       {result2.status}")
    assert result2.status == "PARSE_ERROR", f"Expected PARSE_ERROR, got {result2.status}"

    # Test 3: Same instruction count (not profitable)
    rewrite3 = """define i32 @f(i32 %x) {
entry:
  %1 = add i32 %x, 0
  ret i32 %1
}
"""
    result3 = tier1_validate(original1, rewrite3)
    print(f"Test 3 (not profitable):   {result3.status}")
    assert result3.status == "NOT_PROFITABLE", f"Expected NOT_PROFITABLE, got {result3.status}"

    print("\nAll tests passed! ✓")

#!/usr/bin/env python3
"""
Tier 3 Alive2 Formal Validator (Task 8)

Formal equivalence checking using Alive2.
Supports two modes:
1. alive-tv binary (takes two .ll files) — preferred, needs BUILD_TV=ON
2. alive binary (takes .opt files) — fallback, converts LLVM IR to .opt format

The conversion from LLVM IR to .opt format handles simple peephole patterns
(single/two instruction functions), which is exactly what this project generates.
"""

import os
import re
import shutil
import subprocess
import tempfile
from pathlib import Path


def find_alive2(possible_paths: list = None) -> str:
    """
    Find the alive2 binary.
    Prefers alive-tv (LLVM IR mode), falls back to alive (.opt mode).
    """
    # Check environment variable first
    env_path = os.environ.get("ALIVE2_PATH", "")
    if env_path and os.path.isfile(env_path):
        return env_path

    # Check common locations — prefer alive-tv
    default_paths = [
        os.path.expanduser("~/alive2/build/alive-tv"),
        "/usr/local/bin/alive-tv",
        "/usr/bin/alive-tv",
        os.path.expanduser("~/alive2/build/alive"),
    ]

    if possible_paths:
        default_paths = possible_paths + default_paths

    for path in default_paths:
        if os.path.isfile(path):
            return path

    return ""


def _is_alive_tv(binary_path: str) -> bool:
    """Check if the binary is alive-tv (LLVM IR mode) vs alive (.opt mode)."""
    return 'alive-tv' in os.path.basename(binary_path)


def _ir_to_opt(original_ir: str, rewrite_ir: str, name: str = "opt_check") -> str:
    """
    Convert two LLVM IR functions into Alive2 .opt format.
    
    The .opt format is:
      Name: <name>
      <source instructions>
        =>
      <target instructions>
    
    This handles simple peephole patterns (1-2 instructions + ret).
    """
    def extract_body_instrs(ir: str) -> list:
        """Extract instruction lines from a function body, excluding define/entry/ret/}."""
        lines = ir.strip().split('\n')
        instrs = []
        in_func = False
        for line in lines:
            stripped = line.strip()
            if stripped.startswith('define'):
                in_func = True
                continue
            if stripped == '}':
                in_func = False
                continue
            if not in_func:
                continue
            if stripped.endswith(':'):  # label
                continue
            if stripped.startswith(';'):
                continue
            if not stripped:
                continue
            instrs.append(stripped)
        return instrs

    def get_ret_value(instrs: list) -> str:
        """Find what value is returned."""
        for instr in instrs:
            m = re.match(r'ret\s+i\d+\s+(.+)', instr)
            if m:
                return m.group(1).strip()
        return ""

    def get_return_type(ir: str) -> str:
        """Extract return type from function signature."""
        m = re.search(r'define\s+(?:[\w\s]*?)(i\d+)\s+@', ir)
        if m:
            return m.group(1)
        return "i32"

    orig_instrs = extract_body_instrs(original_ir)
    rewrite_instrs = extract_body_instrs(rewrite_ir)
    ret_type = get_return_type(original_ir)

    # Build source (original)
    source_lines = []
    for instr in orig_instrs:
        if not instr.startswith('ret '):
            source_lines.append(instr)
    ret_val = get_ret_value(orig_instrs)

    # Build target (rewrite)
    target_lines = []
    for instr in rewrite_instrs:
        if not instr.startswith('ret '):
            target_lines.append(instr)
    ret_val_rewrite = get_ret_value(rewrite_instrs)

    # If source has a result assignment, use it as the final value
    # Otherwise, create one from the return value
    if source_lines:
        # The last assignment is the result
        last_source = source_lines[-1]
        m = re.match(r'(%\w+)\s*=', last_source)
        result_var = m.group(1) if m else ret_val
    else:
        result_var = ret_val

    opt_lines = [f"Name: {name}"]

    # Source
    for line in source_lines:
        opt_lines.append(line)
    if not source_lines and ret_val:
        opt_lines.append(f"%r = add {ret_type} {ret_val}, 0")  # identity as placeholder

    opt_lines.append("  =>")

    # Target
    if target_lines:
        for line in target_lines:
            # Rename %0, %1, etc to %tgt_0, %tgt_1 to avoid Alive2 name collisions
            line = re.sub(r'%(\d+)', r'%tgt_\1', line)
            opt_lines.append(line)
    else:
        # Direct return — the rewrite is just the return value
        if ret_val_rewrite and ret_val_rewrite.startswith('%'):
            # Rename in return value too
            ret_val_rewrite = re.sub(r'%(\d+)', r'%tgt_\1', ret_val_rewrite)
            # Returning an argument directly
            if source_lines:
                m = re.match(r'(%\w+)\s*=', source_lines[-1])
                if m:
                    opt_lines.append(f"{m.group(1)} = {ret_val_rewrite}")
        elif ret_val_rewrite:
            if source_lines:
                m = re.match(r'(%\w+)\s*=', source_lines[-1])
                if m:
                    opt_lines.append(f"{m.group(1)} = {ret_val_rewrite}")
        
        # If there are target lines, we still need to assign to the final source var
    if target_lines and ret_val_rewrite and source_lines:
        m = re.match(r'(%\w+)\s*=', source_lines[-1])
        if m:
            ret_val_rewrite = re.sub(r'%(\d+)', r'%tgt_\1', ret_val_rewrite)
            opt_lines.append(f"{m.group(1)} = {ret_val_rewrite}")

    opt_lines.append("")  # Trailing newline
    return '\n'.join(opt_lines)


def alive2_validate(original_ir: str, rewrite_ir: str,
                    alive_tv_path: str = None, timeout: int = 30) -> dict:
    """
    Formally validate that a rewrite is semantically equivalent using Alive2.

    Returns dict with:
    - status: FORMALLY_VALID | FORMALLY_INVALID | TIMEOUT | ALIVE2_NOT_FOUND | UNKNOWN
    - counterexample: parsed counterexample if FORMALLY_INVALID
    - raw_output: full stdout
    - reason: human readable
    """
    # Find alive2
    if alive_tv_path is None:
        alive_tv_path = find_alive2()

    if not alive_tv_path or not os.path.isfile(alive_tv_path):
        return {
            "status": "ALIVE2_NOT_FOUND",
            "counterexample": None,
            "raw_output": "",
            "reason": f"Alive2 not found at: {alive_tv_path or 'any default location'}"
        }

    is_tv = _is_alive_tv(alive_tv_path)
    temp_dir = tempfile.mkdtemp()

    try:
        if is_tv:
            # alive-tv mode: two separate .ll files
            orig_file = os.path.join(temp_dir, "original.ll")
            rewrite_file = os.path.join(temp_dir, "rewrite.ll")

            with open(orig_file, 'w') as f:
                f.write(original_ir)
            with open(rewrite_file, 'w') as f:
                f.write(rewrite_ir)

            cmd = [alive_tv_path, orig_file, rewrite_file]
        else:
            # alive mode: single .opt file with source => target
            opt_content = _ir_to_opt(original_ir, rewrite_ir)
            opt_file = os.path.join(temp_dir, "check.opt")

            with open(opt_file, 'w') as f:
                f.write(opt_content)

            cmd = [alive_tv_path, opt_file]

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout
            )
        except subprocess.TimeoutExpired:
            return {
                "status": "TIMEOUT",
                "counterexample": None,
                "raw_output": "",
                "reason": f"Alive2 timed out after {timeout}s"
            }

        stdout = result.stdout
        stderr = result.stderr
        combined = stdout + "\n" + stderr

        # Parse the output
        if "0 incorrect transformations" in combined or "seems to be correct" in combined:
            return {
                "status": "FORMALLY_VALID",
                "counterexample": None,
                "raw_output": combined,
                "reason": "Alive2 confirmed: 0 incorrect transformations"
            }
        elif "Counterexample" in combined or "counterexample" in combined.lower() or "ERROR: Value mismatch" in combined:
            # Extract counterexample block
            ce_lines = []
            in_ce = False
            for line in combined.split('\n'):
                if 'counterexample' in line.lower() or 'Example:' in line or 'ERROR:' in line:
                    in_ce = True
                if in_ce:
                    ce_lines.append(line)
                    if line.strip() == '' and len(ce_lines) > 4:
                        break

            counterexample = '\n'.join(ce_lines) if ce_lines else "Counterexample found (could not parse)"

            return {
                "status": "FORMALLY_INVALID",
                "counterexample": counterexample,
                "raw_output": combined,
                "reason": "Alive2 found a counterexample / value mismatch"
            }
        elif "incorrect transformation" in combined.lower():
            return {
                "status": "FORMALLY_INVALID",
                "counterexample": None,
                "raw_output": combined,
                "reason": "Alive2 reported incorrect transformation"
            }
        elif result.returncode == 0 and "correct transformation" in combined.lower():
            return {
                "status": "FORMALLY_VALID",
                "counterexample": None,
                "raw_output": combined,
                "reason": "Alive2 confirmed correct transformation"
            }
        else:
            return {
                "status": "UNKNOWN",
                "counterexample": None,
                "raw_output": combined,
                "reason": f"Could not parse Alive2 output (return code: {result.returncode})"
            }

    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


if __name__ == '__main__':
    print("=" * 60)
    print("Tier 3 Alive2 Validator — Tests")
    print("=" * 60)

    alive_path = find_alive2()
    if not alive_path:
        print("WARNING: Alive2 not found. Set ALIVE2_PATH environment variable.")
        print("  export ALIVE2_PATH=$HOME/alive2/build/alive")
        exit(0)

    print(f"Found Alive2 at: {alive_path}")
    print(f"Mode: {'alive-tv (LLVM IR)' if _is_alive_tv(alive_path) else 'alive (.opt format)'}\n")

    # Test 1: Valid transformation (xor 0 → identity)
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
    print("Test 1 (valid: xor 0 → identity):")
    result1 = alive2_validate(original1, rewrite1, alive_path)
    print(f"  Status: {result1['status']}")
    print(f"  Reason: {result1['reason']}")

    # Test 2: Invalid transformation (add 1 → identity is wrong)
    original2 = """define i32 @g(i32 %x) {
entry:
  %1 = add i32 %x, 1
  ret i32 %1
}
"""
    rewrite2 = """define i32 @g(i32 %x) {
entry:
  ret i32 %x
}
"""
    print("\nTest 2 (invalid: add 1 → identity is wrong):")
    result2 = alive2_validate(original2, rewrite2, alive_path)
    print(f"  Status: {result2['status']}")
    print(f"  Reason: {result2['reason']}")

    print("\nDone.")

#!/usr/bin/env python3
"""
Tier 2 Dynamic Testing Validator (Task 7)

Compiles both the original and rewrite IR to shared libraries,
runs test inputs through both, checks if outputs ever differ.
"""

import ctypes
import os
import random
import re
import shutil
import subprocess
import tempfile
from pathlib import Path


def compile_ir_to_executable(ir_code: str, func_name: str, temp_dir: str) -> str:
    """
    Compile LLVM IR to a shared library (.so).
    Returns the path to the .so file.
    Raises RuntimeError on failure.
    """
    ll_path = os.path.join(temp_dir, f"{func_name}.ll")
    obj_path = os.path.join(temp_dir, f"{func_name}.o")
    so_path = os.path.join(temp_dir, f"{func_name}.so")

    # Write IR to file
    with open(ll_path, 'w') as f:
        f.write(ir_code)

    # Compile to object file
    result = subprocess.run(
        ['llc', '-filetype=obj', '-relocation-model=pic', ll_path, '-o', obj_path],
        capture_output=True, text=True, timeout=30
    )
    if result.returncode != 0:
        raise RuntimeError(f"llc failed: {result.stderr[:200]}")

    # Compile to shared library
    result = subprocess.run(
        ['clang', obj_path, '-shared', '-fPIC', '-o', so_path],
        capture_output=True, text=True, timeout=30
    )
    if result.returncode != 0:
        raise RuntimeError(f"clang link failed: {result.stderr[:200]}")

    return so_path


def load_function(lib_path: str, func_name: str, argtypes: list, restype):
    """Load a function from a shared library using ctypes."""
    lib = ctypes.CDLL(lib_path)
    func = getattr(lib, func_name)
    func.argtypes = argtypes
    func.restype = restype
    return func


def generate_test_inputs(n: int, n_args: int, bit_width: int = 32) -> list:
    """Generate boundary values + random test inputs."""
    if bit_width == 32:
        boundaries = [0, 1, -1, 2, -2, 127, -128, 255, -256,
                       32767, -32768, 2147483647, -2147483648]
        min_val = -2147483648
        max_val = 2147483647
    else:  # 64-bit
        boundaries = [0, 1, -1, 2, -2, 127, -128, 255, -256,
                       32767, -32768, 2147483647, -2147483648,
                       2**63 - 1, -(2**63)]
        min_val = -(2**63)
        max_val = 2**63 - 1

    inputs = []

    # Add boundary values first
    if n_args == 1:
        for b in boundaries:
            inputs.append(b)
    else:
        for b in boundaries:
            inputs.append(tuple([b] * n_args))
        # Also add mixed boundary pairs
        for i in range(min(len(boundaries), 5)):
            for j in range(min(len(boundaries), 5)):
                if n_args == 2:
                    inputs.append((boundaries[i], boundaries[j]))

    # Fill remaining with random values
    remaining = n - len(inputs)
    if remaining > 0:
        for _ in range(remaining):
            if n_args == 1:
                inputs.append(random.randint(min_val, max_val))
            else:
                inputs.append(tuple(random.randint(min_val, max_val) for _ in range(n_args)))

    return inputs[:n]


def detect_arg_count(ir_code: str) -> tuple:
    """
    Parse the function signature to detect argument count and bit width.
    Returns (n_args, bit_width).
    """
    match = re.search(r'define\s+\w+\s+i(\d+)\s+@\w+\s*\(([^)]*)\)', ir_code)
    if not match:
        # Try with more flexible pattern
        match = re.search(r'define\s+(?:[\w\s]*?)i(\d+)\s+@\w+\s*\(([^)]*)\)', ir_code)
    if not match:
        return (1, 32)  # default

    bit_width = int(match.group(1))
    args_str = match.group(2).strip()

    if not args_str:
        return (0, bit_width)

    # Count arguments by counting type patterns
    arg_types = re.findall(r'i\d+', args_str)
    n_args = len(arg_types)

    return (n_args, bit_width)


def extract_func_name(ir_code: str) -> str:
    """Extract the function name from LLVM IR."""
    match = re.search(r'@(\w+)\s*\(', ir_code)
    if match:
        return match.group(1)
    return "unknown"


def tier2_validate(original_ir: str, rewrite_ir: str, n_trials: int = 10000) -> dict:
    """
    Dynamic testing of original vs rewrite IR functions.

    Returns dict with:
    - status: DYNAMIC_PASS | COUNTEREXAMPLE_FOUND | COMPILE_ERROR | LOAD_ERROR | RUNTIME_ERROR
    - counterexample, orig_output, rewrite_output, trials_run, reason
    """
    temp_dir = tempfile.mkdtemp()
    try:
        # Detect args and bit width
        n_args, bit_width = detect_arg_count(original_ir)
        func_name = extract_func_name(original_ir)

        # Choose ctypes type based on bit width
        if bit_width == 64:
            c_type = ctypes.c_int64
        else:
            c_type = ctypes.c_int32

        argtypes = [c_type] * n_args
        restype = c_type

        # Compile original
        try:
            orig_so = compile_ir_to_executable(original_ir, f"{func_name}_orig", temp_dir)
        except RuntimeError as e:
            return {
                "status": "COMPILE_ERROR",
                "counterexample": None,
                "orig_output": None,
                "rewrite_output": None,
                "trials_run": 0,
                "reason": f"Original compile error: {e}"
            }

        # Compile rewrite
        try:
            rewrite_so = compile_ir_to_executable(rewrite_ir, f"{func_name}_rewrite", temp_dir)
        except RuntimeError as e:
            return {
                "status": "COMPILE_ERROR",
                "counterexample": None,
                "orig_output": None,
                "rewrite_output": None,
                "trials_run": 0,
                "reason": f"Rewrite compile error: {e}"
            }

        # Load functions
        try:
            orig_func = load_function(orig_so, func_name, argtypes, restype)
            rewrite_func = load_function(rewrite_so, func_name, argtypes, restype)
        except Exception as e:
            return {
                "status": "LOAD_ERROR",
                "counterexample": None,
                "orig_output": None,
                "rewrite_output": None,
                "trials_run": 0,
                "reason": f"Function load error: {e}"
            }

        # Generate test inputs
        test_inputs = generate_test_inputs(n_trials, n_args, bit_width)

        # Run tests
        for i, inp in enumerate(test_inputs):
            try:
                if n_args == 1:
                    orig_out = orig_func(c_type(inp).value)
                    rewrite_out = rewrite_func(c_type(inp).value)
                elif n_args == 0:
                    orig_out = orig_func()
                    rewrite_out = rewrite_func()
                else:
                    args = [c_type(v).value for v in inp]
                    orig_out = orig_func(*args)
                    rewrite_out = rewrite_func(*args)

                if orig_out != rewrite_out:
                    return {
                        "status": "COUNTEREXAMPLE_FOUND",
                        "counterexample": str(inp),
                        "orig_output": str(orig_out),
                        "rewrite_output": str(rewrite_out),
                        "trials_run": i + 1,
                        "reason": f"Outputs differ for input {inp}: orig={orig_out}, rewrite={rewrite_out}"
                    }
            except Exception as e:
                return {
                    "status": "RUNTIME_ERROR",
                    "counterexample": str(inp),
                    "orig_output": None,
                    "rewrite_output": None,
                    "trials_run": i + 1,
                    "reason": f"Runtime error on input {inp}: {e}"
                }

        return {
            "status": "DYNAMIC_PASS",
            "counterexample": None,
            "orig_output": None,
            "rewrite_output": None,
            "trials_run": len(test_inputs),
            "reason": f"All {len(test_inputs)} test inputs produced matching outputs"
        }

    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


if __name__ == '__main__':
    print("=" * 60)
    print("Tier 2 Dynamic Testing Validator — Tests")
    print("=" * 60)

    # Test 1: Correct rewrite (add 0 → identity)
    original1 = """define i32 @f(i32 %x) {
entry:
  %1 = add i32 %x, 0
  ret i32 %1
}
"""
    rewrite1 = """define i32 @f(i32 %x) {
entry:
  ret i32 %x
}
"""
    print("\nTest 1 (correct rewrite — add 0 identity):")
    result1 = tier2_validate(original1, rewrite1, n_trials=1000)
    print(f"  Status: {result1['status']}")
    print(f"  Trials: {result1['trials_run']}")
    assert result1['status'] == 'DYNAMIC_PASS', f"Expected DYNAMIC_PASS, got {result1['status']}"

    # Test 2: Wrong rewrite (add 1 → identity is WRONG)
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
    print("\nTest 2 (wrong rewrite — add 1 ≠ identity):")
    result2 = tier2_validate(original2, rewrite2, n_trials=1000)
    print(f"  Status: {result2['status']}")
    if result2['counterexample']:
        print(f"  Counterexample: input={result2['counterexample']}, "
              f"orig={result2['orig_output']}, rewrite={result2['rewrite_output']}")
    assert result2['status'] == 'COUNTEREXAMPLE_FOUND', f"Expected COUNTEREXAMPLE_FOUND, got {result2['status']}"

    print("\nAll tests passed! ✓")

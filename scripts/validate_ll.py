#!/usr/bin/env python3
"""
Standalone Validation Script
Validates a pair of .ll files (original vs optimized) using Tier 1, 2, and 3 validation.
"""
import argparse
import sys
import os
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.validate.tier1_syntax import tier1_validate
from src.validate.tier2_dynamic import tier2_validate
from src.validate.tier3_alive2 import alive2_validate, find_alive2

def validate_pair(original_path, optimized_path):
    with open(original_path, 'r') as f:
        orig_ir = f.read()
    with open(optimized_path, 'r') as f:
        opt_ir = f.read()
        
    print(f"Validating:\n  Original:  {original_path}\n  Optimized: {optimized_path}\n")
    
    # Tier 1
    t1 = tier1_validate(orig_ir, opt_ir)
    print(f"[Tier 1] Syntax Check: {t1.status}")
    if t1.status != "SYNTACTIC_PASS":
        print(f"  Reason: {t1.reason}")
        return
        
    # Tier 2
    t2 = tier2_validate(orig_ir, opt_ir, n_trials=10000)
    print(f"[Tier 2] Dynamic Check: {t2['status']}")
    if t2["status"] != "DYNAMIC_PASS":
        print(f"  Reason: {t2['reason']}")
        return
        
    # Tier 3
    alive_path = find_alive2()
    if not alive_path:
        print("[Tier 3] Formal Verification: SKIPPED (Alive2 not found)")
        return
        
    t3 = alive2_validate(orig_ir, opt_ir, alive_path, timeout=90)
    print(f"[Tier 3] Formal Verification: {t3['status']}")
    if t3["status"] != "FORMALLY_VALID":
        print(f"  Reason: {t3['reason']}")
        
    print("\nOverall Result: VALID")

def main():
    parser = argparse.ArgumentParser(description="Validate LLVM IR Rewrite")
    parser.add_argument("original_ll", help="Path to original .ll file")
    parser.add_argument("optimized_ll", help="Path to optimized .ll file")
    args = parser.parse_args()
    
    if not os.path.exists(args.original_ll):
        print(f"Error: {args.original_ll} not found")
        sys.exit(1)
    if not os.path.exists(args.optimized_ll):
        print(f"Error: {args.optimized_ll} not found")
        sys.exit(1)
        
    validate_pair(args.original_ll, args.optimized_ll)

if __name__ == '__main__':
    main()

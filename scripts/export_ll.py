#!/usr/bin/env python3
"""
Export LLVM IR Rewrites to .ll files
"""
import sqlite3
import os
from pathlib import Path

def main():
    db_path = 'data/results.sqlite'
    out_dir = Path('data/rewrites')
    out_dir.mkdir(parents=True, exist_ok=True)
    
    if not os.path.exists(db_path):
        print(f"Database {db_path} not found.")
        return
        
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # We join patterns and results to get both original and optimized IR
    query = """
        SELECT p.id, p.family, p.input_ir, r.optimized_ir, r.final_class
        FROM patterns p
        JOIN results r ON p.id = r.pattern_id
    """
    
    exported = 0
    for row in cursor.execute(query):
        name_id, family, original_ir, optimized_ir, final_class = row
        name = f"pattern_{name_id}"
        
        # We export all patterns where the LLM attempted an optimization
        if optimized_ir and optimized_ir not in ('NO_OPT', 'PARSE_ERROR'):
            family_dir = out_dir / family
            family_dir.mkdir(exist_ok=True)
            
            orig_path = family_dir / f"{name}_original.ll"
            opt_path = family_dir / f"{name}_optimized.ll"
            
            with open(orig_path, 'w') as f:
                f.write(original_ir)
            with open(opt_path, 'w') as f:
                f.write(optimized_ir)
                
            exported += 1
            
    conn.close()
    print(f"Successfully exported {exported} pairs of .ll files to {out_dir}")

if __name__ == '__main__':
    main()

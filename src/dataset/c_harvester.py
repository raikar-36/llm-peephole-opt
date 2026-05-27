#!/usr/bin/env python3
"""
Enhanced C-to-IR Harvester (Task 2 — Extended)

Generates a much larger set of C functions covering complex patterns
that LLVM's opt -O2 is more likely to miss. Compiles them to LLVM IR
and extracts function bodies.

Design rationale: Simple identities (x+0, x^x) get optimized by clang -O1
already. This extended set focuses on:
- Multi-step algebraic chains
- Conditional patterns with select/phi
- Overflow-related edge cases
- Bit manipulation idioms
- Mixed-type operations
- Patterns requiring knowledge of value ranges
"""

import itertools
import os
import re
import shutil
import subprocess
import tempfile
from pathlib import Path

try:
    from tqdm import tqdm
except ImportError:
    def tqdm(iterable, **kwargs):
        total = kwargs.get('total', None)
        desc = kwargs.get('desc', '')
        for i, item in enumerate(iterable):
            if total:
                print(f"\r{desc} [{i+1}/{total}]", end='', flush=True)
            yield item
        print()

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DATA_DIR = PROJECT_ROOT / 'data' / 'patterns'


# ═══════════════════════════════════════════════════════════════════════
# EXTENDED C FUNCTION TEMPLATES
# ═══════════════════════════════════════════════════════════════════════
C_FUNCTIONS = []
_counter = [0]

def _add(name, cat, code):
    _counter[0] += 1
    C_FUNCTIONS.append((name, cat, code))

# ── ARITHMETIC: Multi-step chains ──────────────────────────────────────
_add("arith_add_zero", "arithmetic",
     "int f_a001(int x) { return x + 0; }")
_add("arith_mul_one", "arithmetic",
     "int f_a002(int x) { return x * 1; }")
_add("arith_sub_self", "arithmetic",
     "int f_a003(int x) { return x - x; }")
_add("arith_add_sub_5", "arithmetic",
     "int f_a004(int x) { int a = x + 5; int b = a - 5; return b; }")
_add("arith_mul_div_4", "arithmetic",
     "int f_a005(int x) { return x * 4 / 4; }")
_add("arith_add_sub_1", "arithmetic",
     "int f_a006(int x) { return (x + 1) - 1; }")
_add("arith_mul2_sub", "arithmetic",
     "int f_a007(int x) { return x * 2 - x; }")
_add("arith_add_sub_y", "arithmetic",
     "int f_a008(int x, int y) { return (x + y) - y; }")
_add("arith_neg_neg", "arithmetic",
     "int f_a009(int x) { return -(-x); }")
_add("arith_add_neg", "arithmetic",
     "int f_a010(int x, int y) { return x + (-y); }")
# More complex chains
_add("arith_chain_3op", "arithmetic",
     "int f_a011(int x) { return ((x + 3) * 2) - (x + 3); }")
_add("arith_mul_add_distrib", "arithmetic",
     "int f_a012(int x) { return x * 5 + x * 3; }")
_add("arith_sub_neg_add", "arithmetic",
     "int f_a013(int x, int y) { return x - (x - y); }")
_add("arith_double_negate", "arithmetic",
     "int f_a014(int x, int y) { return -(x - y) + x; }")
_add("arith_mul_pow2", "arithmetic",
     "int f_a015(int x) { return x * 16; }")
_add("arith_div_pow2_signed", "arithmetic",
     "int f_a016(int x) { return x / 8; }")
_add("arith_mod_pow2_unsigned", "arithmetic",
     "unsigned f_a017(unsigned x) { return x % 16; }")
_add("arith_mul_then_div_3", "arithmetic",
     "int f_a018(int x) { return (x * 3 + x) / 4; }")
_add("arith_strength_reduce_mul7", "arithmetic",
     "int f_a019(int x) { return x * 7; }")
_add("arith_strength_reduce_mul15", "arithmetic",
     "int f_a020(int x) { return x * 15; }")
_add("arith_assoc_add", "arithmetic",
     "int f_a021(int x, int y) { return (x + 1) + (y + 2); }")
_add("arith_commute_sub", "arithmetic",
     "int f_a022(int x, int y) { return (x - y) + y; }")
_add("arith_reassoc_mul", "arithmetic",
     "int f_a023(int x) { return (x * 3) * 5; }")
_add("arith_factor_common", "arithmetic",
     "int f_a024(int x, int y) { return x * y + x * 3; }")
_add("arith_square_diff", "arithmetic",
     "int f_a025(int x, int y) { return (x + y) * (x - y); }")
_add("arith_inc_dec_cancel", "arithmetic",
     "int f_a026(int x) { int a = x + 1; return a - 1; }")

# Larger constant mul patterns
for c in [3, 5, 6, 7, 9, 10, 12, 14, 15, 17, 24, 31, 33, 63, 127, 255]:
    _add(f"arith_mul_{c}", "arithmetic",
         f"int f_am{c:03d}(int x) {{ return x * {c}; }}")
for c in [3, 5, 6, 7, 9, 10, 12, 15]:
    _add(f"arith_mul_neg{c}", "arithmetic",
         f"int f_amn{c:03d}(int x) {{ return x * (-{c}); }}")

# ── BITWISE: Complex patterns ─────────────────────────────────────────
_add("bitwise_and_zero", "bitwise",
     "int f_b001(int x) { return x & 0; }")
_add("bitwise_or_zero", "bitwise",
     "int f_b002(int x) { return x | 0; }")
_add("bitwise_xor_self", "bitwise",
     "int f_b003(int x) { return x ^ x; }")
_add("bitwise_and_neg1", "bitwise",
     "int f_b004(int x) { return x & -1; }")
_add("bitwise_or_neg1", "bitwise",
     "int f_b005(int x) { return x | -1; }")
_add("bitwise_and_self", "bitwise",
     "int f_b006(int x) { return x & x; }")
_add("bitwise_merge_masks", "bitwise",
     "int f_b007(int x) { return (x & 15) | (x & 240); }")
_add("bitwise_double_not", "bitwise",
     "int f_b008(int x) { return ~~x; }")
_add("bitwise_or_self", "bitwise",
     "int f_b009(int x) { return x | x; }")
_add("bitwise_xor_zero", "bitwise",
     "int f_b010(int x) { return x ^ 0; }")
# Complex bit manipulation
_add("bitwise_demorgan_and", "bitwise",
     "int f_b011(int x, int y) { return ~(~x & ~y); }")
_add("bitwise_demorgan_or", "bitwise",
     "int f_b012(int x, int y) { return ~(~x | ~y); }")
_add("bitwise_xor_cancel", "bitwise",
     "int f_b013(int x, int y) { return (x ^ y) ^ y; }")
_add("bitwise_and_or_absorb", "bitwise",
     "int f_b014(int x, int y) { return x & (x | y); }")
_add("bitwise_or_and_absorb", "bitwise",
     "int f_b015(int x, int y) { return x | (x & y); }")
_add("bitwise_mask_and_shift", "bitwise",
     "unsigned f_b016(unsigned x) { return (x & 0xFF00) >> 8; }")
_add("bitwise_isolate_bit", "bitwise",
     "int f_b017(int x) { return (x >> 3) & 1; }")
_add("bitwise_clear_bit", "bitwise",
     "int f_b018(int x) { return x & ~(1 << 5); }")
_add("bitwise_set_bit", "bitwise",
     "int f_b019(int x) { return x | (1 << 5); }")
_add("bitwise_toggle_bit", "bitwise",
     "int f_b020(int x) { return x ^ (1 << 5); }")
_add("bitwise_popcount_hack", "bitwise",
     "int f_b021(int x) { return x & (x - 1); }")  # clears lowest set bit
_add("bitwise_isolate_lowest", "bitwise",
     "int f_b022(int x) { return x & (-x); }")  # isolate lowest set bit
_add("bitwise_mask_low_n", "bitwise",
     "unsigned f_b023(unsigned x, unsigned n) { return x & ((1u << n) - 1); }")
_add("bitwise_swap_nibbles", "bitwise",
     "unsigned char f_b024(unsigned char x) { return (x >> 4) | (x << 4); }")
_add("bitwise_byte_reverse_16", "bitwise",
     "unsigned short f_b025(unsigned short x) { return (x >> 8) | (x << 8); }")
_add("bitwise_sign_extend_8_32", "bitwise",
     "int f_b026(int x) { return (x << 24) >> 24; }")
_add("bitwise_sign_extend_16_32", "bitwise",
     "int f_b027(int x) { return (x << 16) >> 16; }")
_add("bitwise_triple_and", "bitwise",
     "int f_b028(int x) { return (x & 0xFF) & 0x0F; }")
_add("bitwise_triple_or", "bitwise",
     "int f_b029(int x, int y) { return (x | y) | x; }")
_add("bitwise_xor_and_dist", "bitwise",
     "int f_b030(int x, int y) { return (x ^ y) & x; }")

# Mask combinations
for m1, m2 in [(0xFF, 0x0F), (0xFFFF, 0xFF), (0xF0, 0x0F), (0xFF00, 0x00FF)]:
    _add(f"bitwise_and_chain_{m1:x}_{m2:x}", "bitwise",
         f"unsigned f_bm_{m1:x}_{m2:x}(unsigned x) {{ return (x & 0x{m1:X}) & 0x{m2:X}; }}")
    _add(f"bitwise_or_and_{m1:x}_{m2:x}", "bitwise",
         f"unsigned f_bo_{m1:x}_{m2:x}(unsigned x) {{ return (x | 0x{m1:X}) & 0x{m2:X}; }}")

# ── SHIFTS: Complex patterns ──────────────────────────────────────────
_add("shift_left_zero", "shifts",
     "int f_s001(int x) { return x << 0; }")
_add("shift_right_zero", "shifts",
     "int f_s002(int x) { return x >> 0; }")
_add("shift_left_right_clear", "shifts",
     "unsigned f_s003(unsigned x) { return (x << 4) >> 4; }")
_add("shift_right_left_clear_lsb", "shifts",
     "int f_s004(int x) { return (x >> 1) << 1; }")
_add("shift_mul8", "shifts",
     "int f_s005(int x) { return x * 8; }")
_add("shift_div4_unsigned", "shifts",
     "unsigned f_s006(unsigned x) { return x / 4; }")
_add("shift_mul4_unsigned", "shifts",
     "unsigned f_s007(unsigned x) { return x * 4; }")
_add("shift_left_right_2", "shifts",
     "unsigned f_s008(unsigned x) { return (x << 2) >> 2; }")
# Complex shift patterns
_add("shift_rotate_left_8", "shifts",
     "unsigned f_s009(unsigned x) { return (x << 8) | (x >> 24); }")
_add("shift_rotate_right_8", "shifts",
     "unsigned f_s010(unsigned x) { return (x >> 8) | (x << 24); }")
_add("shift_extract_byte1", "shifts",
     "unsigned f_s011(unsigned x) { return (x >> 8) & 0xFF; }")
_add("shift_extract_byte2", "shifts",
     "unsigned f_s012(unsigned x) { return (x >> 16) & 0xFF; }")
_add("shift_double_shift", "shifts",
     "unsigned f_s013(unsigned x) { return (x << 3) << 2; }")
_add("shift_combine_shifts", "shifts",
     "unsigned f_s014(unsigned x) { return (x >> 3) >> 2; }")
_add("shift_and_shift", "shifts",
     "unsigned f_s015(unsigned x) { return (x & 0xFF) << 8; }")
_add("shift_mul_add_shift", "shifts",
     "unsigned f_s016(unsigned x) { return (x << 2) + x; }")  # x*5
_add("shift_mul_sub_shift", "shifts",
     "unsigned f_s017(unsigned x) { return (x << 3) - x; }")  # x*7

# Variable shift amounts
for n in [1, 2, 3, 4, 5, 7, 8, 15, 16]:
    _add(f"shift_shl_lshr_{n}", "shifts",
         f"unsigned f_shl{n}(unsigned x) {{ return (x << {n}) >> {n}; }}")
    _add(f"shift_lshr_shl_{n}", "shifts",
         f"unsigned f_lshr{n}(unsigned x) {{ return (x >> {n}) << {n}; }}")

# ── COMPARISON: Complex patterns ──────────────────────────────────────
_add("cmp_eq_self", "comparison",
     "int f_c001(int x) { return x == x; }")
_add("cmp_ne_self", "comparison",
     "int f_c002(int x) { return x != x; }")
_add("cmp_gt_self", "comparison",
     "int f_c003(int x) { return x > x; }")
_add("cmp_lt_gt_equiv", "comparison",
     "int f_c004(int x, int y) { return (x < y) == (y > x); }")
_add("cmp_test_even", "comparison",
     "int f_c005(int x) { return (x & 1) == 0; }")
_add("cmp_redundant_ge", "comparison",
     "int f_c006(int x) { return x >= 0 && x >= 0; }")
_add("cmp_le_self", "comparison",
     "int f_c007(int x) { return x <= x; }")
_add("cmp_ne_zero_identity", "comparison",
     "int f_c008(int x) { return (x != 0) != 0; }")
# Complex comparison patterns
_add("cmp_abs_positive", "comparison",
     "int f_c009(int x) { return (x >= 0) ? x : -x; }")
_add("cmp_min", "comparison",
     "int f_c010(int x, int y) { return (x < y) ? x : y; }")
_add("cmp_max", "comparison",
     "int f_c011(int x, int y) { return (x > y) ? x : y; }")
_add("cmp_clamp", "comparison",
     "int f_c012(int x) { return (x < 0) ? 0 : (x > 255) ? 255 : x; }")
_add("cmp_signum", "comparison",
     "int f_c013(int x) { return (x > 0) - (x < 0); }")
_add("cmp_bool_and", "comparison",
     "int f_c014(int x, int y) { return (x > 0) & (y > 0); }")
_add("cmp_bool_or", "comparison",
     "int f_c015(int x, int y) { return (x > 0) | (y > 0); }")
_add("cmp_chain_lt_eq", "comparison",
     "int f_c016(int x, int y) { return (x < y) || (x == y); }")
_add("cmp_negate_cond", "comparison",
     "int f_c017(int x, int y) { return !(x < y) && !(x == y); }")
_add("cmp_unsigned_lt_zero", "comparison",
     "int f_c018(unsigned x) { return x < 0; }")
_add("cmp_unsigned_ge_zero", "comparison",
     "int f_c019(unsigned x) { return x >= 0; }")
_add("cmp_double_neg", "comparison",
     "int f_c020(int x) { return !(!x); }")

# ── CASTS: Type conversion patterns ───────────────────────────────────
_add("cast_int_char_round", "casts",
     "int f_t001(char x) { return (int)(char)x; }")
_add("cast_uint_uchar", "casts",
     "unsigned f_t002(unsigned char x) { return (unsigned)(unsigned char)x; }")
_add("cast_int_short", "casts",
     "int f_t003(int x) { return (int)(short)x; }")
_add("cast_longlong_int", "casts",
     "long long f_t004(int x) { return (long long)(int)x; }")
_add("cast_char_int_char", "casts",
     "char f_t005(char x) { char y = (char)(int)x; return y; }")
_add("cast_uint_round_trip", "casts",
     "unsigned f_t006(unsigned x) { return (unsigned)(unsigned short)(unsigned)x; }")
_add("cast_trunc_extend", "casts",
     "int f_t007(int x) { return (int)(unsigned char)x; }")
_add("cast_sext_zext", "casts",
     "unsigned f_t008(char x) { return (unsigned)(int)x; }")
_add("cast_narrow_widen", "casts",
     "long long f_t009(long long x) { return (long long)(int)x; }")
_add("cast_uint_to_float_back", "casts",
     "unsigned f_t010(unsigned x) { return (unsigned)(float)x; }")

# ── SELECT/PHI: Conditional patterns ──────────────────────────────────
_add("sel_redundant_true", "select_phi",
     "int f_sp001(int x, int y) { return x ? x : y; }")
_add("sel_always_true", "select_phi",
     "int f_sp002(int x) { return 1 ? x : 0; }")
_add("sel_always_false", "select_phi",
     "int f_sp003(int x) { return 0 ? 0 : x; }")
_add("sel_same_branch", "select_phi",
     "int f_sp004(int c, int x) { return c ? x : x; }")
_add("sel_not_cond", "select_phi",
     "int f_sp005(int c, int x, int y) { return c ? x : (!c ? y : x); }")
_add("sel_nested_cond", "select_phi",
     "int f_sp006(int x) { return (x > 0) ? ((x > 0) ? x : 0) : 0; }")
_add("sel_max_zero", "select_phi",
     "int f_sp007(int x) { return (x > 0) ? x : 0; }")
_add("sel_abs", "select_phi",
     "int f_sp008(int x) { return (x < 0) ? -x : x; }")
_add("sel_neg_abs", "select_phi",
     "int f_sp009(int x) { return (x > 0) ? -x : x; }")
_add("sel_bool_to_int", "select_phi",
     "int f_sp010(int x) { return x ? 1 : 0; }")
_add("sel_cond_and", "select_phi",
     "int f_sp011(int a, int b) { return a ? (b ? 1 : 0) : 0; }")
_add("sel_cond_or", "select_phi",
     "int f_sp012(int a, int b) { return a ? 1 : (b ? 1 : 0); }")

# ── OVERFLOW: Patterns with overflow considerations ────────────────────
_add("ovf_add_check", "overflow_flags",
     "int f_o001(int x) { return (x + 1) > x; }")
_add("ovf_sub_check", "overflow_flags",
     "int f_o002(int x) { return (x - 1) < x; }")
_add("ovf_unsigned_wrap", "overflow_flags",
     "unsigned f_o003(unsigned x) { return (x + 1) > x; }")
_add("ovf_mul_overflow_check", "overflow_flags",
     "int f_o004(int x) { return (x * 2) / 2; }")
_add("ovf_negate_min", "overflow_flags",
     "int f_o005(int x) { return (x == -2147483647 - 1) ? x : -x; }")
_add("ovf_add_sat_upper", "overflow_flags",
     "int f_o006(int x) { int r = x + 100; return (r < x) ? 2147483647 : r; }")
_add("ovf_abs_safe", "overflow_flags",
     "int f_o007(int x) { return (x < 0 && x != (-2147483647 - 1)) ? -x : x; }")
_add("ovf_unsigned_sub_sat", "overflow_flags",
     "unsigned f_o008(unsigned x, unsigned y) { return (x > y) ? x - y : 0; }")

# ── ADDITIONAL COMPLEX PATTERNS ────────────────────────────────────────
# Power of 2 checks
_add("complex_is_pow2", "bitwise",
     "int f_x001(unsigned x) { return (x != 0) && ((x & (x - 1)) == 0); }")
_add("complex_round_up_pow2", "bitwise",
     "unsigned f_x002(unsigned x) { return (x + 3) & ~3u; }")
_add("complex_align_16", "bitwise",
     "unsigned f_x003(unsigned x) { return (x + 15) & ~15u; }")
_add("complex_count_trailing", "bitwise",
     "unsigned f_x004(unsigned x) { return x & (-x); }")

# Multi-expression chains
_add("complex_triple_add", "arithmetic",
     "int f_x005(int x) { return (x + 1) + (x + 2) + (x + 3); }")
_add("complex_distribute", "arithmetic",
     "int f_x006(int x) { return x * 3 + x * 5; }")
_add("complex_polynomial", "arithmetic",
     "int f_x007(int x) { return x * x + 2 * x + 1; }")
_add("complex_reassociate", "arithmetic",
     "int f_x008(int a, int b, int c) { return (a + b) + c; }")

# Division patterns
for d in [3, 5, 6, 7, 9, 10, 11, 12, 13]:
    _add(f"arith_div_{d}_unsigned", "arithmetic",
         f"unsigned f_du{d:03d}(unsigned x) {{ return x / {d}; }}")
    _add(f"arith_mod_{d}_unsigned", "arithmetic",
         f"unsigned f_mu{d:03d}(unsigned x) {{ return x % {d}; }}")


# ═══════════════════════════════════════════════════════════════════════
# COMPILATION FUNCTIONS (same as original)
# ═══════════════════════════════════════════════════════════════════════

def compile_c_to_ir(c_code: str, func_name: str, temp_dir: str) -> str:
    """Compile C code to LLVM IR, return the IR text or empty string on failure."""
    c_file = Path(temp_dir) / f"{func_name}.c"
    ll_file = Path(temp_dir) / f"{func_name}.ll"
    c_file.write_text(c_code)

    result = subprocess.run(
        ['clang', '-O1', '-emit-llvm', '-S', '-o', str(ll_file), str(c_file)],
        capture_output=True, text=True, timeout=30
    )
    if result.returncode != 0:
        return ""
    if not ll_file.exists():
        return ""
    return ll_file.read_text()


def extract_function_body(ir_text: str, func_name: str) -> str:
    """Extract a single function definition from LLVM IR text."""
    lines = ir_text.split('\n')
    in_function = False
    func_lines = []
    brace_depth = 0

    for line in lines:
        if not in_function:
            if line.startswith('define') and func_name in line:
                in_function = True
                func_lines.append(line)
                brace_depth += line.count('{') - line.count('}')
        else:
            func_lines.append(line)
            brace_depth += line.count('{') - line.count('}')
            if brace_depth <= 0:
                break

    if not func_lines:
        return ""
    return '\n'.join(func_lines) + '\n'


def main():
    """Generate LLVM IR patterns by compiling C code."""
    print("=" * 60)
    print("Extended C-to-IR Harvester")
    print(f"Total C functions to compile: {len(C_FUNCTIONS)}")
    print("=" * 60)

    summary = {}
    generated = 0
    failed = 0

    for name, category, c_code in tqdm(C_FUNCTIONS, desc="Compiling", total=len(C_FUNCTIONS)):
        cat_dir = DATA_DIR / category
        cat_dir.mkdir(parents=True, exist_ok=True)

        match = re.search(r'\b(f_\w+)\s*\(', c_code)
        if not match:
            failed += 1
            continue
        c_func_name = match.group(1)

        temp_dir = tempfile.mkdtemp()
        try:
            ir_text = compile_c_to_ir(c_code, c_func_name, temp_dir)
            if not ir_text:
                failed += 1
                continue

            func_body = extract_function_body(ir_text, c_func_name)
            if not func_body:
                failed += 1
                continue

            output_file = cat_dir / f"{name}.ll"
            output_file.write_text(func_body)
            summary[category] = summary.get(category, 0) + 1
            generated += 1

        except subprocess.TimeoutExpired:
            failed += 1
        except Exception as e:
            failed += 1
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    total = generated + failed
    print(f"\n{'=' * 60}")
    print(f"Extended C-to-IR Harvester Summary")
    print(f"{'=' * 60}")
    print(f"  Total C functions: {total}")
    print(f"  Successfully compiled: {generated}")
    print(f"  Failed/skipped: {failed}")
    print(f"\n  By category:")
    for cat, cnt in sorted(summary.items()):
        print(f"    {cat:20s}: {cnt:4d}")
    print(f"\nOutput directory: {DATA_DIR}")
    return summary


if __name__ == '__main__':
    main()

# Implementation Details - LLM Peephole Optimization

This document covers the technical implementation details of each component, including LLVM toolchain usage, Alive2 integration, and the internal workings of the pipeline.

---

## Table of Contents

- [1. LLVM Toolchain Usage](#1-llvm-toolchain-usage)
- [2. Alive2 Integration](#2-alive2-integration)
- [3. Dataset Generation](#3-dataset-generation)
- [4. LLM Client](#4-llm-client)
- [5. Validation Pipeline](#5-validation-pipeline)
- [6. Classification System](#6-classification-system)
- [7. Database Schema](#7-database-schema)
- [8. Pipeline Orchestration](#8-pipeline-orchestration)
- [9. Analysis and Reporting](#9-analysis-and-reporting)

---

## 1. LLVM Toolchain Usage

This project uses four LLVM tools extensively:

### `clang` - C to LLVM IR compilation

```bash
clang -O1 -emit-llvm -S -o output.ll input.c
```

- **`-O1`**: Applies basic optimizations so the generated IR is realistic, but does not over-optimize so patterns remain for analysis.
- **`-emit-llvm`**: Output LLVM IR instead of machine code.
- **`-S`**: Text format (human-readable `.ll` files, not binary `.bc`).

Used in: `src/dataset/c_harvester.py`

### `opt` - LLVM IR optimizer

```bash
opt -O2 -S input.ll -o output.ll
```

- **`-O2`**: Full optimization pipeline (InstCombine, GVN, LICM, etc.).
- **`-S`**: Text output (critical - binary output cannot be compared textually).

Used in: `src/dataset/filter_preopt.py` - if `opt -O2` changes the IR, the pattern is already handled by LLVM and gets discarded.

### `llvm-as` - LLVM IR assembler

```bash
llvm-as input.ll -o output.bc
```

Used in: `src/validate/tier1_syntax.py` - validates that LLM-generated IR is syntactically correct. If `llvm-as` fails, the rewrite is classified as `HALLUCINATED` or `PARSE_ERROR`.

### `llc` - LLVM IR to machine code compiler

```bash
llc -filetype=obj -relocation-model=pic input.ll -o output.o
```

- **`-filetype=obj`**: Generate object file (not assembly).
- **`-relocation-model=pic`**: Position-independent code, required for shared libraries.

Used in: `src/validate/tier2_dynamic.py` - compiles both original and rewrite IR to shared libraries for dynamic testing.

### `clang` (linker) - Shared library creation

```bash
clang input.o -shared -fPIC -o output.so
```

Used in: `src/validate/tier2_dynamic.py` - links object files into `.so` shared libraries that Python can load via `ctypes`.

---

## 2. Alive2 Integration

### What is Alive2?

[Alive2](https://github.com/AliveToolkit/alive2) is a formal verification tool for LLVM IR transformations. Given a source function and a target function, it uses the Z3 SMT solver to either:
- **Prove** they are semantically equivalent (for all possible inputs)
- **Find a counterexample** - a concrete input where they differ

### Two operating modes

This project supports two Alive2 binaries:

#### Mode 1: `alive-tv` (Translation Validator)

The preferred mode. Takes two `.ll` files directly:

```bash
alive-tv original.ll rewrite.ll
```

**Output parsing:**
- `"0 incorrect transformations"` → `FORMALLY_VALID`
- `"Counterexample"` in output → `FORMALLY_INVALID`
- Timeout → `TIMEOUT`

#### Mode 2: `alive` (Native .opt format)

Fallback mode. Converts LLVM IR to Alive2's `.opt` format:

```
Name: opt_check
%1 = xor i32 %x, 0
  =>
%1 = %x
```

**Output parsing:**
- `"seems to be correct"` → `FORMALLY_VALID`
- `"Counterexample"` in output → `FORMALLY_INVALID`

---

## 3. Dataset Generation

### Combinatorial Generator (`src/dataset/generator.py`)

Generates every combination of:
- Operations: `add`, `sub`, `mul`, `and`, `or`, `xor`, `shl`, `lshr`, `ashr`
- Constants: 0, 1, -1, 2, -2, 255, -128, 128, 65535, -65536
- Bit Widths: 32, 64

### C-to-IR Harvester (`src/dataset/c_harvester.py`)

Harvests functions across categories like arithmetic, bitwise, shifts, comparison, select_phi, casts, and overflow_flags.

### Filter (`src/dataset/filter_preopt.py`)

Runs `opt -O2` on generated `.ll` files. If normalized original IR matches normalized optimized IR, the pattern is kept (missed by LLVM). 

---

## 4. LLM Client

### Prompt structure (`src/llm/client.py`)

- **System Prompt**: Rules about semantic equivalence, flags, JSON format.
- **Few-Shot Examples**: 4 examples including identity, identity+flags, no-opt, and real rewrite.
- **User Input**: "Now analyze this pattern:\n\n" + IR code.

### Execution

The client utilizes the Gemini API using `google-generativeai`. It uses a rotating pool of API keys if provided to handle rate limits.

---

## 5. Validation Pipeline

### Tier 1: Syntactic Validation (`src/validate/tier1_syntax.py`)

Checks for `NO_OPT`, uses `llvm-as` for parsing, matches signatures, and ensures instruction count is reduced (profitability).

### Tier 2: Dynamic Testing (`src/validate/tier2_dynamic.py`)

Compiles IR to shared libraries, generates 10,000 test inputs (boundary and random), and compares execution outputs.

### Tier 3: Formal Verification (`src/validate/tier3_alive2.py`)

Uses `alive-tv` or `alive` to formally verify equivalence using SMT solvers.

---

## 6. Classification System

### Labels (`src/analysis/classifier.py`)

| Label | Meaning | How determined |
|-------|---------|---------------|
| `VALID` | Correct rewrite, LLVM misses it | Tier 3 = FORMALLY_VALID |
| `INVALID` | Semantically wrong | Tier 2 found counterexample or Tier 3 = FORMALLY_INVALID |
| `HALLUCINATED` | Unparseable IR or wrong signature | Tier 1 fail or Tier 2 compile error |
| `CORRECT_REFUSAL` | LLM correctly said no optimization | LLM returned NO_OPT on a non-missed pattern |
| `MISSED_DETECTION` | LLM missed an optimization | LLM said NO_OPT on a missed pattern |
| `UNCERTAIN` | Passed Tier 2 but Tier 3 unavailable/timeout | Tier 2 pass, Tier 3 unknown |
| `FALSE_POSITIVE`| Found optimization on already optimized pattern | Reserved for control groups |

---

## 7. Database Schema

### `patterns` table

- `id`: TEXT PK
- `category`: TEXT
- `input_ir`: TEXT
- `source`: TEXT
- `is_missed`: INTEGER

### `results` table

- `result_id`: INTEGER PK
- `pattern_id`: TEXT FK
- `llm_model`: TEXT
- `raw_response_1`: TEXT
- `optimized_ir`: TEXT
- `confidence`: TEXT
- `tier1_status`, `tier2_status`, `tier3_status`: TEXT
- `final_class`: TEXT
- `instr_count_original`, `instr_count_rewrite`: INTEGER
- `instr_reduction_ratio`: REAL
- `timestamp`: DATETIME

---

## 8. Pipeline Orchestration

### Flow per pattern (`src/pipeline.py`)

1. Load dataset, skip existing if requested.
2. Query LLM via `client.py`.
3. Run Tier 1, Tier 2, and Tier 3 validation sequentially.
4. Classify based on validation results and `is_missed` flag.
5. Save to database.

---

## 9. Analysis and Reporting

- **Metrics**: Computes validity rate, novelty rate, hallucination rate, and instruction reduction (`src/analysis/metrics.py`).
- **Plots**: Generates bar charts and histograms using `matplotlib` and `seaborn` (`src/analysis/visualize.py`).
- **Failure Analysis**: Categorizes dynamic and syntactic failures into specific modes (`src/analysis/failure_analysis.py`).
- **Markdown Report**: Summarizes the entire experiment run into a comprehensive markdown document (`src/analysis/report.py`).

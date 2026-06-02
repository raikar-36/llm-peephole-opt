# Can LLMs Discover Missed Peephole Optimizations in LLVM IR?
## Research Report — Automated Analysis

*Generated from 200 experimental results*

---

### 1. Dataset Summary

| Category | Patterns |
|----------|----------|
| arithmetic | 58 |
| bitwise | 57 |
| casts | 15 |
| comparison | 20 |
| overflow_flags | 10 |
| select_phi | 15 |
| shifts | 25 |
| **Total** | **200** |

**Source Breakdown:**

- : 200 patterns

### 2. Overall Results

#### Missed Optimizations (is_missed = True)
| Metric | Count / Value |
|--------|---------------|
| Total Patterns | 150 |
| Accuracy (Valid) | 93.3% |
| HALLUCINATED | 7 |
| MISSED_DETECTION | 3 |
| VALID | 140 |

#### Control Group (is_missed = False)
| Metric | Count / Value |
|--------|---------------|
| Total Patterns | 50 |
| Accuracy (Correct Refusal) | 98.0% |
| CORRECT_REFUSAL | 49 |
| HALLUCINATED | 1 |

**Key Finding:** LLMs show strong capability in discovering valid peephole optimizations, with a validity rate of 93.3%.

### 3. Results by Category

| Category | Count | Validity Rate | Hallucination Rate |
|----------|-------|---------------|-------------------|
| arithmetic | 58 | 56.9% | 3.4% |
| bitwise | 57 | 49.1% | 5.3% |
| casts | 15 | 100.0% | 0.0% |
| comparison | 20 | 100.0% | 0.0% |
| overflow_flags | 10 | 50.0% | 30.0% |
| select_phi | 15 | 100.0% | 0.0% |
| shifts | 25 | 96.0% | 0.0% |

### 4. Confidence Calibration

| Confidence Level | Validity Rate |
|-----------------|---------------|
| HIGH | 72.0% |
| MEDIUM | 100.0% |
| LOW | 0.0% |

⚠️ **Calibration is poor:** confidence levels don't consistently predict validity.

### 5. Instruction Reduction Analysis

| Metric | Value |
|--------|-------|
| Mean reduction | 47.6% |
| Median reduction | 40.0% |
| Max reduction | 66.7% |
| Min reduction | 20.0% |

### 6. Failure Analysis

Total failures analyzed: 8

| Failure Mode | Count | Percentage |
|-------------|-------|------------|
| Unparseable LLVM IR | 8 | 100.0% |

**Top failure mode:** Unparseable LLVM IR (8 cases, 100.0%)

### 7. Conclusions

LLMs show significant promise as tools for discovering missed peephole optimizations in LLVM IR. With a validity rate of 93.3%, they can find new optimization patterns. The hallucination rate was 4.0%, meaning the model successfully produced syntactically valid IR in the vast majority of cases, though semantic correctness varied. 0.0% of patterns exceeded Alive2's verification timeout, representing cases where SMT-based equivalence checking was too complex. The dominant failure mode — Unparseable LLVM IR — suggests targeted improvements to the prompting strategy could further improve results.

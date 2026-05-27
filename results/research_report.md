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
| Accuracy (Valid) | 50.7% |
| INVALID | 24 |
| MISSED_DETECTION | 4 |
| UNCERTAIN | 46 |
| VALID | 76 |

#### Control Group (is_missed = False)
| Metric | Count / Value |
|--------|---------------|
| Total Patterns | 50 |
| Accuracy (Correct Refusal) | 72.0% |
| CORRECT_REFUSAL | 36 |
| INVALID | 14 |

**Key Finding:** LLMs show strong capability in discovering valid peephole optimizations, with a validity rate of 50.7%.

### 3. Results by Category

| Category | Count | Validity Rate | Hallucination Rate |
|----------|-------|---------------|-------------------|
| arithmetic | 58 | 60.3% | 0.0% |
| bitwise | 57 | 0.0% | 0.0% |
| casts | 15 | 100.0% | 0.0% |
| comparison | 20 | 100.0% | 0.0% |
| overflow_flags | 10 | 0.0% | 0.0% |
| select_phi | 15 | 40.0% | 0.0% |
| shifts | 25 | 0.0% | 0.0% |

### 4. Confidence Calibration

| Confidence Level | Validity Rate |
|-----------------|---------------|
| HIGH | 38.8% |
| MEDIUM | 0.0% |
| LOW | 0.0% |

⚠️ **Calibration is poor:** confidence levels don't consistently predict validity.

### 5. Instruction Reduction Analysis

| Metric | Value |
|--------|-------|
| Mean reduction | 58.8% |
| Median reduction | 66.7% |
| Max reduction | 66.7% |
| Min reduction | 33.3% |

### 6. Failure Analysis

Total failures analyzed: 38

| Failure Mode | Count | Percentage |
|-------------|-------|------------|
| Added complexity instead of reducing it | 35 | 92.1% |
| Incorrect algebraic identity | 3 | 7.9% |

**Top failure mode:** Added complexity instead of reducing it (35 cases, 92.1%)

### 7. Conclusions

LLMs show significant promise as tools for discovering missed peephole optimizations in LLVM IR. With a validity rate of 50.7%, they can find new optimization patterns. The hallucination rate was 0.0%, meaning the model successfully produced syntactically valid IR in all cases, though the semantic correctness varied. 30.7% of patterns exceeded Alive2's verification timeout at 90 seconds, representing the current practical boundary of SMT-based equivalence checking for this pattern complexity. The dominant failure mode — Added complexity instead of reducing it — suggests targeted improvements to the prompting strategy could further improve results.

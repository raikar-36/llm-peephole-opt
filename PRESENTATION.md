# Can LLMs Discover Missed Peephole Optimizations in LLVM IR?
**Assignment 14 — Final Presentation**

---

## 1. The Core Problem
Peephole optimization involves replacing short instruction sequences with more efficient, mathematically equivalent ones.
- **The Challenge:** LLVM's `opt` pass has thousands of hand-coded patterns, but it cannot anticipate every inefficient sequence.
- **The Question:** Can an LLM accurately discover these missed optimizations, or will it hallucinate invalid compiler transformations?
- **The Solution:** A 3-Tier validation pipeline integrating LLMs with the `Alive2` formal SMT solver.

---

## 2. Dataset & Architecture
We generated a strict dataset of **200 LLVM IR patterns**:
- **150 Missed Optimizations** (Patterns LLVM natively fails to optimize)
- **50 Control Group Patterns** (Mathematically optimal patterns)

### The 3-Tier Pipeline
1. **Tier 1 (Syntactic):** `llvm-as` parsing and instruction count validation.
2. **Tier 2 (Dynamic):** Shared library fuzzing with 10,000 randomized bounded inputs.
3. **Tier 3 (Formal):** `Alive2` translation validation using Z3 solvers to formally prove equivalence.

---

## 3. Multi-Model Performance Comparison

We evaluated three state-of-the-art models. `GPT-OSS-120b` significantly outperformed the rest.

![Model Accuracy Comparison](./model_comparison/accuracy_comparison.png)

- **GPT-OSS-120b:** 93.3% accuracy on missed targets, 98% correct refusal rate.
- **Gemini 3.1 Flash-Lite:** 81.3% accuracy, struggled with LLVM IR syntax (19% parse failure).
- **Llama 3.3 70b:** 67.3% accuracy, highest semantic hallucination rate (3%).

---

## 4. Understanding the Failures

A major success of the framework is that **0 semantic hallucinations reached the compiler** for our top model.

![Error Breakdown](./model_comparison/error_breakdown.png)

The failures for highly capable LLMs were almost entirely Syntactic (Tier 1). The LLM would figure out the correct algebraic simplification but fail to format the output as strict LLVM IR (often injecting pseudo-code). Weaker models (like Llama) suffered from Semantic errors (Tier 2/3), silently generating mathematically incorrect simplifications.

---

## 5. Profitability: Are the Rewrites Useful?

The rewrites were highly profitable and significantly reduced IR bloat.

![Instruction Reduction](./results/plot4_instruction_reduction.png)

- **Mean Reduction:** 47.6% instruction removal.
- **Max Reduction:** Up to 66.7% instructions eliminated in a single pass.
- Example: Complex `xor` and `add` chains successfully constant-folded into simple `ret` instructions.

---

## 6. Lessons Learned & Conclusion

**Can LLMs discover missed optimizations? Yes!**

1. **Formal Verification is Mandatory:** LLMs *will* occasionally hallucinate semantic bugs. An SMT solver like `Alive2` is non-negotiable for integrating LLMs into compiler infrastructure.
2. **Prompt Engineering is Key:** Strictly enforcing output formats via JSON and few-shot examples drastically reduced syntax-related parsing failures.
3. **LLMs as Heuristic Search Engines:** Rather than treating the LLM as a direct compiler pass, treating it as an "Optimization Hypothesis Generator" (with the SMT solver acting as the judge) creates a safe, powerful, and novel compiler workflow.

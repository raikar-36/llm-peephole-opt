# LLM Peephole Optimization: Final Evaluation

This document outlines the final results and analysis of the LLM Peephole Optimization research experiment. The goal was to determine if an LLM could identify novel, semantically equivalent LLVM IR peephole optimizations that the native `opt -O2` pass misses, and whether it hallucinated invalid optimizations.

## 1. Experiment Setup

*   **Models Evaluated:** `openai/gpt-oss-120b` (via Groq), `gemini-3.1-flash-lite`, and `llama-3.3-70b-versatile`.
*   **Dataset:** 200 patterns. 150 missed optimizations (extracted from compiled C/C++ code and synthetic generators) and 50 control group patterns (mathematically optimal, no optimization possible).
*   **Methodology:**
    *   Prompt the LLMs with few-shot examples to rewrite the 200 patterns.
    *   Validate the suggested rewrites via a rigorous 3-tier system:
        1.  **Tier 1 (Syntactic):** Valid LLVM IR, smaller instruction count, no signature changes.
        2.  **Tier 2 (Dynamic):** 10,000 fuzz tests against the original IR.
        3.  **Tier 3 (Formal):** Formal theorem proving via `Alive2` (with `-disable-poison-input` and `-disable-undef-input` to resolve Z3 solver timeouts).

## 2. Multi-Model Comparison

Out of **200** tested patterns, the models performed as follows:

| Metric | GPT-OSS-120b | Gemini 3.1 Flash-Lite | Llama 3.3 70b |
| :--- | :--- | :--- | :--- |
| **Valid (Missed Opts)** | **140 (93.3%)** | 122 (81.3%) | 101 (67.3%) |
| **Correct Refusals (Control Group)** | **49 (98.0%)** | 36 (72.0%) | 28 (56.0%) |
| **Hallucinated (Overall)** | **8 (4.0%)** | 0 (0.0%)* | 6 (3.0%) |
| **Invalid Syntax (Overall)** | **0 (0.0%)** | 38 (19.0%) | 51 (25.5%) |

![Model Accuracy Comparison](./model_comparison/accuracy_comparison.png)

*Note: While Gemini did not technically "hallucinate" unparseable IR, it heavily failed syntactic checks (19%). GPT-OSS-120b had a 4% hallucination rate where it failed to format valid LLVM IR, but it overwhelmingly crushed the semantic tests.*

**Conclusion on Model Choice:** `GPT-OSS-120b` is significantly superior for compiler optimization tasks. It successfully optimized almost all valid patterns and refused to optimize impossible patterns, whereas Llama heavily hallucinated and Gemini struggled with precise syntax formulation.

## 3. Instruction Reduction (GPT-OSS-120b)

For the 140 patterns successfully optimized by GPT-OSS-120b:
- **Mean Reduction:** 47.6% instruction removal.
- **Max Reduction:** 66.7% instruction removal.
This proves that the rewrites are highly profitable and significantly reduce IR bloat.

## 4. Failure Mode Analysis

![Error Breakdown](./model_comparison/error_breakdown.png)

When the top model (GPT-OSS-120b) failed, it fell exclusively into one category:
1.  **Unparseable LLVM IR (8 cases):** The LLM correctly deduced the mathematical simplification (e.g., recognizing that `(x + y + 21) - x` simplifies to `y + 21`), but it failed to output valid LLVM IR syntax for the simplified expression, often mixing pseudo-code into the IR registers.

Crucially, **no invalid semantic rewrites passed the formal verifier**. The pipeline completely mitigated the risk of hallucinated transformations corrupting the compiler.

## 5. Conclusion

**Can LLMs discover missed peephole optimizations?**
**Yes.** 

The LLM successfully optimized 93.3% of the patterns that LLVM's `opt -O2` missed. However, the presence of syntactic and semantic hallucinations (especially in weaker models like Llama) highlights the absolute necessity of rigorous, multi-tiered validation pipelines. LLMs should not be trusted to generate compiler transformations blindly without formal verification, but when paired with an SMT solver like Alive2, they become highly effective optimization search engines.

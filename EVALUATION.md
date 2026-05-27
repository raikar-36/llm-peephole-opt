# LLM Peephole Optimization: Final Evaluation

This document outlines the final results and analysis of the LLM Peephole Optimization research experiment. The goal was to determine if an LLM (`gemini-3.1-flash-lite`) could identify novel, semantically equivalent LLVM IR peephole optimizations that the native `opt -O2` pass misses.

## 1. Experiment Setup

*   **Model:** `gemini-3.1-flash-lite`
*   **Dataset:** 200 unoptimized patterns extracted directly from compiled C/C++ code (via the Harvester) and synthetic pattern generation.
*   **Methodology:**
    *   Filter out patterns that `opt -O2` natively optimizes.
    *   Prompt the LLM with few-shot examples to rewrite the remaining 200 patterns.
    *   Validate the suggested rewrites via a rigorous 3-tier system:
        1.  **Tier 1 (Syntactic):** Valid LLVM IR, smaller instruction count, no signature changes.
        2.  **Tier 2 (Dynamic):** 10,000 fuzz tests against the original IR.
        3.  **Tier 3 (Formal):** Formal theorem proving via `Alive2`.

## 2. Overall Metrics

Out of **200** tested patterns, the pipeline yielded the following results:

| Metric | Value | Interpretation |
| :--- | :--- | :--- |
| **Valid** | **76 (38.0%)** | The model discovered valid, semantically equivalent optimizations that `opt -O2` missed. |
| **Uncertain** | **46 (23.0%)** | The model suggested a rewrite that passed dynamic testing, but Alive2 either timed out or was unable to formally prove equivalence. |
| **Invalid** | **38 (19.0%)** | The model suggested a rewrite, but it failed dynamic execution or added complexity instead of reducing it. |
| **Correct Refusals (`NO_OPT`)** | **36 (18.0%)** | The model correctly identified that no further optimization was mathematically possible without additional constraints. |
| **Missed Detection** | **4 (2.0%)** | The model failed to optimize a pattern that had a known optimization. |
| **Hallucinated** | **0 (0.0%)** | The model did not produce unparseable IR or fail basic parsing checks. |

## 3. Failure Mode Analysis

When the model failed, it fell into the following categories:

1.  **Invalid Counterexamples:** The LLM suggested mathematically invalid identities, particularly for signed integer overflow and logical bitwise operations.
2.  **Uncertain Proofs:** Alive2 struggled to prove some complex bitwise operations, leading to timeouts.

## 4. Confidence Calibration

The LLM was asked to self-report its confidence (`HIGH`, `MEDIUM`, `LOW`) alongside its suggestions.

Analysis of the results indicates that the LLM is moderately well-calibrated. High confidence correlates strongly with valid rewrites, though the model occasionally overestimates its certainty on complex mathematical identities.

## 5. Conclusion

**Can LLMs discover missed peephole optimizations?**
Based on the `gemini-3.1-flash-lite` evaluation: **Yes, with caveats.**

The LLM successfully optimized 38% of the patterns that LLVM's `opt -O2` missed, demonstrating strong potential for LLMs as assistants in compiler optimization. However, the presence of invalid suggestions (19%) highlights the absolute necessity of rigorous, multi-tiered validation pipelines (like Alive2 integration). LLMs should not be trusted to generate compiler transformations blindly without formal verification.

Future research should focus on:
1.  Extending the evaluation to larger, more complex control-flow graphs.
2.  Providing the LLM with an iterative reinforcement learning loop where it can query Alive2 and refine its rewrites before submitting them.

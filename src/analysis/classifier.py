#!/usr/bin/env python3
"""
Result Classifier (Task 9)

Takes all validation tier results and assigns a final classification
to each LLM-suggested rewrite, aware of whether the pattern was a
genuinely missed optimization (is_missed).
"""

# ── Classification Labels ──────────────────────────────────────────────
VALID            = "VALID"
FALSE_POSITIVE   = "FALSE_POSITIVE"
INVALID          = "INVALID"
HALLUCINATED     = "HALLUCINATED"
MISSED_DETECTION = "MISSED_DETECTION"
CORRECT_REFUSAL  = "CORRECT_REFUSAL"
UNCERTAIN        = "UNCERTAIN"

ALL_CLASSES = [
    VALID, FALSE_POSITIVE,
    INVALID, HALLUCINATED,
    MISSED_DETECTION, CORRECT_REFUSAL,
    UNCERTAIN
]


def detect_flag_issues(original_ir: str, rewrite_ir: str) -> bool:
    """
    Check if flags (nsw, nuw, exact) were dropped from the rewrite.
    Returns True if flags were dropped (potential issue).
    """
    flags = ['nsw', 'nuw', 'exact']
    for flag in flags:
        if flag in original_ir and flag not in rewrite_ir:
            return True
    return False


def classify(pattern_id: str, original_ir: str, rewrite_ir: str,
             tier1_status: str, tier2_status: str, tier3_status: str,
             llm_said_no_opt: bool, is_missed: bool) -> str:
    """
    Classify the result into a specific bucket based on tier statuses and is_missed.
    """
    if llm_said_no_opt or tier1_status == 'NO_OPT_CLAIMED':
        return "MISSED_DETECTION" if is_missed else "CORRECT_REFUSAL"

    if tier1_status in ('PARSE_ERROR', 'SIGNATURE_MISMATCH'):
        return "HALLUCINATED"

    if tier1_status == 'NOT_PROFITABLE':
        return "INVALID"
        
    if tier2_status == 'COMPILE_ERROR':
        return "HALLUCINATED"

    if tier2_status in ('COUNTEREXAMPLE_FOUND', 'RUNTIME_ERROR', 'LOAD_ERROR'):
        return "INVALID"

    if tier3_status == 'ALIVE2_VALID' or tier3_status == 'FORMALLY_VALID':
        return "VALID" if is_missed else "FALSE_POSITIVE"

    if tier3_status == 'ALIVE2_INVALID' or tier3_status == 'FORMALLY_INVALID':
        return "INVALID"

    if tier3_status == 'ALIVE2_TIMEOUT' or tier3_status == 'TIMEOUT':
        return "UNCERTAIN"

    # If it passed dynamic but we didn't run alive2 or alive2 gave an unknown error
    if tier2_status == 'DYNAMIC_PASS':
        return "UNCERTAIN"

    return "UNCERTAIN"


def classify_batch(results: list) -> list:
    """Apply classify() to each result in the list."""
    for r in results:
        r['final_class'] = classify(
            pattern_id=r.get('pattern_id', ''),
            original_ir=r.get('input_ir', ''),
            rewrite_ir=r.get('optimized_ir', ''),
            tier1_status=r.get('tier1_status', ''),
            tier2_status=r.get('tier2_status', ''),
            tier3_status=r.get('tier3_status', ''),
            llm_said_no_opt=bool(r.get('llm_said_no_opt', False)),
            is_missed=bool(r.get('is_missed', False))
        )
    return results


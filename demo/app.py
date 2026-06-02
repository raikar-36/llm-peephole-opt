#!/usr/bin/env python3
"""
Demo Server

FastAPI server for the interactive LLVM IR Peephole Optimization demo.
The API key is provided by the user through the frontend.
"""

import json
import logging
import os
import sqlite3
import sys
from pathlib import Path

# Add project root to path so we can import src modules
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel


app = FastAPI(title="LLM Peephole Optimization Demo")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve static files
STATIC_DIR = Path(__file__).parent / "static"
STATIC_DIR.mkdir(exist_ok=True)


# -- Request / Response Models ------------------------------------------

class OptimizeRequest(BaseModel):
    ir_code: str
    api_key: str


class OptimizeResponse(BaseModel):
    classification: str
    confidence: str
    reason: str
    optimized_ir: str
    tier1_status: str
    tier1_reason: str
    tier2_status: str
    tier2_reason: str
    tier3_status: str
    tier3_reason: str
    instr_original: int
    instr_rewrite: int
    reduction_ratio: float


# -- Routes -------------------------------------------------------------

@app.get("/")
def serve_index():
    """Serve the single-page frontend."""
    index_path = STATIC_DIR / "index.html"
    if not index_path.exists():
        raise HTTPException(status_code=404, detail="index.html not found")
    return FileResponse(index_path, media_type="text/html")


@app.get("/favicon.ico", include_in_schema=False)
def favicon():
    from fastapi.responses import Response
    # Return an empty 204 No Content for the favicon
    return Response(status_code=204)



@app.get("/examples")
def get_examples():
    """Return preloaded example patterns."""
    examples_path = Path(__file__).parent / "examples.json"
    if not examples_path.exists():
        return []
    with open(examples_path) as f:
        return json.load(f)


@app.get("/stats")
def get_stats():
    """Return aggregate experiment stats from the results database."""
    db_path = PROJECT_ROOT / "data" / "results.sqlite"
    if not db_path.exists():
        return {"error": "No results database found. Run the pipeline first."}

    conn = sqlite3.connect(str(db_path))
    try:
        total = conn.execute("SELECT COUNT(*) FROM results").fetchone()[0]
        classes = dict(conn.execute(
            "SELECT final_class, COUNT(*) FROM results GROUP BY final_class"
        ).fetchall())

        # Per-category breakdown (only missed patterns)
        cat_rows = conn.execute("""
            SELECT p.family,
                   COUNT(*) as total,
                   SUM(CASE WHEN r.final_class = 'VALID' THEN 1 ELSE 0 END) as valid
            FROM results r
            JOIN patterns p ON r.pattern_id = p.id
            WHERE p.is_missed = 1
            GROUP BY p.family
            ORDER BY p.family
        """).fetchall()
        categories = [
            {"family": row[0], "total": row[1], "valid": row[2],
             "validity_rate": round(row[2] / row[1] * 100, 1) if row[1] > 0 else 0}
            for row in cat_rows
        ]

        # Instruction reduction for valid
        reduction = conn.execute("""
            SELECT AVG(instr_reduction_ratio), MIN(instr_reduction_ratio),
                   MAX(instr_reduction_ratio), COUNT(*)
            FROM results WHERE final_class = 'VALID' AND instr_reduction_ratio IS NOT NULL
        """).fetchone()

        valid_count = classes.get('VALID', 0)
        refusals = classes.get('CORRECT_REFUSAL', 0) + classes.get('MISSED_DETECTION', 0)
        non_refusal = total - refusals

        return {
            "total": total,
            "classifications": classes,
            "validity_rate": round(valid_count / non_refusal * 100, 1) if non_refusal > 0 else 0,
            "categories": categories,
            "instruction_reduction": {
                "mean": round(reduction[0] * 100, 1) if reduction[0] else 0,
                "min": round(reduction[1] * 100, 1) if reduction[1] else 0,
                "max": round(reduction[2] * 100, 1) if reduction[2] else 0,
                "count": reduction[3] if reduction[3] else 0,
            }
        }
    finally:
        conn.close()


@app.post("/optimize", response_model=OptimizeResponse)
def optimize(req: OptimizeRequest):
    """Run the full optimization pipeline on submitted IR."""
    if not req.api_key or not req.api_key.strip():
        raise HTTPException(status_code=400, detail="API key is required")

    if not req.ir_code or not req.ir_code.strip():
        raise HTTPException(status_code=400, detail="IR code is required")

    ir_code = req.ir_code.strip()
    api_key = req.api_key.strip()

    logger = logging.getLogger("demo")

    # Step 1: Query LLM
    try:
        from src.llm.client import GroqClient
        client = GroqClient(api_key=api_key, model="openai/gpt-oss-120b")
        llm_result = client.query_single(ir_code)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"LLM query failed: {str(e)[:200]}")

    optimized_ir = llm_result.get("optimized_ir", "")
    confidence = llm_result.get("confidence", "LOW")
    reason = llm_result.get("reason", "")

    # Check for NO_OPT or parse error
    if optimized_ir in ("NO_OPT", "PARSE_ERROR"):
        return OptimizeResponse(
            classification="NO_OPT" if optimized_ir == "NO_OPT" else "PARSE_ERROR",
            confidence=confidence,
            reason=reason,
            optimized_ir=optimized_ir,
            tier1_status="SKIPPED",
            tier1_reason="LLM returned " + optimized_ir,
            tier2_status="SKIPPED",
            tier2_reason="",
            tier3_status="SKIPPED",
            tier3_reason="",
            instr_original=0,
            instr_rewrite=0,
            reduction_ratio=0,
        )

    # Step 2: Tier 1 validation
    from src.validate.tier1_syntax import tier1_validate, count_instructions
    t1 = tier1_validate(ir_code, optimized_ir)

    orig_count = count_instructions(ir_code)
    rewrite_count = count_instructions(optimized_ir)
    reduction = 1 - (rewrite_count / orig_count) if orig_count > 0 else 0

    if t1.status != "SYNTACTIC_PASS":
        return OptimizeResponse(
            classification="HALLUCINATED" if t1.status in ("PARSE_ERROR", "SIGNATURE_MISMATCH") else "INVALID",
            confidence=confidence,
            reason=reason,
            optimized_ir=optimized_ir,
            tier1_status=t1.status,
            tier1_reason=t1.reason,
            tier2_status="SKIPPED",
            tier2_reason="Tier 1 failed",
            tier3_status="SKIPPED",
            tier3_reason="Tier 1 failed",
            instr_original=orig_count,
            instr_rewrite=rewrite_count,
            reduction_ratio=round(reduction, 3),
        )

    # Step 3: Tier 2 validation
    from src.validate.tier2_dynamic import tier2_validate
    t2 = tier2_validate(ir_code, optimized_ir, n_trials=10000)

    if t2["status"] != "DYNAMIC_PASS":
        cls = "HALLUCINATED" if t2["status"] == "COMPILE_ERROR" else "INVALID"
        return OptimizeResponse(
            classification=cls,
            confidence=confidence,
            reason=reason,
            optimized_ir=optimized_ir,
            tier1_status=t1.status,
            tier1_reason=t1.reason,
            tier2_status=t2["status"],
            tier2_reason=t2["reason"],
            tier3_status="SKIPPED",
            tier3_reason="Tier 2 failed",
            instr_original=orig_count,
            instr_rewrite=rewrite_count,
            reduction_ratio=round(reduction, 3),
        )

    # Step 4: Tier 3 validation (if available)
    from src.validate.tier3_alive2 import alive2_validate, find_alive2
    alive_path = find_alive2()
    if alive_path:
        t3 = alive2_validate(ir_code, optimized_ir, alive_path, timeout=90)
        t3_status = t3["status"]
        t3_reason = t3["reason"]

        if t3_status == "FORMALLY_VALID":
            classification = "VALID"
        elif t3_status == "FORMALLY_INVALID":
            classification = "INVALID"
        else:
            classification = "UNCERTAIN"
    else:
        t3_status = "ALIVE2_NOT_FOUND"
        t3_reason = "Alive2 not installed; result is UNCERTAIN"
        classification = "UNCERTAIN"

    return OptimizeResponse(
        classification=classification,
        confidence=confidence,
        reason=reason,
        optimized_ir=optimized_ir,
        tier1_status=t1.status,
        tier1_reason=t1.reason,
        tier2_status=t2["status"],
        tier2_reason=t2["reason"],
        tier3_status=t3_status,
        tier3_reason=t3_reason,
        instr_original=orig_count,
        instr_rewrite=rewrite_count,
        reduction_ratio=round(reduction, 3),
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

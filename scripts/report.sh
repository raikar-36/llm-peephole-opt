#!/usr/bin/env bash
# ═══════════════════════════════════════════════════════════════
# report.sh — Generate all analysis outputs
# ═══════════════════════════════════════════════════════════════
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$PROJECT_DIR"

# Activate venv if present
if [ -f "venv/bin/activate" ]; then
    source venv/bin/activate
fi

# ── Check database exists ─────────────────────────────────────
if [ ! -f "data/results.sqlite" ]; then
    echo "ERROR: data/results.sqlite not found!"
    echo "  Run the experiment first: ./scripts/run.sh"
    exit 1
fi

RESULT_COUNT=$(python3 -c "
import sqlite3
conn = sqlite3.connect('data/results.sqlite')
count = conn.execute('SELECT COUNT(*) FROM results').fetchone()[0]
print(count)
conn.close()
" 2>/dev/null || echo "0")

if [ "$RESULT_COUNT" = "0" ]; then
    echo "ERROR: No results in database yet!"
    echo "  Run the experiment first: ./scripts/run.sh"
    exit 1
fi

echo "════════════════════════════════════════════════════════"
echo "  LLM Peephole Optimization — Analysis Report"
echo "  ($RESULT_COUNT results in database)"
echo "════════════════════════════════════════════════════════"

# ── 1. Metrics ────────────────────────────────────────────────
echo ""
echo "[1/4] Computing metrics..."
python3 src/analysis/metrics.py

# ── 2. Plots ──────────────────────────────────────────────────
echo ""
echo "[2/4] Generating plots..."
python3 src/analysis/visualize.py

# ── 3. Failure analysis ───────────────────────────────────────
echo ""
echo "[3/4] Running failure analysis..."
python3 src/analysis/failure_analysis.py

# ── 4. Research report ────────────────────────────────────────
echo ""
echo "[4/4] Generating research report..."
python3 src/analysis/report.py

echo ""
echo "════════════════════════════════════════════════════════"
echo "  Analysis complete!"
echo ""
echo "  Outputs:"
echo "    results/research_report.md              — Full report"
echo "    results/plot1_validity_by_category.png   — Validity by category"
echo "    results/plot2_classification_breakdown.png — Classification breakdown"
echo "    results/plot3_confidence_calibration.png  — Confidence calibration"
echo "    results/plot4_instruction_reduction.png   — Instruction reduction"
echo "    results/pipeline.log                     — Pipeline execution log"
echo "════════════════════════════════════════════════════════"

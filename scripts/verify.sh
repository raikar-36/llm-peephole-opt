#!/usr/bin/env bash
# ═══════════════════════════════════════════════════════════════
# verify.sh — Verify all components work correctly
# ═══════════════════════════════════════════════════════════════
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$PROJECT_DIR"

# Activate venv if present
if [ -f "venv/bin/activate" ]; then
    source venv/bin/activate
fi

echo "════════════════════════════════════════════════════════"
echo "  LLM Peephole Optimization — Component Verification"
echo "════════════════════════════════════════════════════════"

PASS=0
FAIL=0

check() {
    local name="$1"
    shift
    if "$@" > /dev/null 2>&1; then
        echo "  ✓ $name"
        PASS=$((PASS + 1))
    else
        echo "  ✗ $name"
        FAIL=$((FAIL + 1))
    fi
}

# ── System tools ──────────────────────────────────────────────
echo ""
echo "[System Tools]"
check "clang"       command -v clang
check "opt"         command -v opt
check "llvm-as"     command -v llvm-as
check "llc"         command -v llc
check "python3"     command -v python3

# ── Python imports ────────────────────────────────────────────
echo ""
echo "[Python Imports]"
check "google-generativeai"  python3 -c "import google.generativeai"
check "pandas"               python3 -c "import pandas"
check "matplotlib"           python3 -c "import matplotlib"
check "seaborn"              python3 -c "import seaborn"
check "tqdm"                 python3 -c "import tqdm"

# ── Project modules ───────────────────────────────────────────
echo ""
echo "[Project Modules]"
check "dataset/generator"       python3 -c "from src.dataset.generator import OPS"
check "dataset/c_harvester"     python3 -c "from src.dataset.c_harvester import C_FUNCTIONS"
check "dataset/filter_preopt"   python3 -c "from src.dataset.filter_preopt import normalize_ir"
check "llm/client"              python3 -c "from src.llm.client import GeminiClient"
check "validate/tier1_syntax"   python3 -c "from src.validate.tier1_syntax import tier1_validate"
check "validate/tier2_dynamic"  python3 -c "from src.validate.tier2_dynamic import tier2_validate"
check "validate/tier3_alive2"   python3 -c "from src.validate.tier3_alive2 import alive2_validate"
check "analysis/db"             python3 -c "from src.analysis.db import DatabaseManager"
check "analysis/classifier"     python3 -c "from src.analysis.classifier import classify"
check "analysis/metrics"        python3 -c "from src.analysis.metrics import MetricsComputer"
check "analysis/visualize"      python3 -c "from src.analysis.visualize import Visualizer"
check "analysis/failure"        python3 -c "from src.analysis.failure_analysis import build_failure_report"
check "analysis/report"         python3 -c "from src.analysis.report import generate_report"
check "pipeline"                python3 -c "from src.pipeline import Pipeline"

# ── Unit tests ────────────────────────────────────────────────
echo ""
echo "[Unit Tests]"
check "Classifier (9 cases)"    python3 src/analysis/classifier.py

# Tier 1 test
check "Tier 1 validator"        python3 -c "
from src.validate.tier1_syntax import tier1_validate
r = tier1_validate('define i32 @f(i32 %x) {\nentry:\n  %r = add i32 %x, 0\n  ret i32 %r\n}\n', 'define i32 @f(i32 %x) {\nentry:\n  ret i32 %x\n}\n')
assert r.status == 'SYNTACTIC_PASS', r.status
"

# Alive2 test (if available)
ALIVE2="${ALIVE2_PATH:-$HOME/alive2/build/alive}"
if [ -f "$ALIVE2" ]; then
    check "Tier 3 Alive2" python3 -c "
import os
os.environ['ALIVE2_PATH'] = '$ALIVE2'
from src.validate.tier3_alive2 import alive2_validate
r = alive2_validate('define i32 @f(i32 %x) {\nentry:\n  %1 = xor i32 %x, 0\n  ret i32 %1\n}\n', 'define i32 @f(i32 %x) {\nentry:\n  ret i32 %x\n}\n')
assert r['status'] == 'FORMALLY_VALID', r['status']
"
else
    echo "  ⚠ Alive2 not found — skipping Tier 3 test"
fi

# ── Data files ────────────────────────────────────────────────
echo ""
echo "[Data Files]"
check "dataset.json exists"     test -f data/dataset.json
check "results.sqlite exists"   test -f data/results.sqlite

PATTERN_COUNT=$(python3 -c "import json; print(len(json.load(open('data/dataset.json'))))" 2>/dev/null || echo "0")
echo "  📊 Dataset: $PATTERN_COUNT patterns"

# ── Environment ───────────────────────────────────────────────
echo ""
echo "[Environment]"
if [ -n "${GEMINI_API_KEYS:-}" ]; then
    echo "  ✓ GEMINI_API_KEYS is set"
else
    echo "  ⚠ GEMINI_API_KEYS not set (source .env first)"
fi
if [ -n "${GEMINI_MODEL:-}" ]; then
    echo "  ✓ GEMINI_MODEL=${GEMINI_MODEL}"
else
    echo "  ℹ GEMINI_MODEL not set (default: gemini-3.1-flash-lite)"
fi
if [ -f "$ALIVE2" ]; then
    echo "  ✓ Alive2 at: $ALIVE2"
else
    echo "  ⚠ Alive2 not found"
fi

# ── Summary ───────────────────────────────────────────────────
echo ""
echo "════════════════════════════════════════════════════════"
TOTAL=$((PASS + FAIL))
echo "  Results: $PASS/$TOTAL passed"
if [ "$FAIL" -gt 0 ]; then
    echo "  ⚠  $FAIL components failed"
else
    echo "  ✅ All components verified!"
fi
echo "════════════════════════════════════════════════════════"

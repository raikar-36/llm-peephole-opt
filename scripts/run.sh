#!/usr/bin/env bash
# ═══════════════════════════════════════════════════════════════
# run.sh — Run the LLM peephole optimization experiment
# ═══════════════════════════════════════════════════════════════
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$PROJECT_DIR"

# ── Load environment ──────────────────────────────────────────
if [ -f ".env" ]; then
    set -a
    source .env
    set +a
fi

# Activate venv if present
if [ -f "venv/bin/activate" ]; then
    source venv/bin/activate
fi

LLM_PROVIDER="${LLM_PROVIDER:-gemini}"

if [ "$LLM_PROVIDER" = "gemini" ]; then
    if [ -z "${GEMINI_API_KEYS:-}" ]; then
        echo "ERROR: GEMINI_API_KEYS is not set!"
        echo ""
        echo "  Option 1: Edit .env and add your keys, then: source .env"
        echo "  Option 2: export GEMINI_API_KEYS='key1,key2,key3'"
        echo ""
        echo "  Get free keys at: https://aistudio.google.com"
        exit 1
    fi
elif [ "$LLM_PROVIDER" = "groq" ]; then
    if [ -z "${GROQ_API_KEY:-}" ]; then
        echo "ERROR: GROQ_API_KEY is not set!"
        echo ""
        echo "  Option 1: Edit .env and add your key, then: source .env"
        echo "  Option 2: export GROQ_API_KEY='your_key'"
        echo ""
        echo "  Get a key at: https://console.groq.com/"
        exit 1
    fi
fi

if [ ! -f "data/dataset.json" ]; then
    echo "ERROR: data/dataset.json not found!"
    echo "  Run ./scripts/setup.sh first"
    exit 1
fi

# ── Set Alive2 path if available ──────────────────────────────
if [ -z "${ALIVE2_PATH:-}" ]; then
    if [ -f "$HOME/alive2/build/alive" ]; then
        export ALIVE2_PATH="$HOME/alive2/build/alive"
        echo "Auto-detected Alive2 at: $ALIVE2_PATH"
    fi
fi

# ── Run the pipeline ──────────────────────────────────────────
echo "════════════════════════════════════════════════════════"
echo "  LLM Peephole Optimization — Experiment Run"
echo "════════════════════════════════════════════════════════"
echo ""
if [ "$LLM_PROVIDER" = "gemini" ]; then
    MODEL_NAME="${GEMINI_MODEL:-gemini-3.1-flash-lite}"
else
    MODEL_NAME="${GROQ_MODEL:-llama-3.3-70b-versatile}"
fi
echo "  Provider: ${LLM_PROVIDER}"
echo "  Model:    ${MODEL_NAME}"
echo "  Dataset:  $(python3 -c "import json; print(len(json.load(open('data/dataset.json'))))" 2>/dev/null || echo '?') patterns"
echo "  Alive2:   ${ALIVE2_PATH:-not set (Tier 3 skipped)}"
echo ""

# Pass all arguments through to the pipeline
python3 src/pipeline.py "$@"

echo ""
echo "════════════════════════════════════════════════════════"
echo "  Experiment complete!"
echo ""
echo "  Next: ./scripts/report.sh"
echo "════════════════════════════════════════════════════════"

#!/usr/bin/env bash
# ═══════════════════════════════════════════════════════════════
# setup.sh — One-time project setup
# ═══════════════════════════════════════════════════════════════
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$PROJECT_DIR"

echo "════════════════════════════════════════════════════════"
echo "  LLM Peephole Optimization — Setup"
echo "════════════════════════════════════════════════════════"

# ── 1. Check system dependencies ──────────────────────────────
echo ""
echo "[1/5] Checking system dependencies..."

missing=()
for cmd in clang opt llvm-as llc python3; do
    if ! command -v "$cmd" &> /dev/null; then
        missing+=("$cmd")
    else
        echo "  ✓ $cmd"
    fi
done

if [ ${#missing[@]} -gt 0 ]; then
    echo ""
    echo "  ✗ Missing: ${missing[*]}"
    echo "  Install with: sudo apt install llvm clang python3"
    exit 1
fi

# ── 2. Set up Python packages ─────────────────────────────────
echo ""
echo "[2/5] Installing Python packages..."

if [ -f "venv/bin/activate" ]; then
    echo "  Using existing venv..."
    source venv/bin/activate
    pip install -q google-generativeai pandas matplotlib seaborn tqdm
elif command -v python3 -m venv &> /dev/null 2>&1; then
    echo "  Creating venv..."
    python3 -m venv venv 2>/dev/null && {
        source venv/bin/activate
        pip install -q google-generativeai pandas matplotlib seaborn tqdm
    } || {
        echo "  venv creation failed — installing with --user"
        pip3 install --user --break-system-packages google-generativeai pandas matplotlib seaborn tqdm 2>/dev/null || \
        pip3 install --user google-generativeai pandas matplotlib seaborn tqdm
    }
else
    echo "  No venv support — installing with --user"
    pip3 install --user --break-system-packages google-generativeai pandas matplotlib seaborn tqdm 2>/dev/null || \
    pip3 install --user google-generativeai pandas matplotlib seaborn tqdm
fi
echo "  ✓ Python packages installed"

# ── 3. Create directory structure ──────────────────────────────
echo ""
echo "[3/5] Creating project directories..."

mkdir -p data/patterns/{arithmetic,bitwise,shifts,comparison,casts,select_phi,overflow_flags,const_chains}
mkdir -p src/{dataset,llm,validate,analysis}
mkdir -p results notebooks

for pkg in src src/dataset src/llm src/validate src/analysis; do
    touch "$pkg/__init__.py"
done
echo "  ✓ Directories created"

# ── 4. Generate dataset ───────────────────────────────────────
echo ""
echo "[4/5] Generating dataset..."

python3 src/dataset/generator.py
python3 src/dataset/c_harvester.py
python3 src/dataset/filter_preopt.py

PATTERN_COUNT=$(python3 -c "import json; print(len(json.load(open('data/dataset.json'))))")
echo ""
echo "  ✓ Dataset: $PATTERN_COUNT patterns"

# ── 5. Initialize database ────────────────────────────────────
echo ""
echo "[5/5] Initializing database..."

python3 -c "
from src.analysis.db import DatabaseManager
db = DatabaseManager('data/results.sqlite')
count = db.load_patterns('data/dataset.json')
print(f'  ✓ Loaded {count} patterns into SQLite')
db.close()
"

# ── 6. Environment file ───────────────────────────────────────
echo ""
if [ ! -f ".env" ]; then
    cp .env.example .env
    echo "  Created .env from .env.example"
    echo "  ⚠  Edit .env and add your GEMINI_API_KEYS before running!"
else
    echo "  .env already exists"
fi

# ── 7. Check Alive2 ───────────────────────────────────────────
ALIVE2_BIN="$HOME/alive2/build/alive"
if [ -f "$ALIVE2_BIN" ]; then
    echo "  ✓ Alive2 found at: $ALIVE2_BIN"
else
    echo "  ⚠  Alive2 not found (Tier 3 will be skipped)"
    echo "     Build from: https://github.com/AliveToolkit/alive2"
fi

echo ""
echo "════════════════════════════════════════════════════════"
echo "  Setup complete!"
echo ""
echo "  Next steps:"
echo "    1. Edit .env and add your GEMINI_API_KEYS"
echo "    2. source .env"
echo "    3. ./scripts/run.sh --limit 5    # test run"
echo "    4. ./scripts/run.sh              # full experiment"
echo "════════════════════════════════════════════════════════"

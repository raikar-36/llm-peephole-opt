#!/usr/bin/env bash
# ═══════════════════════════════════════════════════════════════
# build_alive2.sh — Build Alive2 from source
# ═══════════════════════════════════════════════════════════════
set -euo pipefail

ALIVE2_DIR="${ALIVE2_DIR:-$HOME/alive2}"

echo "════════════════════════════════════════════════════════"
echo "  Alive2 Build Script"
echo "════════════════════════════════════════════════════════"

# ── Check prerequisites ───────────────────────────────────────
echo ""
echo "[1/4] Checking prerequisites..."

for cmd in cmake ninja g++ z3; do
    if command -v "$cmd" &> /dev/null; then
        echo "  ✓ $cmd"
    else
        echo "  ✗ $cmd not found"
        echo "  Install: sudo apt install cmake ninja-build g++ libz3-dev"
        exit 1
    fi
done

# ── Clone if needed ───────────────────────────────────────────
echo ""
echo "[2/4] Checking Alive2 source..."

if [ -d "$ALIVE2_DIR" ]; then
    echo "  Found existing at: $ALIVE2_DIR"
    cd "$ALIVE2_DIR"
    git fetch --tags
    git checkout v19.0
else
    echo "  Cloning Alive2..."
    git clone https://github.com/AliveToolkit/alive2.git "$ALIVE2_DIR"
    cd "$ALIVE2_DIR"
    git checkout v19.0
fi

# ── Build basic (alive binary — .opt mode) ────────────────────
echo ""
echo "[3/4] Building alive (basic mode)..."

mkdir -p "$ALIVE2_DIR/build"
cd "$ALIVE2_DIR/build"

cmake -GNinja ..
ninja

if [ -f "$ALIVE2_DIR/build/alive" ]; then
    echo "  ✓ alive built successfully"
else
    echo "  ✗ Build failed"
    exit 1
fi

# ── Try building alive-tv (requires LLVM dev + libzstd) ───────
echo ""
echo "[4/4] Attempting to build alive-tv (LLVM IR mode)..."

if cmake -DBUILD_TV=ON -DLLVM_DIR=/usr/lib/llvm-19/cmake -GNinja .. 2>/dev/null || cmake -DBUILD_TV=ON -GNinja .. 2>/dev/null; then
    if ninja alive-tv 2>/dev/null; then
        echo "  ✓ alive-tv built successfully"
        echo ""
        echo "  Set ALIVE2_PATH to use alive-tv:"
        echo "    export ALIVE2_PATH=\"$ALIVE2_DIR/build/alive-tv\""
    else
        echo "  ⚠  alive-tv build failed (likely missing libzstd-dev)"
        echo "  Install: sudo apt install libzstd-dev"
        echo "  Then re-run this script"
        # Revert to basic build
        cmake -DBUILD_TV=OFF -GNinja .. > /dev/null 2>&1
    fi
else
    echo "  ⚠  alive-tv cmake failed — using basic alive binary"
    cmake -DBUILD_TV=OFF -GNinja .. > /dev/null 2>&1
fi

echo ""
echo "════════════════════════════════════════════════════════"
echo "  Alive2 ready at: $ALIVE2_DIR/build/alive"
echo ""
echo "  Add to your .env:"
echo "    ALIVE2_PATH=\"$ALIVE2_DIR/build/alive\""
echo "════════════════════════════════════════════════════════"

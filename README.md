# LLM Peephole Optimization

### Can Large Language Models Discover Missed Peephole Optimizations in LLVM IR?

A research tool that uses Large Language Models (LLMs) to suggest peephole optimizations on LLVM IR, then rigorously validates them through a 3-tier pipeline: syntactic checking, dynamic testing with 10,000 inputs, and formal verification via [Alive2](https://github.com/AliveToolkit/alive2).

---

## Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Quick Start](#quick-start)
- [Usage](#usage)
- [Project Structure](#project-structure)
- [Results](#results)
- [License](#license)

---

## Overview

Peephole optimizations are local rewrites that replace a small sequence of instructions with a more efficient equivalent. LLVM's optimizer handles thousands of such patterns, but it may not catch them all.

This project:
1. **Generates** a dataset of 200 LLVM IR patterns that `opt -O2` does not optimize.
2. **Queries** an LLM (Gemini 3.1 Flash Lite) to suggest equivalent, simplified rewrites.
3. **Validates** each suggestion through 3 tiers:
   - **Tier 1**: Syntax check via `llvm-as`, signature match, profitability (instruction count reduction).
   - **Tier 2**: Dynamic testing by compiling both versions and running 10,000 random and boundary inputs.
   - **Tier 3**: Formal verification via Alive2 (SMT-based proof of equivalence).
4. **Classifies** results (Valid, Invalid, Hallucinated, Correct Refusal, Missed Detection, Uncertain).
5. **Reports** metrics, plots, and failure analysis for research.

---

## Architecture

```text
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────────┐
│  Dataset Gen    │───▶│  LLM Query       │───▶│  3-Tier Validation  │
│  (generator.py) │    │  (client.py)     │    │                     │
│  (c_harvester.py│    │                  │    │  T1: llvm-as syntax │
│  (filter.py)    │    │                  │    │  T2: 10K dyn tests  │
└─────────────────┘    └──────────────────┘    │  T3: Alive2 formal  │
                                               └─────────┬───────────┘
                                                         │
                             ┌───────────────────────────▼───────────┐
                             │  Classification + Analysis            │
                             │  (classifier.py → metrics.py)         │
                             │  (visualize.py → report.py)           │
                             │  (failure_analysis.py)                │
                             └───────────────────────────────────────┘
```

---

## Prerequisites

### Required

| Tool | Version | Purpose |
|------|---------|---------|
| **Python** | 3.10+ | Runtime |
| **LLVM** | 14+ | `llvm-as`, `opt`, `llc`, `clang` for IR manipulation |
| **Gemini API Key** | Free | LLM queries |

### Optional (Recommended)

| Tool | Version | Purpose |
|------|---------|---------|
| **Alive2** | latest | Formal verification (Tier 3) |
| **Z3** | 4.8+ | SMT solver (required by Alive2) |

---

## Installation

### 1. Clone and enter the project

```bash
git clone https://github.com/raikar-36/llm-peephole-opt.git
cd llm-peephole-opt
```

### 2. Install system dependencies (Ubuntu/Debian)

```bash
sudo apt update
sudo apt install -y llvm clang python3 python3-pip python3-venv
# Optional for Alive2:
sudo apt install -y cmake ninja-build libz3-dev libzstd-dev
```

### 3. Setup Virtual Environment & Install Python packages

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 4. Set up environment variables

```bash
cp .env.example .env
# Edit .env and add your Gemini API keys (comma-separated):
# GEMINI_API_KEYS="key1,key2,key3"

# (Optional) If you want to use Groq instead of Gemini:
# GROQ_API_KEY="your_groq_key"
# LLM_PROVIDER="groq"

source .env
```

### 5. Build Alive2 (Optional, for Tier 3)

```bash
git clone https://github.com/AliveToolkit/alive2.git ~/alive2
cd ~/alive2
mkdir build && cd build
cmake -GNinja ..
ninja
# Set the path:
export ALIVE2_PATH="$HOME/alive2/build/alive-tv"
```

---

## Quick Start

```bash
# Start the interactive FastAPI demo
uvicorn demo.app:app --reload

# Open http://localhost:8000 in your browser
```

---

## Usage

### 1. Dataset Generation (Optional)

The repository comes with a pre-generated `dataset.json` containing 200 patterns (150 missed optimizations and 50 control patterns). If you wish to regenerate these exact 200 patterns from scratch, run the synthetic pattern generator:

```bash
python3 src/dataset/generator.py
```

*(Note: `c_harvester.py` and `filter_preopt.py` are extended scripts used for broader discovery, but the core 200 pattern dataset is generated directly via `generator.py`.)*

### 2. Using Shell Scripts (Recommended)

The easiest way to interact with the project is using the provided shell scripts in the `scripts/` directory:

```bash
./scripts/setup.sh         # One-time setup: installs dependencies, sets up directories, and builds the dataset
./scripts/build_alive2.sh  # Downloads and builds Alive2 (for Tier 3 formal verification)
./scripts/verify.sh        # Runs tests to verify all components and dependencies are working
./scripts/run.sh           # Runs the main LLM peephole optimization experiment
./scripts/report.sh        # Generates metrics, plots, failure analysis, and the final markdown report
```

### 3. Step-by-step Execution

If you prefer to run the components manually instead of using the shell scripts:

```bash
# 1. Run the pipeline (generates results.sqlite)
source .env
python3 src/pipeline.py --limit 10       # Test run
python3 src/pipeline.py                  # Full run on the 200 patterns

# 2. Analyze results
python3 src/analysis/metrics.py          # Print metrics summary
python3 src/analysis/visualize.py        # Generate 4 plots
python3 src/analysis/failure_analysis.py # Failure breakdown
python3 src/analysis/report.py           # Generate markdown report
```

### Pipeline CLI Options

```text
python3 src/pipeline.py [OPTIONS]

  --dataset PATH    Path to dataset.json (default: data/dataset.json)
  --db PATH         Path to results.sqlite (default: data/results.sqlite)
  --limit N         Process only N patterns (useful for testing)
  --no-skip         Re-run patterns already in the database
  --no-alive2       Skip Alive2 validation even if available
  --category CAT    Only run patterns from this category
```

---

## Project Structure

```text
llm-peephole-opt/
├── .env.example                # Environment variable template
├── requirements.txt            # Python dependencies
├── README.md                   # This file
├── DESIGN.md                   # Approach, architecture, alternatives
├── IMPLEMENTATION.md           # Implementation details
├── demo/                       # FastAPI interactive demo
│   ├── app.py                  # Backend server
│   └── static/                 # Frontend assets (index.html)
├── data/
│   ├── dataset.json            # Filtered patterns (200 entries)
│   ├── results.sqlite          # Experiment results database
│   └── patterns/               # Raw .ll files by category
├── src/
│   ├── dataset/                # Dataset generation tools
│   ├── llm/                    # LLM API client
│   ├── validate/               # 3-tier validation (Syntax, Dynamic, Formal)
│   ├── analysis/               # DB management, classification, reporting
│   └── pipeline.py             # Main experiment orchestrator
└── results/                    # Output plots and reports
```

---

## Results

Based on the 200 evaluated patterns (76 Valid, 46 Uncertain, 38 Invalid, 36 Correct Refusal, 4 Missed Detection), the pipeline demonstrates the feasibility of LLM-driven compiler optimizations for small functions. Comprehensive results are generated into the `results/` directory using the analysis scripts.

---

## License

Research project for academic use.

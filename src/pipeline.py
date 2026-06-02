#!/usr/bin/env python3
"""
Pipeline Orchestrator (Task 10)

Master script that runs the whole experiment end-to-end:
Load dataset → query LLM → validate → classify → store → print progress.
"""

import argparse
import json
import logging
import os
import sys
import time
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.llm.client import GeminiClient, GroqClient, create_llm_client
from src.validate.tier1_syntax import tier1_validate
from src.validate.tier2_dynamic import tier2_validate
from src.validate.tier3_alive2 import alive2_validate, find_alive2
from src.analysis.db import DatabaseManager
from src.analysis.classifier import classify

# ── Default Config ─────────────────────────────────────────────────────
def parse_api_keys() -> list:
    """Parse GEMINI_API_KEYS (comma-separated)."""
    raw_keys = os.environ.get("GEMINI_API_KEYS", "").strip()
    if raw_keys:
        if raw_keys.startswith("[") and raw_keys.endswith("]"):
            raw_keys = raw_keys[1:-1]
        return [k.strip() for k in raw_keys.split(",") if k.strip()]

    return []


config = {
    "llm_provider": os.environ.get("LLM_PROVIDER", "gemini").strip().lower(),
    "gemini_api_keys": parse_api_keys(),
    "gemini_model": os.environ.get("GEMINI_MODEL", "gemini-3.1-flash-lite"),
    "groq_api_key": os.environ.get("GROQ_API_KEY", "").strip(),
    "groq_model": os.environ.get("GROQ_MODEL", "llama-3.3-70b-versatile"),
    "alive2_path": os.environ.get("ALIVE2_PATH", ""),
    "dataset_path": "data/dataset.json",
    "db_path": "data/results.sqlite",
    "n_llm_samples": 1,
    "n_dynamic_trials": 10000,
    "use_alive2": bool(os.environ.get("ALIVE2_PATH", "")),
    "skip_existing": True,
    "max_patterns": None,
}


def setup_logging():
    """Set up logging to console (INFO) and file (DEBUG)."""
    log_dir = PROJECT_ROOT / 'results'
    log_dir.mkdir(exist_ok=True)

    logger = logging.getLogger('pipeline')
    logger.setLevel(logging.DEBUG)

    # Console handler
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    ch.setFormatter(logging.Formatter('%(message)s'))
    logger.addHandler(ch)

    # File handler
    fh = logging.FileHandler(log_dir / 'pipeline.log')
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(logging.Formatter('%(asctime)s %(levelname)s %(message)s'))
    logger.addHandler(fh)

    return logger


class Pipeline:
    """Orchestrates the full LLM peephole optimization experiment."""

    def __init__(self, config: dict):
        self.config = config
        self.logger = setup_logging()

        # Initialize LLM client via factory
        provider = config.get('llm_provider', 'gemini')
        try:
            if provider == 'groq':
                self.llm_client = create_llm_client(
                    provider='groq',
                    api_key=config.get('groq_api_key'),
                    model=config.get('groq_model', 'llama-3.3-70b-versatile'),
                    rpm_limit=int(os.environ.get('GROQ_RPM_LIMIT', '30')),
                    logger=self.logger,
                )
            else:
                api_keys = config.get('gemini_api_keys') or []
                if not api_keys:
                    self.logger.error("GEMINI_API_KEYS not set!")
                    self.logger.error("  export GEMINI_API_KEYS='key1,key2,key3'")
                    sys.exit(1)
                self.llm_client = create_llm_client(
                    provider='gemini',
                    api_keys=api_keys,
                    model=config.get('gemini_model', 'gemini-3.1-flash-lite'),
                    rpm_per_key=15,
                    cooldown_seconds=60,
                    logger=self.logger,
                )
        except Exception as e:
            self.logger.error(f"Failed to initialize LLM client: {e}")
            sys.exit(1)
        self.logger.info(f"LLM client initialized (provider={provider})")

        # Initialize database
        self.db = DatabaseManager(config['db_path'])
        count = self.db.load_patterns(config['dataset_path'])
        self.logger.info(f"Database: {count} patterns loaded")

        # Find Alive2
        if config['use_alive2']:
            self.alive2_path = find_alive2()
            if self.alive2_path:
                self.logger.info(f"Alive2 found at: {self.alive2_path}")
            else:
                self.logger.warning("Alive2 not found. Tier 3 validation will be skipped.")
                config['use_alive2'] = False
        else:
            self.alive2_path = ""

        # Running counters
        self.counters = {}

    def run_single(self, pattern: dict) -> dict:
        """Run the full pipeline on a single pattern."""
        pattern_id = pattern['id']
        input_ir = pattern['input_ir']
        is_missed = bool(pattern.get('is_missed', False))

        # Check if already processed
        if self.config['skip_existing'] and self.db.result_exists(pattern_id):
            self.logger.debug(f"Skipping {pattern_id} (already exists)")
            return None

        result = {
            'pattern_id': pattern_id,
            'llm_model': config.get('groq_model' if config.get('llm_provider') == 'groq' else 'gemini_model', 'gemini-3.1-flash-lite'),
            'prompt_version': 'v1',
        }

        # ── Step 1: Query LLM (single query) ──
        max_retries = 3
        llm_result = None
        for attempt in range(max_retries):
            try:
                llm_result = self.llm_client.query_single(input_ir, category=pattern.get('family', ''))
                break
            except Exception as e:
                if '429' in str(e) or 'rate' in str(e).lower():
                    self.logger.warning(f"Rate limited. Sleeping 60s... (attempt {attempt + 1})")
                    time.sleep(60)
                else:
                    self.logger.error(f"LLM error for {pattern_id}: {e}")
                    if attempt == max_retries - 1:
                        result['optimized_ir'] = 'PARSE_ERROR'
                        result['tier1_status'] = 'PARSE_ERROR'
                        result['tier1_reason'] = str(e)[:200]
                        result['final_class'] = 'HALLUCINATED'
                        self.db.save_result(result)
                        return result
                    time.sleep(5)

        if llm_result is None:
            result['optimized_ir'] = 'PARSE_ERROR'
            result['tier1_status'] = 'PARSE_ERROR'
            result['tier1_reason'] = 'All retries failed'
            result['final_class'] = 'HALLUCINATED'
            self.db.save_result(result)
            return result

        optimized_ir = llm_result.get('optimized_ir', '')
        result['optimized_ir'] = optimized_ir
        result['confidence'] = llm_result.get('confidence', 'LOW')
        result['reason'] = llm_result.get('reason', '')
        result['precondition'] = llm_result.get('precondition', 'none')

        # Store raw response
        result['raw_response'] = json.dumps(llm_result)

        # Check if LLM said NO_OPT
        is_no_opt = (
            optimized_ir.strip().upper() == "NO_OPT" or
            "NO_OPT" in optimized_ir.upper()
        )
        result['llm_said_no_opt'] = 1 if is_no_opt else 0

        if is_no_opt:
            result['tier1_status'] = 'NO_OPT_CLAIMED'
            result['tier1_reason'] = 'LLM said no optimization possible'
            result['final_class'] = classify(
                pattern_id=pattern_id, original_ir=input_ir,
                rewrite_ir=optimized_ir,
                tier1_status='NO_OPT_CLAIMED', tier2_status='', tier3_status='',
                llm_said_no_opt=True, is_missed=is_missed
            )
            self.db.save_result(result)
            return result

        # ── Step 2: Tier 1 Validation ──
        t1_result = tier1_validate(input_ir, optimized_ir)
        result['tier1_status'] = t1_result.status
        result['tier1_reason'] = t1_result.reason

        if t1_result.details:
            result['instr_count_original'] = t1_result.details.get('original_instr_count')
            result['instr_count_rewrite'] = t1_result.details.get('rewrite_instr_count')
            if result['instr_count_original'] and result['instr_count_original'] > 0:
                result['instr_reduction_ratio'] = (
                    1.0 - result['instr_count_rewrite'] / result['instr_count_original']
                )

        if t1_result.status != "SYNTACTIC_PASS":
            result['final_class'] = classify(
                pattern_id=pattern_id, original_ir=input_ir,
                rewrite_ir=optimized_ir,
                tier1_status=t1_result.status, tier2_status='', tier3_status='',
                llm_said_no_opt=False, is_missed=is_missed
            )
            self.db.save_result(result)
            return result

        # ── Step 3: Tier 2 Validation ──
        try:
            t2_result = tier2_validate(
                input_ir, optimized_ir,
                n_trials=self.config['n_dynamic_trials']
            )
            result['tier2_status'] = t2_result['status']
            if t2_result.get('counterexample'):
                result['tier2_counterexample'] = t2_result['counterexample']
        except Exception as e:
            self.logger.debug(f"Tier 2 error for {pattern_id}: {e}")
            result['tier2_status'] = 'COMPILE_ERROR'
            t2_result = {'status': 'COMPILE_ERROR'}

        if t2_result['status'] not in ('DYNAMIC_PASS',):
            result['final_class'] = classify(
                pattern_id=pattern_id, original_ir=input_ir,
                rewrite_ir=optimized_ir,
                tier1_status=t1_result.status,
                tier2_status=t2_result['status'],
                tier3_status='',
                llm_said_no_opt=False, is_missed=is_missed
            )
            self.db.save_result(result)
            return result

        # ── Step 4: Tier 3 Validation (Alive2) ──
        if self.config['use_alive2'] and self.alive2_path:
            try:
                t3_result = alive2_validate(
                    input_ir, optimized_ir,
                    alive_tv_path=self.alive2_path,
                    timeout=self.config.get('alive2_timeout', 30)
                )
                result['tier3_status'] = t3_result['status']
                result['tier3_output'] = t3_result.get('raw_output', '')[:500]
            except Exception as e:
                self.logger.debug(f"Tier 3 error for {pattern_id}: {e}")
                result['tier3_status'] = 'UNKNOWN'
                t3_result = {'status': 'UNKNOWN'}
        else:
            result['tier3_status'] = ''
            t3_result = {'status': ''}

        # ── Step 5: Classify ──
        result['final_class'] = classify(
            pattern_id=pattern_id, original_ir=input_ir,
            rewrite_ir=optimized_ir,
            tier1_status=t1_result.status,
            tier2_status=t2_result['status'],
            tier3_status=t3_result['status'],
            llm_said_no_opt=False, is_missed=is_missed
        )

        # ── Step 6: Save ──
        self.db.save_result(result)
        return result

    def run_all(self):
        """Run the pipeline on all patterns."""
        patterns = self.db.get_all_patterns()

        if self.config.get('category') == 'uncertain_only':
            uncertain_ids = {row['pattern_id'] for row in self.db.conn.execute("SELECT pattern_id FROM results WHERE final_class = 'UNCERTAIN'").fetchall()}
            patterns = [p for p in patterns if p['id'] in uncertain_ids]
            with self.db.conn:
                self.db.conn.execute("DELETE FROM results WHERE final_class = 'UNCERTAIN'")
        elif self.config.get('category') == 'ablation_bitwise_shifts':
            target_ids = {row['p_id'] for row in self.db.conn.execute("SELECT p.id as p_id FROM patterns p JOIN results r ON p.id = r.pattern_id WHERE p.family IN ('bitwise', 'shifts', 'overflow_flags')").fetchall()}
            patterns = [p for p in patterns if p['id'] in target_ids]
            with self.db.conn:
                self.db.conn.execute("DELETE FROM results WHERE pattern_id IN (SELECT id FROM patterns WHERE family IN ('bitwise', 'shifts', 'overflow_flags'))")
        elif self.config.get('category') == 'control_group_ablation':
            target_ids = {row['p_id'] for row in self.db.conn.execute("SELECT p.id as p_id FROM patterns p JOIN results r ON p.id = r.pattern_id WHERE p.is_missed = 0").fetchall()}
            patterns = [p for p in patterns if p['id'] in target_ids]
            with self.db.conn:
                self.db.conn.execute("DELETE FROM results WHERE pattern_id IN (SELECT id FROM patterns WHERE is_missed = 0)")
        elif self.config.get('category'):
            patterns = [p for p in patterns if p.get('family', '') == self.config['category']]

        if self.config['max_patterns']:
            print(f"Loaded {len(patterns)} patterns from {self.config['dataset_path']}")
            patterns = patterns[:self.config['max_patterns']]

        total = len(patterns)
        self.logger.info(f"\nRunning pipeline on {total} patterns...\n")

        counters = {}
        processed = 0

        for i, pattern in enumerate(patterns):
            try:
                result = self.run_single(pattern)

                if result is None:
                    # Skipped (already exists)
                    continue

                processed += 1
                final_class = result.get('final_class', 'UNKNOWN')
                counters[final_class] = counters.get(final_class, 0) + 1
                confidence = result.get('confidence', '?')

                self.logger.info(
                    f"  [{i + 1}/{total}] {pattern['id'][:40]:40s} → {final_class} ({confidence})"
                )

                # Print running summary every 10 patterns
                if processed % 10 == 0:
                    valid = counters.get('VALID_NOVEL', 0) + counters.get('VALID_KNOWN', 0)
                    invalid = sum(v for k, v in counters.items() if k.startswith('INVALID'))
                    halluc = counters.get('HALLUCINATED', 0)
                    uncertain = counters.get('UNCERTAIN', 0)
                    no_opt = counters.get('NO_OPT_CORRECT', 0) + counters.get('NO_OPT_WRONG', 0)
                    self.logger.info(
                        f"    ── Running: Valid={valid} | Invalid={invalid} | "
                        f"Hallucinated={halluc} | Uncertain={uncertain} | NO_OPT={no_opt}"
                    )

            except Exception as e:
                self.logger.error(f"  [{i + 1}/{total}] ERROR on {pattern['id']}: {e}")
                continue

        self.logger.info(f"\nProcessed {processed} patterns.")
        self.counters = counters
        self.print_summary()

    def print_summary(self):
        """Print a formatted summary table."""
        stats = self.db.get_stats()
        class_counts = stats.get('class_counts', {})
        total = stats.get('total', 0)

        if total == 0:
            self.logger.info("No results to summarize.")
            return

        self.logger.info(f"\n{'=' * 55}")
        self.logger.info(f"  FINAL RESULTS SUMMARY")
        self.logger.info(f"{'=' * 55}")
        self.logger.info(f"  {'Classification':<25s} {'Count':>6s} {'Rate':>8s}")
        self.logger.info(f"  {'-' * 25} {'-' * 6} {'-' * 8}")

        for cls in ['VALID', 'FALSE_POSITIVE',
                     'INVALID', 'HALLUCINATED',
                     'CORRECT_REFUSAL', 'MISSED_DETECTION', 'UNCERTAIN']:
            count = class_counts.get(cls, 0)
            rate = f"{count / total * 100:.1f}%" if total > 0 else "0.0%"
            self.logger.info(f"  {cls:<25s} {count:>6d} {rate:>8s}")

        self.logger.info(f"  {'-' * 25} {'-' * 6} {'-' * 8}")
        self.logger.info(f"  {'TOTAL':<25s} {total:>6d}")

        validity_rate = stats.get('validity_rate', 0)
        hallucination_rate = stats.get('hallucination_rate', 0)
        self.logger.info(f"\n  Validity Rate:       {validity_rate * 100:.1f}%")
        self.logger.info(f"  Hallucination Rate:  {hallucination_rate * 100:.1f}%")
        self.logger.info(f"{'=' * 55}")


def main():
    parser = argparse.ArgumentParser(description='LLM Peephole Optimization Pipeline')
    parser.add_argument('--dataset', default='data/dataset.json',
                        help='Path to dataset.json')
    parser.add_argument('--db', default='data/results.sqlite',
                        help='Path to results.sqlite')
    parser.add_argument('--limit', type=int, default=None,
                        help='Max patterns to process')
    parser.add_argument('--no-skip', action='store_true',
                        help='Re-run patterns already in DB')
    parser.add_argument('--no-alive2', action='store_true',
                        help='Skip Alive2 validation')
    parser.add_argument('--category', default=None,
                        help='Only run patterns from this category')
    parser.add_argument('--alive2-timeout', type=int, default=30,
                        help='Timeout for Alive2 verification in seconds')

    args = parser.parse_args()

    # Update config from args
    config['dataset_path'] = args.dataset
    config['db_path'] = args.db
    config['max_patterns'] = args.limit
    config['skip_existing'] = not args.no_skip
    if args.no_alive2:
        config['use_alive2'] = False
    if args.category:
        config['category'] = args.category
    config['alive2_timeout'] = args.alive2_timeout

    pipeline = Pipeline(config)
    pipeline.run_all()


if __name__ == '__main__':
    main()

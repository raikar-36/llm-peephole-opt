#!/usr/bin/env python3
"""
SQLite Database Manager (Task 4)

Manages the SQLite database for storing LLM optimization experiment results.
"""

import json
import sqlite3
from datetime import datetime
from pathlib import Path


class DatabaseManager:
    """Manages the SQLite database for LLM optimization results."""

    def __init__(self, db_path: str):
        """Connect to SQLite at db_path and initialize schema."""
        self.db_path = db_path
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row
        self.init_schema()

    def init_schema(self):
        """Create tables if they don't exist."""
        with self.conn:
            self.conn.executescript("""
                CREATE TABLE IF NOT EXISTS patterns (
                    id TEXT PRIMARY KEY,
                    category TEXT NOT NULL,
                    family TEXT NOT NULL,
                    is_missed BOOLEAN NOT NULL,
                    before_instr_count INTEGER,
                    expected_instr_count INTEGER,
                    instr_delta INTEGER,
                    input_ir TEXT NOT NULL,
                    expected_after_ir TEXT,
                    source TEXT,
                    notes TEXT
                );

                CREATE TABLE IF NOT EXISTS results (
                    result_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    pattern_id TEXT REFERENCES patterns(id),
                    llm_model TEXT,
                    prompt_version TEXT DEFAULT 'v1',
                    raw_response TEXT,
                    optimized_ir TEXT,
                    llm_said_no_opt INTEGER DEFAULT 0,
                    confidence TEXT,
                    reason TEXT,
                    precondition TEXT,
                    tier1_status TEXT,
                    tier1_reason TEXT,
                    tier2_status TEXT,
                    tier2_counterexample TEXT,
                    tier3_status TEXT,
                    tier3_output TEXT,
                    final_class TEXT,
                    instr_count_original INTEGER,
                    instr_count_rewrite INTEGER,
                    instr_reduction_ratio REAL,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                );
            """)

    def load_patterns(self, dataset_json_path: str) -> int:
        """Load all patterns from dataset.json into the patterns table."""
        with open(dataset_json_path, 'r') as f:
            patterns = json.load(f)

        count = 0
        with self.conn:
            for p in patterns:
                try:
                    self.conn.execute(
                        "INSERT OR IGNORE INTO patterns "
                        "(id, category, family, is_missed, before_instr_count, expected_instr_count, instr_delta, input_ir, expected_after_ir, source, notes) "
                        "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                        (p['id'], p.get('category', 'unknown'), p.get('family', 'unknown'),
                         p.get('is_missed', False),
                         p.get('before_instr_count'), p.get('expected_instr_count'), p.get('instr_delta'),
                         p['input_ir'], p.get('expected_after_ir', ''),
                         p.get('source', ''), p.get('notes', ''))
                    )
                    count += 1
                except sqlite3.IntegrityError:
                    pass  # Skip if already exists

        return count

    def save_result(self, result: dict):
        """Insert a result record into the results table."""
        columns = [
            'pattern_id', 'llm_model', 'prompt_version',
            'raw_response', 'optimized_ir',
            'llm_said_no_opt', 'confidence',
            'reason', 'precondition',
            'tier1_status', 'tier1_reason',
            'tier2_status', 'tier2_counterexample',
            'tier3_status', 'tier3_output',
            'final_class',
            'instr_count_original', 'instr_count_rewrite', 'instr_reduction_ratio'
        ]

        values = []
        present_cols = []
        for col in columns:
            if col in result:
                present_cols.append(col)
                values.append(result[col])

        placeholders = ', '.join(['?'] * len(present_cols))
        col_str = ', '.join(present_cols)

        with self.conn:
            self.conn.execute(
                f"INSERT INTO results ({col_str}) VALUES ({placeholders})",
                values
            )

    def get_all_results(self) -> list:
        """Return all results as list of dicts."""
        cursor = self.conn.execute(
            "SELECT r.*, p.category, p.input_ir "
            "FROM results r JOIN patterns p ON r.pattern_id = p.id"
        )
        rows = cursor.fetchall()
        return [dict(row) for row in rows]

    def get_results_by_class(self, final_class: str) -> list:
        """Filter results by final_class."""
        cursor = self.conn.execute(
            "SELECT r.*, p.category, p.input_ir "
            "FROM results r JOIN patterns p ON r.pattern_id = p.id "
            "WHERE r.final_class = ?",
            (final_class,)
        )
        rows = cursor.fetchall()
        return [dict(row) for row in rows]

    def get_stats(self) -> dict:
        """Return counts per final_class, per category, and overall rates."""
        stats = {}

        # Counts per final_class
        cursor = self.conn.execute(
            "SELECT final_class, COUNT(*) as cnt FROM results GROUP BY final_class"
        )
        class_counts = {row['final_class']: row['cnt'] for row in cursor.fetchall()}
        stats['class_counts'] = class_counts

        # Counts per category
        cursor = self.conn.execute(
            "SELECT p.family, COUNT(*) as cnt "
            "FROM results r JOIN patterns p ON r.pattern_id = p.id "
            "GROUP BY p.family"
        )
        family_counts = {row['family']: row['cnt'] for row in cursor.fetchall()}
        stats['family_counts'] = family_counts

        # Overall rates
        total = sum(class_counts.values()) if class_counts else 0
        valid = class_counts.get('VALID', 0) + class_counts.get('FALSE_POSITIVE', 0)
        hallucinated = class_counts.get('HALLUCINATED', 0)
        refusals = class_counts.get('CORRECT_REFUSAL', 0) + class_counts.get('MISSED_DETECTION', 0)
        total_non_refusal = total - refusals

        stats['total'] = total
        stats['validity_rate'] = valid / total_non_refusal if total_non_refusal > 0 else 0
        stats['hallucination_rate'] = hallucinated / total if total > 0 else 0

        return stats

    def result_exists(self, pattern_id: str) -> bool:
        """Check if a result already exists for this pattern_id."""
        cursor = self.conn.execute(
            "SELECT COUNT(*) as cnt FROM results WHERE pattern_id = ?",
            (pattern_id,)
        )
        return cursor.fetchone()['cnt'] > 0

    def get_all_patterns(self) -> list:
        """Return all patterns as list of dicts."""
        cursor = self.conn.execute("SELECT * FROM patterns")
        return [dict(row) for row in cursor.fetchall()]

    def close(self):
        """Close the database connection."""
        self.conn.close()

    def __del__(self):
        try:
            self.conn.close()
        except Exception:
            pass


if __name__ == '__main__':
    import sys

    db = DatabaseManager('data/results.sqlite')

    # Check if dataset.json exists
    dataset_path = Path('data/dataset.json')
    if dataset_path.exists():
        count = db.load_patterns(str(dataset_path))
        print(f"Loaded {count} patterns into DB")
    else:
        print("data/dataset.json not found — run filter_preopt.py first")

    db.close()

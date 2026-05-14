#!/usr/bin/env python3
"""
Print a summary table of all completed prompt experiments.

Usage (from project root):
    ../openevolve/.venv/bin/python openevolve/show_results.py [--verbose] [--run <run_id>]

Columns:
  prompt        — name of the prompt file used
  mem_score     — best memory-access score (>1.0 means fewer accesses than baseline)
  iter_found    — iteration at which the best program was first found
  accesses      — absolute load+store count for the best evolved pipeline
  reduction     — percentage reduction vs. baseline (128,862,705 accesses)

Supports both consolidated (results.json) and legacy (best_program_info.json) formats.
Prefers consolidated format if available.
"""

import argparse
import glob
import json
import os
import re
import sys

SCRIPT_DIR         = os.path.dirname(os.path.abspath(__file__))
OUTPUT_ROOT        = os.path.join(SCRIPT_DIR, "openevolve_output")
REFERENCE_ACCESSES = 128_862_705


def load_consolidated_result(prompt_name: str) -> dict | None:
    """Try to load consolidated results.json"""
    try:
        from results_loader import load_results
        results_path = os.path.join(OUTPUT_ROOT, prompt_name, "results.json")
        if os.path.isfile(results_path):
            df = load_results(results_path)
            if not df.empty:
                best_row = df[df['memory_accesses'] == df['memory_accesses'].min()].iloc[0]
                return {
                    'prompt': prompt_name,
                    'mem_score': best_row['mem_score'],
                    'iter_found': int(best_row['iteration']),
                    'accesses': int(best_row['memory_accesses']),
                    'format': 'consolidated',
                }
    except Exception:
        pass
    return None


def load_legacy_result(prompt_name: str) -> dict | None:
    """Load result from legacy best_program_info.json format"""
    info_path = os.path.join(OUTPUT_ROOT, prompt_name, "best", "best_program_info.json")
    if not os.path.isfile(info_path):
        return None
    try:
        with open(info_path) as f:
            info = json.load(f)
        metrics = info.get("metrics", {})
        score = metrics.get("mem_score") or metrics.get("combined_score")
        if score is None:
            return None
        accesses = int(REFERENCE_ACCESSES / score) if score > 0 else 0
        return {
            "prompt": prompt_name,
            "mem_score": score,
            "iter_found": info.get("iteration", "?"),
            "accesses": accesses,
            "format": "legacy",
        }
    except Exception:
        return None


def load_result(prompt_name: str) -> dict | None:
    """Load results, preferring consolidated format, falling back to legacy"""
    # Try consolidated first
    result = load_consolidated_result(prompt_name)
    if result:
        return result

    # Fall back to legacy format
    return load_legacy_result(prompt_name)


def load_result_from_path(results_path: str, run_id: str, prompt_name: str) -> dict | None:
    """Load consolidated result from a specific results.json path."""
    try:
        from results_loader import load_results
        if os.path.isfile(results_path):
            df = load_results(results_path)
            if not df.empty:
                best_row = df[df['memory_accesses'] == df['memory_accesses'].min()].iloc[0]
                return {
                    'prompt': prompt_name,
                    'mem_score': best_row['mem_score'],
                    'iter_found': int(best_row['iteration']),
                    'accesses': int(best_row['memory_accesses']),
                    'format': 'consolidated',
                    'run_id': run_id,
                }
    except Exception:
        pass
    return None


def main():
    parser = argparse.ArgumentParser(description="Show experiment results (best per prompt)")
    parser.add_argument("--verbose", action="store_true", help="Show data format used")
    parser.add_argument("--run", default=None,
        help="Filter output to a specific run ID (default: show all runs)")
    args = parser.parse_args()

    runs_dir = os.path.join(OUTPUT_ROOT, "runs")
    if not os.path.isdir(runs_dir):
        print("No results yet — run  make evolve-all  first.")
        return

    pattern = os.path.join(runs_dir, "**", "results.json")
    paths = glob.glob(pattern, recursive=True)

    rows = []
    for path in paths:
        # Parse run_id and prompt from path structure:
        # <runs_dir>/<run_id>/cavitydetection/<prompt>/results.json
        rel = os.path.relpath(path, runs_dir)
        parts = rel.split(os.sep)
        if len(parts) < 4:
            continue
        run_id = parts[0]
        prompt = parts[-2]

        if args.run is not None and run_id != args.run:
            continue

        result = load_result_from_path(path, run_id, prompt)
        if result:
            rows.append(result)

    if not rows:
        print("No completed experiments found.")
        return

    rows.sort(key=lambda r: r["mem_score"], reverse=True)

    col_w = max(len(r["prompt"]) for r in rows)
    col_w = max(col_w, 6)

    header = f"{'prompt':<{col_w}}  {'mem_score':>9}  {'iter_found':>10}  {'accesses':>13}  {'reduction':>9}"
    print(header)
    print("-" * len(header))

    for r in rows:
        accesses = r.get("accesses", 0)
        if accesses == 0 and r["mem_score"] > 0:
            accesses = int(REFERENCE_ACCESSES / r["mem_score"])
        reduction = (1.0 - r["mem_score"] ** -1) * 100 if r["mem_score"] > 0 else 0.0
        print(
            f"{r['prompt']:<{col_w}}  {r['mem_score']:>9.4f}  "
            f"{str(r['iter_found']):>10}  {accesses:>13,}  {reduction:>8.1f}%"
        )

    # Print data source if verbose
    if args.verbose:
        formats = set(r.get("format", "unknown") for r in rows)
        print(f"\nData source: {', '.join(sorted(formats))}")


if __name__ == "__main__":
    main()

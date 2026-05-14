#!/usr/bin/env python3
"""
Display consolidated results from all experiments (unified format).
Shows convergence speed and best quality per prompt.

Usage (from project root):
    ../openevolve/.venv/bin/python openevolve/show_consolidated.py [--run <run_id>]

Columns:
  prompt          — name of the prompt variant
  best_accesses   — lowest memory access count achieved
  conv_iter       — iteration at which best was found
  improve_%       — percentage improvement vs. baseline
  mem_score       — memory access score (>1.0 = better than baseline)
"""

import argparse
import glob
import os
import re
import sys

import pandas as pd

# Add parent directory to path for imports
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SCRIPT_DIR)

from results_loader import load_results


def extract_run_id(filepath: str) -> str:
    """Extract run_id from a results.json filepath under the runs/ tree."""
    filepath = filepath.replace("\\", "/")
    parts = filepath.split("/")
    try:
        runs_idx = parts.index("runs")
        return parts[runs_idx + 1]
    except (ValueError, IndexError):
        return "unknown"


def main():
    parser = argparse.ArgumentParser(description="Show consolidated results from all experiments")
    parser.add_argument("--run", default=None, help="Filter to a specific run ID")
    parser.add_argument("--output-root", default=None,
        help="Override output base directory (default: openevolve/openevolve_output/)")
    args = parser.parse_args()

    try:
        results_root = os.path.join(args.output_root or SCRIPT_DIR, "openevolve_output", "runs")

        paths = glob.glob(os.path.join(results_root, "**", "results.json"), recursive=True)

        if not paths:
            print("No results found — run make evolve-all first.")
            return

        frames = []
        for path in paths:
            try:
                file_df = load_results(path)
                file_df["run_id"] = extract_run_id(path)
                frames.append(file_df)
            except Exception:
                continue

        if not frames:
            print("No results found — run make evolve-all first.")
            return

        df = pd.concat(frames, ignore_index=True)

        if args.run is not None:
            df = df[df["run_id"] == args.run]
            if df.empty:
                print(f"No results found for run: {args.run}")
                return

        if df.empty:
            print("No consolidated results found. Run 'make evolve-all' first.")
            return

        # Group by prompt, find best per prompt
        results = []
        for prompt in sorted(df['prompt'].unique()):
            subset = df[df['prompt'] == prompt]
            best_row = subset[subset['memory_accesses'] == subset['memory_accesses'].min()].iloc[0]
            results.append({
                'prompt': prompt,
                'best_accesses': int(best_row['memory_accesses']),
                'convergence_iter': int(best_row['iteration']),
                'improvement_percent': best_row['improvement_percent'],
                'mem_score': best_row['mem_score'],
            })

        # Sort by improvement descending
        results.sort(key=lambda r: r['improvement_percent'], reverse=True)

        # Print table
        header = f"{'prompt':<15}  {'best_accesses':>13}  {'conv_iter':>10}  {'improve_%':>10}  {'mem_score':>10}"
        print(header)
        print("-" * len(header))
        for r in results:
            print(
                f"{r['prompt']:<15}  {r['best_accesses']:>13,}  "
                f"{r['convergence_iter']:>10}  {r['improvement_percent']:>9.1f}%  "
                f"{r['mem_score']:>10.4f}"
            )

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()

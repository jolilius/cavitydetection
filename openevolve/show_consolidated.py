#!/usr/bin/env python3
"""
Display consolidated results from all experiments (unified format).
Shows convergence speed and best quality per prompt.

Usage (from project root):
    ../openevolve/.venv/bin/python openevolve/show_consolidated.py

Columns:
  prompt          — name of the prompt variant
  best_accesses   — lowest memory access count achieved
  conv_iter       — iteration at which best was found
  improve_%       — percentage improvement vs. baseline
  mem_score       — memory access score (>1.0 = better than baseline)
"""

import os
import sys

# Add parent directory to path for imports
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SCRIPT_DIR)

from results_loader import load_all_results


def main():
    try:
        df = load_all_results()
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

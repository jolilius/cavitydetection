"""
Pandas-compatible loader for consolidated OpenEvolve results.

Loads unified results JSON files (from consolidate_results.py) into pandas
DataFrames for analysis, visualization, and batch processing.

Usage:
    from openevolve.results_loader import load_results, load_all_results
    import matplotlib.pyplot as plt

    # Single experiment
    df = load_results('openevolve_output/baseline/results.json')
    print(df[['iteration', 'memory_accesses', 'improvement_percent']])

    # All experiments
    df_all = load_all_results()
    for prompt in df_all['prompt'].unique():
        subset = df_all[df_all['prompt'] == prompt]
        plt.plot(subset['iteration'], subset['memory_accesses'], label=prompt)
    plt.show()
"""

import json
import logging
import os
from typing import Optional

import pandas as pd


logger = logging.getLogger(__name__)


def get_explanations(df: pd.DataFrame) -> dict:
    """
    Group explanations by iteration for analysis.

    Extracts all non-NaN explanations from a DataFrame loaded via load_results()
    or load_all_results() and organizes them by iteration number and prompt.

    Args:
        df: DataFrame from load_results() or load_all_results()

    Returns:
        Dictionary mapping iteration -> {prompt: explanation_text}
        Example:
        {
            1: {"baseline": "Fused loops to reduce intermediate buffers...", "variant_a": "Reordered loops..."},
            5: {"baseline": "Added bounds-check elimination..."},
        }

    Example:
        df = load_all_results()
        explained_by_iter = get_explanations(df)
        for iteration, prompts in sorted(explained_by_iter.items()):
            print(f"Iteration {iteration}:")
            for prompt, explanation in prompts.items():
                print(f"  {prompt}: {explanation[:60]}...")
    """
    result = {}
    if 'explanation' not in df.columns or 'iteration' not in df.columns:
        return result

    # Filter for rows with explanations
    explained_df = df[df['explanation'].notna()].copy()

    for iteration in sorted(explained_df['iteration'].unique()):
        iter_data = explained_df[explained_df['iteration'] == iteration]
        result[iteration] = {}

        # If 'prompt' column exists, group by prompt; otherwise use single entry
        if 'prompt' in iter_data.columns:
            for _, row in iter_data.iterrows():
                prompt = row['prompt']
                explanation = row['explanation']
                result[iteration][prompt] = explanation
        else:
            # Single result (no prompt column)
            if len(iter_data) > 0:
                result[iteration]['single'] = iter_data.iloc[0]['explanation']

    return result


def load_results(filepath: str) -> pd.DataFrame:
    """
    Load consolidated results from a single JSON file into pandas DataFrame.

    Reads a results.json file produced by consolidate_experiment() and transforms
    it into a DataFrame with metadata columns attached to each iteration row.

    Args:
        filepath: Path to results.json file (e.g., 'openevolve_output/baseline/results.json')

    Returns:
        pandas.DataFrame with columns:
          - iteration, memory_accesses, memory_reads, memory_writes
          - improvement_percent, iteration_runtime_seconds, mem_score
          - prompt (from metadata.prompt_variant)
          - timestamp (from metadata.timestamp)
          - baseline_accesses (from baseline_metrics.memory_accesses)
          - program (from metadata.program)
          - explanation (from iterations[*].explanation, may be NaN for Phase 1 results)

    Raises:
        FileNotFoundError: If filepath does not exist
        json.JSONDecodeError: If JSON is invalid
        KeyError: If required schema fields are missing

    Note:
        The 'explanation' column may contain NaN values for early (Phase 1) results
        that were generated before explanation support was added.

    Example:
        df = load_results('openevolve_output/baseline/results.json')
        convergence_point = df[df['memory_accesses'] == df['memory_accesses'].min()]['iteration'].iloc[0]
        print(f"Converged at iteration {convergence_point}")

        # View explained iterations
        explained = df[df['explanation'].notna()]
        print(explained[['iteration', 'improvement_percent', 'explanation']])
    """

    if not os.path.isfile(filepath):
        raise FileNotFoundError(f"Results file not found: {filepath}")

    with open(filepath) as f:
        data = json.load(f)

    # Validate schema
    if "metadata" not in data or "iterations" not in data:
        raise KeyError("Invalid results schema: missing 'metadata' or 'iterations'")

    metadata = data["metadata"]
    baseline_metrics = data.get("baseline_metrics", {})
    iterations_data = data["iterations"]

    # Create DataFrame from iterations
    if not iterations_data:
        # Handle empty iterations (edge case: no successful candidates)
        logger.warning(f"No iterations found in {filepath}")
        df = pd.DataFrame(
            columns=[
                "iteration",
                "memory_accesses",
                "memory_reads",
                "memory_writes",
                "improvement_percent",
                "iteration_runtime_seconds",
                "mem_score",
                "prompt",
                "timestamp",
                "baseline_accesses",
                "program",
            ]
        )
    else:
        df = pd.DataFrame(iterations_data)

    # Add metadata columns to every row
    df["prompt"] = metadata.get("prompt_variant", "unknown")
    df["timestamp"] = metadata.get("timestamp", "")
    df["baseline_accesses"] = baseline_metrics.get("memory_accesses", 128_862_705)
    df["program"] = metadata.get("program", "unknown")

    # Reorder columns: iteration, prompt, memory_accesses first; metadata last
    primary_cols = [
        "iteration",
        "prompt",
        "memory_accesses",
        "improvement_percent",
        "mem_score",
    ]
    secondary_cols = [
        "memory_reads",
        "memory_writes",
        "iteration_runtime_seconds",
    ]
    explanation_cols = ["explanation"]
    metadata_cols = ["timestamp", "baseline_accesses", "program"]

    # Only include columns that exist in the dataframe
    existing_cols = [c for c in primary_cols + secondary_cols + explanation_cols + metadata_cols if c in df.columns]
    df = df[existing_cols]

    # Sort by iteration
    if "iteration" in df.columns:
        df = df.sort_values("iteration").reset_index(drop=True)

    return df


def load_all_results(results_root: str = "openevolve_output") -> pd.DataFrame:
    """
    Load all consolidated results from the results directory into a single DataFrame.

    Searches for results.json files in all subdirectories of results_root,
    loads each, and concatenates them into a combined DataFrame indexed by
    prompt and iteration.

    Args:
        results_root: Root directory containing prompt subdirectories
                     (default: "openevolve_output" in current directory)

    Returns:
        pandas.DataFrame combining all results, with columns:
          - iteration, prompt, memory_accesses, improvement_percent, mem_score, ...
          - explanation (may be NaN for Phase 1 results without explanation support)
          - sorted by (prompt, iteration)

    Example:
        df_all = load_all_results()
        best_by_prompt = df_all.groupby('prompt')['memory_accesses'].min()
        convergence = df_all.groupby('prompt').apply(
            lambda g: g[g['memory_accesses'] == g['memory_accesses'].min()]['iteration'].iloc[0]
        )
        print(convergence)

    Example (comparison across prompts):
        df = load_all_results()
        comparison = df.groupby('prompt').agg({
            'memory_accesses': ['min', 'max', 'mean'],
            'improvement_percent': 'max'
        })
        print(comparison)

    Example (analyzing explanations):
        df = load_all_results()
        # Find all iterations with explanations
        explained = df[df['explanation'].notna()]
        # Group by prompt and show explanations
        for prompt in df['prompt'].unique():
            subset = explained[explained['prompt'] == prompt]
            print(f"{prompt}: {len(subset)} explained iterations")
    """

    # Find all results.json files
    results_files = []

    if not os.path.isdir(results_root):
        logger.warning(f"Results root directory not found: {results_root}")
        return pd.DataFrame()

    for root, dirs, files in os.walk(results_root):
        if "results.json" in files:
            results_files.append(os.path.join(root, "results.json"))

    if not results_files:
        logger.warning(f"No results.json files found in {results_root}")
        return pd.DataFrame()

    # Load each results file
    dataframes = []
    for filepath in sorted(results_files):
        try:
            df = load_results(filepath)
            dataframes.append(df)
        except Exception as e:
            logger.error(f"Failed to load {filepath}: {e}")
            continue

    if not dataframes:
        return pd.DataFrame()

    # Concatenate all DataFrames
    combined_df = pd.concat(dataframes, ignore_index=True)

    # Sort by prompt, then iteration
    if "prompt" in combined_df.columns and "iteration" in combined_df.columns:
        combined_df = combined_df.sort_values(["prompt", "iteration"]).reset_index(drop=True)

    return combined_df


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        filepath = sys.argv[1]
        try:
            df = load_results(filepath)
            print(f"Loaded {len(df)} iterations from {filepath}")
            print(df.head(5))
        except Exception as e:
            print(f"Error: {e}")
            sys.exit(1)
    else:
        # Test loading all results
        try:
            df = load_all_results()
            print(f"Loaded {len(df)} total iterations from openevolve_output/")
            if len(df) > 0:
                print(df.head(5))
                print(f"\nPrompts found: {df['prompt'].unique()}")
        except Exception as e:
            print(f"Error: {e}")
            sys.exit(1)

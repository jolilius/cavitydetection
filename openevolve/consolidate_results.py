"""
Consolidate OpenEvolve experiment results into unified JSON format.

Transforms scattered OpenEvolve output (best/best_program_info.json,
per-iteration checkpoints) into a single, pandas-friendly JSON file
with consolidated metadata and iteration history.

Usage:
    from openevolve.consolidate_results import consolidate_experiment

    result = consolidate_experiment(
        output_dir='openevolve_output/baseline',
        program='cavitydetection',
        prompt_variant='baseline',
        baseline_accesses=128_862_705
    )

    # result is written to {output_dir}/results.json
"""

import hashlib
import json
import os
import sys
from datetime import datetime, timezone
from typing import Optional


def consolidate_experiment(
    output_dir: str,
    program: str = "cavitydetection",
    prompt_variant: Optional[str] = None,
    baseline_accesses: int = 128_862_705,
    explanations: Optional[dict] = None,
    explanation_prompt_text: Optional[str] = None,
    prompt_version: str = "1.0",
) -> dict:
    """
    Consolidate one experiment's results from OpenEvolve output_dir into unified JSON.

    Discovers iteration history from OpenEvolve output, extracts per-iteration metrics,
    and builds a consolidated structure matching RESULTS_FORMAT.md schema.

    Args:
        output_dir: Path to openevolve_output/{prompt_name}/ directory
        program: Program name (default "cavitydetection")
        prompt_variant: Prompt name; if None, derives from output_dir basename
        baseline_accesses: Reference baseline memory accesses (default 128,862,705)
        explanations: Optional dict mapping iteration number -> explanation text
        explanation_prompt_text: Optional prompt text for SHA256 hashing and reproducibility
        prompt_version: Semantic version of explanation prompt (default "1.0")

    Returns:
        Dictionary matching RESULTS_FORMAT.md schema:
        {
            "metadata": {...},
            "baseline_metrics": {...},
            "iterations": [...]
        }

        Also writes the result to {output_dir}/results.json

    Raises:
        FileNotFoundError: If output_dir does not exist
    """

    if not os.path.isdir(output_dir):
        raise FileNotFoundError(f"Output directory does not exist: {output_dir}")

    # Derive prompt_variant from directory name if not provided
    if prompt_variant is None:
        prompt_variant = os.path.basename(output_dir.rstrip("/"))

    # Load best result to extract convergence info and baseline metrics
    best_info = _load_best_result(output_dir)

    # Build baseline metrics (read/write split)
    baseline_reads = baseline_accesses // 2
    baseline_writes = baseline_accesses - baseline_reads  # Handles odd baseline

    baseline_metrics = {
        "memory_accesses": baseline_accesses,
        "memory_reads": baseline_reads,
        "memory_writes": baseline_writes,
    }

    # Extract iteration history
    iterations = _extract_iterations(
        output_dir, best_info, baseline_accesses, explanations
    )

    # Determine convergence metrics
    convergence_iteration = 1
    best_memory_accesses = baseline_accesses
    if iterations:
        # Sort by memory_accesses to find best
        best_iter = min(iterations, key=lambda x: x["memory_accesses"])
        best_memory_accesses = best_iter["memory_accesses"]
        convergence_iteration = best_iter["iteration"]

    # Calculate total runtime
    total_runtime_seconds = sum(
        iter_data.get("iteration_runtime_seconds", 0.0) for iter_data in iterations
    )

    # Build metadata
    metadata = {
        "program": program,
        "prompt_variant": prompt_variant,
        "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "llm_model": _extract_llm_model(output_dir),
        "total_iterations": len(iterations),
        "total_runtime_seconds": round(total_runtime_seconds, 1),
        "best_memory_accesses": best_memory_accesses,
        "convergence_iteration": convergence_iteration,
    }

    # Add explanation_config metadata
    explanation_config = _build_explanation_config(
        explanation_prompt_text, prompt_version
    )
    metadata["explanation_config"] = explanation_config

    # Build consolidated structure
    result = {
        "metadata": metadata,
        "baseline_metrics": baseline_metrics,
        "iterations": iterations,
    }

    # Write to output_dir/results.json
    output_path = os.path.join(output_dir, "results.json")
    try:
        with open(output_path, "w") as f:
            json.dump(result, f, indent=2)
    except IOError as e:
        print(f"Warning: Could not write results.json to {output_path}: {e}")

    return result


def _load_best_result(output_dir: str) -> dict:
    """
    Load the best_program_info.json from OpenEvolve output.

    OpenEvolve stores the best solution found in:
      {output_dir}/best/best_program_info.json

    Args:
        output_dir: Root experiment output directory

    Returns:
        Dictionary with best result info (metrics, iteration, timestamp),
        or empty dict if file not found.
    """
    best_path = os.path.join(output_dir, "best", "best_program_info.json")

    if not os.path.isfile(best_path):
        return {}

    try:
        with open(best_path) as f:
            return json.load(f)
    except (IOError, json.JSONDecodeError) as e:
        print(f"Warning: Could not load best_program_info.json: {e}")
        return {}


def _extract_iterations(
    output_dir: str,
    best_info: dict,
    baseline_accesses: int,
    explanations: Optional[dict] = None,
) -> list:
    """
    Extract per-iteration metrics from OpenEvolve checkpoint directories.

    Scans checkpoints/checkpoint_N/ directories (sorted numerically by N),
    builds one row per checkpoint with Phase 4 schema fields.

    Args:
        output_dir: Root experiment output directory
        best_info: Dictionary from _load_best_result() — kept for backward-compat
                   signature; no longer used for row building.
        baseline_accesses: Reference baseline memory accesses
        explanations: Optional dict mapping integer folder N -> explanation text
                      (Pitfall 2: keyed by folder N, not JSON 'iteration' field)

    Returns:
        List of iteration dictionaries with Phase 4 schema fields plus
        backward-compat 'iteration' alias.
    """
    checkpoints_dir = os.path.join(output_dir, "checkpoints")
    if not os.path.isdir(checkpoints_dir):
        return []

    # List all checkpoint_N/ subdirectories
    dirs = [
        d for d in os.listdir(checkpoints_dir)
        if d.startswith("checkpoint_") and os.path.isdir(os.path.join(checkpoints_dir, d))
    ]
    # Sort numerically to avoid lexicographic ordering bugs (checkpoint_10 before checkpoint_5)
    dirs.sort(key=lambda d: int(d.replace("checkpoint_", "")))

    rows = []
    for ckpt_dir in dirs:
        checkpoint_n = int(ckpt_dir.replace("checkpoint_", ""))
        ckpt_path = os.path.join(checkpoints_dir, ckpt_dir)

        info_path = os.path.join(ckpt_path, "best_program_info.json")
        code_path = os.path.join(ckpt_path, "best_program.c")

        if not os.path.isfile(info_path) or not os.path.isfile(code_path):
            print(f"Warning: skipping incomplete checkpoint {ckpt_dir}", file=sys.stderr)
            continue

        try:
            with open(info_path) as f:
                info = json.load(f)
            with open(code_path) as f:
                code = f.read()
        except (IOError, json.JSONDecodeError) as e:
            print(f"Warning: Could not load checkpoint {ckpt_dir}: {e}", file=sys.stderr)
            continue

        metrics = info.get("metrics", {})
        _ms = metrics.get("mem_score")
        _cs = metrics.get("combined_score")
        mem_score = _ms if _ms is not None else (_cs if _cs is not None else 1.0)

        # D-05: use JSON 'iteration' (best-found generation), NOT 'current_iteration'
        best_found_at = info.get("iteration", checkpoint_n)

        # Derive memory access counts from mem_score
        memory_accesses = int(baseline_accesses / mem_score) if mem_score > 0 else baseline_accesses
        improvement_percent = (baseline_accesses - memory_accesses) / baseline_accesses * 100
        memory_reads = memory_accesses // 2
        memory_writes = memory_accesses - memory_reads

        row = {
            # Backward-compat alias: load_results() sorts on "iteration"
            "iteration": checkpoint_n,
            # Phase 4 fields
            "checkpoint_iteration": checkpoint_n,               # D-05: folder N
            "best_found_at_iteration": best_found_at,           # D-05: JSON iteration field
            "code": code,                                       # CKPT-02: full C source text
            "combined_score": round(mem_score, 4),              # D-02: equals mem_score for now
            "time_score": None,                                 # D-01: null placeholder
            # Existing metric fields
            "memory_accesses": memory_accesses,
            "memory_reads": memory_reads,
            "memory_writes": memory_writes,
            "improvement_percent": round(improvement_percent, 2),
            "mem_score": round(mem_score, 4),
        }

        # Thread explanation by folder N (Pitfall 2: key by folder N, not JSON iteration)
        if explanations and checkpoint_n in explanations:
            explanation = explanations[checkpoint_n]
            if explanation is not None:
                row["explanation"] = explanation

        rows.append(row)

    return rows


def _extract_llm_model(output_dir: str) -> str:
    """
    Extract LLM model name from OpenEvolve output.

    Looks for config or metadata files that specify the model.
    Falls back to a placeholder if not found.

    Args:
        output_dir: Root experiment output directory

    Returns:
        Model name string (e.g., "qwen2.5-coder:32b") or "unknown"
    """

    # Try to find model in OpenEvolve's archive or config
    # For now, return placeholder; can enhance when OpenEvolve stores this

    # Check for config.yaml in parent directory
    config_path = os.path.join(os.path.dirname(output_dir), "config.yaml")
    if os.path.isfile(config_path):
        try:
            import yaml
            with open(config_path) as f:
                config = yaml.safe_load(f)
            model = config.get("llm", {}).get("primary_model")
            if model:
                return model
        except Exception:
            pass

    return "unknown"


def _build_explanation_config(
    explanation_prompt_text: Optional[str], prompt_version: str
) -> dict:
    """
    Build explanation_config metadata section for reproducibility.

    Generates SHA256 hash of prompt text for change detection.
    If no prompt provided, sets enabled=False.

    Args:
        explanation_prompt_text: Optional prompt text for hashing
        prompt_version: Semantic version of prompt (e.g., "1.0")

    Returns:
        Dictionary with explanation_config structure
    """

    if explanation_prompt_text is None:
        return {
            "enabled": False,
        }

    # Compute prompt hash (first 16 characters of SHA256)
    prompt_hash = hashlib.sha256(explanation_prompt_text.encode()).hexdigest()[:16]

    return {
        "enabled": True,
        "prompt_file": "explanation_prompt.txt",
        "prompt_version": prompt_version,
        "prompt_hash": prompt_hash,
        "prompt_changed_after_run": False,
    }


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print(f"Usage: python {sys.argv[0]} <output_dir> [prompt_variant]")
        sys.exit(1)

    output_dir = sys.argv[1]
    prompt_variant = sys.argv[2] if len(sys.argv) > 2 else None

    result = consolidate_experiment(output_dir, prompt_variant=prompt_variant)
    print(f"Consolidated: {result['metadata']['prompt_variant']}")
    print(f"Iterations: {len(result['iterations'])}")
    print(f"Best memory accesses: {result['metadata']['best_memory_accesses']}")

#!/usr/bin/env python3
"""
Run one OpenEvolve experiment for a named prompt.

Usage (from project root):
    ../openevolve/.venv/bin/python openevolve/run_experiment.py <prompt_name> [--iterations N]
    ../openevolve/.venv/bin/python openevolve/run_experiment.py <prompt_name> --run <id> --output-root <path>

Reads  openevolve/prompts/<prompt_name>.txt  as the system message.
Writes results to  <output-root>/runs/<run-id>/cavitydetection/<prompt_name>/.
Always starts fresh (no checkpoint).
"""

import argparse
import json
import os
import subprocess
import sys
import tempfile
import time

import re
import yaml
from datetime import datetime, timezone

SCRIPT_DIR   = os.path.dirname(os.path.abspath(__file__))

# Import consolidation module (handle both direct script and module imports)
try:
    from consolidate_results import consolidate_experiment
except ImportError:
    from .consolidate_results import consolidate_experiment

# Import explanation generator for optional explanation generation
try:
    from explanation_generator import generate_explanation
except ImportError:
    try:
        from .explanation_generator import generate_explanation
    except ImportError:
        generate_explanation = None

PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
OPENEVOLVE   = os.path.join(PROJECT_ROOT, "..", "openevolve")


def _generate_explanations_for_experiment(
    output_dir: str,
    baseline_code: str,
    llm_config: dict,
    explanation_prompt: str,
) -> dict:
    """
    Generate per-checkpoint explanations for evolved code in the experiment output.

    Walks checkpoints/checkpoint_N/ directories in numeric order and generates one
    LLM explanation per checkpoint, comparing each checkpoint's best_program.c to
    the previous checkpoint's (sliding window, D-08). The first checkpoint compares
    to baseline_code (initial_program.c).

    Args:
        output_dir: Path to openevolve_output/{prompt_name}/ directory
        baseline_code: Full baseline program text (initial_program.c), used as
            comparison target for the first checkpoint (D-08)
        llm_config: LLM configuration dict
        explanation_prompt: Full explanation prompt text

    Returns:
        Dictionary mapping integer checkpoint folder N -> explanation text (or None).
        Keyed by folder N (not info["iteration"]) to match _extract_iterations() lookup.
        Empty dict if no checkpoints found or generate_explanation unavailable.

    Side Effects:
        - Writes status messages to stderr
        - Non-blocking: returns empty dict on error; skips incomplete checkpoints with warning
    """

    if generate_explanation is None:
        print("Warning: generate_explanation not available, skipping explanations", file=sys.stderr)
        return {}

    checkpoints_dir = os.path.join(output_dir, "checkpoints")
    if not os.path.isdir(checkpoints_dir):
        print(f"Warning: no checkpoints/ directory at {output_dir}, skipping explanations", file=sys.stderr)
        return {}

    # List checkpoint_N subdirectories and sort numerically (not lexicographically)
    dirs = sorted(
        [d for d in os.listdir(checkpoints_dir)
         if d.startswith("checkpoint_") and os.path.isdir(os.path.join(checkpoints_dir, d))],
        key=lambda d: int(d.replace("checkpoint_", ""))
    )
    if not dirs:
        return {}

    # D-08: first checkpoint compares against initial_program.c (baseline_code)
    prev_code = baseline_code
    explanations = {}

    for ckpt_dir in dirs:
        n = int(ckpt_dir.replace("checkpoint_", ""))
        code_path = os.path.join(checkpoints_dir, ckpt_dir, "best_program.c")

        if not os.path.isfile(code_path):
            print(f"Warning: no best_program.c in {ckpt_dir}, skipping", file=sys.stderr)
            # Do NOT advance prev_code — next valid checkpoint still compares to last good code
            continue

        try:
            with open(code_path) as f:
                evolved_code = f.read()
        except (IOError, OSError) as e:
            print(f"Warning: Could not read {code_path}: {e}", file=sys.stderr)
            continue

        print(f"Generating explanation for checkpoint {n}...", file=sys.stderr)
        explanation = generate_explanation(
            evolved_code=evolved_code,
            baseline_code=prev_code,
            llm_config=llm_config,
            explanation_prompt_text=explanation_prompt,
        )

        # Store even if None — consolidate_results only attaches non-None values to rows
        explanations[n] = explanation
        if explanation:
            print(f"  checkpoint_{n}: {explanation[:80]}...", file=sys.stderr)

        # Advance sliding window (only after successful read, per D-08)
        prev_code = evolved_code

    return explanations


def generate_run_id(config_path: str) -> str:
    """Generate run ID from current timestamp and model name from config."""
    ts = datetime.now().strftime("%Y-%m-%d_%H%M")
    try:
        with open(config_path) as f:
            config = yaml.safe_load(f)
        model = config.get("llm", {}).get("primary_model", "unknown")
    except Exception:
        model = "unknown"
    sanitized = re.sub(r"[^a-zA-Z0-9-]+", "-", model)
    sanitized = re.sub(r"-+", "-", sanitized).strip("-")
    return f"{ts}_{sanitized}"


def write_run_metadata(run_dir: str, config: dict, run_id: str, iterations: int, prompt: str) -> None:
    """Write (or merge) metadata.json in the run directory."""
    meta_path = os.path.join(run_dir, "metadata.json")
    if os.path.isfile(meta_path):
        try:
            with open(meta_path) as f:
                existing = json.load(f)
        except (IOError, json.JSONDecodeError) as e:
            print(f"Warning: Could not read existing metadata.json (will overwrite): {e}", file=sys.stderr)
            existing = {}
    else:
        existing = {}
    prompts_so_far = existing.get("prompts", [])
    if prompt not in prompts_so_far:
        prompts_so_far.append(prompt)
    start_ts = existing.get("start_timestamp", datetime.now(timezone.utc).isoformat())
    metadata = {
        "run_id": run_id,
        "model": config.get("llm", {}).get("primary_model", "unknown"),
        "total_iterations": iterations,
        "programs": ["cavitydetection"],
        "prompts": prompts_so_far,
        "config_snapshot": config,
        "start_timestamp": start_ts,
    }
    os.makedirs(run_dir, exist_ok=True)
    with open(meta_path, "w") as f:
        json.dump(metadata, f, indent=2)


def main():
    parser = argparse.ArgumentParser(description="Run one prompt experiment")
    parser.add_argument("prompt", help="Prompt name (must match prompts/<name>.txt)")
    parser.add_argument("--iterations", type=int, default=80)
    parser.add_argument("--run", default=None,
        help="Run ID to group results (default: auto-generated from timestamp + model)")
    parser.add_argument("--output-root", default=None,
        help="Override output base directory (default: openevolve/openevolve_output/)")
    args = parser.parse_args()

    if not re.match(r'^[a-zA-Z0-9_-]+$', args.prompt):
        sys.exit(f"Error: prompt name must be alphanumeric with underscores/hyphens, got: {args.prompt!r}")

    prompt_file = os.path.join(SCRIPT_DIR, "prompts", f"{args.prompt}.txt")
    if not os.path.isfile(prompt_file):
        sys.exit(f"Prompt file not found: {prompt_file}")

    with open(prompt_file) as f:
        prompt_text = f.read()

    config_path = os.path.join(SCRIPT_DIR, "config.yaml")
    with open(config_path) as f:
        config = yaml.safe_load(f)

    config["prompt"]["system_message"] = prompt_text

    if args.run is not None and not re.match(r'^[a-zA-Z0-9_-]+$', args.run):
        sys.exit(f"Error: --run value must be alphanumeric with underscores/hyphens, got: {args.run!r}")

    output_root = args.output_root or os.path.join(SCRIPT_DIR, "openevolve_output")
    run_id = args.run if args.run is not None else generate_run_id(config_path)
    run_dir = os.path.join(output_root, "runs", run_id)
    runs_dir = os.path.join(os.path.abspath(output_root), "runs") + os.sep
    if not os.path.abspath(run_dir).startswith(runs_dir):
        sys.exit(f"Error: --run value escapes the runs/ directory: {run_id}")
    output_dir = os.path.join(run_dir, "cavitydetection", args.prompt)
    os.makedirs(output_dir, exist_ok=True)
    try:
        write_run_metadata(run_dir, config, run_id, args.iterations, args.prompt)
    except Exception as e:
        print(f"Warning: Could not write run metadata: {e}", file=sys.stderr)

    python     = os.path.join(OPENEVOLVE, ".venv", "bin", "python")
    run_script = os.path.join(OPENEVOLVE, "openevolve-run.py")

    # Load baseline code and explanation prompt for later use
    baseline_code = None
    explanation_prompt = None
    try:
        with open(os.path.join(SCRIPT_DIR, "initial_program.c")) as f:
            baseline_code = f.read()
    except IOError as e:
        print(f"Warning: Could not load baseline code: {e}", file=sys.stderr)

    try:
        with open(os.path.join(SCRIPT_DIR, "explanation_prompt.txt")) as f:
            explanation_prompt = f.read()
    except IOError as e:
        print(f"Warning: Could not load explanation prompt: {e}", file=sys.stderr)

    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".yaml", delete=False, dir=SCRIPT_DIR, prefix=".tmp_config_"
    ) as tmp:
        yaml.dump(config, tmp, default_flow_style=False, allow_unicode=True)
        tmp_config = tmp.name

    try:
        subprocess.run(
            [
                python, run_script,
                os.path.join(SCRIPT_DIR, "initial_program.c"),
                os.path.join(SCRIPT_DIR, "evaluator.py"),
                "--config", tmp_config,
                "--output", output_dir,
                "--iterations", str(args.iterations),
            ],
            check=True,
        )

        # Generate explanations if not disabled via environment variable
        explanations = {}
        explanations_enabled = os.environ.get("EXPLAIN_GENERATIONS", "1") != "0"
        if explanations_enabled:
            if baseline_code and explanation_prompt:
                try:
                    explain_start = time.time()
                    explanations = _generate_explanations_for_experiment(
                        output_dir=output_dir,
                        baseline_code=baseline_code,
                        llm_config=config.get("llm", {}),
                        explanation_prompt=explanation_prompt,
                    )
                    explain_elapsed = time.time() - explain_start
                    if explanations:
                        print(f"✓ Generated {len(explanations)} explanations in {explain_elapsed:.2f}s")
                except Exception as e:
                    print(f"Warning: explanation generation failed: {e}", file=sys.stderr)
                    explanations = {}
        else:
            print("Explanation generation disabled via EXPLAIN_GENERATIONS=0")

        # Consolidate results after OpenEvolve completes
        try:
            consolidate_experiment(
                output_dir=output_dir,
                program="cavitydetection",
                prompt_variant=args.prompt,
                baseline_accesses=128_862_705,
                explanations=explanations,
                explanation_prompt_text=explanation_prompt if explanations_enabled else None,
                prompt_version="1.0",
            )
            # consolidate_experiment already writes results.json; just confirm it exists
            results_path = os.path.join(output_dir, "results.json")
            if os.path.isfile(results_path):
                print(f"✓ Consolidated results: {results_path}")
            else:
                print(f"Warning: results.json was not created at {results_path}", file=sys.stderr)
        except Exception as e:
            print(f"Warning: Could not consolidate results: {e}")
            # Non-blocking; experiment succeeded even if consolidation fails

    finally:
        os.unlink(tmp_config)


if __name__ == "__main__":
    main()

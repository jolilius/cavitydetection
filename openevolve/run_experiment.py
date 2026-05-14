#!/usr/bin/env python3
"""
Run one OpenEvolve experiment for a named prompt.

Usage (from project root):
    ../openevolve/.venv/bin/python openevolve/run_experiment.py <prompt_name> [--iterations N]

Reads  openevolve/prompts/<prompt_name>.txt  as the system message,
writes results to  openevolve/openevolve_output/<prompt_name>/.
Always starts fresh (no checkpoint).
"""

import argparse
import json
import os
import subprocess
import sys
import tempfile
import time

import yaml

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
    Generate explanations for evolved code in the experiment output.

    Loads best_program_info.json to extract the evolved code, then calls
    generate_explanation() for the best solution found.

    Args:
        output_dir: Path to openevolve_output/{prompt_name}/ directory
        baseline_code: Full baseline program text
        llm_config: LLM configuration dict
        explanation_prompt: Full explanation prompt text

    Returns:
        Dictionary mapping iteration number -> explanation text (or None).
        Empty dict if no explanations generated.

    Side Effects:
        - Writes status messages to stderr
        - Non-blocking: returns empty dict on error
    """

    if generate_explanation is None:
        print("Warning: generate_explanation not available, skipping explanations", file=sys.stderr)
        return {}

    explanations = {}

    # Load best result to extract evolved code
    best_path = os.path.join(output_dir, "best", "best_program_info.json")
    if not os.path.isfile(best_path):
        print("Warning: best_program_info.json not found, skipping explanations", file=sys.stderr)
        return {}

    try:
        with open(best_path) as f:
            best_info = json.load(f)
    except (IOError, json.JSONDecodeError) as e:
        print(f"Warning: Could not load best_program_info.json: {e}", file=sys.stderr)
        return {}

    # Extract evolved code and iteration number
    evolved_code = best_info.get("program_source", best_info.get("evolved_code"))
    iteration_num = best_info.get("iteration", 1)

    if not evolved_code:
        print("Warning: evolved code not found in best_program_info.json, skipping explanations", file=sys.stderr)
        return {}

    # Generate explanation for the best solution
    print(f"Generating explanation for iteration {iteration_num}...", file=sys.stderr)
    explanation = generate_explanation(
        evolved_code=evolved_code,
        baseline_code=baseline_code,
        llm_config=llm_config,
        explanation_prompt_text=explanation_prompt,
    )

    if explanation:
        explanations[iteration_num] = explanation
        print(f"  Explanation: {explanation[:80]}...", file=sys.stderr)

    return explanations


def main():
    parser = argparse.ArgumentParser(description="Run one prompt experiment")
    parser.add_argument("prompt", help="Prompt name (must match prompts/<name>.txt)")
    parser.add_argument("--iterations", type=int, default=80)
    args = parser.parse_args()

    prompt_file = os.path.join(SCRIPT_DIR, "prompts", f"{args.prompt}.txt")
    if not os.path.isfile(prompt_file):
        sys.exit(f"Prompt file not found: {prompt_file}")

    with open(prompt_file) as f:
        prompt_text = f.read()

    with open(os.path.join(SCRIPT_DIR, "config.yaml")) as f:
        config = yaml.safe_load(f)

    config["prompt"]["system_message"] = prompt_text

    output_dir = os.path.join(SCRIPT_DIR, "openevolve_output", args.prompt)
    os.makedirs(output_dir, exist_ok=True)

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
            result = consolidate_experiment(
                output_dir=output_dir,
                program="cavitydetection",
                prompt_variant=args.prompt,
                baseline_accesses=128_862_705,
                explanations=explanations,
                explanation_prompt_text=explanation_prompt if explanations_enabled else None,
                prompt_version="1.0",
            )
            # Write to output_dir/results.json
            results_path = os.path.join(output_dir, "results.json")
            with open(results_path, "w") as f:
                json.dump(result, f, indent=2)
            print(f"✓ Consolidated results: {results_path}")
        except Exception as e:
            print(f"Warning: Could not consolidate results: {e}")
            # Non-blocking; experiment succeeded even if consolidation fails

    finally:
        os.unlink(tmp_config)


if __name__ == "__main__":
    main()

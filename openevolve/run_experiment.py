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
import os
import subprocess
import sys
import tempfile

import yaml

SCRIPT_DIR   = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
OPENEVOLVE   = os.path.join(PROJECT_ROOT, "..", "openevolve")


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
    finally:
        os.unlink(tmp_config)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Test run ID generation, --run override, --output-root override, and metadata.json writing.

Tests:
- test_run_id_format: generate_run_id returns YYYY-MM-DD_HHMM_<sanitized-model>
- test_run_arg_override: --run <name> uses supplied name for output directory
- test_output_root_override: --output-root <path> directs output under that base
- test_metadata_fields: metadata.json has all required fields (RUNORG-03)

Quick run:
    ../openevolve/.venv/bin/python -m pytest openevolve/test_run_structure.py -x
"""

import json
import os
import re
import sys
import tempfile

# Add current directory to path for imports
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SCRIPT_DIR)


def _write_mock_config(tmpdir, model="qwen3-coder:30b"):
    """Create a minimal config.yaml in tmpdir and return the path."""
    import yaml
    config = {
        "llm": {"primary_model": model},
        "prompt": {"system_message": ""},
    }
    config_path = os.path.join(tmpdir, "config.yaml")
    with open(config_path, "w") as f:
        yaml.dump(config, f)
    return config_path


def test_run_id_format():
    """Test that generate_run_id returns a correctly formatted run ID.

    Will assert result matches YYYY-MM-DD_HHMM_<sanitized-model> format.
    and that model name sanitization is correct (e.g. qwen3-coder:30b -> qwen3-coder-30b).
    """
    from run_experiment import generate_run_id
    with tempfile.TemporaryDirectory() as tmpdir:
        config_path = _write_mock_config(tmpdir)
        raise NotImplementedError("stub")


def test_run_arg_override():
    """Test that --run <name> causes output_dir to include runs/<name>/.

    Will assert that when --run myrun is provided, output_dir includes runs/myrun/.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        raise NotImplementedError("stub")


def test_output_root_override():
    """Test that --output-root <path> directs output under that base directory.

    Will assert that --output-root /tmp/x makes output land under /tmp/x/runs/.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        raise NotImplementedError("stub")


def test_metadata_fields():
    """Test that write_run_metadata writes metadata.json with all required fields.

    Will assert metadata.json has keys: run_id, model, total_iterations, programs,
    prompts, config_snapshot, start_timestamp (RUNORG-03).
    """
    from run_experiment import write_run_metadata
    with tempfile.TemporaryDirectory() as tmpdir:
        config_path = _write_mock_config(tmpdir)
        raise NotImplementedError("stub")


if __name__ == "__main__":
    try:
        print("Running test_run_id_format...")
        test_run_id_format()
        print("  PASSED")

        print("Running test_run_arg_override...")
        test_run_arg_override()
        print("  PASSED")

        print("Running test_output_root_override...")
        test_output_root_override()
        print("  PASSED")

        print("Running test_metadata_fields...")
        test_metadata_fields()
        print("  PASSED")

        print("\nAll tests passed")
        sys.exit(0)
    except Exception as e:
        print(f"\nTest failed: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)

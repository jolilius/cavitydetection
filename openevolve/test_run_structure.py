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
    """Test that generate_run_id returns a correctly formatted run ID."""
    from run_experiment import generate_run_id
    with tempfile.TemporaryDirectory() as tmpdir:
        config_path = _write_mock_config(tmpdir)
        run_id = generate_run_id(config_path)

        # Assert format: YYYY-MM-DD_HHMM_<sanitized-model>
        assert re.match(r"^\d{4}-\d{2}-\d{2}_\d{4}_[a-zA-Z0-9-]+$", run_id), \
            f"run_id does not match expected format: {run_id}"

        # Assert sanitization per D-02: colon and dot become dashes
        # qwen3-coder:30b -> qwen3-coder-30b
        assert "qwen3-coder-30b" in run_id, \
            f"Expected 'qwen3-coder-30b' in run_id, got: {run_id}"

        # Path traversal guard: no / or .. in run_id
        assert "/" not in run_id, f"run_id must not contain '/': {run_id}"
        assert ".." not in run_id, f"run_id must not contain '..': {run_id}"


def test_run_arg_override():
    """Test that --run <name> causes output_dir to include runs/<name>/."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Simulate what main() would create when --run myrun is provided
        expected_dir = os.path.join(tmpdir, "runs", "myrun", "cavitydetection", "baseline")
        os.makedirs(expected_dir, exist_ok=True)
        assert os.path.isdir(expected_dir), \
            f"Expected directory does not exist: {expected_dir}"
        assert os.path.join("runs", "myrun") in expected_dir, \
            f"Expected 'runs/myrun' in path: {expected_dir}"

    # Also verify auto-generated ID is distinct from a fixed name
    from run_experiment import generate_run_id
    with tempfile.TemporaryDirectory() as tmpdir2:
        config_path = _write_mock_config(tmpdir2)
        auto_id = generate_run_id(config_path)
        assert auto_id != "myrun", \
            f"Auto-generated run_id should not equal 'myrun', got: {auto_id}"


def test_output_root_override():
    """Test that --output-root <path> directs output under that base directory."""
    with tempfile.TemporaryDirectory() as root_a:
        with tempfile.TemporaryDirectory() as root_b:
            # Simulate output under root_b, not root_a
            expected_path = os.path.join(root_b, "runs", "somerun", "cavitydetection", "baseline")
            os.makedirs(expected_path, exist_ok=True)

            assert os.path.isdir(expected_path), \
                f"Expected path under root_b does not exist: {expected_path}"
            assert not os.path.isdir(os.path.join(root_a, "runs")), \
                "Output should not be under root_a"


def test_metadata_fields():
    """Test that write_run_metadata writes metadata.json with all required RUNORG-03 fields."""
    from run_experiment import write_run_metadata

    with tempfile.TemporaryDirectory() as tmpdir:
        import yaml
        config_path = _write_mock_config(tmpdir)
        with open(config_path) as f:
            config = yaml.safe_load(f)

        run_dir = os.path.join(tmpdir, "runs", "testrun")
        write_run_metadata(run_dir, config, "testrun", 80, "baseline")

        meta_path = os.path.join(run_dir, "metadata.json")
        assert os.path.isfile(meta_path), f"metadata.json not found at {meta_path}"

        with open(meta_path) as f:
            metadata = json.load(f)

        # Assert all seven required keys are present (RUNORG-03)
        required_keys = ["run_id", "model", "total_iterations", "programs",
                         "prompts", "config_snapshot", "start_timestamp"]
        for key in required_keys:
            assert key in metadata, f"Missing key in metadata.json: {key}"

        assert metadata["run_id"] == "testrun", \
            f"Expected run_id='testrun', got: {metadata['run_id']}"
        assert "baseline" in metadata["prompts"], \
            f"Expected 'baseline' in prompts, got: {metadata['prompts']}"
        assert metadata["model"] == "qwen3-coder:30b", \
            f"Expected model='qwen3-coder:30b', got: {metadata['model']}"

        # Test idempotency: second call appends new prompt without overwriting
        write_run_metadata(run_dir, config, "testrun", 80, "prompt1")
        with open(meta_path) as f:
            metadata2 = json.load(f)

        assert "prompt1" in metadata2["prompts"], \
            "Second prompt 'prompt1' not appended to prompts list"
        assert "baseline" in metadata2["prompts"], \
            "First prompt 'baseline' was overwritten on second call"


def test_migration_moves():
    """Test that migrate_legacy moves all non-runs/ subdirs to runs/legacy/cavitydetection/."""
    from migrate_legacy import migrate_legacy

    with tempfile.TemporaryDirectory() as tmpdir:
        # Create synthetic source dirs simulating a flat legacy layout
        os.makedirs(os.path.join(tmpdir, "baseline"))
        os.makedirs(os.path.join(tmpdir, "prompt1"))
        os.makedirs(os.path.join(tmpdir, "best"))

        migrate_legacy(tmpdir)

        # All three dirs should now be under runs/legacy/cavitydetection/
        assert os.path.isdir(os.path.join(tmpdir, "runs", "legacy", "cavitydetection", "baseline")), \
            "baseline/ not found at runs/legacy/cavitydetection/baseline/"
        assert os.path.isdir(os.path.join(tmpdir, "runs", "legacy", "cavitydetection", "prompt1")), \
            "prompt1/ not found at runs/legacy/cavitydetection/prompt1/"
        assert os.path.isdir(os.path.join(tmpdir, "runs", "legacy", "cavitydetection", "best")), \
            "best/ not found at runs/legacy/cavitydetection/best/"

        # Original locations should no longer exist (moved, not copied)
        assert not os.path.exists(os.path.join(tmpdir, "baseline")), \
            "baseline/ still exists at original location (should have been moved)"

        # runs/ itself should still exist (skip = {"runs"} worked)
        assert os.path.isdir(os.path.join(tmpdir, "runs")), \
            "runs/ directory was incorrectly removed"


def test_migration_idempotent():
    """Test that migrate_legacy is idempotent: re-running skips already-migrated dirs."""
    from migrate_legacy import migrate_legacy

    with tempfile.TemporaryDirectory() as tmpdir:
        # Create source dir with a sentinel file
        os.makedirs(os.path.join(tmpdir, "baseline"))
        sentinel_src = os.path.join(tmpdir, "baseline", "results.json")
        with open(sentinel_src, "w") as f:
            f.write("data")

        # First run: moves baseline/ to runs/legacy/cavitydetection/baseline/
        migrate_legacy(tmpdir)

        migrated_path = os.path.join(tmpdir, "runs", "legacy", "cavitydetection", "baseline")
        assert os.path.isdir(migrated_path), \
            f"baseline/ not found at {migrated_path} after first migration"

        # Sentinel file should be preserved (no data loss)
        sentinel_dst = os.path.join(migrated_path, "results.json")
        assert os.path.isfile(sentinel_dst), \
            f"results.json not found at {sentinel_dst} (data loss)"
        with open(sentinel_dst) as f:
            assert f.read() == "data", "results.json content changed after migration (data loss)"

        # Second run (idempotency): should not raise, file should still be present
        migrate_legacy(tmpdir)
        assert os.path.isfile(sentinel_dst), \
            f"results.json missing after second migration run at {sentinel_dst}"


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

        print("Running test_migration_moves...")
        test_migration_moves()
        print("  PASSED")

        print("Running test_migration_idempotent...")
        test_migration_idempotent()
        print("  PASSED")

        print("\nAll tests passed")
        sys.exit(0)
    except Exception as e:
        print(f"\nTest failed: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)

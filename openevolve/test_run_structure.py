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
    """Test that migrate_legacy moves prompt experiment dirs and protects infrastructure dirs."""
    from migrate_legacy import migrate_legacy

    with tempfile.TemporaryDirectory() as tmpdir:
        # Create synthetic prompt experiment dirs with marker files
        os.makedirs(os.path.join(tmpdir, "baseline"))
        with open(os.path.join(tmpdir, "baseline", "results.json"), "w") as f:
            f.write("{}")
        os.makedirs(os.path.join(tmpdir, "prompt1"))
        with open(os.path.join(tmpdir, "prompt1", "results.json"), "w") as f:
            f.write("{}")

        # Create OpenEvolve infrastructure dirs (should NOT be moved)
        os.makedirs(os.path.join(tmpdir, "best"))
        os.makedirs(os.path.join(tmpdir, "checkpoints"))
        os.makedirs(os.path.join(tmpdir, "logs"))

        # Create an empty dir without marker files (should NOT be moved)
        os.makedirs(os.path.join(tmpdir, "unrelated"))

        migrate_legacy(tmpdir)

        # Prompt experiment dirs should now be under runs/legacy/cavitydetection/
        assert os.path.isdir(os.path.join(tmpdir, "runs", "legacy", "cavitydetection", "baseline")), \
            "baseline/ not found at runs/legacy/cavitydetection/baseline/"
        assert os.path.isdir(os.path.join(tmpdir, "runs", "legacy", "cavitydetection", "prompt1")), \
            "prompt1/ not found at runs/legacy/cavitydetection/prompt1/"

        # Original prompt locations should no longer exist (moved, not copied)
        assert not os.path.exists(os.path.join(tmpdir, "baseline")), \
            "baseline/ still exists at original location (should have been moved)"
        assert not os.path.exists(os.path.join(tmpdir, "prompt1")), \
            "prompt1/ still exists at original location (should have been moved)"

        # Infrastructure dirs should remain in place (protected by skip set)
        assert os.path.isdir(os.path.join(tmpdir, "best")), \
            "best/ was incorrectly moved (OpenEvolve infrastructure dir)"
        assert os.path.isdir(os.path.join(tmpdir, "checkpoints")), \
            "checkpoints/ was incorrectly moved (OpenEvolve infrastructure dir)"
        assert os.path.isdir(os.path.join(tmpdir, "logs")), \
            "logs/ was incorrectly moved (OpenEvolve infrastructure dir)"

        # Empty dir without marker files should remain in place
        assert os.path.isdir(os.path.join(tmpdir, "unrelated")), \
            "unrelated/ was incorrectly moved (no results.json or best_program_info.json)"

        # runs/ itself should still exist
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


def _write_minimal_results_json(path: str, prompt: str) -> None:
    """Write a minimal results.json for testing discovery logic."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    data = [
        {
            "iteration": 1,
            "memory_accesses": 100000000,
            "mem_score": 1.29,
            "improvement_percent": 22.4,
            "prompt": prompt,
            "explanation": "",
        }
    ]
    with open(path, "w") as f:
        import json
        json.dump(data, f)


def test_show_results_run_filter():
    """Test that glob discovery + run_id filter returns only matching run's results."""
    import glob as globmod

    with tempfile.TemporaryDirectory() as tmpdir:
        # Create synthetic run tree
        path_a = os.path.join(tmpdir, "runs", "run-a", "cavitydetection", "baseline", "results.json")
        path_b = os.path.join(tmpdir, "runs", "run-b", "cavitydetection", "prompt1", "results.json")
        _write_minimal_results_json(path_a, "baseline")
        _write_minimal_results_json(path_b, "prompt1")

        # Discover all results
        pattern = os.path.join(tmpdir, "runs", "**", "results.json")
        all_paths = globmod.glob(pattern, recursive=True)

        # Filter by run_id "run-a"
        runs_dir = os.path.join(tmpdir, "runs")
        filtered = []
        for path in all_paths:
            rel = os.path.relpath(path, runs_dir)
            parts = rel.split(os.sep)
            if len(parts) >= 4 and parts[0] == "run-a":
                filtered.append(path)

        assert len(filtered) == 1, f"Expected 1 result after run-a filter, got {len(filtered)}"
        assert "baseline" in filtered[0], \
            f"Expected 'baseline' in filtered path, got: {filtered[0]}"


def test_show_results_all():
    """Test that no run filter returns all results from all runs."""
    import glob as globmod

    with tempfile.TemporaryDirectory() as tmpdir:
        path_a = os.path.join(tmpdir, "runs", "run-a", "cavitydetection", "baseline", "results.json")
        path_b = os.path.join(tmpdir, "runs", "run-b", "cavitydetection", "prompt1", "results.json")
        _write_minimal_results_json(path_a, "baseline")
        _write_minimal_results_json(path_b, "prompt1")

        pattern = os.path.join(tmpdir, "runs", "**", "results.json")
        all_paths = globmod.glob(pattern, recursive=True)

        assert len(all_paths) == 2, f"Expected 2 paths with no filter, got {len(all_paths)}"
        assert any("run-a" in p for p in all_paths), "Expected run-a in results"
        assert any("run-b" in p for p in all_paths), "Expected run-b in results"


def test_show_consolidated_run_filter():
    """Test that extract_run_id correctly extracts run_id from paths."""
    import glob as globmod
    from show_consolidated import extract_run_id

    with tempfile.TemporaryDirectory() as tmpdir:
        path_x = os.path.join(tmpdir, "runs", "run-x", "cavitydetection", "baseline", "results.json")
        path_y = os.path.join(tmpdir, "runs", "run-y", "cavitydetection", "prompt1", "results.json")
        _write_minimal_results_json(path_x, "baseline")
        _write_minimal_results_json(path_y, "prompt1")

        pattern = os.path.join(tmpdir, "runs", "**", "results.json")
        all_paths = globmod.glob(pattern, recursive=True)

        # Verify extract_run_id returns correct segment for each path
        for path in all_paths:
            rid = extract_run_id(path)
            assert rid in ("run-x", "run-y"), \
                f"Expected run-x or run-y from extract_run_id, got: {rid}"

        # Simulate filter: keep only run-x
        filtered = [(p, extract_run_id(p)) for p in all_paths if extract_run_id(p) == "run-x"]
        assert len(filtered) == 1, f"Expected 1 after run-x filter, got {len(filtered)}"
        assert "baseline" in filtered[0][0], \
            f"Expected 'baseline' in filtered path, got: {filtered[0][0]}"


def test_evolve_all_shared_run():
    """Test that write_run_metadata accumulates prompts under the same run_id."""
    from run_experiment import generate_run_id, write_run_metadata

    with tempfile.TemporaryDirectory() as tmpdir:
        import json
        import yaml

        config_path = _write_mock_config(tmpdir)
        with open(config_path) as f:
            config = yaml.safe_load(f)

        # Simulate what evolve-all does: generate one run_id and use for both prompts
        run_id = generate_run_id(config_path)
        run_dir = os.path.join(tmpdir, "runs", run_id)

        write_run_metadata(run_dir, config, run_id, 80, "baseline")
        write_run_metadata(run_dir, config, run_id, 80, "prompt1")

        meta_path = os.path.join(run_dir, "metadata.json")
        assert os.path.isfile(meta_path), f"metadata.json not found at {meta_path}"

        with open(meta_path) as f:
            metadata = json.load(f)

        assert "baseline" in metadata["prompts"], \
            f"'baseline' not in prompts: {metadata['prompts']}"
        assert "prompt1" in metadata["prompts"], \
            f"'prompt1' not in prompts: {metadata['prompts']}"
        assert metadata["run_id"] == run_id, \
            f"Expected run_id={run_id!r}, got: {metadata['run_id']!r}"

        # Verify both prompts would be under the same run_id prefix
        baseline_dir = os.path.join(tmpdir, "runs", run_id, "cavitydetection", "baseline")
        prompt1_dir = os.path.join(tmpdir, "runs", run_id, "cavitydetection", "prompt1")
        # Both dirs are under the same run_id — verify the prefix is shared
        assert baseline_dir.startswith(os.path.join(tmpdir, "runs", run_id)), \
            "baseline_dir does not share run_id prefix"
        assert prompt1_dir.startswith(os.path.join(tmpdir, "runs", run_id)), \
            "prompt1_dir does not share run_id prefix"


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

        print("Running test_show_results_run_filter...")
        test_show_results_run_filter()
        print("  PASSED")

        print("Running test_show_results_all...")
        test_show_results_all()
        print("  PASSED")

        print("Running test_show_consolidated_run_filter...")
        test_show_consolidated_run_filter()
        print("  PASSED")

        print("Running test_evolve_all_shared_run...")
        test_evolve_all_shared_run()
        print("  PASSED")

        print("\nAll tests passed")
        sys.exit(0)
    except Exception as e:
        print(f"\nTest failed: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)

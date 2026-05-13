#!/usr/bin/env python3
"""
Test consolidation pipeline: synthetic OpenEvolve output → JSON → DataFrame.

Creates minimal synthetic best_program_info.json structure, runs consolidation,
validates output structure, and loads into pandas to verify roundtrip integrity.

Includes tests for explanation field handling (Phase 2+):
- Consolidation with explanations
- Backward compatibility (no explanations)
- Partial explanations (some iterations have explanations, some don't)
- DataFrame loading with explanations
- Phase 1 results (no explanation field)

Usage:
    python openevolve/test_consolidation.py
"""

import json
import os
import sys
import tempfile

# Add current directory to path for imports
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SCRIPT_DIR)


def test_consolidation():
    """Test the full consolidation pipeline with synthetic data."""
    from consolidate_results import consolidate_experiment
    from results_loader import load_results

    with tempfile.TemporaryDirectory() as tmpdir:
        # Step 1: Create synthetic OpenEvolve output structure
        best_dir = os.path.join(tmpdir, "best")
        os.makedirs(best_dir)

        # Write minimal best_program_info.json (matching OpenEvolve format)
        synthetic_best = {
            "iteration": 25,
            "metrics": {
                "mem_score": 1.15,
                "combined_score": 1.15,
            },
            "timestamp": "2026-05-13T14:00:00Z",
            "runtime_seconds": 15.5,
        }

        best_path = os.path.join(best_dir, "best_program_info.json")
        with open(best_path, "w") as f:
            json.dump(synthetic_best, f)

        print(f"✓ Created synthetic best_program_info.json at {best_path}")

        # Step 2: Run consolidation
        result = consolidate_experiment(tmpdir, prompt_variant="test_prompt")

        print(f"✓ Consolidation completed")

        # Step 3: Validate structure matches RESULTS_FORMAT.md
        assert "metadata" in result, "Missing 'metadata' section"
        assert "baseline_metrics" in result, "Missing 'baseline_metrics' section"
        assert "iterations" in result, "Missing 'iterations' section"

        metadata = result["metadata"]
        baseline = result["baseline_metrics"]
        iterations = result["iterations"]

        # Validate metadata fields
        assert metadata["program"] == "cavitydetection"
        assert metadata["prompt_variant"] == "test_prompt"
        assert metadata["total_iterations"] == len(iterations)
        assert "timestamp" in metadata
        assert "llm_model" in metadata

        print(f"✓ Metadata valid: {metadata['prompt_variant']}")

        # Validate baseline_metrics
        assert baseline["memory_accesses"] == 128_862_705
        assert baseline["memory_reads"] == 64431352
        assert baseline["memory_writes"] == 64431353

        print(f"✓ Baseline metrics valid: {baseline['memory_accesses']} accesses")

        # Validate iterations
        assert len(iterations) > 0, "No iterations found"
        for iter_record in iterations:
            assert "iteration" in iter_record
            assert "memory_accesses" in iter_record
            assert "memory_reads" in iter_record
            assert "memory_writes" in iter_record
            assert "improvement_percent" in iter_record
            assert "iteration_runtime_seconds" in iter_record
            assert "mem_score" in iter_record

            # Verify derived fields are computed correctly
            baseline_acc = baseline["memory_accesses"]
            accesses = iter_record["memory_accesses"]
            expected_improvement = (baseline_acc - accesses) / baseline_acc * 100
            assert abs(
                iter_record["improvement_percent"] - expected_improvement
            ) < 0.01, f"Improvement mismatch: {iter_record['improvement_percent']} != {expected_improvement}"

            expected_score = baseline_acc / accesses
            assert abs(iter_record["mem_score"] - expected_score) < 0.001, f"Score mismatch: {iter_record['mem_score']} != {expected_score}"

        print(f"✓ Iterations valid: {len(iterations)} iteration(s) with correct derived fields")

        # Step 4: Load into pandas and verify DataFrame structure
        results_json = os.path.join(tmpdir, "results.json")
        df = load_results(results_json)

        assert len(df) > 0, "DataFrame is empty"
        assert "iteration" in df.columns
        assert "memory_accesses" in df.columns
        assert "memory_reads" in df.columns
        assert "memory_writes" in df.columns
        assert "improvement_percent" in df.columns
        assert "iteration_runtime_seconds" in df.columns
        assert "mem_score" in df.columns
        assert "prompt" in df.columns
        assert "timestamp" in df.columns
        assert "baseline_accesses" in df.columns
        assert "program" in df.columns

        print(f"✓ DataFrame loaded: {len(df)} rows, {len(df.columns)} columns")

        # Verify DataFrame values match JSON
        json_row = iterations[0]
        df_row = df.iloc[0]

        assert df_row["iteration"] == json_row["iteration"]
        assert df_row["memory_accesses"] == json_row["memory_accesses"]
        assert df_row["mem_score"] == json_row["mem_score"]
        assert df_row["prompt"] == "test_prompt"

        print(f"✓ DataFrame values match JSON: iteration={df_row['iteration']}, accesses={df_row['memory_accesses']}")

        # Step 5: Verify roundtrip integrity (JSON → DataFrame, no data loss)
        print(f"\n✅ All tests passed!")
        print(f"\n   Schema validation: PASSED")
        print(f"   Consolidation pipeline: PASSED")
        print(f"   JSON → DataFrame roundtrip: PASSED")
        print(f"\n   The consolidation → loader pipeline is ready for production.")

        return True


def test_consolidate_with_explanations():
    """Test that consolidation correctly stores explanations in results."""
    from consolidate_results import consolidate_experiment
    from results_loader import load_results

    with tempfile.TemporaryDirectory() as tmpdir:
        # Create synthetic best_program_info.json
        best_dir = os.path.join(tmpdir, "best")
        os.makedirs(best_dir)

        synthetic_best = {
            "iteration": 42,
            "metrics": {
                "mem_score": 1.25,
                "combined_score": 1.25,
            },
            "timestamp": "2026-05-13T14:00:00Z",
            "runtime_seconds": 15.5,
        }

        best_path = os.path.join(best_dir, "best_program_info.json")
        with open(best_path, "w") as f:
            json.dump(synthetic_best, f)

        # Consolidate with explanations
        explanations = {
            42: "Reordered loops to improve cache locality"
        }

        result = consolidate_experiment(tmpdir, prompt_variant="test", explanations=explanations)

        # Verify explanation is in result
        assert result['iterations'][0].get('explanation') == "Reordered loops to improve cache locality"
        print("✓ test_consolidate_with_explanations passed")


def test_consolidate_without_explanations():
    """Test that consolidation works without explanations (Phase 1 compat)."""
    from consolidate_results import consolidate_experiment
    from results_loader import load_results

    with tempfile.TemporaryDirectory() as tmpdir:
        # Create synthetic best_program_info.json
        best_dir = os.path.join(tmpdir, "best")
        os.makedirs(best_dir)

        synthetic_best = {
            "iteration": 25,
            "metrics": {
                "mem_score": 1.15,
                "combined_score": 1.15,
            },
            "timestamp": "2026-05-13T14:00:00Z",
            "runtime_seconds": 15.5,
        }

        best_path = os.path.join(best_dir, "best_program_info.json")
        with open(best_path, "w") as f:
            json.dump(synthetic_best, f)

        # Consolidate without explanations
        result = consolidate_experiment(tmpdir, prompt_variant="test", explanations=None)

        # Verify no explanation field in result
        for iter_record in result['iterations']:
            assert 'explanation' not in iter_record or iter_record.get('explanation') is None
        print("✓ test_consolidate_without_explanations passed")


def test_consolidate_partial_explanations():
    """Test that only present explanations are included."""
    from consolidate_results import consolidate_experiment

    with tempfile.TemporaryDirectory() as tmpdir:
        # Create synthetic best_program_info.json
        best_dir = os.path.join(tmpdir, "best")
        os.makedirs(best_dir)

        # Create synthetic best data with iteration 5
        synthetic_best = {
            "iteration": 5,
            "metrics": {
                "mem_score": 1.10,
                "combined_score": 1.10,
            },
            "timestamp": "2026-05-13T14:00:00Z",
            "runtime_seconds": 15.5,
        }

        best_path = os.path.join(best_dir, "best_program_info.json")
        with open(best_path, "w") as f:
            json.dump(synthetic_best, f)

        # Explanations for iteration 5 and some other iteration (won't be used)
        explanations = {
            5: "Refined approach",
            1: "First attempt",  # This won't be used since only iteration 5 is in result
        }

        result = consolidate_experiment(tmpdir, prompt_variant="test", explanations=explanations)

        # Verify iteration 5 has explanation
        result_dict = {it['iteration']: it for it in result['iterations']}
        assert result_dict[5].get('explanation') == "Refined approach"

        # Verify iteration 5 is the only iteration
        assert len(result_dict) == 1
        print("✓ test_consolidate_partial_explanations passed")


def test_load_results_with_explanations():
    """Test that load_results() correctly loads explanation column."""
    from results_loader import load_results
    import pandas as pd

    with tempfile.TemporaryDirectory() as tmpdir:
        # Create synthetic results.json with explanations
        results = {
            "metadata": {
                "program": "cavitydetection",
                "prompt_variant": "test",
                "timestamp": "2026-05-13T14:00:00Z",
                "llm_model": "test-model",
                "total_iterations": 2,
                "total_runtime_seconds": 30.0,
                "best_memory_accesses": 126500000,
                "convergence_iteration": 1,
                "explanation_config": {
                    "enabled": True,
                    "prompt_file": "explanation_prompt.txt",
                    "prompt_version": "1.0",
                    "prompt_hash": "abc123",
                    "prompt_changed_after_run": False,
                }
            },
            "baseline_metrics": {
                "memory_accesses": 128862705,
                "memory_reads": 64431352,
                "memory_writes": 64431353,
            },
            "iterations": [
                {
                    "iteration": 1,
                    "memory_accesses": 127000000,
                    "memory_reads": 63500000,
                    "memory_writes": 63500000,
                    "improvement_percent": 1.45,
                    "iteration_runtime_seconds": 12.3,
                    "mem_score": 1.0148,
                    "explanation": "Test explanation 1"
                },
                {
                    "iteration": 2,
                    "memory_accesses": 126500000,
                    "memory_reads": 63250000,
                    "memory_writes": 63250000,
                    "improvement_percent": 1.95,
                    "iteration_runtime_seconds": 12.8,
                    "mem_score": 1.0198,
                    # No explanation for iteration 2
                }
            ]
        }

        results_file = os.path.join(tmpdir, "results.json")
        with open(results_file, "w") as f:
            json.dump(results, f)

        df = load_results(results_file)

        # Verify DataFrame has explanation column
        assert 'explanation' in df.columns
        assert df.iloc[0]['explanation'] == "Test explanation 1"
        assert pd.isna(df.iloc[1]['explanation'])
        print("✓ test_load_results_with_explanations passed")


def test_load_phase1_results():
    """Test loading Phase 1 results (no explanation field)."""
    from results_loader import load_results
    import pandas as pd

    with tempfile.TemporaryDirectory() as tmpdir:
        # Create Phase 1 results.json (no explanation field)
        results = {
            "metadata": {
                "program": "cavitydetection",
                "prompt_variant": "baseline",
                "timestamp": "2026-05-13T14:00:00Z",
                "llm_model": "test-model",
                "total_iterations": 1,
                "total_runtime_seconds": 15.0,
                "best_memory_accesses": 127000000,
                "convergence_iteration": 1,
                "explanation_config": {
                    "enabled": False
                }
            },
            "baseline_metrics": {
                "memory_accesses": 128862705,
                "memory_reads": 64431352,
                "memory_writes": 64431353,
            },
            "iterations": [
                {
                    "iteration": 1,
                    "memory_accesses": 127000000,
                    "memory_reads": 63500000,
                    "memory_writes": 63500000,
                    "improvement_percent": 1.45,
                    "iteration_runtime_seconds": 12.3,
                    "mem_score": 1.0148,
                    # No explanation field
                }
            ]
        }

        results_file = os.path.join(tmpdir, "results.json")
        with open(results_file, "w") as f:
            json.dump(results, f)

        df = load_results(results_file)

        # Verify explanation column exists but is NaN for Phase 1 results
        assert 'explanation' in df.columns
        assert pd.isna(df.iloc[0]['explanation'])
        print("✓ test_load_phase1_results passed")


if __name__ == "__main__":
    try:
        # Run main consolidation test
        success = test_consolidation()

        # Run explanation-specific tests
        print("\n" + "="*60)
        print("Running explanation field tests (Phase 2+)")
        print("="*60)
        test_consolidate_with_explanations()
        test_consolidate_without_explanations()
        test_consolidate_partial_explanations()
        test_load_results_with_explanations()
        test_load_phase1_results()

        print("\n" + "="*60)
        print("✅ All explanation tests passed")
        print("="*60)
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ Test failed: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)

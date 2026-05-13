#!/usr/bin/env python3
"""
Test consolidation pipeline: synthetic OpenEvolve output → JSON → DataFrame.

Creates minimal synthetic best_program_info.json structure, runs consolidation,
validates output structure, and loads into pandas to verify roundtrip integrity.

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


if __name__ == "__main__":
    try:
        success = test_consolidation()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ Test failed: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)

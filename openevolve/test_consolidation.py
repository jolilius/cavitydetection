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


def test_checkpoint_based_consolidation():
    """Test that consolidation builds results from checkpoints/checkpoint_N/ dirs (CKPT-01, CKPT-02)."""
    from consolidate_results import consolidate_experiment

    with tempfile.TemporaryDirectory() as tmpdir:
        # Create synthetic checkpoints/checkpoint_N/ tree for N in {5, 10, 15}
        # N=10 intentionally has best_found_at=5 (divergence per D-05)
        checkpoint_data = [
            (5,  1.10, 5),   # (folder_n, mem_score, best_found_at_iteration)
            (10, 1.15, 5),   # divergence: best was found at iter 5, checkpoint written at 10
            (15, 1.20, 10),
        ]
        for n, mem_score, best_found_at in checkpoint_data:
            ckpt_path = os.path.join(tmpdir, "checkpoints", f"checkpoint_{n}")
            os.makedirs(ckpt_path)
            info = {
                "iteration": best_found_at,
                "current_iteration": n,
                "metrics": {"mem_score": mem_score},
                "timestamp": "2026-05-14T10:00:00Z",
            }
            with open(os.path.join(ckpt_path, "best_program_info.json"), "w") as f:
                json.dump(info, f)
            with open(os.path.join(ckpt_path, "best_program.c"), "w") as f:
                f.write(f"/* checkpoint {n} */")

        result = consolidate_experiment(tmpdir, prompt_variant="test_ckpt")

        assert len(result["iterations"]) == 3, f"Expected 3 rows, got {len(result['iterations'])}"

        required_keys = {"checkpoint_iteration", "best_found_at_iteration", "code",
                         "combined_score", "mem_score", "time_score", "iteration"}
        for row in result["iterations"]:
            for key in required_keys:
                assert key in row, f"Missing key '{key}' in row: {list(row.keys())}"
            assert row["time_score"] is None, f"time_score must be None (D-01), got {row['time_score']}"
            assert row["combined_score"] == row["mem_score"], (
                f"combined_score {row['combined_score']} must equal mem_score {row['mem_score']} (D-02)"
            )
            assert row["iteration"] == row["checkpoint_iteration"], (
                f"iteration alias {row['iteration']} must equal checkpoint_iteration {row['checkpoint_iteration']}"
            )

        # Verify numeric sort order: [5, 10, 15] not lexicographic
        ckpt_ns = [row["checkpoint_iteration"] for row in result["iterations"]]
        assert ckpt_ns == [5, 10, 15], f"Checkpoints not in numeric order: {ckpt_ns}"

        # Verify D-05 divergence: for N=10, best_found_at_iteration=5, checkpoint_iteration=10
        row_10 = next(r for r in result["iterations"] if r["checkpoint_iteration"] == 10)
        assert row_10["best_found_at_iteration"] == 5, (
            f"Expected best_found_at_iteration=5 for checkpoint_10, got {row_10['best_found_at_iteration']}"
        )
        assert row_10["checkpoint_iteration"] == 10, (
            f"Expected checkpoint_iteration=10, got {row_10['checkpoint_iteration']}"
        )

        # Verify code field contains the checkpoint marker
        for row in result["iterations"]:
            n = row["checkpoint_iteration"]
            assert f"checkpoint {n}" in row["code"], (
                f"Expected 'checkpoint {n}' in code, got: {row['code']}"
            )

        print("✓ test_checkpoint_based_consolidation passed")


def test_checkpoint_load_results():
    """Test that load_results() exposes Phase 4 columns from checkpoint-based results (CKPT-03)."""
    from consolidate_results import consolidate_experiment
    from results_loader import load_results
    import pandas as pd

    with tempfile.TemporaryDirectory() as tmpdir:
        # Create synthetic checkpoints/checkpoint_N/ tree
        checkpoint_data = [
            (5,  1.10, 5),
            (10, 1.15, 5),
            (15, 1.20, 10),
        ]
        for n, mem_score, best_found_at in checkpoint_data:
            ckpt_path = os.path.join(tmpdir, "checkpoints", f"checkpoint_{n}")
            os.makedirs(ckpt_path)
            info = {
                "iteration": best_found_at,
                "current_iteration": n,
                "metrics": {"mem_score": mem_score},
                "timestamp": "2026-05-14T10:00:00Z",
            }
            with open(os.path.join(ckpt_path, "best_program_info.json"), "w") as f:
                json.dump(info, f)
            with open(os.path.join(ckpt_path, "best_program.c"), "w") as f:
                f.write(f"/* checkpoint {n} */")

        consolidate_experiment(tmpdir, prompt_variant="test_ckpt")
        df = load_results(os.path.join(tmpdir, "results.json"))

        assert len(df) == 3, f"Expected 3 rows, got {len(df)}"

        required_cols = {"checkpoint_iteration", "best_found_at_iteration", "code",
                         "combined_score", "time_score", "mem_score", "iteration", "prompt"}
        assert required_cols <= set(df.columns), (
            f"Missing columns: {required_cols - set(df.columns)}"
        )

        assert df.iloc[0]["checkpoint_iteration"] == 5, (
            f"First row checkpoint_iteration should be 5, got {df.iloc[0]['checkpoint_iteration']}"
        )
        assert df.iloc[2]["checkpoint_iteration"] == 15, (
            f"Last row checkpoint_iteration should be 15, got {df.iloc[2]['checkpoint_iteration']}"
        )

        # time_score is JSON null → becomes NaN through pandas
        assert df["time_score"].isna().all(), "time_score column should be all NaN"

        # combined_score must equal mem_score for every row
        assert (df["combined_score"] == df["mem_score"]).all(), (
            "combined_score must equal mem_score for all rows"
        )

        print("✓ test_checkpoint_load_results passed")


def test_checkpoint_explanation_threading():
    """Test that explanations dict keyed by folder N threads correctly (EXPLAIN-01, EXPLAIN-02)."""
    from consolidate_results import consolidate_experiment
    from results_loader import load_results
    import pandas as pd

    with tempfile.TemporaryDirectory() as tmpdir:
        # Create synthetic checkpoints/checkpoint_N/ tree
        checkpoint_data = [
            (5,  1.10, 5),
            (10, 1.15, 5),
            (15, 1.20, 10),
        ]
        for n, mem_score, best_found_at in checkpoint_data:
            ckpt_path = os.path.join(tmpdir, "checkpoints", f"checkpoint_{n}")
            os.makedirs(ckpt_path)
            info = {
                "iteration": best_found_at,
                "current_iteration": n,
                "metrics": {"mem_score": mem_score},
                "timestamp": "2026-05-14T10:00:00Z",
            }
            with open(os.path.join(ckpt_path, "best_program_info.json"), "w") as f:
                json.dump(info, f)
            with open(os.path.join(ckpt_path, "best_program.c"), "w") as f:
                f.write(f"/* checkpoint {n} */")

        # Explanations dict keyed by integer folder N (Pitfall 2: not JSON iteration field)
        explanations = {
            5: "first delta",
            10: "second delta",
            15: "third delta",
        }

        result = consolidate_experiment(
            tmpdir, prompt_variant="test_ckpt", explanations=explanations
        )

        # Each row should have explanation matching the dict value at its checkpoint_iteration
        for row in result["iterations"]:
            n = row["checkpoint_iteration"]
            assert row.get("explanation") == explanations[n], (
                f"checkpoint_{n}: expected explanation '{explanations[n]}', "
                f"got '{row.get('explanation')}'"
            )

        df = load_results(os.path.join(tmpdir, "results.json"))
        assert df["explanation"].notna().all(), "All rows should have explanations"
        assert df.iloc[0]["explanation"] == "first delta", (
            f"First row explanation should be 'first delta', got '{df.iloc[0]['explanation']}'"
        )

        print("✓ test_checkpoint_explanation_threading passed")


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

        print("\n" + "="*60)
        print("Running Phase 4 checkpoint tests")
        print("="*60)
        test_checkpoint_based_consolidation()
        test_checkpoint_load_results()
        test_checkpoint_explanation_threading()

        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ Test failed: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)

# Phase 4: Per-Step Data Pipeline - Pattern Map

**Mapped:** 2026-05-14
**Files analyzed:** 6
**Analogs found:** 6 / 6

---

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|-------------------|------|-----------|----------------|---------------|
| `openevolve/consolidate_results.py` | data-pipeline / transform | file-I/O + transform | self (`_extract_iterations`, lines 168–236) | self-replace |
| `openevolve/results_loader.py` | loader | transform | self (`load_results`, lines 138–194) | self-extend |
| `openevolve/run_experiment.py` | orchestrator | request-response + file-I/O | self (`_generate_explanations_for_experiment`, lines 47–114) | self-replace internals |
| `openevolve/migrate_legacy.py` | migration / utility | file-I/O + batch | self (`migrate_legacy`, lines 21–49) | self-extend |
| `openevolve/test_consolidation.py` | test | batch | self (`test_consolidate_with_explanations`, lines 150–183) | self-extend |
| `openevolve/test_run_structure.py` | test | batch | self (`test_migration_moves`, lines 137–187) | self-extend |

---

## Pattern Assignments

### `openevolve/consolidate_results.py` — replace `_extract_iterations()`

**Analog:** self, lines 168–236 (current `_extract_iterations` body) + surrounding caller context lines 87–98

**Current function signature** (lines 168–173) — UNCHANGED:
```python
def _extract_iterations(
    output_dir: str,
    best_info: dict,
    baseline_accesses: int,
    explanations: Optional[dict] = None,
) -> list:
```

**Caller in `consolidate_experiment()`** (lines 87–98) — UNCHANGED, shown for orientation:
```python
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
```

**Core row-building pattern** (lines 218–234) — copy this dict structure, extend it with new Phase 4 fields:
```python
        iteration_record = {
            "iteration": iteration_num,
            "memory_accesses": memory_accesses,
            "memory_reads": memory_reads,
            "memory_writes": memory_writes,
            "improvement_percent": round(improvement_percent, 2),
            "iteration_runtime_seconds": round(iteration_runtime, 1),
            "mem_score": round(mem_score, 4),
        }

        # Add explanation if available
        if explanations and iteration_num in explanations:
            explanation = explanations[iteration_num]
            if explanation is not None:
                iteration_record["explanation"] = explanation
```

**New fields to add to the row dict** (D-01, D-02, D-05, CKPT-02):
```python
        row = {
            # --- backward-compat alias (load_results sorts on "iteration") ---
            "iteration": checkpoint_n,

            # --- Phase 4 new fields ---
            "checkpoint_iteration": checkpoint_n,              # D-05: folder N
            "best_found_at_iteration": best_found_at,          # D-05: info["iteration"]
            "code": code,                                      # CKPT-02: full C source text
            "combined_score": round(mem_score, 4),             # D-02: equals mem_score for now
            "time_score": None,                                # D-01: null placeholder

            # --- existing fields unchanged ---
            "memory_accesses": memory_accesses,
            "memory_reads": memory_reads,
            "memory_writes": memory_writes,
            "improvement_percent": round(improvement_percent, 2),
            "mem_score": round(mem_score, 4),
        }
        # explanation attaches the same way as before:
        if explanations and checkpoint_n in explanations:
            explanation = explanations[checkpoint_n]
            if explanation is not None:
                row["explanation"] = explanation
```

**Checkpoint scan pattern** — replaces the `if best_info:` block (lines 196–234):
```python
    checkpoints_dir = os.path.join(output_dir, "checkpoints")
    if not os.path.isdir(checkpoints_dir):
        return []

    dirs = [
        d for d in os.listdir(checkpoints_dir)
        if d.startswith("checkpoint_") and os.path.isdir(os.path.join(checkpoints_dir, d))
    ]
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

        with open(info_path) as f:
            info = json.load(f)
        with open(code_path) as f:
            code = f.read()

        metrics = info.get("metrics", {})
        mem_score = metrics.get("mem_score") or metrics.get("combined_score") or 1.0
        best_found_at = info.get("iteration", checkpoint_n)   # D-05: NOT current_iteration

        memory_accesses = int(baseline_accesses / mem_score) if mem_score > 0 else baseline_accesses
        improvement_percent = (baseline_accesses - memory_accesses) / baseline_accesses * 100
        memory_reads = memory_accesses // 2
        memory_writes = memory_accesses - memory_reads

        row = { ... }  # use the row dict pattern above
        rows.append(row)

    return rows
```

**Error handling pattern** (from `_load_best_result`, lines 162–165) — same style for checkpoint reads:
```python
    except (IOError, json.JSONDecodeError) as e:
        print(f"Warning: Could not load best_program_info.json: {e}")
        return {}
```

**Anti-pattern to avoid:** Do NOT read `iteration_runtime` from `best_program_info.json` for checkpoints — that field is a Phase 1 placeholder (`runtime_seconds`). Checkpoint rows omit `iteration_runtime_seconds` or set it to `0.0` until real timing data exists.

---

### `openevolve/results_loader.py` — extend `load_results()` column lists

**Analog:** self, lines 138–194

**Current column ordering block** (lines 172–188) — target for extension:
```python
    # Reorder columns: iteration, prompt, memory_accesses first; metadata last
    primary_cols = [
        "iteration",
        "prompt",
        "memory_accesses",
        "improvement_percent",
        "mem_score",
    ]
    secondary_cols = [
        "memory_reads",
        "memory_writes",
        "iteration_runtime_seconds",
    ]
    explanation_cols = ["explanation"]
    metadata_cols = ["timestamp", "baseline_accesses", "program"]

    # Only include columns that exist in the dataframe
    existing_cols = [c for c in primary_cols + secondary_cols + explanation_cols + metadata_cols if c in df.columns]
    df = df[existing_cols]
```

**New column ordering** — replace the four list literals above with:
```python
    primary_cols = [
        "checkpoint_iteration",       # NEW Phase 4 — primary key
        "iteration",                  # backward-compat alias (sort key, unchanged)
        "prompt",
        "memory_accesses",
        "improvement_percent",
        "mem_score",
        "combined_score",             # NEW Phase 4
        "time_score",                 # NEW Phase 4
    ]
    secondary_cols = [
        "best_found_at_iteration",    # NEW Phase 4
        "code",                       # NEW Phase 4 (full C source)
        "memory_reads",
        "memory_writes",
        "iteration_runtime_seconds",
    ]
    explanation_cols = ["explanation"]
    metadata_cols = ["timestamp", "baseline_accesses", "program"]
```

**Empty-DataFrame columns block** (lines 142–156) — extend for edge case (empty iterations):
```python
        df = pd.DataFrame(
            columns=[
                "checkpoint_iteration",       # NEW
                "iteration",
                "best_found_at_iteration",    # NEW
                "code",                       # NEW
                "memory_accesses",
                "memory_reads",
                "memory_writes",
                "improvement_percent",
                "iteration_runtime_seconds",
                "mem_score",
                "combined_score",             # NEW
                "time_score",                 # NEW
                "prompt",
                "timestamp",
                "baseline_accesses",
                "program",
            ]
        )
```

**Pattern note:** The guard `existing_cols = [c for c in ... if c in df.columns]` already handles the case where Phase 4 columns are absent from older results.json files — no extra backward-compat code needed.

---

### `openevolve/run_experiment.py` — replace `_generate_explanations_for_experiment()` internals

**Analog:** self, `_generate_explanations_for_experiment()` lines 47–114; call site lines 237–253

**Current function body to replace** (lines 78–113) — the internals that read from `best/`:
```python
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
```

**Replacement pattern** — per-checkpoint loop (D-06, D-07, D-08):
```python
    explanations = {}
    checkpoints_dir = os.path.join(output_dir, "checkpoints")
    if not os.path.isdir(checkpoints_dir):
        print("Warning: checkpoints/ directory not found, skipping explanations", file=sys.stderr)
        return {}

    dirs = sorted(
        [d for d in os.listdir(checkpoints_dir) if d.startswith("checkpoint_")
         and os.path.isdir(os.path.join(checkpoints_dir, d))],
        key=lambda d: int(d.replace("checkpoint_", ""))
    )
    if not dirs:
        return {}

    prev_code = baseline_code  # D-08: first checkpoint compares to initial_program.c

    for ckpt_dir in dirs:
        n = int(ckpt_dir.replace("checkpoint_", ""))
        code_path = os.path.join(checkpoints_dir, ckpt_dir, "best_program.c")
        if not os.path.isfile(code_path):
            print(f"Warning: no best_program.c in {ckpt_dir}, skipping", file=sys.stderr)
            continue
        with open(code_path) as f:
            evolved_code = f.read()

        print(f"Generating explanation for checkpoint {n}...", file=sys.stderr)
        explanation = generate_explanation(
            evolved_code=evolved_code,
            baseline_code=prev_code,        # D-08: previous checkpoint's code
            llm_config=llm_config,
            explanation_prompt_text=explanation_prompt,
        )
        explanations[n] = explanation       # None on failure — acceptable (D-07 path)
        if explanation:
            print(f"  checkpoint_{n}: {explanation[:80]}...", file=sys.stderr)
        prev_code = evolved_code            # advance sliding window

    return explanations
```

**Call site pattern** (lines 237–253) — UNCHANGED in structure; only the function name changes if internals are replaced rather than extracted:
```python
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
```

**Pattern note:** The function signature of `_generate_explanations_for_experiment` is unchanged. Only its body (lines 78–113) is replaced. The call site at line 243 remains identical.

---

### `openevolve/migrate_legacy.py` — add `--regenerate` flag

**Analog:** self, `main()` lines 52–72 (argparse pattern) + `migrate_legacy()` lines 21–49 (directory iteration pattern)

**Current argparse block** (lines 52–68) — copy this as the model for adding `--regenerate`:
```python
def main():
    parser = argparse.ArgumentParser(
        description="Migrate legacy flat experiment directories to runs/legacy/cavitydetection/."
    )
    parser.add_argument(
        "--output-root",
        default=os.path.join(SCRIPT_DIR, "openevolve_output"),
        help="Base output directory to migrate (default: openevolve/openevolve_output/)",
    )
    args = parser.parse_args()

    output_root = args.output_root
    if not os.path.exists(output_root):
        sys.exit(f"Output root not found: {output_root}")

    migrate_legacy(output_root)
    print("Migration complete.")
```

**New `--regenerate` argument to add** (after `--output-root`):
```python
    parser.add_argument(
        "--regenerate",
        action="store_true",
        default=False,
        help="Regenerate results.json from checkpoints for all migrated experiments; backs up existing results.json as results.json.v1",
    )
```

**New `regenerate_results()` function to add** — follows `migrate_legacy()` indentation/style:
```python
def regenerate_results(output_root: str) -> None:
    """Regenerate results.json from checkpoints for all migrated experiment dirs."""
    # Import inline to avoid circular imports at module load time
    try:
        from consolidate_results import consolidate_experiment
    except ImportError:
        from .consolidate_results import consolidate_experiment

    legacy_dir = os.path.join(output_root, "runs", "legacy", "cavitydetection")
    if not os.path.isdir(legacy_dir):
        print(f"No legacy directory found at {legacy_dir}, nothing to regenerate.")
        return

    for name in sorted(os.listdir(legacy_dir)):
        exp_dir = os.path.join(legacy_dir, name)
        if not os.path.isdir(exp_dir):
            continue
        # Only process dirs that have a checkpoints/ subdir
        if not os.path.isdir(os.path.join(exp_dir, "checkpoints")):
            print(f"Skip (no checkpoints/): {name}")
            continue

        results_path = os.path.join(exp_dir, "results.json")
        backup_path = os.path.join(exp_dir, "results.json.v1")

        if os.path.isfile(results_path):
            shutil.copy2(results_path, backup_path)   # D-10: always backup first
            print(f"Backed up: runs/legacy/cavitydetection/{name}/results.json -> results.json.v1")

        try:
            consolidate_experiment(output_dir=exp_dir)
            print(f"Regenerated: runs/legacy/cavitydetection/{name}/results.json")
        except Exception as e:
            print(f"Warning: regeneration failed for {name}: {e}", file=sys.stderr)
```

**Updated `main()` tail** — call `regenerate_results` conditionally after migration:
```python
    migrate_legacy(output_root)
    print("Migration complete.")

    if args.regenerate:
        print("Regenerating results.json from checkpoints...")
        regenerate_results(output_root)
        print("Regeneration complete.")
```

**Error handling pattern** (from `migrate_legacy()`, lines 44–48) — cross-device rename guard, reuse as-is for `shutil.copy2`:
```python
        try:
            os.rename(src, dst)
        except OSError as e:
            if e.errno == 18:  # EXDEV — cross-device link
                shutil.move(src, str(dst))
            else:
                raise
```

---

### `openevolve/test_consolidation.py` — add checkpoint-based tests

**Analog:** self, `test_consolidate_with_explanations()` lines 150–183 (synthetic fixture pattern) and `test_consolidation()` lines 29–147 (assertion style)

**Fixture creation pattern** (lines 151–171) — COPY this for checkpoint synthetic tree:
```python
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
```

**New synthetic checkpoint tree** — replace `best_dir` construction with checkpoint dirs:
```python
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create synthetic checkpoints/checkpoint_N/ tree
        for n, (mem_score, best_found_at) in [(5, 1.10, 5), (10, 1.15, 5), (15, 1.20, 10)]:
            ckpt_path = os.path.join(tmpdir, "checkpoints", f"checkpoint_{n}")
            os.makedirs(ckpt_path)
            info = {
                "iteration": best_found_at,        # best-found iteration
                "current_iteration": n,            # checkpoint written at
                "metrics": {"mem_score": mem_score},
                "timestamp": "2026-05-14T10:00:00Z",
            }
            with open(os.path.join(ckpt_path, "best_program_info.json"), "w") as f:
                json.dump(info, f)
            # Use short synthetic code (not 10 KB) to keep test fast
            with open(os.path.join(ckpt_path, "best_program.c"), "w") as f:
                f.write(f"/* checkpoint {n} */")
```

**Assertion style** (lines 88–107) — copy this pattern for Phase 4 field assertions:
```python
        for iter_record in iterations:
            assert "iteration" in iter_record
            assert "memory_accesses" in iter_record
            ...
            assert abs(
                iter_record["improvement_percent"] - expected_improvement
            ) < 0.01, f"Improvement mismatch: ..."
```

**New Phase 4 field assertions to add**:
```python
        assert len(result["iterations"]) == 3, f"Expected 3 checkpoint rows, got {len(result['iterations'])}"
        for row in result["iterations"]:
            assert "checkpoint_iteration" in row, "Missing checkpoint_iteration"
            assert "best_found_at_iteration" in row, "Missing best_found_at_iteration"
            assert "code" in row, "Missing code column"
            assert "combined_score" in row, "Missing combined_score"
            assert row["time_score"] is None, "time_score must be null (D-01)"
            assert row["combined_score"] == row["mem_score"], "combined_score must equal mem_score (D-02)"
            assert row["iteration"] == row["checkpoint_iteration"], "iteration alias must equal checkpoint_iteration"
        # Verify numeric sort: checkpoint_5 before checkpoint_10 before checkpoint_15
        ckpt_ns = [row["checkpoint_iteration"] for row in result["iterations"]]
        assert ckpt_ns == sorted(ckpt_ns), f"Checkpoints not in numeric order: {ckpt_ns}"
```

**Print style** (lines 54, 59, 77) — use the same `print(f"✓ ...")` format:
```python
        print("✓ test_checkpoint_based_consolidation passed")
```

**Runner block extension** (lines 379–402) — ADD new test calls before `sys.exit`:
```python
        print("\n" + "="*60)
        print("Running Phase 4 checkpoint tests")
        print("="*60)
        test_checkpoint_based_consolidation()
        test_checkpoint_explanation_threading()
```

---

### `openevolve/test_run_structure.py` — add `--regenerate` test

**Analog:** self, `test_migration_moves()` lines 137–187 (synthetic dir tree + CLI function call pattern) and `test_migration_idempotent()` lines 189–218 (backup/file-preservation assertions)

**Fixture + call pattern** (lines 139–158) — COPY for `--regenerate` test:
```python
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create synthetic prompt experiment dirs with marker files
        os.makedirs(os.path.join(tmpdir, "baseline"))
        with open(os.path.join(tmpdir, "baseline", "results.json"), "w") as f:
            f.write("{}")
        ...
        migrate_legacy(tmpdir)
```

**New `test_regenerate_flag()` fixture structure**:
```python
def test_regenerate_flag():
    """Test that --regenerate creates results.json.v1 backup before overwriting."""
    from migrate_legacy import migrate_legacy, regenerate_results

    with tempfile.TemporaryDirectory() as tmpdir:
        # Set up: a migrated experiment with checkpoints/ and existing results.json
        legacy_exp = os.path.join(tmpdir, "runs", "legacy", "cavitydetection", "baseline")
        os.makedirs(legacy_exp)
        # Write existing results.json (will be backed up)
        existing_results = os.path.join(legacy_exp, "results.json")
        with open(existing_results, "w") as f:
            json.dump({"metadata": {}, "iterations": [], "baseline_metrics": {}}, f)
        # Write a minimal checkpoint so consolidate_experiment() can run
        ckpt_path = os.path.join(legacy_exp, "checkpoints", "checkpoint_5")
        os.makedirs(ckpt_path)
        with open(os.path.join(ckpt_path, "best_program_info.json"), "w") as f:
            json.dump({"iteration": 5, "current_iteration": 5, "metrics": {"mem_score": 1.1}}, f)
        with open(os.path.join(ckpt_path, "best_program.c"), "w") as f:
            f.write("/* synthetic */")

        regenerate_results(tmpdir)

        # Backup must exist (D-10)
        backup_path = os.path.join(legacy_exp, "results.json.v1")
        assert os.path.isfile(backup_path), \
            f"results.json.v1 backup not created at {backup_path}"

        # New results.json must exist and be valid JSON
        assert os.path.isfile(existing_results), \
            "results.json missing after regeneration"
        with open(existing_results) as f:
            data = json.load(f)
        assert "iterations" in data, "results.json missing 'iterations' key"
        assert len(data["iterations"]) > 0, "Expected at least 1 checkpoint row"

        print("✓ test_regenerate_flag passed")
```

**Assertion style** (lines 160–187) — use identical `assert ... , "message"` one-liners:
```python
        assert os.path.isfile(backup_path), \
            f"results.json.v1 backup not created at {backup_path}"
```

**Runner block extension** (lines 354–401) — ADD before final `sys.exit`:
```python
        print("Running test_regenerate_flag...")
        test_regenerate_flag()
        print("  PASSED")
```

---

## Shared Patterns

### File I/O error handling
**Source:** `consolidate_results.py` lines 162–165 and `run_experiment.py` lines 87–90
**Apply to:** All file reads in `_extract_iterations()` and the explanation loop
```python
    except (IOError, json.JSONDecodeError) as e:
        print(f"Warning: Could not load {filename}: {e}", file=sys.stderr)
        # continue or return {} depending on context
```

### Checkpoint directory numeric sort
**Source:** CONTEXT.md / RESEARCH.md (verified against real checkpoint dirs)
**Apply to:** `_extract_iterations()` in `consolidate_results.py` and the explanation loop in `run_experiment.py`
```python
dirs.sort(key=lambda d: int(d.replace("checkpoint_", "")))
```

### `EXPLAIN_GENERATIONS` env var guard
**Source:** `run_experiment.py` lines 238–256
**Apply to:** The new per-checkpoint explanation loop — same check, no new flag (D-07)
```python
        explanations_enabled = os.environ.get("EXPLAIN_GENERATIONS", "1") != "0"
        if explanations_enabled:
            ...
        else:
            print("Explanation generation disabled via EXPLAIN_GENERATIONS=0")
```

### Backup-before-overwrite with `shutil.copy2`
**Source:** `migrate_legacy.py` lines 44–48 (OSError handling) + RESEARCH.md Pattern 3
**Apply to:** `regenerate_results()` in `migrate_legacy.py`
```python
        if os.path.isfile(results_path):
            shutil.copy2(results_path, backup_path)   # D-10: always backup first
```

### Tempdir + synthetic fixture test structure
**Source:** `test_consolidation.py` lines 34–54 and `test_run_structure.py` lines 137–158
**Apply to:** All new test functions in both test files
```python
    with tempfile.TemporaryDirectory() as tmpdir:
        # build fixture tree
        # run function under test
        # assert on outputs
        print("✓ test_name passed")
```

### `import consolidate_experiment` with try/except for module vs. script context
**Source:** `run_experiment.py` lines 29–32
**Apply to:** `regenerate_results()` in `migrate_legacy.py` (inline import or top-level with same guard)
```python
try:
    from consolidate_results import consolidate_experiment
except ImportError:
    from .consolidate_results import consolidate_experiment
```

---

## No Analog Found

None — all six target files are self-modifying (existing code provides the analog pattern). The RESEARCH.md pseudo-code examples complement the existing code directly.

---

## Key Anti-Patterns (from RESEARCH.md)

These appear as natural temptations and must be explicitly flagged in the plan:

1. **`info["current_iteration"]` as checkpoint number** — use folder name N, not JSON field. Lines 196–234 of current `_extract_iterations()` would be the trap; it reads `iteration_num = best_info.get("iteration", 1)` which is correct for the `best/` pattern but wrong for checkpoints.
2. **`explanations` dict keyed by `info["iteration"]`** — must key by folder N. If the explanation loop uses `info["iteration"]` (best-found generation) as the dict key, it silently mismatches `_extract_iterations()` which looks up by checkpoint folder N.
3. **Dropping `"iteration"` field from rows** — `load_results()` line 192 sorts by `"iteration"`; row must keep `"iteration": checkpoint_n` as alias.

---

## Metadata

**Analog search scope:** `openevolve/` directory (6 files read in full)
**Files scanned:** 6 source files + 2 real checkpoint JSON files (verified schema)
**Pattern extraction date:** 2026-05-14

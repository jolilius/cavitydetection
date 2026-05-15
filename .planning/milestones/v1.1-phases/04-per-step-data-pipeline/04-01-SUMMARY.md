---
phase: 04-per-step-data-pipeline
plan: "01"
subsystem: openevolve/data-pipeline
tags: [consolidation, checkpoint-scan, tdd, phase4-schema]
dependency_graph:
  requires: []
  provides:
    - openevolve/consolidate_results.py::_extract_iterations (checkpoint-based row builder)
    - openevolve/results_loader.py::load_results (Phase 4 column schema)
    - openevolve/test_consolidation.py (9-test suite, Wave 0 stubs + implementation)
  affects:
    - openevolve/run_experiment.py (uses consolidate_experiment — no call-site changes)
    - plans 04-02, 04-03 (consume checkpoint_iteration, best_found_at_iteration, code columns)
tech_stack:
  added: []
  patterns:
    - checkpoint directory scan with numeric sort (int(d.replace("checkpoint_", "")))
    - backward-compat iteration alias (checkpoint_n stored as both "iteration" and "checkpoint_iteration")
    - Phase 4 schema: checkpoint_iteration, best_found_at_iteration, code, combined_score, time_score
key_files:
  created: []
  modified:
    - openevolve/test_consolidation.py
    - openevolve/consolidate_results.py
    - openevolve/results_loader.py
decisions:
  - D-01 honored: time_score=None in every checkpoint row
  - D-02 honored: combined_score=round(mem_score,4) in every checkpoint row
  - D-03 honored: top-level container key remains "iterations" (unchanged in consolidate_experiment)
  - D-04 honored: _extract_iterations() signature unchanged; best_info param kept for backward compat
  - D-05 honored: checkpoint_iteration=folder_N, best_found_at_iteration=info["iteration"] (not current_iteration)
  - Pitfall 1 avoided: numeric sort lambda d int(d.replace("checkpoint_","")) prevents checkpoint_10 before checkpoint_5
  - Pitfall 2 avoided: explanations dict keyed by folder N, not JSON iteration field
  - Pitfall 4 avoided: "iteration" alias preserved so load_results sort_values("iteration") keeps working
metrics:
  duration: "~8 minutes"
  completed: "2026-05-14T15:35:27Z"
  tasks_completed: 3
  tasks_total: 3
  files_modified: 3
---

# Phase 4 Plan 01: Checkpoint-Based Consolidation Pipeline Summary

**One-liner:** Checkpoint directory scan replacing best/-only fallback, emitting six Phase 4 schema fields per row with backward-compat iteration alias.

## What Was Built

### Task 1 — Wave 0 failing test stubs (commit `bce1bf7`)

Added three new test functions to `openevolve/test_consolidation.py` that exercised the new Phase 4 schema before any implementation existed (TDD RED state):

- `test_checkpoint_based_consolidation`: creates synthetic `checkpoints/checkpoint_{5,10,15}/` tree, verifies numeric sort order `[5,10,15]`, all six schema fields, D-05 divergence (`checkpoint_iteration=10, best_found_at_iteration=5`), and code field content.
- `test_checkpoint_load_results`: calls `load_results()` on a checkpoint-built `results.json`, asserts `time_score.isna().all()` and `combined_score == mem_score`.
- `test_checkpoint_explanation_threading`: passes `explanations={5:"first delta", 10:"second delta", 15:"third delta"}` (keyed by folder N, not JSON iteration field) and verifies threading per row.

All three tests exited non-zero (RED state) against the original implementation.

### Task 2 — Rewrite `_extract_iterations()` (commit `1a4742e`)

Replaced the `if best_info:` body in `openevolve/consolidate_results.py` with a checkpoint directory scan:

1. Checks for `checkpoints/` subdirectory; returns `[]` if absent (no fallback to `best/`).
2. Lists all `checkpoint_N/` dirs, sorts by `int(d.replace("checkpoint_", ""))` to avoid lexicographic bugs.
3. For each checkpoint: reads `best_program_info.json` and `best_program.c`, builds a row with Phase 4 fields.
4. Attaches explanations keyed by folder N (not by `info["iteration"]`).

Added `import sys` for `print(..., file=sys.stderr)`. Signature unchanged (D-04). Real baseline: 12 checkpoint dirs → 12 rows.

### Task 3 — Extend `load_results()` + reconcile legacy tests (commit `2cae80e`)

**`openevolve/results_loader.py`:**
- Empty-DataFrame columns extended with `checkpoint_iteration`, `best_found_at_iteration`, `code`, `combined_score`, `time_score`.
- `primary_cols`: `checkpoint_iteration` prepended before `iteration`; `combined_score` and `time_score` appended after `mem_score`.
- `secondary_cols`: `best_found_at_iteration` and `code` prepended before `memory_reads`.
- Existing guard `[c for c in ... if c in df.columns]` ensures Phase 1/2 results without new fields keep loading without KeyError.

**`openevolve/test_consolidation.py`:** Converted three legacy `best/`-based tests to `checkpoints/checkpoint_N/` fixtures:
- `test_consolidate_with_explanations`: `best/` with `iteration=42` → `checkpoints/checkpoint_42/`.
- `test_consolidate_without_explanations`: `best/` with `iteration=25` → `checkpoints/checkpoint_25/`.
- `test_consolidate_partial_explanations`: `best/` with `iteration=5` → `checkpoints/checkpoint_5/`.

Also removed the `iteration_runtime_seconds` assertion from `test_consolidation()` since checkpoint rows intentionally omit that Phase 1 field.

## Test Results

All 9 tests pass with exit code 0:

```
✓ test_consolidation passed
✓ test_consolidate_with_explanations passed
✓ test_consolidate_without_explanations passed
✓ test_consolidate_partial_explanations passed
✓ test_load_results_with_explanations passed
✓ test_load_phase1_results passed
✓ test_checkpoint_based_consolidation passed
✓ test_checkpoint_load_results passed
✓ test_checkpoint_explanation_threading passed
```

## Sample Row from Regenerated `baseline/results.json`

```json
{
  "iteration": 5,
  "checkpoint_iteration": 5,
  "best_found_at_iteration": 5,
  "code": "/* initial_program.c — OpenEvolve seed for cavity-detection pipeline optimisation. ...",
  "combined_score": 1.155,
  "time_score": null,
  "memory_accesses": 111572927,
  "memory_reads": 55786463,
  "memory_writes": 55786464,
  "improvement_percent": 13.41,
  "mem_score": 1.155
}
```

(Real baseline checkpoint_5 row; 12 rows total)

## Deviations from Plan

### Auto-fixed Issues

None.

### Intentional Adjustments

**1. `test_consolidation()` row assertion update — iteration_runtime_seconds**
- **Found during:** Task 3
- **Issue:** `test_consolidation()` originally asserted `"iteration_runtime_seconds" in iter_record` and `"iteration_runtime_seconds" in df.columns`. Checkpoint rows intentionally omit this Phase 1 placeholder field (per PATTERNS.md anti-pattern note). After converting the fixture to use `checkpoints/checkpoint_25/`, these assertions would fail on valid data.
- **Fix:** Removed the two `iteration_runtime_seconds` assertions and added inline comments explaining the field is not emitted for checkpoint rows.
- **Files modified:** `openevolve/test_consolidation.py`
- **Commit:** `2cae80e`

**2. Legacy `best/`-fixture test conversion**
- **Scope:** Per plan Task 3 acceptance criteria (expected deviation, not a bug).
- **Three tests converted:** `test_consolidate_with_explanations` (iteration=42 → checkpoint_42), `test_consolidate_without_explanations` (iteration=25 → checkpoint_25), `test_consolidate_partial_explanations` (iteration=5 → checkpoint_5).
- Each now creates `checkpoints/checkpoint_N/` with both `best_program_info.json` and `best_program.c`. The assertion on `result['iterations'][0].get('explanation')` and `result_dict[5]` keep working because `iteration` alias equals checkpoint folder N.

## Requirements Satisfied

- **CKPT-01:** `results.json` built from `checkpoints/checkpoint_N/` sorted numerically — verified by `test_checkpoint_based_consolidation` asserting `[5, 10, 15]` order.
- **CKPT-02:** Each row has `checkpoint_iteration`, `best_found_at_iteration`, `code`, `combined_score`, `mem_score`, `time_score` — verified by direct key-presence asserts.
- **CKPT-03:** `load_results()` exposes those columns in a DataFrame with one row per checkpoint — verified by `test_checkpoint_load_results` and real-data smoke check (12 rows).

## Known Stubs

- `time_score: null` — intentional per D-01; will be populated when real per-checkpoint timing data is available (future plan).
- `combined_score = mem_score` — intentional per D-02; `time_score` component not yet available.

## Self-Check: PASSED

| Item | Status |
|------|--------|
| openevolve/test_consolidation.py | FOUND |
| openevolve/consolidate_results.py | FOUND |
| openevolve/results_loader.py | FOUND |
| .planning/phases/04-per-step-data-pipeline/04-01-SUMMARY.md | FOUND |
| commit bce1bf7 (task 1) | FOUND |
| commit 1a4742e (task 2) | FOUND |
| commit 2cae80e (task 3) | FOUND |
| Full test suite exit 0 (9/9 tests pass) | PASSED |
| Real baseline 12 rows with Phase 4 columns | PASSED |

---
phase: 04-per-step-data-pipeline
plan: "02"
subsystem: openevolve/explanation-pipeline
tags: [explanations, checkpoint-scan, sliding-window, phase4-explain]
dependency_graph:
  requires:
    - openevolve/consolidate_results.py::_extract_iterations (checkpoint-based row builder — Plan 04-01)
    - openevolve/results_loader.py::load_results (Phase 4 column schema — Plan 04-01)
  provides:
    - openevolve/run_experiment.py::_generate_explanations_for_experiment (per-checkpoint explanation loop)
  affects:
    - openevolve/run_experiment.py (explanation generation path)
    - consolidate_experiment call site (unchanged — dict passed through as explanations=explanations)
tech_stack:
  added: []
  patterns:
    - checkpoint directory scan with numeric sort (int(d.replace("checkpoint_", "")))
    - sliding-window baseline for LLM explanation (prev_code advances per checkpoint)
    - skip-without-advance on missing best_program.c (prev_code not updated on skip)
    - integer-keyed dict matching _extract_iterations() lookup key space
key_files:
  created: []
  modified:
    - openevolve/run_experiment.py
decisions:
  - D-06 honored: explanation generation runs at END of main() after OpenEvolve finishes, call site unchanged
  - D-07 honored: EXPLAIN_GENERATIONS=0 gate (line 238) untouched; no new env var introduced
  - D-08 honored: sliding window — checkpoint N compares to checkpoint N-1; first checkpoint compares to initial_program.c (baseline_code arg)
  - Pitfall 2 avoided: dict keys are integer folder Ns matching _extract_iterations() lookup, not info["iteration"]
  - Skip-without-advance: when best_program.c is missing, prev_code is NOT advanced so next valid checkpoint compares to last good code
metrics:
  duration: "~7 minutes"
  completed: "2026-05-14T15:40:07Z"
  tasks_completed: 2
  tasks_total: 2
  files_modified: 1
---

# Phase 4 Plan 02: Per-Checkpoint Explanation Loop Summary

**One-liner:** Per-checkpoint sliding-window explanation loop replacing best/-only explanation, keyed by integer folder N to match consolidation pipeline.

## What Was Built

### Task 1 — Rewrite `_generate_explanations_for_experiment()` body (commit `bf78922`)

Replaced the body of `_generate_explanations_for_experiment()` in `openevolve/run_experiment.py` (lines 47-114). The function signature, four-parameter interface, and return type are unchanged.

**Removed (dead code from Phase 2):**
- Read from `best/best_program_info.json`
- Extract `evolved_code` from `program_source`/`evolved_code` JSON fields
- `iteration_num = best_info.get("iteration", 1)` extraction
- Single `generate_explanation()` call for the best solution only

**New behavior (D-06, D-07, D-08):**
1. Guard: `generate_explanation is None` → return `{}`
2. Resolve `checkpoints_dir = os.path.join(output_dir, "checkpoints")`; not a dir → print warning + return `{}`
3. List `checkpoint_N/` dirs, sort by `int(d.replace("checkpoint_", ""))` (numeric, not lexicographic)
4. If empty list → return `{}`
5. Initialize `prev_code = baseline_code` (per D-08, first checkpoint compares to initial_program.c)
6. For each checkpoint dir:
   - Compute `n = int(ckpt_dir.replace("checkpoint_", ""))` — integer folder N (dict key)
   - Skip missing `best_program.c` with warning; do NOT advance `prev_code`
   - Wrap file read in `try/except (IOError, OSError)` with warning + continue
   - Call `generate_explanation(evolved_code=evolved_code, baseline_code=prev_code, ...)`
   - Store `explanations[n] = explanation` (None is acceptable)
   - Print truncated preview if explanation is truthy
   - Advance `prev_code = evolved_code` (sliding window)
7. Return `explanations`

**Call site verification:** Lines 237-256 in `main()` are unchanged. The env-var gate `EXPLAIN_GENERATIONS != "0"` (D-07) is preserved. `consolidate_experiment(... explanations=explanations ...)` call at line 265 is unchanged.

### Task 2 — End-to-end smoke test on real baseline data (verification-only, no code change)

Ran `consolidate_experiment` on the real `openevolve/openevolve_output/baseline` directory with `explanations={}` (empty), then `load_results` on the produced `results.json`. Results:

**Smoke test output:**
```
OK rows=12 code_min_len=9935 cols=['baseline_accesses', 'best_found_at_iteration', 'checkpoint_iteration', 'code', 'combined_score', 'explanation', 'improvement_percent', 'iteration', 'mem_score', 'memory_accesses', 'memory_reads', 'memory_writes', 'program', 'prompt', 'time_score', 'timestamp']
```

**Detailed breakdown:**
- rows=12 (12 checkpoint dirs: checkpoint_5 through checkpoint_80, gap between 55 and 80)
- code_len range: min=9935 max=9935 (all checkpoints contain the same best program — checkpoint_5 won)
- checkpoint_iterations: [5, 10, 15, 20, 25, 30, 35, 40, 45, 50, 55, 80]
- best_found_at_iteration values: [5] (every checkpoint's best solution was found at iteration 5 — confirms RESEARCH.md observation)
- time_score all NaN: True
- explanation all NaN: True (no explanations passed, as expected)

## Test Results

All 9 tests pass with exit code 0 (EXPLAIN_GENERATIONS=0):

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

## Sliding-Window Verification Output

```
Generating explanation for checkpoint 5...
  checkpoint_5: EXPL(10 vs 4)...
Generating explanation for checkpoint 10...
  checkpoint_10: EXPL(20 vs 10)...
Generating explanation for checkpoint 15...
  checkpoint_15: EXPL(30 vs 20)...
OK sliding window
```

The test confirms:
- `result[5]` compares to baseline (len=4): `'vs 4' in result[5]`
- `result[10]` compares to checkpoint_5's code (len=10): `'vs 10' in result[10]`
- `result[15]` compares to checkpoint_10's code (len=20): `'vs 20' in result[15]`

## Deviations from Plan

None — plan executed exactly as written.

The verify commands in the plan referenced `cd /home/jolilius/home/src/cavitydetection` (main repo root), but the implementation lives in the worktree. All verifications were run against the worktree's `run_experiment.py` with Python from the sibling `openevolve/.venv`. This is expected behavior for the worktree execution model and not a deviation.

## Requirements Satisfied

- **EXPLAIN-01:** One explanation generated per checkpoint, comparing to previous checkpoint (or initial_program.c for the first). Verified by synthetic sliding-window assertion with stubbed `generate_explanation`.
- **EXPLAIN-02:** Explanations stored in results.json per checkpoint row and exposed as `df['explanation']`. Verified by `test_checkpoint_explanation_threading` (Plan 04-01) which passes `explanations={5:"first delta", 10:"second delta", 15:"third delta"}` keyed by folder N — the dict produced by this plan's function.
- **D-06:** Explanation generation runs post-OpenEvolve at the end of `run_experiment.py main()` — preserved by NOT moving the call site.
- **D-07:** `EXPLAIN_GENERATIONS=0` disables explanations — preserved by NOT modifying the env-var check at line 238.
- **D-08:** Sliding-window baseline verified by synthetic test.

## Known Stubs

None introduced by this plan. The `time_score=null` and `combined_score=mem_score` stubs pre-exist from Plan 04-01 (D-01, D-02).

## Threat Flags

None — this plan modifies only the explanation generation helper function within an already-existing orchestration script. No new network endpoints, auth paths, file access patterns, or schema changes at trust boundaries were introduced. The LLM call itself (`generate_explanation`) existed before this plan.

## Self-Check: PASSED

| Item | Status |
|------|--------|
| openevolve/run_experiment.py | FOUND and MODIFIED |
| .planning/phases/04-per-step-data-pipeline/04-02-SUMMARY.md | FOUND (this file) |
| commit bf78922 (task 1) | FOUND |
| task_2 verification: rows=12, code_min_len=9935, all cols present | PASSED |
| Full test suite exit 0 (9/9 tests pass) | PASSED |
| Call site lines 237-256 unchanged | VERIFIED |
| EXPLAIN_GENERATIONS=0 gate unchanged | VERIFIED |
| "best/best_program_info.json" absent from body | VERIFIED by AST check |
| "program_source" absent from body | VERIFIED by AST check |

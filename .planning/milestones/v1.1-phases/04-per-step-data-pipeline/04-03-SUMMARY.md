---
phase: 04-per-step-data-pipeline
plan: "03"
subsystem: openevolve/migration
tags: [migration, regenerate, backup, tdd, phase4-schema]
dependency_graph:
  requires:
    - openevolve/consolidate_results.py::consolidate_experiment (Plan 04-01)
  provides:
    - openevolve/migrate_legacy.py::regenerate_results (--regenerate upgrade path)
    - openevolve/test_run_structure.py::test_regenerate_flag (D-09, D-10 coverage)
    - openevolve/test_run_structure.py::test_regenerate_no_legacy_dir (graceful no-op path)
  affects:
    - openevolve/migrate_legacy.py (--regenerate flag; default behavior unchanged)
tech_stack:
  added: []
  patterns:
    - inline try/except import guard (module vs. script context)
    - shutil.copy2 backup-before-overwrite (D-10)
    - checkpoint directory skip guard (Pitfall 5)
    - graceful no-op on missing legacy dir
key_files:
  created: []
  modified:
    - openevolve/test_run_structure.py
    - openevolve/migrate_legacy.py
decisions:
  - D-09: --regenerate flag is opt-in; running without flag preserves migration-only behavior
  - D-10: results.json.v1 backup always created via shutil.copy2 before consolidate_experiment writes
  - Pitfall 5: regenerate_results() scans runs/legacy/cavitydetection/*/ only; skips subdirs without checkpoints/
  - consolidate_experiment imported inline inside regenerate_results() to avoid circular import at module load time
metrics:
  duration: "~10 minutes"
  completed: "2026-05-14T15:40:00Z"
  tasks_completed: 2
  tasks_total: 2
  files_modified: 2
---

# Phase 4 Plan 03: --regenerate Flag for Legacy Experiment Upgrade Summary

**One-liner:** opt-in `--regenerate` CLI flag on `migrate_legacy.py` that rebuilds `results.json` from Phase 4 checkpoints with `results.json.v1` rollback backup, verified by TDD test pair.

## What Was Built

### Task 1 — Wave 0 failing tests (commit `c2d4e55`)

Added two new test functions to `openevolve/test_run_structure.py` covering D-09 and D-10:

**`test_regenerate_flag()`:**
- Builds a synthetic post-migration tree with two checkpoints (`checkpoint_5`, `checkpoint_10`) and a `best_program.c` per checkpoint containing `"/* synthetic checkpoint N */"`.
- Also creates an `empty_exp/` dir (no `checkpoints/`) to verify the skip path.
- Calls `regenerate_results(tmpdir)` and asserts:
  - `results.json.v1` backup exists (D-10)
  - Backup bytes equal original legacy payload byte-for-byte
  - Regenerated `results.json` has 2 checkpoint rows
  - `checkpoint_iteration` values are `[5, 10]` in sorted order
  - `code` field contains `"synthetic checkpoint 5"`
  - `time_score is None` (D-01)
  - `empty_exp/results.json.v1` NOT created (Pitfall 5 — no checkpoints/)
  - `empty_exp/results.json` unchanged

**`test_regenerate_no_legacy_dir()`:**
- Fresh tmpdir with no `runs/legacy/cavitydetection/` subtree.
- Calls `regenerate_results(tmpdir)` and asserts no exception raised.

Both tests wired into `if __name__ == "__main__"` runner block.
RED state confirmed: `ImportError: cannot import name 'regenerate_results'` before Task 2.

### Task 2 — Implementation (commit `f75537b`)

Added `regenerate_results()` function and `--regenerate` argparse flag to `openevolve/migrate_legacy.py`:

**`regenerate_results(output_root)`:**
1. Inline import guard: `try: from consolidate_results import consolidate_experiment except ImportError: from .consolidate_results import consolidate_experiment`
2. Computes `legacy_dir = output_root/runs/legacy/cavitydetection`. Returns with friendly message if dir absent.
3. Iterates `sorted(os.listdir(legacy_dir))`, skipping non-dirs and dirs without `checkpoints/` subdir (Pitfall 5).
4. If `results.json` exists: `shutil.copy2(results_path, backup_path)` BEFORE any write (D-10).
5. Calls `consolidate_experiment(output_dir=exp_dir)` in try/except — partial failures print warning to stderr and continue.

**`main()` changes:**
- Added `--regenerate` argparse flag (`action="store_true"`, default `False`).
- After `migrate_legacy(output_root)`, conditionally calls `regenerate_results(output_root)` only when `args.regenerate` is set (D-09 opt-in).

Existing `migrate_legacy()` body and signature are untouched.

## Test Results

All 12 tests in `openevolve/test_run_structure.py` pass:

```
Running test_run_id_format...          PASSED
Running test_run_arg_override...       PASSED
Running test_output_root_override...   PASSED
Running test_metadata_fields...        PASSED
Running test_migration_moves...        PASSED
Running test_migration_idempotent...   PASSED
Running test_show_results_run_filter...PASSED
Running test_show_results_all...       PASSED
Running test_show_consolidated_run_filter... PASSED
Running test_evolve_all_shared_run...  PASSED
Running test_regenerate_flag...        PASSED
Running test_regenerate_no_legacy_dir...PASSED

All tests passed
```

All 9 tests in `openevolve/test_consolidation.py` continue to pass (no regression from Plan 04-01).

## --help Output

```
usage: migrate_legacy.py [-h] [--output-root OUTPUT_ROOT] [--regenerate]

Migrate legacy flat experiment directories to runs/legacy/cavitydetection/.

options:
  -h, --help            show this help message and exit
  --output-root OUTPUT_ROOT
                        Base output directory to migrate (default:
                        openevolve/openevolve_output/)
  --regenerate          Regenerate results.json from checkpoints for all
                        migrated experiments; backs up existing results.json
                        as results.json.v1
```

## Status of Real Data Migration

`baseline/` and `prompt1/` are still at the flat root of `openevolve/openevolve_output/` on this branch. Running `migrate_legacy.py` (without `--regenerate`) is a prerequisite to populate `runs/legacy/cavitydetection/`. Once migration is run, executing `migrate_legacy.py --regenerate` will rebuild both experiments' `results.json` files from their `checkpoints/` dirs using the Phase 4 schema. This is a manual follow-up for the user.

## Deviations from Plan

None - plan executed exactly as written.

## Known Stubs

None relevant to this plan. The `time_score: null` in regenerated rows is intentional per D-01 (documented in Plan 04-01 SUMMARY as a known stub).

## Self-Check: PASSED

| Item | Status |
|------|--------|
| openevolve/test_run_structure.py | FOUND |
| openevolve/migrate_legacy.py | FOUND |
| .planning/phases/04-per-step-data-pipeline/04-03-SUMMARY.md | FOUND |
| commit c2d4e55 (task 1 — failing tests) | FOUND |
| commit f75537b (task 2 — implementation) | FOUND |
| test_run_structure.py 12/12 tests pass | PASSED |
| test_consolidation.py 9/9 tests pass (no regression) | PASSED |
| --help advertises --regenerate | PASSED |
| results.json.v1 in src (D-10 guard) | PASSED |
| shutil.copy2 in src | PASSED |
| from consolidate_results import consolidate_experiment inline | PASSED |

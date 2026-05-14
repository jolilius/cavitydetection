---
phase: "03"
plan: "03-03"
subsystem: "openevolve-display"
tags: ["display", "makefile", "run-filter", "glob-discovery", "testing"]
dependency_graph:
  requires: ["03-01", "03-02"]
  provides: ["show-results-run-filter", "show-consolidated-run-filter", "evolve-all-run-grouping"]
  affects: ["openevolve/show_results.py", "openevolve/show_consolidated.py", "Makefile", "openevolve/test_run_structure.py"]
tech_stack:
  added: ["glob.glob", "argparse (show_consolidated.py)", "extract_run_id helper"]
  patterns: ["glob-based recursive discovery", "run_id path parsing", "Makefile if-expansion"]
key_files:
  created: []
  modified:
    - "openevolve/show_results.py"
    - "openevolve/show_consolidated.py"
    - "openevolve/test_run_structure.py"
    - "Makefile"
decisions:
  - "Used glob.glob recursive walk instead of os.listdir to support runs/<run_id>/ tree depth"
  - "extract_run_id() finds 'runs' index in path parts for robustness against absolute vs. relative paths"
  - "Legacy load_result/load_legacy_result helpers kept in show_results.py for backward compatibility"
  - "Python subprocess (generate_run_id) used in Makefile for RUN_ID to centralize sanitization"
metrics:
  duration: "2m 56s"
  completed: "2026-05-14T13:51:59Z"
  tasks_completed: 4
  tasks_total: 4
  files_modified: 4
---

# Phase 03 Plan 03: Display scripts + Makefile RUN= filter and evolve-all run grouping Summary

Glob-based discovery with --run filter in both display scripts and evolve-all RUN_ID grouping in Makefile, enabling `make show-results RUN=<id>` filtered views.

## Tasks Completed

| Task | Name | Commit | Files |
|------|------|--------|-------|
| 1 | Rewrite show_results.py discovery and add --run filter | 9525c8c | openevolve/show_results.py |
| 2 | Add --run filter and update results_root in show_consolidated.py | d91d9fd | openevolve/show_consolidated.py |
| 3 | Update Makefile — evolve-all with RUN_ID and RUN= pass-through | 1ef3264 | Makefile |
| 4 | Implement display and evolve-all tests in test_run_structure.py | e984d7d | openevolve/test_run_structure.py |

## What Was Delivered

**show_results.py** — replaced `os.listdir(OUTPUT_ROOT)` loop with `glob.glob` walk under `openevolve_output/runs/`. Added `load_result_from_path()` helper that accepts a full `results.json` path and returns a dict tagged with `run_id`. Added `--run` argument for optional single-run filtering.

**show_consolidated.py** — replaced `load_all_results()` call with direct glob walk under `openevolve_output/runs/`. Added `extract_run_id()` helper that locates the `runs` segment in a path and returns the next segment. Added `--run` argparse argument. Each per-file DataFrame is tagged with `run_id` before concatenation.

**Makefile** — `evolve-all` now generates a single `RUN_ID` before the prompt loop using a Python subprocess call to `generate_run_id()`. Each `run_experiment.py` invocation receives `--run $$RUN_ID`. Both `show-results` and `show-consolidated-results` targets use `$(if $(RUN),--run $(RUN),)` for transparent pass-through.

**test_run_structure.py** — 4 new tests added (total 10):
- `test_show_results_run_filter`: verifies glob + run_id filter returns only matching run
- `test_show_results_all`: verifies no-filter glob returns all runs
- `test_show_consolidated_run_filter`: verifies `extract_run_id` parses paths correctly and filter works
- `test_evolve_all_shared_run`: verifies `write_run_metadata` accumulates both prompts under the same run_id

## Verification Results

```
openevolve/test_run_structure.py: 10 passed
openevolve/ suite: 16 passed, 1 warning
make show-results --dry-run: no --run flag (backward-compatible)
make show-results RUN=legacy --dry-run: contains --run legacy
```

## Deviations from Plan

None — plan executed exactly as written.

## Known Stubs

None. All display logic wired to real data from the glob-discovered `results.json` files.

## Threat Flags

No new security surface introduced. `--run` values are used only as string equality filters against parsed path segments — no filesystem writes and no path interpolation in display scripts.

## Self-Check: PASSED

Files verified present:
- openevolve/show_results.py: FOUND
- openevolve/show_consolidated.py: FOUND
- openevolve/test_run_structure.py: FOUND
- Makefile: FOUND

Commits verified:
- 9525c8c: FOUND (feat: rewrite show_results.py)
- d91d9fd: FOUND (feat: update show_consolidated.py)
- 1ef3264: FOUND (feat: update Makefile)
- e984d7d: FOUND (test: add display filter tests)

---
phase: 3
plan: "03-01"
subsystem: openevolve
tags: [run-structure, cli, metadata, testing]
dependency_graph:
  requires: []
  provides:
    - generate_run_id (run_experiment.py)
    - write_run_metadata (run_experiment.py)
    - --run CLI argument (run_experiment.py)
    - --output-root CLI argument (run_experiment.py)
    - run directory layout: output_root/runs/run_id/cavitydetection/prompt/
    - test_run_structure.py with 4 passing tests
  affects:
    - openevolve/run_experiment.py (modified: new path layout, new functions, new args)
    - openevolve/test_run_structure.py (created)
tech_stack:
  added:
    - datetime.timezone (stdlib, for UTC timestamps in metadata.json)
    - re (stdlib, for model name sanitization)
  patterns:
    - Read-then-merge pattern for metadata.json (idempotent prompt append)
    - Non-blocking try/except for write_run_metadata call in main()
    - Path traversal guard via os.path.abspath().startswith()
key_files:
  created:
    - openevolve/test_run_structure.py
  modified:
    - openevolve/run_experiment.py
decisions:
  - "Sanitize model name with re.sub('[^a-zA-Z0-9-]+', '-', model) — qwen3-coder:30b becomes qwen3-coder-30b (colon and dot each become a dash)"
  - "Path traversal guard: os.path.abspath(run_dir).startswith(os.path.abspath(output_root)) rejects ../../etc style --run values"
  - "Metadata.json uses read-then-merge to allow repeated calls with different prompts to append rather than overwrite"
metrics:
  duration: "4 minutes"
  completed: "2026-05-14T13:43:50Z"
  tasks_completed: 4
  tasks_total: 4
  files_created: 1
  files_modified: 1
requirements_addressed:
  - RUNORG-01
  - RUNORG-03
---

# Phase 3 Plan 01: Test scaffolding + run_experiment.py run ID and metadata Summary

Run ID contract established: `generate_run_id()` produces `YYYY-MM-DD_HHMM_<sanitized-model>` and `write_run_metadata()` writes a merged `metadata.json` with all six RUNORG-03 fields; `run_experiment.py` now accepts `--run` and `--output-root` CLI args and writes to the structured `runs/<run_id>/cavitydetection/<prompt>/` layout.

## Tasks Completed

| Task | Description | Commit |
|------|-------------|--------|
| 1 | Create test_run_structure.py with stub tests (Wave 0) | 30e3086 |
| 2 | Add generate_run_id and write_run_metadata to run_experiment.py | 9553a00 |
| 3 | Wire --run, --output-root, output path, and metadata.json into main() | d671ee9 |
| 4 | Implement real test assertions in test_run_structure.py | d75dc87 |

## What Was Built

### openevolve/test_run_structure.py (new)

Four pytest tests covering RUNORG-01 and RUNORG-03:
- `test_run_id_format`: verifies `generate_run_id()` format and sanitization (`qwen3-coder:30b` → `qwen3-coder-30b`), plus path-traversal guard (no `/` or `..`)
- `test_run_arg_override`: verifies `runs/myrun/` directory layout and that auto-generated IDs differ from fixed names
- `test_output_root_override`: verifies output goes under the specified root, not the default
- `test_metadata_fields`: verifies all 7 RUNORG-03 keys present in `metadata.json`, correct values, and idempotent prompt append

### openevolve/run_experiment.py (modified)

Three additions:
1. `generate_run_id(config_path)`: reads config, sanitizes model name via regex, returns `YYYY-MM-DD_HHMM_<model>`
2. `write_run_metadata(run_dir, config, run_id, iterations, prompt)`: writes/merges `metadata.json` with read-then-merge pattern
3. `main()` wired with `--run`, `--output-root`, new path construction, path traversal guard (T-03-01), and non-blocking `write_run_metadata` call

## Verification Results

All acceptance criteria met:
- `pytest openevolve/test_run_structure.py -v` — 4 passed
- `python openevolve/run_experiment.py --help` — lists `--run` and `--output-root`
- `generate_run_id('openevolve/config.yaml')` — returns `2026-05-14_1643_qwen3-coder-30b`
- Path traversal test: `--run ../../etc baseline` → "escapes the output root" error
- `pytest openevolve/test_consolidation.py -x` — 6 passed (no regressions)

## Deviations from Plan

None - plan executed exactly as written.

## Known Stubs

None. All four test stubs were replaced with real assertions in Task 4.

## Threat Flags

No new security-relevant surface beyond what is documented in the plan's threat model (T-03-01 through T-03-04). The path traversal mitigation for T-03-01 is implemented as specified.

## Self-Check: PASSED

- [x] `openevolve/test_run_structure.py` exists
- [x] `openevolve/run_experiment.py` modified
- [x] Commit 30e3086 exists (Task 1)
- [x] Commit 9553a00 exists (Task 2)
- [x] Commit d671ee9 exists (Task 3)
- [x] Commit d75dc87 exists (Task 4)
- [x] All 4 tests green

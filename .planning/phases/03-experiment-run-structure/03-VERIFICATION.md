---
phase: 03-experiment-run-structure
verified: 2026-05-14T17:00:00Z
status: passed
score: 13/13 must-haves verified
overrides_applied: 0
re_verification: false
---

# Phase 3: Experiment Run Structure Verification Report

**Phase Goal:** Establish an organized experiment run structure so that each invocation of run_experiment.py is grouped under a named run, display scripts can filter by run, and legacy flat directories are migrated cleanly.
**Verified:** 2026-05-14T17:00:00Z
**Status:** passed
**Re-verification:** No — initial verification

## Goal Achievement

### Observable Truths

| #  | Truth | Status | Evidence |
|----|-------|--------|----------|
| 1  | generate_run_id('config.yaml') returns a string matching YYYY-MM-DD_HHMM_<sanitized-model> | VERIFIED | `generate_run_id` returns e.g. `2026-05-14_1659_qwen3-coder-30b`; regex match confirmed by test and direct CLI call |
| 2  | Model name qwen2.5-coder:32b is sanitized to qwen2-5-coder-32b | VERIFIED | Confirmed by running re.sub logic directly: `'qwen2.5-coder:32b'` → `'qwen2-5-coder-32b'` |
| 3  | run_experiment.py --run <name> uses the supplied name; without --run it auto-generates one | VERIFIED | `main()` lines 181: `run_id = args.run or generate_run_id(config_path)`; --help shows both args |
| 4  | run_experiment.py --output-root <path> directs output to that base instead of openevolve_output | VERIFIED | `output_root = args.output_root or os.path.join(SCRIPT_DIR, "openevolve_output")` at line 180 |
| 5  | output_dir is always runs/<run_id>/cavitydetection/<prompt>/ under the chosen output root | VERIFIED | Lines 182-185: `run_dir = os.path.join(output_root, "runs", run_id)`; `output_dir = os.path.join(run_dir, "cavitydetection", args.prompt)` |
| 6  | metadata.json is written to runs/<run_id>/metadata.json with all six RUNORG-03 fields (plus run_id = 7 total) | VERIFIED | `write_run_metadata` writes 7-field dict; test_metadata_fields verifies all keys present |
| 7  | Repeated run_experiment.py calls with same run_id append prompt to metadata.json without overwriting | VERIFIED | Read-then-merge pattern in `write_run_metadata`; `test_metadata_fields` verifies idempotent append |
| 8  | All non-runs/ subdirectories under openevolve_output/ are moved to runs/legacy/cavitydetection/ | VERIFIED | `migrate_legacy()` uses `skip = {"runs"}` and os.rename; `test_migration_moves` verifies 3 dirs |
| 9  | Migration is idempotent: re-running skips already-migrated dirs without error | VERIFIED | dst existence check before rename; `test_migration_idempotent` verifies second run raises no error |
| 10 | No data loss: results.json and checkpoints survive the rename | VERIFIED | Sentinel file test in `test_migration_idempotent` — writes "data", migrates, reads back "data" |
| 11 | make show-results (no RUN=) displays flat per-prompt table; make show-results RUN=<id> filters to run | VERIFIED | `show_results.py` glob walk; `$(if $(RUN),--run $(RUN),)` in Makefile; dry-run confirms no --run without RUN=, --run legacy with RUN=legacy |
| 12 | make show-consolidated-results RUN=<id> filters consolidated view to specified run | VERIFIED | `show_consolidated.py` extracts run_id per path, filters df; Makefile passes `--run $(RUN)` |
| 13 | make evolve-all generates one RUN_ID before the prompt loop and passes --run $RUN_ID to every invocation | VERIFIED | Makefile line 166: Python subprocess generates RUN_ID once; line 173: `--run $$RUN_ID` in loop |

**Score:** 13/13 truths verified

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `openevolve/run_experiment.py` | CLI runner with --run, --output-root; generate_run_id; write_run_metadata | VERIFIED | All three functions present and wired into main() |
| `openevolve/migrate_legacy.py` | Standalone migration script using os.rename() | VERIFIED | 68 lines; os.rename + shutil.move EXDEV fallback; skip={"runs"} guard |
| `openevolve/show_results.py` | Updated discovery loop walking runs/ tree; --run filter arg | VERIFIED | glob.glob walk; load_result_from_path; --run filter; 0 os.listdir calls in discovery path |
| `openevolve/show_consolidated.py` | Updated results_root to runs/; --run filter; run_id column extraction | VERIFIED | extract_run_id helper; glob walk under openevolve_output/runs; --run argparse |
| `openevolve/test_run_structure.py` | 10 pytest tests (4+2+4 across plans) | VERIFIED | 10 test functions; all 10 pass |
| `Makefile` | evolve-all with RUN_ID generation; show-results/show-consolidated-results with RUN= pass-through | VERIFIED | Lines 163-175 (evolve-all); lines 193-197 (display targets) |

### Key Link Verification

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| run_experiment.py main() | generate_run_id() | args.run or generate_run_id(config_path) | WIRED | Line 181 confirmed |
| run_experiment.py main() | metadata.json | write_run_metadata(run_dir, config, run_id, ...) | WIRED | Lines 187-190 confirmed; non-blocking try/except |
| run_experiment.py main() | path traversal guard | os.path.abspath(run_dir).startswith(os.path.abspath(output_root)) | WIRED | Lines 183-184; test confirms rejection of ../../etc |
| migrate_legacy.py main() | os.rename(src, dst) | migrate_legacy(output_root) | WIRED | Lines 38-43 confirmed |
| os.listdir(output_root) | runs/legacy/cavitydetection/<name>/ | skip={"runs"} filter | WIRED | Line 26: skip = {"runs"} |
| show_results.py main() | glob.glob('runs/**/results.json', recursive=True) | replace os.listdir with glob walk | WIRED | Lines 120-121; zero os.listdir calls in discovery |
| show_consolidated.py | load_results(path) per file | results_root = os.path.join(SCRIPT_DIR, 'openevolve_output', 'runs') | WIRED | Lines 49-61 confirmed; no load_all_results |
| Makefile evolve-all | run_experiment.py --run $$RUN_ID | RUN_ID generated by Python before loop | WIRED | Lines 166, 173 confirmed |

### Data-Flow Trace (Level 4)

| Artifact | Data Variable | Source | Produces Real Data | Status |
|----------|---------------|--------|--------------------|--------|
| show_results.py | rows list | glob.glob → load_result_from_path → load_results(path) | Yes — reads actual results.json from disk | FLOWING |
| show_consolidated.py | df (DataFrame) | glob.glob → load_results(path) per file → pd.concat | Yes — reads actual results.json files | FLOWING |
| run_experiment.py | metadata.json | write_run_metadata reads config dict and writes merged JSON | Yes — reads real config, writes to disk | FLOWING |

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
|----------|---------|--------|--------|
| generate_run_id format | `python -c "from openevolve.run_experiment import generate_run_id; r = generate_run_id('openevolve/config.yaml'); assert re.match(r'^\d{4}-\d{2}-\d{2}_\d{4}_[a-zA-Z0-9-]+$', r)"` | OK 2026-05-14_1659_qwen3-coder-30b | PASS |
| Path traversal rejected | `python run_experiment.py --run ../../etc baseline --iterations 1 2>&1 \| grep -c "escapes the output root"` | 1 | PASS |
| --help shows --run and --output-root | `python run_experiment.py --help` | Both flags present with descriptions | PASS |
| make show-results no RUN= | `make show-results --dry-run` | Command has no --run flag | PASS |
| make show-results RUN=legacy | `make show-results RUN=legacy --dry-run` | Command contains --run legacy | PASS |
| All 10 tests green | `python -m pytest openevolve/test_run_structure.py -v` | 10 passed in 0.17s | PASS |
| Full suite: 16 tests green | `python -m pytest openevolve/ -x` | 16 passed, 1 pre-existing warning | PASS |

### Probe Execution

Step 7c: SKIPPED — no probe-*.sh files declared in this phase; phase is library/script work, not a runnable server. Behavioral spot-checks above substitute.

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|------------|-------------|--------|----------|
| RUNORG-01 | 03-01 | Researcher can identify experiment as named run; auto-generates from timestamp + model; overridable with --run | SATISFIED | generate_run_id(), --run arg, run_id format verified |
| RUNORG-02 | 03-03 | make evolve-all creates one run directory before prompt loop; all prompts share same run ID | SATISFIED | Makefile evolve-all generates RUN_ID once, passes --run $$RUN_ID to each invocation |
| RUNORG-03 | 03-01 | Each run directory contains metadata.json with model, total_iterations, programs, prompts, config_snapshot, start_timestamp | SATISFIED | write_run_metadata writes all 6 required fields (plus run_id as 7th); test_metadata_fields verifies |
| MIGRATE-01 | 03-02 | Existing openevolve_output/baseline/ and prompt1/ migrated to openevolve_output/runs/legacy/cavitydetection/ with no data loss | SATISFIED | migrate_legacy.py uses os.rename + EXDEV fallback; idempotent; sentinel file test confirms data preservation |
| DISPLAY-01 | 03-03 | make show-results and make show-consolidated-results work with new run structure; both accept optional RUN=<id> | SATISFIED | Both scripts use glob walk under runs/; both accept --run; Makefile RUN= pass-through verified by dry-run |

**Orphaned requirements check:** CKPT-01, CKPT-02, CKPT-03, EXPLAIN-01, EXPLAIN-02 are Phase 4 requirements per REQUIREMENTS.md traceability table — not orphaned, correctly deferred.

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| (none) | — | — | — | — |

No TBD, FIXME, or XXX markers found in any of the 6 modified files. No stub patterns. No empty implementations.

### Human Verification Required

None. All observable behaviors are fully verifiable through code inspection and automated tests.

### Gaps Summary

No gaps. All 13 truths verified, all 5 requirement IDs satisfied, all 6 artifacts substantive and wired, all key links confirmed functional. The full test suite (16 tests) passes with no regressions.

---

_Verified: 2026-05-14T17:00:00Z_
_Verifier: Claude (gsd-verifier)_

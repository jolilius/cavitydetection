---
phase: 04-per-step-data-pipeline
verified: 2026-05-14T16:20:00Z
status: human_needed
score: 9/10 must-haves verified
overrides_applied: 0
human_verification:
  - test: "Run a real OpenEvolve experiment with EXPLAIN_GENERATIONS=1 (default) and inspect the generated explanations in the resulting DataFrame."
    expected: "df['explanation'] is non-NaN for every checkpoint row; each explanation mentions actual code changes (e.g. loop reorder, cache locality). The explanation for checkpoint N should reference changes relative to checkpoint N-1 or to initial_program.c for the first checkpoint."
    why_human: "The live LLM call (generate_explanation via Ollama) cannot be exercised in a no-network, no-server verification context. The sliding-window mechanism is verified synthetically, but ROADMAP SC1 ('explanation all populated') and SC3 ('each explanation describes what changed since the previous checkpoint') require a real LLM response."
---

# Phase 4: Per-Step Data Pipeline — Verification Report

**Phase Goal:** Build a checkpoint-based per-step data pipeline so that results.json is populated from checkpoints/checkpoint_N/ directories, each row carries the full Phase 4 schema (checkpoint_iteration, best_found_at_iteration, code, combined_score, mem_score, time_score), and explanation generation runs per-checkpoint with a sliding-window baseline.

**Verified:** 2026-05-14T16:20:00Z
**Status:** human_needed
**Re-verification:** No — initial verification

---

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | results.json is built from checkpoints/checkpoint_N/ sorted numerically | VERIFIED | `_extract_iterations` scans `checkpoints_dir`, sorts with `int(d.replace("checkpoint_",""))`. Real baseline produces 12 rows for checkpoint_5 through checkpoint_80. `test_checkpoint_based_consolidation` asserts `[5,10,15]` order. |
| 2 | Each row carries all six Phase 4 schema fields: checkpoint_iteration, best_found_at_iteration, code, combined_score, mem_score, time_score | VERIFIED | All six fields present in `_extract_iterations` row dict (lines 238-252 of consolidate_results.py). Real baseline smoke check: `{'checkpoint_iteration','best_found_at_iteration','code','combined_score','time_score'} <= set(df.columns)` passes. |
| 3 | time_score is JSON null in every row (D-01) | VERIFIED | `"time_score": None` hard-coded in row dict. Smoke check: `df['time_score'].isna().all()` is True on real baseline (12 rows). `test_checkpoint_load_results` asserts `df["time_score"].isna().all()`. |
| 4 | combined_score equals mem_score in every row (D-02) | VERIFIED | `"combined_score": round(mem_score, 4)` assigned same value as `"mem_score": round(mem_score, 4)`. Smoke check: `(df['combined_score']==df['mem_score']).all()` True on real baseline. |
| 5 | Top-level container key in results.json is still "iterations" (D-03) | VERIFIED | `consolidate_experiment()` body unchanged; `result = {"metadata": ..., "iterations": iterations}` at line 125. Tests confirm `result["iterations"]` access works. |
| 6 | checkpoint_iteration = folder N; best_found_at_iteration = JSON 'iteration' field (D-05) | VERIFIED | `checkpoint_n = int(ckpt_dir.replace("checkpoint_",""))`, `best_found_at = info.get("iteration", checkpoint_n)`. `current_iteration` never used for row building. `test_checkpoint_based_consolidation` verifies divergence: checkpoint_10 has `checkpoint_iteration=10`, `best_found_at_iteration=5`. |
| 7 | load_results() exposes all Phase 4 columns including the new ones | VERIFIED | `results_loader.py` primary_cols includes `checkpoint_iteration` (before `iteration`), `combined_score`, `time_score`. secondary_cols includes `best_found_at_iteration`, `code`. Empty-DataFrame branch lists all 5 new columns. Smoke check returns DataFrame with all 16 columns. |
| 8 | _generate_explanations_for_experiment() walks checkpoints numerically with sliding-window baseline | VERIFIED | Function body confirmed: no `best/best_program_info.json` reference, uses `prev_code = baseline_code` initializer, advances `prev_code = evolved_code` per checkpoint. Synthetic sliding-window test confirms checkpoint_5 compares to baseline, checkpoint_10 compares to checkpoint_5 code, checkpoint_15 compares to checkpoint_10 code. |
| 9 | EXPLAIN_GENERATIONS=0 skips explanation loop; each row's explanation field is absent/None | VERIFIED | Env-var gate at line 256 (`os.environ.get("EXPLAIN_GENERATIONS","1") != "0"`) preserved unchanged. When `generate_explanation is None`, function returns `{}`. Smoke check with `explanations={}` produces `df['explanation'].isna().all()` True. |
| 10 | df['explanation'] is non-NaN for every checkpoint row in a live run; explanations describe actual code changes | UNCERTAIN | The mechanism is verified (test_checkpoint_explanation_threading threads explanations correctly); the real LLM output quality cannot be verified without a live Ollama server. ROADMAP SC1 and SC3 are blocked on human verification. |

**Score:** 9/10 truths verified

---

### Deferred Items

None.

---

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `openevolve/consolidate_results.py` | Checkpoint-scanning `_extract_iterations()` replacing best/-only fallback | VERIFIED | `_extract_iterations` scans `checkpoints/checkpoint_N/` numerically; emits all 6 Phase 4 fields; signature unchanged (`best_info` kept for backward compat). `iteration_runtime_seconds` absent from checkpoint rows. |
| `openevolve/results_loader.py` | Extended column ordering covering Phase 4 fields | VERIFIED | All 5 new columns (`checkpoint_iteration`, `best_found_at_iteration`, `code`, `combined_score`, `time_score`) present in empty-DataFrame branch and column ordering blocks. `checkpoint_iteration` is first in primary_cols. |
| `openevolve/run_experiment.py` | Per-checkpoint explanation loop replacing best/-only explanation | VERIFIED | `_generate_explanations_for_experiment` body replaced; no `best/best_program_info.json` or `program_source` references; sliding-window `prev_code`; dict keyed by integer folder N. Call site and EXPLAIN_GENERATIONS gate unchanged. |
| `openevolve/migrate_legacy.py` | `regenerate_results()` helper + `--regenerate` CLI flag | VERIFIED | `regenerate_results` function present; `--regenerate` argparse flag present; `shutil.copy2` backup before overwrite; inline `from consolidate_results import consolidate_experiment` import guard. |
| `openevolve/test_consolidation.py` | 9-test suite passing (6 legacy + 3 Phase 4 tests) | VERIFIED | All 9 tests pass with exit code 0. Three new Phase 4 tests: `test_checkpoint_based_consolidation`, `test_checkpoint_load_results`, `test_checkpoint_explanation_threading`. Three legacy best/-fixture tests converted to checkpoint fixtures. |
| `openevolve/test_run_structure.py` | 12-test suite passing (10 legacy + 2 Phase 4 tests) | VERIFIED | All 12 tests pass with exit code 0. Two new tests: `test_regenerate_flag` (asserts byte-for-byte backup, 2-row regenerated results, D-09/D-10, Pitfall 5 skip path), `test_regenerate_no_legacy_dir` (graceful no-op). |

---

### Key Link Verification

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| `consolidate_results.py::_extract_iterations` | `results_loader.py::load_results` | shared row schema (`iteration` alias + new columns) | VERIFIED | `_extract_iterations` emits `"iteration": checkpoint_n` as alias; `load_results` sorts on `"iteration"` unchanged. `test_checkpoint_load_results` exercises full round-trip. |
| `test_consolidation.py::test_checkpoint_based_consolidation` | `consolidate_results.py::consolidate_experiment` | synthetic `checkpoints/checkpoint_{5,10,15}/` tree + assertion on iterations rows | VERIFIED | Test creates tree, calls `consolidate_experiment`, asserts on all 6 schema fields and numeric sort order. |
| `run_experiment.py::_generate_explanations_for_experiment` | `explanation_generator.py::generate_explanation` | per-checkpoint sliding-window call | VERIFIED | Function calls `generate_explanation(evolved_code=..., baseline_code=prev_code, ...)` per checkpoint. Stub test confirms sliding window advances correctly. |
| `run_experiment.py` (call site ~line 261) | `consolidate_results.py::_extract_iterations` | `explanations` dict keyed by integer folder N | VERIFIED | `explanations[n] = explanation` uses integer n. Call site passes `explanations=explanations` to `consolidate_experiment`. `_extract_iterations` looks up `explanations[checkpoint_n]`. |
| `migrate_legacy.py::regenerate_results` | `consolidate_results.py::consolidate_experiment` | inline import + called per experiment dir | VERIFIED | `from consolidate_results import consolidate_experiment` inside `regenerate_results()` body. Called as `consolidate_experiment(output_dir=exp_dir)`. `test_regenerate_flag` verifies end-to-end. |
| `migrate_legacy.py::regenerate_results` | `shutil.copy2` backup of results.json | always-before-overwrite (D-10) | VERIFIED | `shutil.copy2(results_path, backup_path)` called before `consolidate_experiment`. Test asserts byte-for-byte fidelity of backup. |

---

### Data-Flow Trace (Level 4)

| Artifact | Data Variable | Source | Produces Real Data | Status |
|----------|--------------|--------|--------------------|--------|
| `results_loader.py::load_results` | `df` (DataFrame) | `consolidate_results.py::_extract_iterations` reading `best_program_info.json` + `best_program.c` from checkpoint dirs | Yes — real baseline: 12 rows, code min length 9935 chars | FLOWING |
| `run_experiment.py::_generate_explanations_for_experiment` | `explanations` (dict) | `generate_explanation()` LLM call per checkpoint | Mechanism verified; live LLM output requires human test | STATIC (mechanism wired; live data path needs human test) |

---

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
|----------|---------|--------|--------|
| test_consolidation.py 9/9 tests pass | `../openevolve/.venv/bin/python openevolve/test_consolidation.py` | exit 0, all 9 `passed` lines printed | PASS |
| test_run_structure.py 12/12 tests pass | `../openevolve/.venv/bin/python openevolve/test_run_structure.py` | exit 0, all 12 `PASSED` lines printed | PASS |
| Real baseline produces 12 rows with all Phase 4 columns | `consolidate_experiment + load_results` on real data | rows=12, all 6 Phase 4 columns present, time_score all NaN | PASS |
| Sliding-window explanation mechanism | Stub LLM test: ckpt_5 vs baseline, ckpt_10 vs ckpt_5, ckpt_15 vs ckpt_10 | All three comparisons match expected code lengths | PASS |
| EXPLAIN_GENERATIONS=0 path | Manually set `generate_explanation=None` | Returns `{}` immediately | PASS |
| load_all_results aggregates multiple runs | Synthetic two-run tree | Returns 2 rows with both prompts | PASS |

---

### Probe Execution

No probe scripts declared in phase plans. Step 7c: SKIPPED (no probe files found).

---

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|------------|-------------|--------|---------|
| CKPT-01 | 04-01 | `results.json` built from `checkpoints/checkpoint_N/` sorted numerically | SATISFIED | `_extract_iterations` scans and sorts numerically. Real baseline: 12 rows for checkpoints 5–80. `test_checkpoint_based_consolidation` asserts `[5,10,15]`. |
| CKPT-02 | 04-01 | Each row includes all 6 schema fields | SATISFIED | All fields present in row dict and in DataFrame. Source checks and smoke test both pass. |
| CKPT-03 | 04-01 | `load_results()` returns one row per checkpoint with all schema fields | SATISFIED | DataFrame has one row per checkpoint dir. All 5 new columns present via column ordering block. `test_checkpoint_load_results` and smoke check pass. |
| EXPLAIN-01 | 04-02 | One LLM explanation per checkpoint, comparing to previous checkpoint | SATISFIED (mechanism) / NEEDS HUMAN (live output) | Sliding-window loop implemented and verified synthetically. Live LLM quality needs human test. |
| EXPLAIN-02 | 04-02 | Explanations stored in results.json and exposed as `df['explanation']` | SATISFIED (mechanism) | `_extract_iterations` threads explanations by folder N; `load_results` ensures explanation column. `test_checkpoint_explanation_threading` passes. Live data needs human test. |

---

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| All 6 modified files | — | No TBD/FIXME/XXX/HACK/PLACEHOLDER markers found | — | None |

No stub implementations found in the modified files. The only intentional `None` values (`time_score: None`, `combined_score = mem_score`) are documented by design decisions D-01 and D-02 and are tested explicitly.

---

### Human Verification Required

#### 1. Live LLM Explanation Quality

**Test:** Run a live experiment with explanations enabled:
```sh
cd /home/jolilius/home/src/cavitydetection
EXPLAIN_GENERATIONS=1 ../openevolve/.venv/bin/python openevolve/run_experiment.py baseline --iterations 10
```
Then load the results:
```python
import sys; sys.path.insert(0, 'openevolve')
from results_loader import load_results
df = load_results('openevolve/openevolve_output/runs/<run_id>/cavitydetection/baseline/results.json')
print(df[['checkpoint_iteration', 'explanation']].to_string())
```

**Expected:**
- `df['explanation'].notna().all()` is True (every checkpoint row has an explanation, satisfying ROADMAP SC1)
- Each explanation string mentions actual code changes (loop reorder, memory layout, etc.) — satisfying ROADMAP SC3
- The first checkpoint's explanation references changes vs `initial_program.c`; subsequent checkpoints reference changes vs the previous checkpoint's code

**Why human:** Requires a live Ollama server with the configured model. The sliding-window mechanism is fully verified synthetically, but the LLM output content and non-null guarantee can only be confirmed with a real LLM response.

---

### Gaps Summary

No automated gaps found. The only unverified item (Truth #10) requires a live LLM and is routed to human verification. All 9/10 mechanically verifiable truths pass:

- Checkpoint-based scan with numeric sort: VERIFIED
- Six Phase 4 schema fields per row: VERIFIED
- D-01 (time_score=null), D-02 (combined_score=mem_score), D-03 (iterations key), D-04 (signature unchanged), D-05 (best_found_at_iteration from JSON iteration field): all VERIFIED
- Column ordering in load_results(): VERIFIED
- Sliding-window explanation mechanism: VERIFIED
- EXPLAIN_GENERATIONS=0 path: VERIFIED
- migrate_legacy.py --regenerate with backup-before-overwrite: VERIFIED
- All test suites (9/9 + 12/12) pass with exit 0: VERIFIED

---

_Verified: 2026-05-14T16:20:00Z_
_Verifier: Claude (gsd-verifier)_

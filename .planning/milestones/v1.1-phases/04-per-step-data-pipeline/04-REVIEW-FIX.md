---
phase: 04-per-step-data-pipeline
fixed_at: 2026-05-15T04:53:00Z
review_path: .planning/phases/04-per-step-data-pipeline/04-REVIEW.md
iteration: 1
findings_in_scope: 5
fixed: 5
skipped: 0
status: all_fixed
---

# Phase 04: Code Review Fix Report

**Fixed at:** 2026-05-15T04:53:00Z
**Source review:** .planning/phases/04-per-step-data-pipeline/04-REVIEW.md
**Iteration:** 1

**Summary:**
- Findings in scope: 5
- Fixed: 5
- Skipped: 0

## Fixed Issues

### CR-01: `--run` path traversal bypasses `runs/` containment

**Files modified:** `openevolve/run_experiment.py`
**Commit:** fa3f3a1
**Applied fix:** Added an alphanumeric regex validation on `args.run` at argument-parse time (same pattern as prompt). Also tightened the path guard: instead of checking `startswith(abspath(output_root))`, it now builds `runs_dir = abspath(output_root)/runs/` (with trailing separator) and asserts the resolved `run_dir` falls under that subtree. Both defenses together prevent `../evil` from escaping the `runs/` directory.

---

### CR-02: Falsy `or`-chain silently replaces `mem_score=0.0` with `1.0`

**Files modified:** `openevolve/consolidate_results.py`
**Commit:** 2fa6fb8
**Applied fix:** Replaced the falsy `or`-chain `metrics.get("mem_score") or metrics.get("combined_score") or 1.0` with explicit `None`-checks using two intermediate variables (`_ms`, `_cs`) and a conditional expression. A `mem_score` of `0.0` is now preserved rather than silently falling through to `1.0`.

---

### WR-01: `convergence_iteration` reports checkpoint folder N instead of actual best-found generation

**Files modified:** `openevolve/consolidate_results.py`
**Commit:** 5beea9a
**Applied fix:** Changed `convergence_iteration = best_iter["iteration"]` to `best_iter.get("best_found_at_iteration", best_iter["iteration"])`. This reads the `best_found_at_iteration` field (which holds the OpenEvolve generation number from `best_program_info.json`) with a fallback to the `iteration` alias if the field is absent, giving semantically correct convergence-speed metadata.

---

### WR-02: Empty-string explanations stored in rows; `None` explanations are not

**Files modified:** `openevolve/consolidate_results.py`
**Commit:** e3065fa
**Applied fix:** Changed the guard in `_extract_iterations` from `if explanation is not None` to `if explanation` (truthy check). Both `None` and `""` now result in the `explanation` key being omitted from the row, making the behavior consistent and preventing mixed `explanation=""` / `explanation=NaN` states in loaded DataFrames.

---

### WR-03: Temp config placed in `SCRIPT_DIR` and leaks on `yaml.dump` failure

**Files modified:** `openevolve/run_experiment.py`
**Commit:** cb1e2d2
**Applied fix:** Replaced `tempfile.NamedTemporaryFile(dir=SCRIPT_DIR, delete=False)` with `tempfile.mkstemp()` (system temp dir). The file descriptor is captured first so `tmp_config` is bound before `yaml.dump` runs; the `finally` block now uses `if os.path.exists(tmp_config): os.unlink(tmp_config)` so cleanup is safe even if `yaml.dump` raises. Temp files no longer appear in the source tree on crash.

---

_Fixed: 2026-05-15T04:53:00Z_
_Fixer: Claude (gsd-code-fixer)_
_Iteration: 1_

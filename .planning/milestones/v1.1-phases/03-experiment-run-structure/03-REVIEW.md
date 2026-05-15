---
phase: 03-experiment-run-structure
reviewed: 2026-05-14T00:00:00Z
depth: standard
files_reviewed: 6
files_reviewed_list:
  - Makefile
  - openevolve/migrate_legacy.py
  - openevolve/run_experiment.py
  - openevolve/show_consolidated.py
  - openevolve/show_results.py
  - openevolve/test_run_structure.py
findings:
  critical: 3
  warning: 5
  info: 3
  total: 11
status: fixed
---

# Phase 03: Code Review Report

**Reviewed:** 2026-05-14T00:00:00Z
**Depth:** standard
**Files Reviewed:** 6
**Status:** issues_found

## Summary

This phase introduces structured experiment run directories (`runs/<run_id>/cavitydetection/<prompt>/`), a migration script for legacy flat output, and two display scripts. Cross-referenced `consolidate_results.py` and `results_loader.py` as called modules.

Three critical bugs were found: `migrate_legacy.py` destroys non-prompt OpenEvolve infrastructure directories (`best/`, `checkpoints/`, `logs/`) with no undo path; `run_experiment.py` has a path traversal allowing `args.prompt` to escape `cavitydetection/`; and `write_run_metadata` crashes on a corrupt `metadata.json` file.  Additionally, the `args.run or generate_run_id()` fallback in `run_experiment.py` silently breaks the "one run groups all prompts" invariant when the Makefile's `RUN_ID` generation fails.

---

## Critical Issues

### CR-01: migrate_legacy destroys OpenEvolve infrastructure directories

**File:** `openevolve/migrate_legacy.py:26-44`
**Issue:** The skip set is `{"runs"}` only. The actual `openevolve_output/` directory contains `best/`, `checkpoints/`, and `logs/` as top-level siblings of the prompt directories (`baseline/`, `prompt1/`). These are OpenEvolve's own output directories — `best/` contains `best_program_info.json` and `best_program.c`; `checkpoints/` contains hundreds of iteration snapshots; `logs/` contains run logs. `migrate_legacy` moves all of them into `runs/legacy/cavitydetection/`, treating them as if they were prompt experiments. This permanently relocates data OpenEvolve expects to find at its original paths and may corrupt future runs that try to resume. The move is irreversible on the same filesystem (rename).

**Fix:**
```python
# Add all known OpenEvolve infrastructure dirs to the skip set:
skip = {"runs", "best", "checkpoints", "logs", "archive"}
for name in sorted(os.listdir(output_root)):
    if name in skip:
        continue
    src = os.path.join(output_root, name)
    if not os.path.isdir(src):
        continue
    # Only migrate dirs that look like prompt experiments (contain results.json
    # or best/best_program_info.json):
    has_results = os.path.isfile(os.path.join(src, "results.json"))
    has_best    = os.path.isfile(os.path.join(src, "best", "best_program_info.json"))
    if not (has_results or has_best):
        continue
    ...
```

---

### CR-02: Path traversal via args.prompt escapes cavitydetection/ output directory

**File:** `openevolve/run_experiment.py:167-185`
**Issue:** `args.prompt` is used directly as a path component in two places without sanitization:
1. `prompt_file = os.path.join(SCRIPT_DIR, "prompts", f"{args.prompt}.txt")` — only validated by `os.path.isfile(prompt_file)`, which prevents reading non-existent files but does not prevent path traversal if a crafted `.txt` file exists outside `prompts/`.
2. `output_dir = os.path.join(run_dir, "cavitydetection", args.prompt)` — **not validated at all**. A value like `../../../tmp` resolves to a path outside `run_dir`. The existing path traversal guard (line 183) only protects `run_id`, not `args.prompt`. OpenEvolve writes its entire output tree under `output_dir`, so this can direct writes outside the intended tree.

**Fix:**
```python
# After parsing args, reject any prompt name containing path separators or dots:
if not re.match(r'^[a-zA-Z0-9_-]+$', args.prompt):
    sys.exit(f"Error: prompt name must be alphanumeric with underscores/hyphens, got: {args.prompt!r}")

# Alternatively, use os.path.basename to strip any traversal:
prompt_name = os.path.basename(args.prompt)
if prompt_name != args.prompt:
    sys.exit(f"Error: prompt name must not contain path separators: {args.prompt!r}")
```

---

### CR-03: write_run_metadata crashes on corrupt metadata.json — unhandled JSONDecodeError

**File:** `openevolve/run_experiment.py:134-136`
**Issue:** `write_run_metadata` opens and parses the existing `metadata.json` with `json.load(f)` but does not catch `json.JSONDecodeError`. If the file is truncated or corrupt (e.g., interrupted write from a previous run), this raises an unhandled exception. The call site at line 187-190 does catch `Exception`, so the failure is swallowed with a warning — but that means the metadata is never written, silently losing the current run's metadata.

**Fix:**
```python
def write_run_metadata(run_dir: str, config: dict, run_id: str, iterations: int, prompt: str) -> None:
    meta_path = os.path.join(run_dir, "metadata.json")
    existing = {}
    if os.path.isfile(meta_path):
        try:
            with open(meta_path) as f:
                existing = json.load(f)
        except (IOError, json.JSONDecodeError) as e:
            print(f"Warning: Could not read existing metadata.json (will overwrite): {e}", file=sys.stderr)
            existing = {}
    ...
```

---

## Warnings

### WR-01: args.run uses falsy-check instead of None-check — silently breaks run grouping when RUN_ID is empty

**File:** `openevolve/run_experiment.py:181`
**Issue:** `run_id = args.run or generate_run_id(config_path)` uses Python's falsy test. In `evolve-all`, the Makefile generates `RUN_ID` via a subprocess call (line 166 of Makefile). If that call fails or `generate_run_id` raises, bash sets `RUN_ID` to an empty string and passes `--run ""` to each `run_experiment.py` invocation. Because `""` is falsy, each prompt call auto-generates its own run_id, silently placing each prompt under a different run directory. The user sees `Run ID: ` (blank) in the Makefile echo, then results are scattered across multiple runs rather than grouped.

**Fix:**
```python
# Use explicit None check instead of falsy check:
run_id = args.run if args.run is not None else generate_run_id(config_path)
```
The Makefile should also fail-fast if `RUN_ID` is empty:
```makefile
@RUN_ID=$$($(OPENEVOLVE_PYTHON) -c "...generate_run_id(...)"); \
if [ -z "$$RUN_ID" ]; then echo "ERROR: Failed to generate run ID" >&2; exit 1; fi; \
```

---

### WR-02: Double-write of results.json — consolidate_experiment already writes the file

**File:** `openevolve/run_experiment.py:262-265`
**Issue:** `consolidate_experiment()` writes `{output_dir}/results.json` internally (see `consolidate_results.py:131-135`), then returns the dict. `run_experiment.py` then immediately overwrites the same file with `json.dump(result, f, indent=2)` (lines 264-265). The two writes produce identical content. The redundant write is harmless today, but it creates a maintenance trap: if `consolidate_experiment` is refactored to write a different serialization (e.g., streaming, compression), the second write would silently revert it.

**Fix:** Remove the redundant write in `run_experiment.py`:
```python
result = consolidate_experiment(...)
results_path = os.path.join(output_dir, "results.json")
# consolidate_experiment already writes this file; just confirm it exists:
if os.path.isfile(results_path):
    print(f"✓ Consolidated results: {results_path}")
else:
    print(f"Warning: results.json was not created at {results_path}", file=sys.stderr)
```

---

### WR-03: load_consolidated_result and load_result use legacy flat path — dead code in show_results.py

**File:** `openevolve/show_results.py:31-84`
**Issue:** `load_consolidated_result`, `load_legacy_result`, and `load_result` all read from the old flat path (`OUTPUT_ROOT/<prompt_name>/results.json` or `OUTPUT_ROOT/<prompt_name>/best/best_program_info.json`). These functions are never called from `main()`, which exclusively uses `load_result_from_path` operating under the new `runs/` tree. These three functions are dead code. Their presence creates confusion about which loading path is authoritative, and `load_legacy_result` contains logic that would give wrong results if ever wired up (it approximates `accesses = int(REFERENCE_ACCESSES / score)` without access to actual accesses).

**Fix:** Remove `load_consolidated_result`, `load_legacy_result`, and `load_result` from `show_results.py`, or mark them with a clear deprecation notice if retained for future use.

---

### WR-04: show_consolidated.py and show_results.py have no --output-root flag — inconsistent with run_experiment.py

**File:** `openevolve/show_consolidated.py:49` and `openevolve/show_results.py:27`
**Issue:** `run_experiment.py` accepts `--output-root` to redirect where experiments are written. Neither display script (`show_consolidated.py`, `show_results.py`) accepts a corresponding flag — they hardcode `SCRIPT_DIR/openevolve_output`. When a user runs experiments with a custom `--output-root`, the display scripts silently show no results (or different results). The `show-consolidated-results` Makefile target does not pass `--output-root` either.

**Fix:** Add `--output-root` argument to both display scripts:
```python
parser.add_argument("--output-root", default=None,
    help="Override output base directory (default: openevolve/openevolve_output/)")
args = parser.parse_args()
results_root = os.path.join(args.output_root or SCRIPT_DIR, "openevolve_output", "runs")
```

---

### WR-05: Makefile evolve-all does not propagate --output-root to run_experiment.py

**File:** `Makefile:163-175`
**Issue:** The `evolve-all` target hardcodes the output path by not passing `--output-root` to `run_experiment.py`. If a user sets `OUTPUT_ROOT` or similar to redirect output, `evolve-all` ignores it. There is no documented way to override the output directory via the Makefile interface. Combined with WR-04, this means the `--output-root` feature in `run_experiment.py` has no end-to-end Makefile support.

**Fix:** Add an `OUTPUT_ROOT` make variable and thread it through:
```makefile
OUTPUT_ROOT ?=
evolve-all:
    ...
    $(OPENEVOLVE_PYTHON) openevolve/run_experiment.py $$p \
        --run $$RUN_ID \
        $(if $(OUTPUT_ROOT),--output-root $(OUTPUT_ROOT),) \
        --iterations $${ITERATIONS:-80}; \
```

---

## Info

### IN-01: test_run_arg_override and test_output_root_override are tautological — never exercise production code

**File:** `openevolve/test_run_structure.py:60-91`
**Issue:** Both tests create directories with `os.makedirs`, then assert `os.path.isdir` on the directories they just created. They never call `run_experiment.main()` or exercise any production path-building logic. The tests would pass even if `run_experiment.py` were deleted. The docstrings claim they test `--run <name>` and `--output-root` behavior, but that claim is false.

**Fix:** Replace with tests that invoke `run_experiment.main()` (via `unittest.mock.patch` for `subprocess.run`) and assert on the resulting `output_dir` and `run_dir` paths actually constructed by the production code.

---

### IN-02: Misleading "..." suffix when explanation is shorter than 80 characters

**File:** `openevolve/run_experiment.py:112`
**Issue:** `print(f"  Explanation: {explanation[:80]}...", file=sys.stderr)` always appends `...` even when the explanation is 80 characters or fewer, implying truncation that did not occur.

**Fix:**
```python
preview = explanation[:80]
suffix = "..." if len(explanation) > 80 else ""
print(f"  Explanation: {preview}{suffix}", file=sys.stderr)
```

---

### IN-03: errno magic number 18 used instead of errno.EXDEV

**File:** `openevolve/migrate_legacy.py:40`
**Issue:** `if e.errno == 18:` uses a raw integer. The `errno` module provides `errno.EXDEV` (cross-device link error) for readability and portability. The `errno` module is not imported in this file.

**Fix:**
```python
import errno as errno_mod
...
except OSError as e:
    if e.errno == errno_mod.EXDEV:  # cross-device link
        shutil.move(src, str(dst))
    else:
        raise
```

---

_Reviewed: 2026-05-14T00:00:00Z_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_

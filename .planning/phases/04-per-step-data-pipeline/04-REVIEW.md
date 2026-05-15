---
phase: 04-per-step-data-pipeline
reviewed: 2026-05-14T16:00:03Z
depth: standard
files_reviewed: 6
files_reviewed_list:
  - openevolve/test_consolidation.py
  - openevolve/consolidate_results.py
  - openevolve/results_loader.py
  - openevolve/run_experiment.py
  - openevolve/test_run_structure.py
  - openevolve/migrate_legacy.py
findings:
  critical: 2
  warning: 3
  info: 3
  total: 8
status: fixed
fixed_at: 2026-05-15T00:00:00Z
fixed_findings: [CR-01, CR-02, WR-01, WR-02, WR-03]
open_findings: [IN-01, IN-02, IN-03]
---

# Phase 04: Code Review Report

**Reviewed:** 2026-05-14T16:00:03Z
**Depth:** standard
**Files Reviewed:** 6
**Status:** issues_found

## Summary

Six files were reviewed: the checkpoint-based consolidation pipeline (`consolidate_results.py`, `results_loader.py`), the experiment runner (`run_experiment.py`), legacy migration (`migrate_legacy.py`), and the two test suites (`test_consolidation.py`, `test_run_structure.py`). The implementation is mostly well-structured but contains two blockers: a path-traversal bypass in the `--run` argument handler that allows experiment data to escape the `runs/` subdirectory, and a logic error in the `mem_score` fallback chain that silently corrupts score data when a checkpoint records a zero score. Three additional warnings cover a semantic bug in `convergence_iteration`, an empty-string explanation inconsistency, and a temp-file leak. Three info-level findings cover the `_extract_llm_model` path, a degenerate model-name edge case, and an invalid-schema helper in tests.

---

## Critical Issues

### CR-01: `--run` path traversal bypasses `runs/` containment

**File:** `openevolve/run_experiment.py:207-209`

**Issue:** The `--run` CLI argument accepts any string including path components (e.g., `../evil`). The guard on line 208 checks whether the resolved path is under `output_root`, but `../evil` resolves to `output_root/evil` which _does_ start with `output_root` (string prefix), so the guard passes. The resulting `run_dir` is `output_root/evil/` — outside the intended `output_root/runs/` tree. Experiment data, metadata.json, and results.json are then written there, silently corrupting the directory structure without any error.

Concrete demonstration:
```python
output_root = "/home/user/openevolve_output"
run_id      = "../evil"
run_dir     = os.path.join(output_root, "runs", run_id)
# run_dir = "/home/user/openevolve_output/runs/../evil"
# abspath  = "/home/user/openevolve_output/evil"
# startswith("/home/user/openevolve_output") => True  # guard passes
```

**Fix:** Validate `--run` input with the same alphanumeric regex used for `prompt`, or tighten the guard to require the resolved path to be inside `output_root/runs/`:
```python
# Option 1: reject non-safe run IDs at argument parse time
if args.run is not None and not re.match(r'^[a-zA-Z0-9_-]+$', args.run):
    sys.exit(f"Error: --run value must be alphanumeric with underscores/hyphens, got: {args.run!r}")

# Option 2 (belt-and-suspenders): fix the guard to check under runs/
runs_dir = os.path.join(os.path.abspath(output_root), "runs") + os.sep
if not os.path.abspath(run_dir).startswith(runs_dir):
    sys.exit(f"Error: --run value escapes the runs/ directory: {run_id}")
```

---

### CR-02: Falsy `or`-chain silently replaces `mem_score=0.0` with `1.0`

**File:** `openevolve/consolidate_results.py:227`

**Issue:** The expression:
```python
mem_score = metrics.get("mem_score") or metrics.get("combined_score") or 1.0
```
uses Python's truthiness evaluation. If `metrics["mem_score"]` is `0.0` (valid: a candidate that accesses infinitely more memory than baseline), the `or` chain skips it and falls through to `combined_score`, then `1.0`. The checkpoint row is then recorded as having a score of `1.0` — baseline performance — instead of the actual zero score. This silently discards a meaningful data point and can make a catastrophically bad candidate look like the baseline.

While `mem_score == 0.0` is unusual in practice, it is a valid output from the evaluator when a candidate's instrumented binary reports zero accesses (e.g., due to a compilation or linking failure returning exit 0).

**Fix:**
```python
mem_score = (
    metrics.get("mem_score")
    if metrics.get("mem_score") is not None
    else metrics.get("combined_score")
    if metrics.get("combined_score") is not None
    else 1.0
)
```
Or equivalently:
```python
def _first_not_none(*values, default=1.0):
    for v in values:
        if v is not None:
            return v
    return default

mem_score = _first_not_none(
    metrics.get("mem_score"),
    metrics.get("combined_score"),
    default=1.0,
)
```

---

## Warnings

### WR-01: `convergence_iteration` in metadata reports checkpoint folder N, not actual best-found generation

**File:** `openevolve/consolidate_results.py:93-99`

**Issue:** `convergence_iteration` is computed as:
```python
best_iter = min(iterations, key=lambda x: x["memory_accesses"])
convergence_iteration = best_iter["iteration"]   # line 99
```
The `"iteration"` field in each row is the backward-compatibility alias set to `checkpoint_n` (the folder number), NOT the `best_found_at_iteration` field which records the actual OpenEvolve generation at which the best program was found. For example, if checkpoint folder `10` contains the best score but its `best_program_info.json` says `"iteration": 5` (the generation when that best was first found), `convergence_iteration` is reported as `10`, not `5`. The metadata field is therefore misleading and will cause incorrect analysis of convergence speed.

**Fix:**
```python
best_iter = min(iterations, key=lambda x: x["memory_accesses"])
best_memory_accesses = best_iter["memory_accesses"]
# Use best_found_at_iteration for semantic correctness
convergence_iteration = best_iter.get("best_found_at_iteration", best_iter["iteration"])
```

---

### WR-02: Empty-string explanations stored in rows; `None` explanations are not — silent inconsistency

**File:** `openevolve/run_experiment.py:125` and `openevolve/consolidate_results.py:256-259`

**Issue:** In `_generate_explanations_for_experiment`, the result of `generate_explanation()` is stored unconditionally:
```python
explanations[n] = explanation   # line 125 — stored even if ""
```
In `_extract_iterations`, the guard `if explanation is not None` (line 258) passes for empty string `""`. So a checkpoint whose LLM call returns an empty string gets `row["explanation"] = ""`, while a checkpoint whose LLM call returns `None` (API error) gets no `"explanation"` key at all. When loaded into a DataFrame, the first row has `explanation=""` while the second has `explanation=NaN`. Code that filters with `df["explanation"].notna()` will include the empty-string row and exclude the `NaN` row, producing different results even though both represent "no useful explanation available."

**Fix:** Treat both `None` and empty string as "no explanation":
```python
# In consolidate_results.py _extract_iterations:
if explanations and checkpoint_n in explanations:
    explanation = explanations[checkpoint_n]
    if explanation:   # truthy check: filters both None and ""
        row["explanation"] = explanation
```

---

### WR-03: Temp config file is placed in the source tree (`SCRIPT_DIR`) and leaks on `yaml.dump` failure

**File:** `openevolve/run_experiment.py:235-239`

**Issue:** The temporary config YAML is written with `dir=SCRIPT_DIR` (the `openevolve/` directory inside the project). Two problems:

1. **Leak path**: `tmp_config = tmp.name` is assigned on line 239, after `yaml.dump` on line 238. If `yaml.dump` raises (e.g., non-serializable config value), the `NamedTemporaryFile` has been created with `delete=False` but `tmp_config` is unbound — the file leaks into `SCRIPT_DIR` and is never cleaned up. The `try/finally` block (lines 241-298) does not cover the `with` block.

2. **Source tree pollution**: `.tmp_config_*.yaml` files in `SCRIPT_DIR` appear in `git status` if the process is killed (SIGKILL) before `os.unlink` runs. The `.gitignore` does not list this prefix pattern.

**Fix:** Use `tempfile.gettempdir()` instead of `SCRIPT_DIR`, and capture the filename before calling `yaml.dump`:
```python
import tempfile
tmp_fd, tmp_config = tempfile.mkstemp(suffix=".yaml", prefix=".tmp_config_")
try:
    with os.fdopen(tmp_fd, "w") as tmp:
        yaml.dump(config, tmp, default_flow_style=False, allow_unicode=True)
    subprocess.run([python, run_script, ..., "--config", tmp_config, ...], check=True)
    ...
finally:
    if os.path.exists(tmp_config):
        os.unlink(tmp_config)
```

---

## Info

### IN-01: `_extract_llm_model` always returns `"unknown"` for the new `runs/` directory structure

**File:** `openevolve/consolidate_results.py:284`

**Issue:**
```python
config_path = os.path.join(os.path.dirname(output_dir), "config.yaml")
```
When `output_dir` follows the new layout (`openevolve_output/runs/<run-id>/cavitydetection/<prompt>/`), `os.path.dirname(output_dir)` is `.../cavitydetection/`, and `config.yaml` is looked for at `.../cavitydetection/config.yaml`. The actual `config.yaml` lives at `openevolve/config.yaml` (three levels up). This function will always fall through to `return "unknown"` for all experiments run under the new structure, meaning all `metadata.llm_model` fields in results.json will be `"unknown"`.

**Fix:** Walk up parent directories looking for `config.yaml`, or pass the model name in from `run_experiment.py` (which already loads the config):
```python
# In run_experiment.py, pass model to consolidate_experiment:
consolidate_experiment(
    output_dir=output_dir,
    ...,
    llm_model=config.get("llm", {}).get("primary_model", "unknown"),
)

# In consolidate_results.py, add llm_model parameter:
def consolidate_experiment(..., llm_model: str = "unknown") -> dict:
    ...
    metadata["llm_model"] = llm_model
```

---

### IN-02: `generate_run_id` produces a trailing-underscore run ID when model name sanitizes to empty string

**File:** `openevolve/run_experiment.py:135-146`

**Issue:** If `config.yaml` contains a model name composed entirely of special characters (e.g., `"::"` or `"---"`), the sanitization produces an empty string after `strip("-")`:
```python
sanitized = re.sub(r"[^a-zA-Z0-9-]+", "-", model)
sanitized = re.sub(r"-+", "-", sanitized).strip("-")
# "::".sanitized = ""
return f"{ts}_{sanitized}"   # "2026-01-01_1200_"
```
The resulting run ID ends with an underscore (`"2026-01-01_1200_"`), which also fails the regex assertion in `test_run_id_format` (`[a-zA-Z0-9-]+` requires at least one character after the final `_`).

**Fix:** Guard against empty sanitized output:
```python
sanitized = sanitized or "unknown-model"
return f"{ts}_{sanitized}"
```

---

### IN-03: `_write_minimal_results_json` in tests writes an invalid JSON schema (list, not dict)

**File:** `openevolve/test_run_structure.py:220-235`

**Issue:** The helper writes a bare JSON array:
```python
data = [{"iteration": 1, "memory_accesses": ..., ...}]
```
but `load_results()` expects a dict with `"metadata"` and `"iterations"` keys and raises `KeyError` on the list format. The three tests that call this helper (`test_show_results_run_filter`, `test_show_results_all`, `test_show_consolidated_run_filter`) happen to work only because they never call `load_results()` — they only perform glob and path-extraction operations. If any future test reuses this helper expecting a loadable fixture, it will fail with a cryptic `KeyError`.

**Fix:** Write a valid schema or rename the helper to make its limitation explicit:
```python
def _write_minimal_results_json(path: str, prompt: str) -> None:
    """Write a minimal (glob-only) results.json stub. NOT loadable via load_results()."""
    ...
```
Or write a conforming schema:
```python
data = {
    "metadata": {"prompt_variant": prompt, "program": "cavitydetection",
                 "timestamp": "2026-01-01T00:00:00Z", "llm_model": "unknown",
                 "total_iterations": 1},
    "baseline_metrics": {"memory_accesses": 128862705,
                         "memory_reads": 64431352, "memory_writes": 64431353},
    "iterations": [{"iteration": 1, "memory_accesses": 100000000,
                    "mem_score": 1.29, "improvement_percent": 22.4}],
}
```

---

_Reviewed: 2026-05-14T16:00:03Z_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_

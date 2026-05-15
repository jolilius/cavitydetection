# Phase 4: Per-Step Data Pipeline - Research

**Researched:** 2026-05-14
**Domain:** Python data pipeline / checkpoint-based consolidation / LLM explanation generation
**Confidence:** HIGH

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

- **D-01:** `time_score = null` in every checkpoint row — forward-compatible placeholder.
- **D-02:** `combined_score = mem_score` in every checkpoint row — evaluator already sets both equal; keeps field present for future multi-objective scoring.
- **D-03:** JSON container key stays `"iterations"` (not renamed to `"checkpoints"`) — backward compatibility with any code reading `results.json` directly.
- **D-04:** Replace `_extract_iterations()` in `consolidate_results.py` in-place (same file, same public `consolidate_experiment()` signature). Old `best/`-only fallback is removed.
- **D-05:** `checkpoint_iteration` = folder number N in `checkpoint_N/`; `best_found_at_iteration` = `iteration` field in `best_program_info.json`.
- **D-06:** Explanations generated at END of `run_experiment.py` (post-run, not mid-loop), iterating over all checkpoints in order.
- **D-07:** `EXPLAIN_GENERATIONS=0` controls checkpoint explanations — reuse existing flag, no new flag. When 0, all explanation fields are `null`.
- **D-08:** Each checkpoint explanation compares `best_program.c` at checkpoint N to `best_program.c` at checkpoint N-1. Checkpoint 0 (first) compares to `initial_program.c`.
- **D-09:** `migrate_legacy.py` gets a `--regenerate` flag; iterates migrated experiment dirs, backs up `results.json` as `results.json.v1`, regenerates from checkpoints.
- **D-10:** `results.json.v1` backup always created before overwriting. `--regenerate` is opt-in.

### Claude's Discretion

- Checkpoint sort key implementation (e.g., `sorted(dirs, key=lambda d: int(d.replace('checkpoint_', '')))`)
- Whether explanation generation in `run_experiment.py` reuses `_generate_explanations_for_experiment()` helper internals or calls `generate_explanation()` directly per checkpoint
- Error handling when a checkpoint directory is incomplete (missing `best_program.c` or `best_program_info.json`) — skip with warning

### Deferred Ideas (OUT OF SCOPE)

- **Time measurement / time_score** — Real per-checkpoint timing data deferred to a future phase.

</user_constraints>

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| CKPT-01 | `results.json` built from `checkpoints/checkpoint_N/` directories sorted by iteration number | Verified: checkpoint dirs exist at `checkpoints/checkpoint_5/`, `checkpoint_10/`, ..., `checkpoint_80/`; sort key `int(d.replace('checkpoint_', ''))` works |
| CKPT-02 | Each checkpoint row includes: `checkpoint_iteration`, `best_found_at_iteration`, `code`, `combined_score`, `mem_score`, `time_score` | Verified: `best_program_info.json` has `iteration` (best-found) and `current_iteration` (checkpoint saved-at); `best_program.c` present in every checkpoint dir |
| CKPT-03 | `load_results()` returns DataFrame with one row per checkpoint including code, metrics, explanation; `load_all_results()` aggregates | Verified: current `load_results()` creates DataFrame from `iterations` array; new columns need adding to column-order list |
| EXPLAIN-01 | One LLM explanation per checkpoint comparing to previous checkpoint's `best_program.c`; first checkpoint compares to `initial_program.c` | Verified: `generate_explanation(evolved_code, baseline_code, llm_config, explanation_prompt_text)` already handles per-pair LLM call |
| EXPLAIN-02 | Explanations stored in `results.json` per checkpoint row, exposed as `df['explanation']` | Verified: explanation field already threaded through `consolidate_experiment()` via `explanations` dict param; pattern established in Phase 2 |

</phase_requirements>

---

## Summary

Phase 4 replaces the current "best-only" single-row consolidation with a full checkpoint trajectory. Instead of reading `best/best_program_info.json` once, `_extract_iterations()` scans every `checkpoints/checkpoint_N/` directory, reads `best_program.c` (full C source) and `best_program_info.json` (metrics), and emits one row per checkpoint. The `explanations` dict passed to `consolidate_experiment()` changes from `{iteration_num: text}` (one entry) to `{checkpoint_N: text}` (one entry per checkpoint directory number).

The existing infrastructure already supports this shape: `consolidate_experiment()` accepts an arbitrary `explanations` dict keyed by iteration number; `generate_explanation()` already handles per-pair LLM calls with timeouts and graceful None returns; `load_results()` already promotes the `iterations` array into a DataFrame. The work is: (1) rewrite `_extract_iterations()` to scan checkpoints, (2) rewrite the explanation-generation loop in `run_experiment.py` to iterate checkpoints instead of just the `best/` result, (3) add new columns to `load_results()`, and (4) add `--regenerate` to `migrate_legacy.py`.

The key real-data insight: in the baseline experiment, `iteration` and `current_iteration` in `best_program_info.json` diverge across checkpoints — `iteration: 5` is the generation at which the best solution was first found, while `current_iteration: 80` is the generation when checkpoint_80 was written. Both remain equal only in checkpoint_5. This is the exact `checkpoint_iteration` vs `best_found_at_iteration` distinction captured in D-05.

**Primary recommendation:** Replace `_extract_iterations()` in-place, drive the new per-checkpoint explanation loop from `run_experiment.py`, thread the `explanations` dict (keyed by checkpoint folder number N) into `consolidate_experiment()` unchanged, and extend `load_results()` column ordering to include `checkpoint_iteration`, `best_found_at_iteration`, `code`, `combined_score`, and `time_score`.

---

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Checkpoint directory scanning | Data pipeline (`consolidate_results.py`) | — | `_extract_iterations()` owns filesystem traversal |
| C source extraction | Data pipeline (`consolidate_results.py`) | — | Reads `best_program.c` alongside `best_program_info.json` |
| Explanation generation loop | Orchestration (`run_experiment.py`) | LLM call (`explanation_generator.py`) | Phase 2 pattern: `run_experiment.py` drives the loop, `generate_explanation()` makes the LLM call |
| Schema emission (results.json) | Data pipeline (`consolidate_results.py`) | — | `consolidate_experiment()` writes the file |
| DataFrame loading | Loader (`results_loader.py`) | — | `load_results()` / `load_all_results()` |
| Legacy regeneration | Migration (`migrate_legacy.py`) | Data pipeline | `--regenerate` calls `consolidate_experiment()` after backup |

---

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Python stdlib (`os`, `json`, `shutil`, `argparse`) | 3.x | File traversal, JSON I/O, CLI flags | Already used throughout; no new deps needed |
| pandas | existing in venv | DataFrame construction | Already imported in `results_loader.py` |
| requests | existing in venv | LLM HTTP call in `explanation_generator.py` | Already used; no change |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| yaml | existing in venv | Config reading in `run_experiment.py` | Already imported; used for `EXPLAIN_GENERATIONS` check |

No new package installations required for this phase. [VERIFIED: codebase grep]

---

## Architecture Patterns

### Recommended Project Structure

No new files at the project root level. Phase 4 modifies these existing files:

```
openevolve/
├── consolidate_results.py   # _extract_iterations() rewritten
├── results_loader.py        # load_results() column list extended
├── run_experiment.py        # explanation loop replaces _generate_explanations_for_experiment() internals
├── migrate_legacy.py        # --regenerate flag added
└── test_consolidation.py    # new checkpoint-based tests added
```

One new test file may be added:

```
openevolve/
└── test_checkpoint_pipeline.py   # Phase 4 specific tests (checkpoint schema, code column, explanation threading)
```

### Pattern 1: Checkpoint Directory Scanning

**What:** Sort checkpoint directories numerically by the suffix N, read `best_program_info.json` and `best_program.c` from each.

**When to use:** Inside the new `_extract_iterations()` implementation.

```python
# Source: CONTEXT.md Specific Ideas + verified against real checkpoint dirs
import os, json

def _extract_iterations(output_dir, best_info, baseline_accesses, explanations=None):
    checkpoints_dir = os.path.join(output_dir, "checkpoints")
    if not os.path.isdir(checkpoints_dir):
        return []

    dirs = [
        d for d in os.listdir(checkpoints_dir)
        if d.startswith("checkpoint_") and os.path.isdir(os.path.join(checkpoints_dir, d))
    ]
    dirs.sort(key=lambda d: int(d.replace("checkpoint_", "")))

    rows = []
    for ckpt_dir in dirs:
        checkpoint_n = int(ckpt_dir.replace("checkpoint_", ""))
        ckpt_path = os.path.join(checkpoints_dir, ckpt_dir)

        info_path = os.path.join(ckpt_path, "best_program_info.json")
        code_path = os.path.join(ckpt_path, "best_program.c")

        if not os.path.isfile(info_path) or not os.path.isfile(code_path):
            print(f"Warning: skipping incomplete checkpoint {ckpt_dir}", ...)
            continue

        with open(info_path) as f:
            info = json.load(f)
        with open(code_path) as f:
            code = f.read()

        metrics = info.get("metrics", {})
        mem_score = metrics.get("mem_score", 1.0)
        best_found_at = info.get("iteration", checkpoint_n)   # D-05

        memory_accesses = int(baseline_accesses / mem_score) if mem_score > 0 else baseline_accesses
        improvement_percent = (baseline_accesses - memory_accesses) / baseline_accesses * 100

        row = {
            "checkpoint_iteration": checkpoint_n,              # D-05: folder N
            "best_found_at_iteration": best_found_at,          # D-05: JSON "iteration"
            "code": code,                                      # CKPT-02
            "mem_score": round(mem_score, 4),
            "combined_score": round(mem_score, 4),             # D-02
            "time_score": None,                                # D-01
            "memory_accesses": memory_accesses,
            "improvement_percent": round(improvement_percent, 2),
            # backward compat: keep "iteration" == checkpoint_iteration for callers
            "iteration": checkpoint_n,
        }

        if explanations and checkpoint_n in explanations:
            explanation = explanations[checkpoint_n]
            if explanation is not None:
                row["explanation"] = explanation

        rows.append(row)

    return rows
```

### Pattern 2: Per-Checkpoint Explanation Loop in run_experiment.py

**What:** After OpenEvolve finishes, iterate checkpoints in order, carry previous checkpoint's code to use as `baseline_code` for the next call to `generate_explanation()`.

**When to use:** In `run_experiment.py`, replacing the body of `_generate_explanations_for_experiment()` or replacing its call site.

```python
# Source: CONTEXT.md D-06, D-07, D-08
def _generate_checkpoint_explanations(output_dir, initial_code, llm_config, explanation_prompt):
    """Generate per-checkpoint explanations; return dict {checkpoint_N: text}."""
    checkpoints_dir = os.path.join(output_dir, "checkpoints")
    if not os.path.isdir(checkpoints_dir):
        return {}

    dirs = sorted(
        [d for d in os.listdir(checkpoints_dir) if d.startswith("checkpoint_")],
        key=lambda d: int(d.replace("checkpoint_", ""))
    )

    explanations = {}
    prev_code = initial_code  # D-08: checkpoint 0 compares to initial_program.c

    for ckpt_dir in dirs:
        n = int(ckpt_dir.replace("checkpoint_", ""))
        code_path = os.path.join(checkpoints_dir, ckpt_dir, "best_program.c")
        if not os.path.isfile(code_path):
            prev_code = prev_code  # skip, keep previous
            continue
        with open(code_path) as f:
            evolved_code = f.read()

        explanation = generate_explanation(
            evolved_code=evolved_code,
            baseline_code=prev_code,   # D-08: compare to previous checkpoint
            llm_config=llm_config,
            explanation_prompt_text=explanation_prompt,
        )
        explanations[n] = explanation  # None on failure is valid (skipped gracefully)
        prev_code = evolved_code       # advance sliding window

    return explanations
```

### Pattern 3: results.json.v1 Backup in migrate_legacy.py

**What:** Before overwriting `results.json`, create `results.json.v1` backup. Then call `consolidate_experiment()` with the checkpoint-based logic.

```python
# Source: CONTEXT.md D-09, D-10
import shutil

def regenerate_results(output_dir: str) -> None:
    results_path = os.path.join(output_dir, "results.json")
    backup_path = os.path.join(output_dir, "results.json.v1")

    if os.path.isfile(results_path):
        shutil.copy2(results_path, backup_path)   # D-10: always backup first
        print(f"Backed up: {results_path} -> {backup_path}")

    consolidate_experiment(output_dir=output_dir)
    print(f"Regenerated: {results_path}")
```

### Pattern 4: load_results() Column Extension

**What:** Add new Phase 4 columns to the ordered column list and empty-DataFrame column list in `load_results()`.

**When to use:** In `results_loader.py` only. The JSON shape drives what lands in the DataFrame; `load_results()` just needs to include new column names in its ordering and empty-schema definitions.

```python
# Source: current results_loader.py lines 143-189
primary_cols = [
    "checkpoint_iteration",       # NEW Phase 4
    "iteration",                  # backward compat alias
    "prompt",
    "memory_accesses",
    "improvement_percent",
    "mem_score",
    "combined_score",             # NEW Phase 4
    "time_score",                 # NEW Phase 4
]
secondary_cols = [
    "best_found_at_iteration",    # NEW Phase 4
    "code",                       # NEW Phase 4 (full C source)
    "memory_reads",
    "memory_writes",
    "iteration_runtime_seconds",
]
explanation_cols = ["explanation"]
metadata_cols = ["timestamp", "baseline_accesses", "program"]
```

### Anti-Patterns to Avoid

- **Reading `best/best_program_info.json` for checkpoint data:** The `best/` directory represents a single final snapshot; checkpoint history is in `checkpoints/checkpoint_N/`. After Phase 4, `_load_best_result()` can still be called for convergence metadata in the `metadata` block, but `_extract_iterations()` must not use it to populate rows.
- **Keying the explanations dict by JSON `iteration` field:** The JSON `iteration` field is the generation at which that solution was first found, not the checkpoint folder N. The `explanations` dict must be keyed by folder N (which becomes `checkpoint_iteration`). D-05 is the rule; mismatching keys silently drops all explanations.
- **Stripping the `"iteration"` field from rows:** `load_results()` currently sorts by `"iteration"`; removing it breaks the sort. Keep `"iteration": checkpoint_n` as a backward-compat alias alongside `"checkpoint_iteration"`.
- **Storing `best_program.c` content in the `explanations` dict:** The `explanations` dict is `{N: explanation_text_or_None}`. Code content is a separate `"code"` field in the row dict. Conflating these breaks the consolidation schema.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| LLM HTTP call with timeouts | Custom requests wrapper | `generate_explanation()` in `explanation_generator.py` | Already handles timeout, connection error, HTTP 4xx/5xx, JSON parse failure, empty response — all return None gracefully |
| JSON backup before overwrite | Custom backup logic | `shutil.copy2(src, dst)` | Preserves metadata; one line |
| Checkpoint numeric sort | Custom string sort | `sorted(dirs, key=lambda d: int(d.replace('checkpoint_', '')))` | Handles `checkpoint_5` before `checkpoint_10` (lexicographic sort would fail) |

**Key insight:** All LLM error handling is already in `explanation_generator.py`. The per-checkpoint loop just calls `generate_explanation()` N times and collects the results; it does not need to replicate the retry/timeout logic.

---

## Common Pitfalls

### Pitfall 1: iteration vs current_iteration vs checkpoint folder N

**What goes wrong:** Using `current_iteration` from `best_program_info.json` as `checkpoint_iteration` instead of parsing the folder name.

**Why it happens:** `current_iteration` looks like it should be the checkpoint number, but it equals the generation at which the checkpoint was written — which matches the folder N only for the final checkpoint. For intermediate checkpoints, `current_iteration` equals the folder N, but `iteration` (best-found generation) may be earlier.

**Real data:** In `baseline/checkpoints/checkpoint_10/best_program_info.json`:
- `"iteration": 5` — best solution first found at generation 5
- `"current_iteration": 10` — this checkpoint was written at generation 10

So `checkpoint_iteration = 10` (folder), `best_found_at_iteration = 5` (JSON `"iteration"` field). [VERIFIED: codebase inspection]

**How to avoid:** Always parse `checkpoint_N` from the directory name for `checkpoint_iteration`; always read `info.get("iteration", N)` for `best_found_at_iteration`.

**Warning signs:** All rows have identical `checkpoint_iteration` values, or rows where `checkpoint_iteration < best_found_at_iteration`.

### Pitfall 2: explanations dict key mismatch

**What goes wrong:** Explanations silently not attached to rows because `explanations[key]` never matches `row["checkpoint_iteration"]`.

**Why it happens:** The explanations loop uses one key type (e.g., from JSON `iteration`) while `_extract_iterations()` looks up by checkpoint folder N.

**How to avoid:** Both the explanation generation loop and `_extract_iterations()` must key by the same value: folder N (the integer from `checkpoint_N/`).

**Warning signs:** `df['explanation'].isna().all()` is True even after explanations_enabled=True run.

### Pitfall 3: `code` column is very large

**What goes wrong:** `results.json` becomes very large when storing full C source per checkpoint. With 12 checkpoints and ~10 KB of C source each, results.json grows by ~120 KB per experiment.

**Why it happens:** The `code` column stores the full text of `best_program.c` (~10,490 bytes verified in baseline/checkpoints/checkpoint_5).

**How to avoid:** This is acceptable for the researcher use case (explicit requirement CKPT-02). No compression or truncation. Just be aware when reading the file in tests — use smaller synthetic C source strings.

**Warning signs:** Tests using real checkpoint files are slow to load; mitigate in tests by using a short synthetic code string (e.g., 20 chars).

### Pitfall 4: load_results() sort key missing after column rename

**What goes wrong:** `df = df.sort_values("iteration")` raises KeyError if "iteration" is dropped from rows.

**Why it happens:** Phase 4 introduces `checkpoint_iteration` as the primary key, tempting the implementer to omit the old `"iteration"` field.

**How to avoid:** Keep `"iteration": checkpoint_n` in the row dict as a backward-compat alias. `load_results()` already sorts by `"iteration"` and `load_all_results()` sorts by `["prompt", "iteration"]`. Both work unchanged if `"iteration"` equals `checkpoint_n`.

### Pitfall 5: --regenerate on runs/ tree vs legacy flat tree

**What goes wrong:** `--regenerate` iterates over the output_root directly and tries to regenerate non-experiment directories (e.g., `runs/` itself), crashing when no `checkpoints/` subdirectory exists.

**Why it happens:** `migrate_legacy.py` currently uses `output_root` as the scan root. After migration, experiments live at `runs/legacy/cavitydetection/<name>/`.

**How to avoid:** The `--regenerate` loop must walk the same tree as `migrate_legacy()` targets — i.e., scan `runs/legacy/cavitydetection/*/` for directories that have a `checkpoints/` subdirectory. Use the same filter logic: check `os.path.isdir(os.path.join(exp_dir, "checkpoints"))`.

---

## Code Examples

### Verified checkpoint schema (real data)

```json
// Source: openevolve/openevolve_output/baseline/checkpoints/checkpoint_5/best_program_info.json
{
  "id": "55f029ed-4b57-46ab-9665-31fcd2d1c18c",
  "generation": 2,
  "iteration": 5,
  "current_iteration": 5,
  "metrics": {
    "mem_score": 1.1549639188008396
  },
  "language": "cpp",
  "timestamp": 1778574353.4207096,
  "saved_at": 1778574353.4281893
}
```

```json
// Source: openevolve/openevolve_output/baseline/checkpoints/checkpoint_10/best_program_info.json
{
  "id": "55f029ed-4b57-46ab-9665-31fcd2d1c18c",
  "iteration": 5,
  "current_iteration": 10,
  "metrics": { "mem_score": 1.1549639188008396 }
}
```

Observation: `iteration` (5) stays constant across checkpoints 5 through 80 in the baseline experiment — the same solution was the best throughout the run. `current_iteration` advances with the folder number.

### Verified checkpoint directory listing

```
baseline/checkpoints/:
  checkpoint_5/    checkpoint_10/   checkpoint_15/   checkpoint_20/
  checkpoint_25/   checkpoint_30/   checkpoint_35/   checkpoint_40/
  checkpoint_45/   checkpoint_50/   checkpoint_55/   checkpoint_80/
```

12 checkpoints total. Note the gap: checkpoint_55 to checkpoint_80 (no checkpoint_60..75). This confirms checkpoints are not guaranteed to be evenly spaced in all runs. [VERIFIED: filesystem inspection]

### Contents of each checkpoint directory

```
checkpoint_5/
  best_program.c          (287 lines / ~10,490 bytes — full C source)
  best_program_info.json  (metrics, iteration fields)
  metadata.json           (MAP-Elites island state — not needed for Phase 4)
  programs/               (per-candidate program files — not needed for Phase 4)
```

### generate_explanation() call signature

```python
# Source: openevolve/explanation_generator.py lines 47-52
def generate_explanation(
    evolved_code: str,
    baseline_code: str,
    llm_config: dict,
    explanation_prompt_text: str,
) -> Optional[str]:
    # Returns str (1-2 sentences) or None on any failure
```

### consolidate_experiment() public signature (unchanged)

```python
# Source: openevolve/consolidate_results.py lines 28-37
def consolidate_experiment(
    output_dir: str,
    program: str = "cavitydetection",
    prompt_variant: Optional[str] = None,
    baseline_accesses: int = 128_862_705,
    explanations: Optional[dict] = None,
    explanation_prompt_text: Optional[str] = None,
    prompt_version: str = "1.0",
) -> dict:
```

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| `best/`-only single row | Checkpoint-per-row trajectory | Phase 4 | Researcher sees full evolution, not just final result |
| Explanation for best iteration only | Explanation per checkpoint (delta vs previous) | Phase 4 | Researcher follows reasoning at each step |
| `code` column absent | `code` = full C source per checkpoint | Phase 4 | Researcher can `print(df.iloc[N]['code'])` and see compilable C |

**Deprecated/outdated after Phase 4:**
- `_load_best_result()` usage as the sole source of iteration data: still called for `metadata.convergence_iteration` and `metadata.best_memory_accesses`, but no longer used to populate `iterations` rows.
- `_generate_explanations_for_experiment()` body: its internals (reads from `best/best_program_info.json`, generates one explanation) are replaced. The function may be repurposed, renamed, or its internals replaced entirely — call site in `run_experiment.py` changes.

---

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | Phase 3 migration is complete and legacy experiments live at `runs/legacy/cavitydetection/<name>/` before `--regenerate` is used | Common Pitfalls §5 | `--regenerate` scans wrong paths; no data loss but zero regeneration |

Note: Phase 3 run structure (`openevolve_output/runs/`) does not yet exist on disk — confirmed by `ls openevolve/openevolve_output/runs/` returning "missing". This is expected: Phase 3 is coded but no new runs have been executed. The `--regenerate` path in `migrate_legacy.py` must handle the case where `runs/legacy/` does exist (post-migration) but be safe to call even when it doesn't.

---

## Open Questions

1. **Should `_load_best_result()` still be called in `consolidate_experiment()` after the rewrite?**
   - What we know: It reads `best/best_program_info.json` and is currently used to populate `iterations` (to be replaced) and as input to convergence metadata calculation.
   - What's unclear: After checkpoint-based `_extract_iterations()`, convergence metadata can be computed from the rows directly (min `memory_accesses` across checkpoint rows). `_load_best_result()` becomes redundant.
   - Recommendation: Keep the call for now (non-breaking); derive `convergence_iteration` and `best_memory_accesses` from the checkpoint rows instead of from `best_info`. Simplifies the code; `_load_best_result()` can be removed in a cleanup phase.

2. **`load_all_results()` currently walks `openevolve_output/` recursively — should it switch to `runs/` subtree only?**
   - What we know: Current `load_all_results()` uses `os.walk(results_root)` and picks up any `results.json`. With the new run tree, it will correctly find `runs/*/cavitydetection/*/results.json` as long as `results_root` is still `openevolve_output`.
   - What's unclear: Whether legacy flat results (pre-migration) should still be picked up.
   - Recommendation: No change needed for Phase 4. The existing `os.walk` traversal continues to work. `show_results.py` and `show_consolidated.py` already use `runs/` glob patterns; `load_all_results()` is separate and more general.

---

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Python (pandas, json, os) | All pipeline code | Yes | existing venv | — |
| requests | explanation_generator.py | Yes | existing venv | — |
| Ollama / LLM API | Explanation generation | Not checked at research time | — | EXPLAIN_GENERATIONS=0 disables explanations entirely |
| `openevolve/initial_program.c` | First-checkpoint explanation baseline | Yes | confirmed on disk | — |
| `checkpoints/checkpoint_N/best_program.c` | Code column population | Yes (baseline experiment verified) | — | Skip checkpoint with warning |

**Missing dependencies with no fallback:** None for code execution. LLM availability is optional (gated by `EXPLAIN_GENERATIONS=0`).

---

## Validation Architecture

`workflow.nyquist_validation` is absent from `.planning/config.json` — treated as enabled.

### Test Framework
| Property | Value |
|----------|-------|
| Framework | Plain Python assertions (no pytest; existing tests use `python script.py` pattern) |
| Config file | None |
| Quick run command | `../openevolve/.venv/bin/python openevolve/test_consolidation.py` |
| Full suite command | `../openevolve/.venv/bin/python openevolve/test_consolidation.py && ../openevolve/.venv/bin/python openevolve/test_run_structure.py` |

### Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| CKPT-01 | `_extract_iterations()` scans `checkpoints/checkpoint_N/` sorted numerically | unit | `../openevolve/.venv/bin/python openevolve/test_consolidation.py` | Needs new test in test_consolidation.py |
| CKPT-02 | Checkpoint row has `checkpoint_iteration`, `best_found_at_iteration`, `code`, `combined_score`, `mem_score`, `time_score` | unit | `../openevolve/.venv/bin/python openevolve/test_consolidation.py` | Needs new test |
| CKPT-03 | `load_results()` returns one row per checkpoint with all schema fields | unit | `../openevolve/.venv/bin/python openevolve/test_consolidation.py` | Needs new test |
| EXPLAIN-01 | Explanation generated per checkpoint, comparing to previous (or initial) | unit | `../openevolve/.venv/bin/python openevolve/test_consolidation.py` | Needs new test |
| EXPLAIN-02 | `df['explanation']` populated per checkpoint row in loaded DataFrame | unit | `../openevolve/.venv/bin/python openevolve/test_consolidation.py` | Needs new test |
| D-10 | `--regenerate` creates `results.json.v1` backup before overwriting | unit | `../openevolve/.venv/bin/python openevolve/test_run_structure.py` | Needs new test |

### Sampling Rate
- **Per task commit:** `../openevolve/.venv/bin/python openevolve/test_consolidation.py`
- **Per wave merge:** Both test files
- **Phase gate:** Both test files green before `/gsd-verify-work`

### Wave 0 Gaps

New test functions to add to **existing** test files (no new test file strictly required, though one may be created for clarity):

- [ ] `test_checkpoint_based_consolidation()` in `test_consolidation.py` — creates synthetic `checkpoints/checkpoint_N/` tree, runs `consolidate_experiment()`, verifies one row per checkpoint with correct `checkpoint_iteration`, `best_found_at_iteration`, `code`, `combined_score`, `time_score` fields
- [ ] `test_checkpoint_explanation_threading()` in `test_consolidation.py` — explanations dict keyed by checkpoint N passed through `consolidate_experiment()` and surfaced in `df['explanation']`
- [ ] `test_regenerate_flag()` in `test_run_structure.py` — creates synthetic experiment dir with existing `results.json`, calls `migrate_legacy --regenerate`, asserts `results.json.v1` backup created and `results.json` updated

*(If no gaps: "None — existing test infrastructure covers all phase requirements")*

The existing test baseline (`test_consolidation()` and `test_consolidate_with_explanations()` etc.) passes as of research date. [VERIFIED: ran `test_consolidation.py`, all 6 tests passed]

---

## Security Domain

`security_enforcement` is absent from `.planning/config.json` — treated as enabled by default. However, this phase involves no authentication, no user-facing API, no secret handling, no network-exposed services, and no privilege escalation. The only external call is to a local Ollama HTTP endpoint (localhost or Tailscale private IP), which is already gated behind `EXPLAIN_GENERATIONS` env var. No ASVS controls are newly introduced.

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | No | — |
| V3 Session Management | No | — |
| V4 Access Control | No | — |
| V5 Input Validation | Minimal | Checkpoint dir name parsed with `int()` — raises ValueError on malformed names, safe to let propagate as skip-with-warning |
| V6 Cryptography | No | — |

No new threat patterns introduced beyond those already present in Phase 2 (LLM API call to localhost).

---

## Sources

### Primary (HIGH confidence)
- Codebase inspection — `openevolve/consolidate_results.py` lines 168–236 (current `_extract_iterations()` body)
- Codebase inspection — `openevolve/results_loader.py` lines 85–195 (`load_results()` full implementation)
- Codebase inspection — `openevolve/run_experiment.py` lines 47–114 (`_generate_explanations_for_experiment()`)
- Codebase inspection — `openevolve/explanation_generator.py` lines 47–170 (`generate_explanation()`)
- Codebase inspection — `openevolve/migrate_legacy.py` (full `migrate_legacy()` function)
- Filesystem inspection — `openevolve/openevolve_output/baseline/checkpoints/` (12 real checkpoint directories confirmed)
- Filesystem inspection — `checkpoint_5/best_program_info.json` and `checkpoint_10/best_program_info.json` (schema and divergence of `iteration` vs `current_iteration` verified)
- Filesystem inspection — `checkpoint_5/best_program.c` (287 lines, 10,490 bytes)

### Secondary (MEDIUM confidence)
- CONTEXT.md decisions D-01 through D-10 — locked user decisions; treated as authoritative constraints

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — no new dependencies; all libraries already present in venv
- Architecture: HIGH — all integration points verified against actual source code
- Pitfalls: HIGH — iteration/current_iteration divergence verified against real checkpoint data
- Test patterns: HIGH — existing test structure inspected and run successfully

**Research date:** 2026-05-14
**Valid until:** 2026-06-14 (stable internal codebase; no external API dependencies for the data pipeline itself)

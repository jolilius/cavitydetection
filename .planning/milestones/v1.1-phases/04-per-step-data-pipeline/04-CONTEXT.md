# Phase 4: Per-Step Data Pipeline - Context

**Gathered:** 2026-05-14
**Status:** Ready for planning

<domain>
## Phase Boundary

Replace the current "best-only" consolidation with checkpoint-based consolidation so that every `checkpoints/checkpoint_N/` directory becomes a row in `results.json` — with the full C source at that step, a comparison explanation vs. the previous checkpoint, and all available metrics. `load_results()` and `load_all_results()` return one row per checkpoint; the researcher gains a full trajectory view without changing the call sites.

Delivers: rewritten `_extract_iterations()` in `consolidate_results.py`, updated `results_loader.py`, explanation generation per-checkpoint (inline, skippable), and a `--regenerate` flag on `migrate_legacy.py` to rebuild legacy `results.json` from checkpoints with `.v1` backup.

</domain>

<decisions>
## Implementation Decisions

### Checkpoint Schema (CKPT-02)
- **D-01:** `time_score = null` in every checkpoint row — forward-compatible placeholder for when OpenEvolve adds real timing data. Real time measurement is deferred to a future phase.
- **D-02:** `combined_score = mem_score` in every checkpoint row — the evaluator already sets both to the same value; copying it keeps the field present for future multi-objective scoring.
- **D-03:** The JSON container key stays `"iterations"` (not renamed to `"checkpoints"`) — preserves compatibility with any analysis code that reads `results.json` directly. The rows inside change (checkpoint-based) but the top-level key is unchanged.

### Code Structure
- **D-04:** Replace `_extract_iterations()` in `consolidate_results.py` in-place (same file, same public `consolidate_experiment()` signature). New implementation scans `checkpoints/checkpoint_N/` sorted numerically; old `best/`-only fallback is removed.
- **D-05:** `checkpoint_iteration` comes from the folder number N in `checkpoint_N/` (not `current_iteration` from `best_program_info.json`). `best_found_at_iteration` comes from the `iteration` field in `best_program_info.json`.

### Explanation Generation
- **D-06:** Explanations are generated at the END of `run_experiment.py` (after OpenEvolve finishes and checkpoints are written), iterating over all checkpoints in order. This is "inline during run" in the sense that a single `run_experiment.py` invocation produces both results and explanations — but generation happens post-run, not mid-loop.
- **D-07:** `EXPLAIN_GENERATIONS=0` (existing Phase 2 flag) controls checkpoint explanations — reuse the same flag, no new flag needed. When `EXPLAIN_GENERATIONS=0`, all explanation fields are `null`.
- **D-08:** Each checkpoint explanation compares `best_program.c` at checkpoint N to `best_program.c` at checkpoint N-1. For checkpoint 0 (the first checkpoint), compare to `initial_program.c` (baseline).

### Legacy Compatibility
- **D-09:** Legacy migration adds a `--regenerate` flag to `migrate_legacy.py`. When run, it iterates over migrated experiment directories, backs up existing `results.json` as `results.json.v1`, and regenerates `results.json` from checkpoints using the new consolidation logic.
- **D-10:** `results.json.v1` backup is always created before overwriting — provides a rollback path. The `--regenerate` flag is opt-in; migration alone (without `--regenerate`) only moves directories.

### Claude's Discretion
- How to sort checkpoint directories numerically (e.g., `sorted(dirs, key=lambda x: int(x.split('_')[1]))`) — implementation detail.
- Whether explanation generation inside `run_experiment.py` reuses the existing `_generate_explanations_for_experiment()` helper or calls `generate_explanation()` directly per-checkpoint.
- Error handling when a checkpoint directory is incomplete (missing `best_program.c` or `best_program_info.json`) — skip with warning.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Requirements
- `.planning/REQUIREMENTS.md` — Full v1.1 requirements; Phase 4 section defines CKPT-01 through CKPT-03 and EXPLAIN-01/EXPLAIN-02 with exact schema fields

### Core files to modify
- `openevolve/consolidate_results.py` — `consolidate_experiment()` public API stays unchanged; `_extract_iterations()` private function gets replaced. Read lines 168–250 (current fallback logic) before touching.
- `openevolve/results_loader.py` — `load_results()` and `load_all_results()` read `results.json`; understand current schema parsing before modifying.
- `openevolve/run_experiment.py` — Calls `consolidate_experiment()` at end of run and currently calls `_generate_explanations_for_experiment()`. Explanation generation for checkpoints hooks here.
- `openevolve/explanation_generator.py` — `generate_explanation(evolved_code, baseline_code, llm_config, explanation_prompt_text)` is the per-pair LLM call to reuse.
- `openevolve/migrate_legacy.py` — Add `--regenerate` flag and backup/regenerate logic here.

### Reference data
- `openevolve/openevolve_output/baseline/checkpoints/checkpoint_5/best_program_info.json` — Real checkpoint file showing actual schema: `{id, generation, iteration, current_iteration, metrics: {mem_score}, language, timestamp, saved_at}`. Only `mem_score` exists; `combined_score` and `time_score` are absent.
- `openevolve/initial_program.c` — Baseline source for first-checkpoint explanations (comparison target for checkpoint 0).

### Tests
- `openevolve/test_consolidation.py` — Existing test patterns for `consolidate_experiment()`; new tests follow same structure.
- `openevolve/test_run_structure.py` — Pattern for new Phase 4 test file.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `generate_explanation(evolved_code, baseline_code, llm_config, explanation_prompt_text)` in `explanation_generator.py` — already handles the per-pair LLM call, timeouts, and None return on failure. Call once per checkpoint pair.
- `_generate_explanations_for_experiment(output_dir, config, explanation_prompt_text)` in `run_experiment.py` — currently generates per-iteration explanations from `best/best_program.c`. The per-checkpoint version replaces its internals but can reuse its error handling and config loading.
- `consolidate_experiment()` public signature: `(output_dir, program, prompt_variant, baseline_accesses, explanations, explanation_prompt_text, prompt_version)` — unchanged. The `explanations` dict parameter (iteration → text) becomes checkpoint_N → text.

### Established Patterns
- Checkpoint directories: `checkpoints/checkpoint_5/`, `checkpoint_10/`, … — numeric suffix, always multiples of 5 with current OpenEvolve config. Sort with `int(x.split('_')[1])`.
- `best_program_info.json` fields: `iteration` (when this solution was first found) and `current_iteration` (when this checkpoint was saved) are DIFFERENT — `checkpoint_iteration` = folder N, `best_found_at_iteration` = JSON's `iteration` field.
- `EXPLAIN_GENERATIONS` env var already checked in `run_experiment.py` line ~240 and in Makefile — reuse the same check.

### Integration Points
- `run_experiment.py` end-of-run: after `consolidate_experiment()` returns, iterate checkpoints and call `generate_explanation()` per pair, then re-write `results.json` with explanations filled in (or pass explanations dict to `consolidate_experiment()` — same as Phase 2 pattern).
- `load_results()` in `results_loader.py`: currently maps `iterations` array to DataFrame rows with columns `[iteration, memory_accesses, mem_score, improvement_percent, prompt, explanation]`. Phase 4 adds `checkpoint_iteration`, `best_found_at_iteration`, `code`, `combined_score`, `time_score` columns.

</code_context>

<specifics>
## Specific Ideas

- Checkpoint sort key: `sorted(dirs, key=lambda d: int(d.replace('checkpoint_', '')))`
- Explanation for first checkpoint: compare `checkpoints/checkpoint_N/best_program.c` to `openevolve/initial_program.c` (the EVOLVE-BLOCK seed program)
- `results.json.v1` backup written by `migrate_legacy.py --regenerate` before overwriting

</specifics>

<deferred>
## Deferred Ideas

- **Time measurement / time_score** — Real per-checkpoint timing data would need OpenEvolve to record wall-clock time per checkpoint. Deferred to a future phase once the researcher decides what "time score" should measure (wall time? CPU time? normalized?).

</deferred>

---

*Phase: 04-per-step-data-pipeline*
*Context gathered: 2026-05-14*

# Phase 3: Experiment Run Structure - Context

**Gathered:** 2026-05-14
**Status:** Ready for planning

<domain>
## Phase Boundary

Restructure how OpenEvolve experiments are stored so all prompts from one `make evolve-all` invocation share a single named run directory, with legacy data migrated cleanly. The researcher gains the ability to identify, filter, and group results by run — without losing any existing experiment data.

Delivers: run directory layout (`runs/<run_id>/cavitydetection/<prompt>/`), `metadata.json` per run, a migration script for legacy data, and `make show-results RUN=<id>` filtering.

</domain>

<decisions>
## Implementation Decisions

### Run ID Format
- **D-01:** Run ID uses full datetime to avoid collisions: `YYYY-MM-DD_HHMM_<model>` (e.g., `2026-05-14_1430_qwen25-32b`). Date-only IDs (`YYYY-MM-DD_<model>`) are rejected — two runs on the same day are indistinguishable.
- **D-02:** Model names are sanitized by collapsing to alphanumeric + dashes. `qwen2.5-coder:32b` → `qwen25-coder-32b`. Any character that is not `[a-zA-Z0-9-]` is replaced with `-`; consecutive dashes collapsed to one.

### Migration
- **D-03:** The migration script uses `os.rename()` (move, not copy). Moving is atomic on the same filesystem — fast, no extra disk. Legacy paths (`openevolve_output/baseline/`, `openevolve_output/prompt1/`) are gone after migration.
- **D-04:** Migration is idempotent. If a directory already exists under `runs/legacy/cavitydetection/`, skip it without error. Safe to re-run after adding more top-level experiment dirs.

### Display Behavior
- **D-05:** `make show-results` (no `RUN=` arg) shows all runs merged, flat by prompt — same visual format as today. One row per prompt, showing the best result across all runs. Backward-compatible.
- **D-06:** `make show-results RUN=<id>` shows the same flat per-prompt table, filtered to only the prompts that ran in that specific run. No additional verbosity.

### Standalone `run_experiment.py` invocation
- **D-07:** When called without `--run`, `run_experiment.py` auto-generates a solo run ID using the same `YYYY-MM-DD_HHMM_<model>` format. Results go to `openevolve_output/runs/<auto-id>/cavitydetection/<prompt>/`. No fallback to the legacy flat path — the new layout is always used after this phase.
- **D-08:** `run_experiment.py` accepts an `--output-root` flag to override the default output base directory (`openevolve/openevolve_output/`). Enables researchers to direct results at any path.

### Claude's Discretion
- How `metadata.json` is written (fields order, JSON formatting) — follow REQUIREMENTS.md spec for field list, details to planner.
- Whether `make evolve-all` generates the run ID in shell or calls a Python helper — planner's choice.
- Config snapshot format in `metadata.json` — inline YAML-as-dict vs. raw YAML string.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Requirements
- `.planning/REQUIREMENTS.md` — Full v1.1 requirements; Phase 3 section defines RUNORG-01 through RUNORG-03, MIGRATE-01, DISPLAY-01 with exact field specs for `metadata.json`

### Existing source files (read before modifying)
- `openevolve/run_experiment.py` — Current experiment runner; output path, CLI args, consolidation call
- `openevolve/consolidate_results.py` — `consolidate_experiment()` function signature and behavior
- `openevolve/results_loader.py` — `load_all_results()` walk logic (currently scans for any `results.json` under root)
- `openevolve/show_consolidated.py` — Current `show-consolidated-results` display logic
- `openevolve/show_results.py` — Current `show-results` display logic
- `Makefile` — `evolve-all`, `show-results`, `show-consolidated-results` targets

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `consolidate_experiment()` in `consolidate_results.py` — takes `output_dir` as first arg; just needs to receive the new path from `run_experiment.py`
- `load_all_results(results_root)` in `results_loader.py` — already uses `os.walk()` recursively; will automatically discover `results.json` at any depth under the new run structure without changes
- `show_consolidated.py` — can accept a filtered DataFrame subset for `RUN=` display

### Established Patterns
- `run_experiment.py` uses `argparse` for CLI args — `--run` and `--output-root` follow the same pattern
- `SCRIPT_DIR` / `PROJECT_ROOT` path construction pattern used throughout — new run output path built the same way
- `consolidate_experiment()` is called post-run inside `run_experiment.py` — output path passed in, no global state

### Integration Points
- `Makefile` `evolve-all` loop must generate `RUN_ID` before the per-prompt loop and pass `--run $$RUN_ID` to each `run_experiment.py` invocation
- `make show-results` and `make show-consolidated-results` targets need `RUN=` optional variable passed through to Python scripts
- `load_all_results()` is the single point that aggregates results — updating its root path is the only change needed for the loader

</code_context>

<specifics>
## Specific Ideas

- Run ID example format: `2026-05-14_1430_qwen25-32b` (matches `YYYY-MM-DD_HHMM_<sanitized-model>`)
- Legacy migration target: `openevolve_output/runs/legacy/cavitydetection/baseline/` and `.../prompt1/`
- `metadata.json` required fields (from RUNORG-03): model name, total iterations, programs, prompts, config snapshot, start timestamp

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>

---

*Phase: 03-experiment-run-structure*
*Context gathered: 2026-05-14*

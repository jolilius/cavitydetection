# Milestones

## v1.0 — Results & Explanations Framework

**Shipped:** 2026-05-13
**Phases:** 1–2 | **Plans:** 5

### Delivered

Unified JSON schema + pandas loader for all OpenEvolve experiment results; per-iteration LLM explanations stored alongside metrics and accessible via `df['explanation']`.

### Key Accomplishments

1. `load_results()` / `load_all_results()` return DataFrames covering all iterations from one or all experiments
2. `run_experiment.py` auto-consolidates results on every run; no manual parsing needed
3. `explanation_generator.py` prompts the LLM after each iteration and stores the response in `results.json`
4. `get_explanations()` surfaces explanation text without raw JSON parsing
5. `make show-results` and `make show-consolidated-results` Makefile targets for quick display

---

## v1.1 — Experiment Runs + Per-Step Analysis

**Shipped:** 2026-05-15
**Phases:** 3–4 | **Plans:** 6 | **Timeline:** 2 days (2026-05-13 → 2026-05-15)

### Delivered

Every checkpoint in the evolution is now a queryable row — with the exact C source at that step and a per-checkpoint sliding-window explanation. All prompts from one `make evolve-all` invocation share a single named run ID, enabling per-run filtering and comparison.

### Key Accomplishments

1. **Run ID contract** — `generate_run_id()` produces `YYYY-MM-DD_HHMM_<model>`; `write_run_metadata()` writes merged `metadata.json`; `run_experiment.py` routes output to `runs/<run_id>/cavitydetection/<prompt>/`
2. **`make evolve-all` run grouping** — single run ID stamped before prompt loop; all prompts grouped under same run; `make show-results RUN=<id>` filters display
3. **Legacy migration** — `migrate_legacy.py` moves `baseline/`+`prompt1/` to `runs/legacy/cavitydetection/` with no data loss; idempotent
4. **Checkpoint-based consolidation** — `_extract_iterations()` scans `checkpoints/checkpoint_N/` numerically, emitting `checkpoint_iteration`, `best_found_at_iteration`, `code`, `combined_score`, `mem_score`, `time_score` per row; `load_results()` returns one row per checkpoint
5. **Per-checkpoint explanation loop** — `_generate_explanations_for_experiment()` rewritten; each checkpoint compared to previous (first to `initial_program.c`); sliding-window verified by UAT 2026-05-15
6. **`--regenerate` flag** — `migrate_legacy.py --regenerate` rebuilds `results.json` from Phase 4 checkpoints; `results.json.v1` rollback backup created before overwrite

### Requirements: 10/10 satisfied

| REQ-ID | Status |
|--------|--------|
| RUNORG-01, RUNORG-02, RUNORG-03 | ✅ SATISFIED |
| MIGRATE-01 | ✅ SATISFIED (code complete; real data migration pending) |
| CKPT-01, CKPT-02, CKPT-03 | ✅ SATISFIED |
| EXPLAIN-01, EXPLAIN-02 | ✅ SATISFIED |
| DISPLAY-01 | ✅ SATISFIED |

### Known Deferred Items at Close

| Area | Item | Status |
|------|------|--------|
| Makefile | `--output-root` inconsistency (W-1): `run_experiment.py` uses flag directly; display scripts append `openevolve_output/runs` | Low — default case works; custom roots affected |
| Makefile | Stale `evolve-explain-test`/`test-explanations-disabled` targets reference flat legacy paths (W-2) | Low — not in primary `make evolve-all` flow |
| Display | `show-explanations` walks all of `openevolve_output/`; other display targets only under `runs/` (W-3) | Low — fixed after migration is run |
| Operations | `migrate_legacy.py` not yet run on real `baseline/`+`prompt1/` data | Low — manual step; code works |

### Archives

- `.planning/milestones/v1.1-ROADMAP.md`
- `.planning/milestones/v1.1-REQUIREMENTS.md`
- `.planning/milestones/v1.1-MILESTONE-AUDIT.md`
- `.planning/milestones/v1.1-phases/` (phase execution artifacts)

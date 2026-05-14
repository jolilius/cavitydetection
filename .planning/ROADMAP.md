# OpenEvolve Results & Explanations Framework — Roadmap

**Goal:** Consolidate experiment results into a unified format; capture LLM explanations of transformations; enable per-step trajectory analysis.

**Research Focus:** Understand how prompts influence search behavior (convergence speed, quality, strategy).

**Milestone:** v1.0 (Phases 1–2, COMPLETE) + v1.1 (Phases 3–4, current)

---

## Phases

- [x] **Phase 1: Results Consolidation** - Unified JSON schema per experiment; pandas loader functional
- [x] **Phase 2: LLM Explanations** - Per-iteration explanation capture; `explanation` field in DataFrame
- [x] **Phase 3: Experiment Run Structure** - Named runs grouping all prompts; legacy data migrated
- [ ] **Phase 4: Per-Step Data Pipeline** - Checkpoint-based consolidation with code field; per-checkpoint explanations

---

## Phase Details

### Phase 1: Results Consolidation
**Goal**: Researchers can load all experiment results into a pandas DataFrame without manual parsing
**Depends on**: Nothing
**Requirements**: (v1.0 — complete)
**Success Criteria** (what must be TRUE):
  1. A single `load_results()` call returns a DataFrame covering all iterations of one experiment
  2. Researcher can plot convergence curves (iteration vs memory accesses) colored by prompt
  3. Results file is machine-readable JSON requiring no custom parsing beyond the loader
**Plans**: Complete
**Status**: COMPLETE

### Phase 2: LLM Explanations
**Goal**: Each experiment iteration has a concise LLM-generated explanation stored alongside metrics
**Depends on**: Phase 1
**Requirements**: (v1.0 — complete)
**Success Criteria** (what must be TRUE):
  1. `df['explanation']` returns a non-empty string for every iteration row
  2. Explanations mention actual code transformations (loop reorder, cache locality, etc.)
  3. `get_explanations()` utility surfaces explanation text without raw JSON parsing
**Plans**: Complete
**Status**: COMPLETE

### Phase 3: Experiment Run Structure
**Goal**: Researchers can group all prompts from one `make evolve-all` invocation as a single named run, and all legacy data is accessible in the new layout without data loss
**Depends on**: Phase 2
**Requirements**: RUNORG-01, RUNORG-02, RUNORG-03, MIGRATE-01, DISPLAY-01
**Success Criteria** (what must be TRUE):
  1. Running `make evolve-all` produces a single dated run directory (`openevolve_output/runs/<run_id>/`) containing one subdirectory per prompt under `<program>/<prompt>/`
  2. Each run directory contains `metadata.json` with model name, iteration budget, programs, prompts, config snapshot, and start timestamp — readable without opening any other file
  3. Existing `baseline/` and `prompt1/` output is accessible at `runs/legacy/cavitydetection/` with all original `results.json` and checkpoint files intact
  4. `make show-results RUN=<id>` filters output to that run; `make show-results` without argument covers all runs
**Plans**: 3 plans in 2 waves
Plans:

**Wave 1**
- [x] 03-01-PLAN.md — Test scaffolding + run_experiment.py run ID, --run/--output-root args, and metadata.json write
- [x] 03-02-PLAN.md — Migration script (migrate_legacy.py) for all legacy flat directories

**Wave 2** *(blocked on Wave 1 completion)*
- [x] 03-03-PLAN.md — Display scripts adaptation (show_results.py, show_consolidated.py) + Makefile RUN= pass-through and evolve-all run grouping

**Cross-cutting constraints:**
- `output_dir` passed to `consolidate_experiment()` must always point to the prompt-level directory (`runs/<run_id>/cavitydetection/<prompt>/`), not the run root
- `make show-results` with no `RUN=` arg must remain backward-compatible (shows all runs merged, flat by prompt)

### Phase 4: Per-Step Data Pipeline
**Goal**: Researchers can inspect the exact C source and an explanation of what changed at every checkpoint, loaded via the same `load_results()` / `load_all_results()` interface
**Depends on**: Phase 3
**Requirements**: CKPT-01, CKPT-02, CKPT-03, EXPLAIN-01, EXPLAIN-02
**Success Criteria** (what must be TRUE):
  1. `load_results()` returns one row per checkpoint (not one row per iteration), with `checkpoint_iteration`, `combined_score`, `mem_score`, `time_score`, `code`, and `explanation` all populated
  2. The `code` column contains the full C source at that checkpoint — researcher can `print(df.iloc[N]['code'])` and see compilable C
  3. Each explanation describes what changed since the previous checkpoint (or vs `initial_program.c` for checkpoint 0) — a researcher can follow the model's reasoning without manually diffing files
  4. `load_all_results()` aggregates across all runs, programs, and prompts into a single DataFrame queryable by run ID, program, or prompt name
**Plans**: 3 plans in 2 waves
Plans:

**Wave 1**
- [x] 04-01-PLAN.md — Wave 0 checkpoint tests + checkpoint-based `_extract_iterations()` in `consolidate_results.py` + extended column list in `results_loader.py` (CKPT-01, CKPT-02, CKPT-03)

**Wave 2** *(blocked on Wave 1 completion)*
- [x] 04-02-PLAN.md — Per-checkpoint explanation loop in `run_experiment.py` (EXPLAIN-01, EXPLAIN-02)
- [x] 04-03-PLAN.md — Wave 0 regenerate test + `--regenerate` flag + `regenerate_results()` helper in `migrate_legacy.py` (D-09, D-10)
**UI hint**: no

---

## Progress Table

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Results Consolidation | — | Complete | 2026-05-13 |
| 2. LLM Explanations | — | Complete | 2026-05-13 |
| 3. Experiment Run Structure | 3/3 | Complete | 2026-05-14 |
| 4. Per-Step Data Pipeline | 0/3 | Planned | - |

---

## Dependency Graph

```
Phase 1 (Results consolidation) — COMPLETE
  ↓
Phase 2 (LLM explanations) — COMPLETE
  ↓
Phase 3 (Experiment run structure) — v1.1
  ↓
Phase 4 (Per-step data pipeline) — v1.1
```

Phase 4 depends on Phase 3: the new `runs/<run_id>/<program>/<prompt>/` directory layout must exist before the checkpoint pipeline reads from it.

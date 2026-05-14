---
gsd_state_version: 1.0
milestone: v1.1
milestone_name: Experiment Runs + Per-Step Analysis
current_phase: 4
status: executing
last_updated: "2026-05-14T15:28:10.271Z"
last_activity: 2026-05-14 -- Phase 4 planning complete
progress:
  total_phases: 4
  completed_phases: 3
  total_plans: 11
  completed_plans: 8
  percent: 73
---

# Project State & Notes

**Last Updated:** 2026-05-14
**Current Phase:** 4

---

## Current Position

Phase: 03 (experiment-run-structure) — EXECUTING
Plan: Not started
Status: Ready to execute
Last activity: 2026-05-14 -- Phase 4 planning complete

---

## Key Decisions

1. **v1.0 complete (Phases 1–2):** Unified JSON, pandas loader, per-iteration explanations all shipped
2. **v1.1 research goal: trajectory observation** — checkpoints are the unit of analysis, not iterations
3. **Phase 3 first:** Directory restructure and legacy migration must land before Phase 4 reads from new paths
4. **Run grouping** — `make evolve-all` stamps a single run ID; all prompts share it; researcher can filter by run
5. **Checkpoint granularity** — `results.json` rebuilt from `checkpoints/checkpoint_N/` directories; `best/`-only approach dropped
6. **Per-checkpoint explanation** — compares checkpoint N to checkpoint N-1 (or initial_program.c for checkpoint 0)
7. **Defer multi-program support** — not in v1.1; future milestone

---

## Phase 3 Scope (Experiment Run Structure)

Requirements: RUNORG-01, RUNORG-02, RUNORG-03, MIGRATE-01, DISPLAY-01

Key deliverables:

- `run_experiment.py --run <name>` flag; auto-generated run ID from timestamp + model
- `make evolve-all` creates one run directory, passes run ID to each prompt invocation
- `openevolve_output/runs/<run_id>/<program>/<prompt>/` layout
- `metadata.json` per run (model, iterations, programs, prompts, config snapshot, start time)
- Migration script: `baseline/` and `prompt1/` → `runs/legacy/cavitydetection/`
- `make show-results RUN=<id>` optional filter

---

## Phase 4 Scope (Per-Step Data Pipeline)

Requirements: CKPT-01, CKPT-02, CKPT-03, EXPLAIN-01, EXPLAIN-02

Key deliverables:

- Consolidator reads `checkpoints/checkpoint_N/best_program.c` + `best_program_info.json` sorted by N
- Schema per checkpoint row: `checkpoint_iteration`, `best_found_at_iteration`, `code`, `combined_score`, `mem_score`, `time_score`, `explanation`
- `load_results()` → one row per checkpoint; `load_all_results()` → aggregated DataFrame
- Explanation generator called once per checkpoint, diff vs previous checkpoint (or baseline for first)

---

## Accumulated Context

### Directory Layout (target)

```
openevolve_output/
  runs/
    legacy/
      cavitydetection/
        baseline/        (migrated from openevolve_output/baseline/)
        prompt1/         (migrated from openevolve_output/prompt1/)
    2026-05-14_qwen25-32b/
      metadata.json
      cavitydetection/
        baseline/
          checkpoints/
          results.json
        prompt1/
          checkpoints/
          results.json
```

### Baseline metrics (reference)

Unoptimized baseline (initial_program.c, gcc -O0): 128,862,705 total memory accesses

| Function | Accesses |
|----------|----------|
| GaussBlur | 19,894,278 |
| ComputeEdges | 67,604,444 |
| DetectRoots | 41,363,979 |
| run_pipeline | 4 |

Score formula: `mem_score = 128,862,705 / accesses` (>1.0 = better than baseline)

---

## Blockers & Open Questions

None currently.

- LLVM instrumentation working
- Ollama / mandelbrot (100.89.90.6) available
- Existing results available for migration testing

---

## v1.0 Summary (COMPLETE)

Phase 1: Results Consolidation

- Unified JSON schema per experiment, `load_results()` → DataFrame, `load_all_results()`
- Auto-consolidation in `run_experiment.py`, Makefile display targets

Phase 2: LLM Explanations

- `explanation_generator.py`, per-iteration explanation capture
- Schema extended with `explanation` field, `get_explanations()` loader utility

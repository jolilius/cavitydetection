# Cavity Detection — OpenEvolve Results & Explanations Framework

**Project:** OpenEvolve Results Consolidation + LLM Explanations  
**Owner:** Johan Lilius  
**Start Date:** 2026-05-13  
**Shipped:** v1.1 — Experiment Runs + Per-Step Analysis (2026-05-15)

---

## What This Is

A research toolkit layered on top of [OpenEvolve](https://github.com/codelion/openevolve) that makes every step of LLM-guided code evolution queryable. For each prompt run on each program, researchers get one pandas row per checkpoint — with the exact C source that was "best" at that point, its memory-access scores, and an LLM-generated explanation of what changed since the previous checkpoint.

Experiments from a single `make evolve-all` invocation are grouped as a named run so prompts that ran under identical conditions can be directly compared.

---

## Core Value

**Trajectory observation, not just the final result.** Each checkpoint is a decision point. Understanding what changed and why at every step is the primary research output — the framework makes that accessible with a single `load_results()` call.

---

## Current State (after v1.1)

- **~2,859 LOC Python** in `openevolve/` (loader, consolidator, explanation generator, display scripts, migration, tests)
- **Tech stack:** Python 3, pandas, pytest, Ollama (qwen2.5-coder:32b on mandelbrot.abo.fi), LLVM memtrace, SDL2
- **Output layout:** `openevolve_output/runs/<run_id>/<program>/<prompt>/` with `results.json` + `checkpoints/`
- **Test suites:** `test_consolidation.py` (9 tests), `test_run_structure.py` (12 tests) — all green
- **Pending operational step:** `python openevolve/migrate_legacy.py` to move real `baseline/`+`prompt1/` to `runs/legacy/cavitydetection/`

---

## Requirements

### Validated

- ✓ Unified results storage + pandas loader (`load_results()`, `load_all_results()`) — v1.0
- ✓ Per-iteration LLM explanations in `results.json` + `df['explanation']` — v1.0
- ✓ `get_explanations()` utility + `make show-results` / `make show-consolidated-results` — v1.0
- ✓ Named run structure: `runs/<run_id>/<program>/<prompt>/` with `metadata.json` — v1.1
- ✓ `make evolve-all` run grouping (single RUN_ID shared across prompts) — v1.1
- ✓ `make show-results RUN=<id>` filtered display — v1.1
- ✓ Legacy migration: `migrate_legacy.py` moves flat dirs to `runs/legacy/cavitydetection/` — v1.1
- ✓ Checkpoint-based consolidation: one row per checkpoint, Phase 4 schema fields — v1.1
- ✓ Per-checkpoint sliding-window explanations (checkpoint N vs N-1; first vs `initial_program.c`) — v1.1
- ✓ `--regenerate` flag on `migrate_legacy.py` for Phase 4 schema upgrade of legacy data — v1.1

### Active (next milestone)

- [ ] Fix `--output-root` inconsistency between `run_experiment.py` and display scripts
- [ ] Clean up stale Makefile targets (`evolve-explain-test`, `test-explanations-disabled`)
- [ ] Run actual `migrate_legacy.py` on real `baseline/`+`prompt1/` data
- [ ] Multi-program support: same prompt variants on different algorithms
- [ ] Baseline normalization: compare against program-specific baselines

### Out of Scope

- Web dashboards or visualization — out of scope for research toolkit; use pandas/matplotlib directly
- Metric plugins (valgrind, energy) — future milestone when needed
- Theme grouping of explanations — motivation unclear after v1.1 implementation

---

## Key Decisions

| Decision | Outcome | Milestone |
|----------|---------|-----------|
| Unified JSON schema per experiment | ✓ Good — load_results() stable across all phases | v1.0 |
| Per-iteration explanations (Phase 2 approach) | ⚠️ Revisit — replaced in v1.1 with per-checkpoint loop (best/-only was too coarse) | v1.0 |
| Checkpoints as primary unit of analysis | ✓ Good — 12 rows from real baseline; researcher can study evolution step by step | v1.1 |
| Phase 3 before Phase 4 | ✓ Good — directory layout stability was prerequisite for checkpoint reads | v1.1 |
| Run grouping via shared run ID | ✓ Good — `make evolve-all` stamps ID before loop; all prompts grouped | v1.1 |
| Integer-keyed explanation dict (folder N, not JSON iteration) | ✓ Good — avoids Pitfall 2 where iteration field ≠ folder name | v1.1 |
| Defer multi-program support | — Pending — still not needed; cavitydetection is the only target | v1.1 |
| `time_score=null` (D-01) | — Pending — intentional stub until per-checkpoint timing is available | v1.1 |

---

## Constraints

- **Programs:** cavitydetection only (for now)
- **Metrics:** Memory accesses via LLVM instrumentation; no new metrics yet
- **LLM:** Ollama on mandelbrot.abo.fi (100.89.90.6); 30B+ model required for valid C output
- **No web UI:** Research toolkit only; analysis done in notebooks/scripts

---

## How to Use Results

```python
from openevolve.results_loader import load_results, load_all_results

# One run, one prompt — one row per checkpoint
df = load_results("openevolve_output/runs/<run_id>/cavitydetection/baseline/results.json")
print(df[['checkpoint_iteration', 'mem_score', 'code', 'explanation']])

# All runs, all prompts
df_all = load_all_results("openevolve_output/runs/")
df_all.groupby(['run_id', 'prompt'])['mem_score'].max()
```

---

## Key Artifacts

| Artifact | Purpose |
|----------|---------|
| `openevolve/run_experiment.py` | Entry point; run ID generation, metadata write, explanation loop |
| `openevolve/consolidate_results.py` | Checkpoint scanner + `results.json` writer |
| `openevolve/results_loader.py` | `load_results()` / `load_all_results()` pandas interface |
| `openevolve/explanation_generator.py` | LLM explanation calls |
| `openevolve/migrate_legacy.py` | Legacy migration + `--regenerate` for Phase 4 schema upgrade |
| `openevolve/show_results.py` | Display script with `--run` filter |
| `openevolve/show_consolidated.py` | Consolidated display with `--run` filter |
| `openevolve/test_consolidation.py` | 9-test suite for consolidation pipeline |
| `openevolve/test_run_structure.py` | 12-test suite for run structure + migration + display |

---

## References

- **CLAUDE.md:** System setup, build commands, remote infrastructure
- **openevolve/:** Existing framework (Ollama-based code evolution)
- **.planning/MILESTONES.md:** Shipped milestone history
- **.planning/milestones/:** Archived roadmaps + requirements per milestone

---

*Last updated: 2026-05-15 after v1.1 milestone*

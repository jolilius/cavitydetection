# Cavity Detection — OpenEvolve Results & Explanations Framework

**Project:** OpenEvolve Results Consolidation + LLM Explanations  
**Owner:** Johan Lilius  
**Start Date:** 2026-05-13  
**Current Milestone:** v1.1 — Experiment Runs + Per-Step Analysis (2026-05-14 onwards)

---

## Overview

This project improves the research workflow for understanding how LLM-guided prompts influence OpenEvolve's code optimization search. Currently, experiment results are scattered across JSON files and difficult to analyze. The goal is to:

1. **Consolidate results** into a unified, pandas-readable format
2. **Capture LLM explanations** (what the model thought at each iteration)
3. **Enable analysis** of prompt influence on convergence speed, solution quality, and strategy

### Why This Matters

Currently:
- Results are scattered; loading into pandas requires custom parsing
- No insight into LLM's reasoning (what transformations did it attempt?)
- Difficult to compare prompt effectiveness systematically

After this work:
- All results in one place, easily analyzed with pandas
- Clear view of prompt strategies (via LLM explanations)
- Research questions answerable: How fast does each prompt converge? How good are the solutions? What is the LLM's strategy?

---

## Scope

**In Scope (M1):**
- Results consolidation: unified JSON format, pandas loader
- LLM explanations: capture what the model thought each iteration
- Cavitydetection only (existing program)
- Memory access metrics (existing LLVM instrumentation)

**Out of Scope (Defer):**
- Multi-program support (future milestone)
- Additional metrics (valgrind, energy, etc.)
- Metric plugin system
- Web dashboards or visualization

---

## Key Artifacts

| Artifact | Purpose |
|----------|---------|
| `REQUIREMENTS.md` | Research goal, user stories, success criteria |
| `ROADMAP.md` | 2-phase plan: consolidation → explanations |
| `openevolve/run_experiment.py` | (to be refactored) Output unified results format |
| `openevolve/results_loader.py` | (to be written) Load results into pandas DataFrame |
| `.planning/STATE.md` | Ongoing notes, decisions, blockers |

---

## Current Milestone: v1.1 — Experiment Runs + Per-Step Analysis

**Goal:** Enable observation of the LLM's full reasoning trajectory by structuring experiments as groupable runs and exposing per-checkpoint code + explanations at each evolution step.

**Target features:**
- Experiment run directory structure: `runs/<run_id>/<program>/<prompt>/` with run metadata
- `make evolve-all` creates a single dated run grouping all prompts
- Legacy data migration: existing `baseline/` and `prompt1/` → `runs/legacy/cavitydetection/`
- Checkpoint-based consolidation: `results.json` built from checkpoint directories, including code (C source) per step
- Per-checkpoint explanations comparing each step's code to the previous checkpoint

**Clarified research goal:** The primary objective is to observe the LLM's reasoning *trajectory* — not just the final optimum. Each checkpoint is a decision point; understanding what changed and why at each step is the primary research output.

---

## v1.0 — Results & Explanations Framework (COMPLETE)

**Phase 1:** Results Consolidation
- Unified JSON schema per experiment, pandas loader (`load_results`, `load_all_results`)
- Auto-consolidation in `run_experiment.py`, Makefile display targets

**Phase 2:** LLM Explanations
- `explanation_generator.py`, per-experiment explanation capture
- Schema extended with `explanation` field, `get_explanations()` loader utility

---

## Team & Communication

**Researcher & Developer:** Johan Lilius (johan.lilius@gmail.com)

**Status Updates:** Check `.planning/STATE.md` for ongoing progress and blockers.

---

## How to Use Results

### Phase 1 (After consolidation)
```python
import pandas as pd
from openevolve.results_loader import load_results

# Load all iterations from one prompt variant
df = load_results("results/cavitydetection/baseline.json")

# Plot convergence
import matplotlib.pyplot as plt
df.plot(x='iteration', y='memory_accesses')
plt.show()

# Compare across prompts
df_baseline = load_results("results/cavitydetection/baseline.json")
df_prompt1 = load_results("results/cavitydetection/prompt1.json")
compare_df = pd.concat([df_baseline, df_prompt1], keys=['baseline', 'prompt1'])
compare_df.plot(x='iteration', y='memory_accesses')
```

### Phase 2 (With explanations)
```python
df = load_results("results/cavitydetection/baseline.json")

# See explanations
print(df[['iteration', 'memory_accesses', 'explanation']])

# Group by explanation theme (manual for now)
loops_optimized = df[df['explanation'].str.contains('loop', case=False)]
cache_optimized = df[df['explanation'].str.contains('cache', case=False)]
```

---

## Evolution

This document evolves at phase transitions and milestone boundaries.

**After each phase transition** (via `/gsd-transition`):
1. Requirements invalidated? → Move to Out of Scope with reason
2. Requirements validated? → Move to Validated with phase reference
3. New requirements emerged? → Add to Active
4. Decisions to log? → Add to Key Decisions
5. "What This Is" still accurate? → Update if drifted

**After each milestone** (via `/gsd-complete-milestone`):
1. Full review of all sections
2. Core Value check — still the right priority?
3. Audit Out of Scope — reasons still valid?
4. Update Context with current state

---

## References

- **CLAUDE.md:** System setup, build commands
- **openevolve/:** Existing framework (Ollama-based code evolution)
- **REQUIREMENTS.md:** Full research motivation and v1.1 requirements

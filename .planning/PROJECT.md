# Cavity Detection — OpenEvolve Results & Explanations Framework

**Project:** OpenEvolve Results Consolidation + LLM Explanations  
**Owner:** Johan Lilius  
**Start Date:** 2026-05-13  
**Current Milestone:** M1 (2026-05-13 to 2026-05-19)

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

## Current State (M1)

**Phase 1:** Results Consolidation (2026-05-13 to 2026-05-15)
- Refactor `run_experiment.py` to output unified JSON per experiment
- Implement pandas loader function
- Test on existing experiments
- **Definition of Done:** Convergence curves visible in pandas

**Phase 2:** LLM Explanations (2026-05-16 to 2026-05-19)
- Integrate LLM explanation prompt into experiment loop
- Extend results schema to capture explanations
- Update pandas loader
- **Definition of Done:** Sample results with explanations; strategy differences visible

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

## References

- **CLAUDE.md:** System setup, build commands
- **openevolve/:** Existing framework (Ollama-based code evolution)
- **REQUIREMENTS.md:** Full research motivation

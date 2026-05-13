# Cavity Detection — OpenEvolve Research Framework Project

**Project:** Multi-Program OpenEvolve Research Instrumentation Framework  
**Owner:** Johan Lilius  
**Start Date:** 2026-05-13  
**Current Milestone:** M1 (2026-05-13 to 2026-05-19)

---

## Overview

This project builds a research framework for systematically investigating how LLM-guided code evolution (via OpenEvolve) optimizes code. The framework supports multiple test programs, flexible metrics collection, and deep instrumentation to answer three core research questions:

1. **RQ1:** How effective is OpenEvolve at minimizing memory accesses?
2. **RQ2:** How do different prompts influence the search (speed, quality, convergence)?
3. **RQ3:** What program transformations does OpenEvolve attempt (compiler theory knowledge)?

### Why This Matters

Currently, OpenEvolve experiments are hard-coded for a single program (cavitydetection), prompt variants are manual, and results lack rich instrumentation. This makes it difficult to:
- Compare prompt effectiveness fairly (different models, hardware configs)
- Understand *what* the LLM is doing (transformations, reasoning)
- Generalize findings to other programs

The new framework enables rigorous, reproducible research across programs and prompts.

---

## Scope

**In Scope:**
- Multi-program experiment runner (cavitydetection, loopoptimization1, extensible for others)
- Flexible metrics collection via plugin system (memory accesses, with hooks for valgrind, energy, runtime)
- LLM-generated explanations of transformations
- Hardware/OS/model metadata tracking per experiment
- Text-based results storage for analysis

**Out of Scope:**
- Real-time monitoring or distributed runs
- Web dashboards (text-based results only)
- Automatic prompt generation
- High-level result visualization (data only; analysis is user's responsibility)

---

## Key Artifacts

| Artifact | Purpose |
|----------|---------|
| `REQUIREMENTS.md` | Research questions, user stories, success criteria |
| `ROADMAP.md` | 4-phase plan for 1-week delivery |
| `.planning/newrequirements.md` | Original research motivation (ref) |
| `openevolve/config.yaml` | Multi-program + metrics configuration |
| `openevolve/run_experiment.py` | Refactored to support multi-program |
| `openevolve/metrics/` | Plugin directory for metric collectors |
| `results/` | Experiment results storage (JSON per run) |

---

## Team & Communication

**Researcher & Developer:** Johan Lilius (johan.lilius@gmail.com)

**Status Updates:** Check `.planning/STATE.md` for ongoing notes and blockers.

---

## Current State

**Milestone 1 (M1):** 2026-05-13 to 2026-05-19

- Phase 1: Framework Architecture (multi-program config, refactor runner)
- Phase 2: Instrumentation (metadata, explanations, results format)
- Phase 3: Metric Plugin System (design + memory metric)
- Phase 4: Validation & Polish (E2E test, documentation)

**Blockers:** None currently  
**Risk:** LLM explanation generation may be slow; have fallback to manual annotation  

---

## How to Extend This Project

### Adding a New Test Program

1. Create `<program>.c` with `EVOLVE-BLOCK` markers and baseline reference
2. Register in `openevolve/config.yaml` under `programs`:
   ```yaml
   programs:
     myprogram:
       seed: openevolve/myprogram.c
       baseline_accesses: 1234567
       output_dir: results/myprogram/
   ```
3. Implement evaluator if custom metrics needed
4. Run: `python openevolve/run_experiment.py <prompt> --programs myprogram`

### Adding a New Metric

1. Create `openevolve/metrics/my_metric.py` implementing `MetricCollector` interface
2. Register in `openevolve/config.yaml`:
   ```yaml
   metrics:
     my_metric:
       plugin: openevolve/metrics/my_metric.py
       enabled: true
   ```
3. Run: metrics are auto-discovered and executed

### Adding a New Prompt Variant

1. Create `openevolve/prompts/<name>.txt`
2. Run: `python openevolve/run_experiment.py <name>`

---

## References

- **CLAUDE.md:** System setup, build commands, architecture overview
- **openevolve/** upstream:** [OpenEvolve repo](https://github.com/codelion/openevolve)
- **Research questions:** `.planning/newrequirements.md`

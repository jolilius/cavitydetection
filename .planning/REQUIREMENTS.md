# Multi-Program OpenEvolve Research Framework — Requirements

## Research Questions

1. **RQ1:** How effective is OpenEvolve at minimizing memory accesses? (Later metrics: valgrind, energy, runtime)
2. **RQ2:** How do different prompts influence the search? (Speed to optimum, quality, convergence behavior)
3. **RQ3:** What program transformations does OpenEvolve attempt? (Understanding of compiler theory, optimization strategies)

## User Stories

### Instrumentation & Tracking
- As a researcher, I want all experiments to use the **same LLM model** so I can isolate prompt effects from model differences.
- As a researcher, I want to **record hardware config and OS** for each experiment so results are reproducible and comparable.
- As a researcher, I want **flexible metrics support** (start with memory accesses split into read/write; later add valgrind, energy, runtime) via a **plugin system** for easy extension.
- As a researcher, I want **LLM-generated explanations** of each optimization attempt so I can understand the model's reasoning.

### Results & Analysis
- As a researcher, I want to **log runtime metrics** (total runtime, iteration count, per-iteration timing) for efficiency comparison across prompts.
- As a researcher, I want **text-based results storage** so data is machine-readable and easy to analyze.

### Program Support
- As a researcher, I want to **run experiments across multiple test programs** (cavitydetection, loopoptimization1, others) without manual per-program setup.
- As a researcher, I want **baseline metrics recorded per program** so I can measure improvement over baseline.

## Success Criteria

- [ ] Framework supports ≥2 distinct programs (cavitydetection, loopoptimization1 minimum)
- [ ] LLM model is consistent across all experiments; configurable in one place
- [ ] Hardware/OS metadata captured and stored for each experiment run
- [ ] Memory metrics (read/write accesses) recorded and reported per program
- [ ] Metric plugin system works; users can add new collectors (sketch interface)
- [ ] LLM-generated explanation captured for each iteration
- [ ] Results stored in text-based format (JSON/CSV/TSV) 
- [ ] Per-iteration timing logged (total runtime, iteration time)
- [ ] Baseline values recorded per program for comparison

## Constraints & Assumptions

- **Timeline:** One week (this week: 2026-05-13 to 2026-05-19)
- **Model:** Using Ollama locally; consistent across experiments
- **Programs:** Start with existing cavitydetection and loopoptimization1; extensible for future programs
- **Metrics:** Memory accesses via LLVM instrumentation (already built); future metrics TBD
- **Explanation:** Prompt the LLM to explain transformations; assume it can generate coherent explanations

## Out of Scope (For Now)

- Real-time metric monitoring (async collection)
- Distributed experiment runs
- Web dashboard (text-based results only)
- Automatic prompt generation (prompt variants manually created)

## Related Documentation

- `CLAUDE.md` — existing build and setup instructions
- `openevolve/config.yaml` — OpenEvolve configuration
- `openevolve/initial_program.c` — current seed program (cavitydetection)
- `.planning/newrequirements.md` — research motivation and questions

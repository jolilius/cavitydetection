# Multi-Program OpenEvolve Research Framework — Roadmap

**Goal:** Build a research instrumentation framework supporting multi-program OpenEvolve experiments with flexible metrics, LLM-generated explanations, and reproducible result tracking.

**Timeline:** 1 week (2026-05-13 to 2026-05-19)

---

## Phase 1: Framework Architecture & Multi-Program Support
**Goal:** Refactor to support multiple test programs; establish config structure.

**Deliverables:**
- [ ] Multi-program config system (YAML defining programs, baseline metrics, evaluators)
- [ ] Abstract program interface (path to seed, evaluator, baseline access count)
- [ ] Refactor `run_experiment.py` to iterate over configured programs
- [ ] Add cavitydetection and loopoptimization1 as registered programs
- [ ] Single `make evolve-all` runs all prompts on all programs

**Success Metrics:**
- One prompt variant successfully runs on both cavitydetection and loopoptimization1
- Config is human-readable and extensible
- No hardcoded program paths in Python

---

## Phase 2: Instrumentation & Results Tracking
**Goal:** Capture hardware, OS, model, explanations; store results in machine-readable format.

**Deliverables:**
- [ ] Metadata collection: capture hardware config (CPU, RAM), OS, LLM model name, timestamp
- [ ] Modify evaluator to log: total runtime, iteration count, per-iteration timing
- [ ] Integrate LLM explanation prompting: after each iteration, ask model to explain the transformation
- [ ] Results schema (JSON structure for: program, prompt, iteration, code, explanation, metrics, timing)
- [ ] Results storage to flat files (one JSON per experiment run)

**Success Metrics:**
- Sample result file shows all metadata, explanations, and timing
- Results are grep-able and importable to analysis tools (Python, R, etc.)
- Can compare iteration timing across prompts

---

## Phase 3: Metric Plugin System
**Goal:** Design and build plugin architecture; implement memory-access plugin.

**Deliverables:**
- [ ] Plugin interface design (input: candidate code; output: metric value + explanation)
- [ ] Plugin discovery (auto-load from `metrics/` directory)
- [ ] Memory plugin implementation (wrap existing LLVM instrumentation)
- [ ] Config extension: specify which metrics to run per program
- [ ] Skeleton for future metrics (valgrind, energy, runtime)

**Success Metrics:**
- Memory metric plugin runs and reports read/write accesses correctly
- New metric can be added by dropping a script in `metrics/` and updating config
- Multiple metrics can run on same candidate in parallel (or sequential, depending on cost)

---

## Phase 4: Validation & Polish
**Goal:** End-to-end testing; document setup and usage.

**Deliverables:**
- [ ] Run full experiment: 1 prompt variant across 2 programs, 20 iterations, all metrics
- [ ] Verify results match expected baseline values
- [ ] Documentation: README for experiment setup, config reference, adding new programs/metrics
- [ ] Cleanup and repo commit

**Success Metrics:**
- All RQs can be partially answered from results (prompt influence visible, transformations logged, memory minimization measurable)
- New contributor can add a program in <30 min
- Experiment results are reproducible across runs

---

## Dependency Graph

```
Phase 1 (Framework) 
  ↓ (required by)
Phase 2 (Instrumentation) ← Phase 3 (Metrics) can start in parallel
  ↓
Phase 4 (Validation)
```

**Parallel opportunity:** Phase 3 plugin design can start during Phase 1, but implementation depends on Phase 2 results structure.

---

## Risk & Mitigation

| Risk | Mitigation |
|------|-----------|
| LLM explanation prompting is slow/unreliable | Start with baseline prompt; iterate; fallback to manual annotation |
| Plugin system over-engineered for timeline | MVP: simple script-per-metric; refactor to framework if time permits |
| Multiple programs have different baselines | Record per-program baseline in config; normalize in analysis |

---

## Success Definition

- ✅ Multi-program framework working for ≥2 programs
- ✅ One experiment run produces: metadata, per-iteration explanations, metrics, timing
- ✅ Results stored as text files; easy to analyze
- ✅ Metric plugin skeleton ready; memory metric functional
- ✅ README documents usage; ready for next researcher to extend

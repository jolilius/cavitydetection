# OpenEvolve Results & Explanations Framework — Requirements

## Research Goal

Understand how different prompts influence OpenEvolve's search behavior:
- How quickly does each prompt converge to an optimum?
- How good is the optimum for each prompt?
- What is the LLM thinking at each iteration?

## Current State

- OpenEvolve runs on cavitydetection with manual prompt variants
- `make evolve-all` executes all prompts; results stored as scattered JSON files
- Python script analyzes results; difficult to load into pandas due to format inconsistency

## Phase 1: Results Consolidation (Immediate)

### User Stories
- As a researcher, I want all experiment results in a **unified, pandas-readable format** so I can easily load and analyze them
- As a researcher, I want to compare **memory access metrics across prompts** to understand relative optimization quality
- As a researcher, I want to track **convergence speed per prompt** (when best was found, how many iterations)

### Deliverables
- [ ] Unified results storage: single consolidated JSON or CSV per experiment run
- [ ] Results schema: prompt, iteration, code, memory_reads, memory_writes, timing_per_iteration
- [ ] Results loader: Python function to read results into pandas DataFrame
- [ ] Update `run_experiment.py` to output consolidated format
- [ ] Update `make evolve-all` to optionally aggregate results

### Success Criteria
- One pandas DataFrame loads all results from one experiment run
- Can filter by prompt, plot convergence curves, compare metrics
- Results are machine-readable; no manual parsing needed

---

## Phase 2: LLM Explanations (Next Priority)

### User Stories
- As a researcher, I want to see **what the LLM thought at each iteration** so I can understand its reasoning
- As a researcher, I want **explanations stored alongside results** so I can correlate transformations with metric improvements

### Deliverables
- [ ] Prompt the LLM after each iteration: "Explain the transformations in [code] compared to baseline"
- [ ] Store explanation in consolidated results (new `explanation` field per iteration)
- [ ] Update results schema to include `explanation`
- [ ] Update results loader to expose explanations in DataFrame

### Success Criteria
- Each iteration has a concise explanation (1-2 sentences)
- Explanations are relevant (mention actual optimizations attempted)
- Can group iterations by explanation theme to understand prompt's strategy

---

## Phase 3+: Optional Future Work

### Not in this milestone, but sketch for later:
- **Multi-program support:** Run same prompt variants on different algorithms
- **Metric plugins:** valgrind, energy, runtime measurements
- **Baseline normalization:** Compare against program-specific baselines

---

## Constraints & Assumptions

- **Timeline:** 1 week (2026-05-13 to 2026-05-19)
- **Programs:** cavitydetection only (for now)
- **Metrics:** Memory accesses via LLVM (existing); no new metrics yet
- **LLM explanations:** Assume Ollama model can generate coherent explanations; simple prompt to start

## Success Definition

- ✅ Phase 1: Consolidated results, easy pandas analysis, convergence visible
- ✅ Phase 2: LLM explanations stored and accessible in results
- ✅ Research questions partially answerable: prompt influence on speed + quality + strategy visible

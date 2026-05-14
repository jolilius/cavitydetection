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

---

---

## v1.1: Experiment Runs + Per-Step Analysis

### Clarified Research Goal

The primary research objective is to **observe the LLM's reasoning trajectory across the full evolution**, not just the final result. Each checkpoint is a decision point: what did the model change, and why? The system must make these intermediate steps first-class data — both the code at each step and an explanation of what changed.

OpenEvolve writes checkpoints every N iterations (default: 5), each containing the best program's C source (`best_program.c`) and metrics (`best_program_info.json`). Checkpoints are the natural unit of observation.

### User Stories

- As a researcher, I want all prompt runs from a single `make evolve-all` invocation grouped as one **experiment run**, so I can compare prompts that ran under identical conditions (same model, same iteration budget, same program)
- As a researcher, I want to see the **code at every checkpoint** alongside its score, so I can study how the program evolved step by step
- As a researcher, I want a **per-checkpoint explanation** of what changed since the previous checkpoint, so I can follow the LLM's reasoning trajectory without manually diffing code
- As a researcher, I want experiment runs **organised by program and prompt** (`runs/<run>/<program>/<prompt>/`), so I can query "how did prompt X treat program Y across 200 iterations?"

### Requirements (v1.1)

#### Run Organization

- [ ] **RUNORG-01:** Researcher can identify an experiment as a named run. Run name auto-generates from timestamp + model name (e.g. `2026-05-14_qwen25-32b`); overridable with `--run <name>` on `run_experiment.py`.
- [ ] **RUNORG-02:** `make evolve-all` creates one run directory before invoking individual prompt runs, so all prompts in one invocation share the same run ID under `openevolve_output/runs/<run_id>/<program>/<prompt>/`.
- [ ] **RUNORG-03:** Each run directory contains `metadata.json` capturing: model name, total iterations, programs optimized, prompts used, config snapshot (from `config.yaml`), and start timestamp.

#### Legacy Migration

- [ ] **MIGRATE-01:** Existing `openevolve_output/baseline/` and `openevolve_output/prompt1/` directories are migrated to `openevolve_output/runs/legacy/cavitydetection/` with no data loss. A migration script handles this; existing `results.json` files and checkpoints remain intact.

#### Checkpoint-Based Consolidation

- [ ] **CKPT-01:** `results.json` is built from `checkpoints/checkpoint_N/` directories sorted by iteration number, replacing the v1.0 `best/`-only placeholder approach.
- [ ] **CKPT-02:** Each checkpoint row in `results.json` includes: `checkpoint_iteration`, `best_found_at_iteration`, `code` (full C source from `best_program.c`), `combined_score`, `mem_score`, `time_score`.
- [ ] **CKPT-03:** `load_results()` returns a DataFrame with one row per checkpoint, including all schema fields (code, metrics, explanation). `load_all_results()` aggregates across runs/programs/prompts.

#### Per-Step Explanations

- [ ] **EXPLAIN-01:** One LLM explanation is generated per checkpoint, comparing the current checkpoint's `best_program.c` to the **previous** checkpoint's code. The first checkpoint compares to `initial_program.c` (baseline).
- [ ] **EXPLAIN-02:** Explanations are stored in `results.json` per checkpoint row and exposed as `df['explanation']` in the DataFrame — same interface as v1.0 but now populated at every checkpoint step.

#### Display & Access

- [ ] **DISPLAY-01:** `make show-results` and `make show-consolidated-results` work with the new run structure. Both accept an optional `RUN=<id>` argument to filter output to a specific run.

### Out of Scope for v1.1

- Multi-program support (still deferred to a future milestone)
- Theme grouping of explanations (dropped — motivation unclear)
- Metric plugins (valgrind, energy)
- Web dashboards or visualization

### Traceability

| REQ-ID | Phase | Status |
|--------|-------|--------|
| RUNORG-01 | TBD | [ ] |
| RUNORG-02 | TBD | [ ] |
| RUNORG-03 | TBD | [ ] |
| MIGRATE-01 | TBD | [ ] |
| CKPT-01 | TBD | [ ] |
| CKPT-02 | TBD | [ ] |
| CKPT-03 | TBD | [ ] |
| EXPLAIN-01 | TBD | [ ] |
| EXPLAIN-02 | TBD | [ ] |
| DISPLAY-01 | TBD | [ ] |

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

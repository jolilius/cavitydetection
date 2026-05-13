# Phase 1 Planning Summary — OpenEvolve Results Consolidation

**Date:** 2026-05-13  
**Phase:** 01-consolidation  
**Timeline:** Days 1-3 (May 13-15, 2026)  
**Status:** Planning Complete — Ready to Execute

---

## Overview

Phase 1 consolidates OpenEvolve experiment results into a unified, pandas-readable format. Currently, results are scattered across per-experiment JSON files making batch analysis difficult. After Phase 1, researchers will load all results with one command and analyze convergence curves, compare prompts, and track improvements.

## Plans Created

### Plan 01: Schema Design & Module Implementation (Wave 1)
**Autonomous:** Yes  
**Tasks:** 5  
**Time estimate:** 1 day

**Deliverables:**
- `.planning/RESULTS_FORMAT.md` — Unified results schema with example JSON
- `openevolve/consolidate_results.py` — Module to transform OpenEvolve output → unified JSON
- `openevolve/results_loader.py` — Pandas loader (load_results, load_all_results)
- `openevolve/test_consolidation.py` — Synthetic data validation
- `.planning/RESULTS_USAGE.md` — Researcher usage guide

**Key tasks:**
1. Design and document results schema (JSON structure, field types, example)
2. Implement consolidate_results.py (transforms OpenEvolve output_dir → results.json)
3. Implement results_loader.py (pandas integration: load_results, load_all_results)
4. Integrate consolidation into run_experiment.py (post-run hook, non-blocking)
5. Test with synthetic data and document usage

**Integration:** consolidate_experiment() called in run_experiment.py after OpenEvolve completes; writes results.json to experiment output directory.

**Success:** Python `load_results('openevolve_output/baseline/results.json')` returns DataFrame with iteration, memory_accesses, improvement_percent, mem_score columns.

---

### Plan 02: Integration & Verification (Wave 2, depends on 01)
**Autonomous:** Yes  
**Tasks:** 5  
**Time estimate:** 1 day  

**Deliverables:**
- Updated Makefile (new targets: show-consolidated-results, results-summary)
- openevolve/show_consolidated.py — New results display script
- Enhanced openevolve/show_results.py (dual-format support: consolidated + legacy)
- Verified backward compatibility
- Tested end-to-end workflow (run → consolidate → load → analyze)

**Key tasks:**
1. Add Makefile targets for consolidated results display
2. Create show_consolidated.py for unified results table
3. Enhance show_results.py to support both formats (consolidated + legacy)
4. Verify backward compatibility with existing experiments
5. Test full workflow with short 5-iteration baseline experiment

**Integration:** `make evolve-all` auto-consolidates results (no Makefile change needed); `make show-consolidated-results` displays new format.

**Success:** Researcher can run `make evolve-all` and immediately load results with `load_all_results()` for analysis.

---

## Wave Structure

```
Wave 1 (Day 1):
  └─ 01-01: Schema design & module implementation (5 tasks, ~4-5 hours)

Wave 2 (Day 2):
  └─ 01-02: Integration & verification (5 tasks, ~3-4 hours)
       Depends: 01-01 must have consolidate_results.py + results_loader.py
```

**Parallelization:** Minimal. Plan 01 is prerequisites for Plan 02. Both are autonomous (no checkpoints).

**Timeline:** 2 days execution (Wave 1 day 1, Wave 2 day 2) + 0.5 day buffer = 2.5 days total (fits 3-day Phase 1 window).

---

## Results Schema (Core Innovation)

**File:** `openevolve_output/{prompt_variant}/results.json`

**Structure:**
```json
{
  "metadata": {
    "program": "cavitydetection",
    "prompt_variant": "baseline",
    "timestamp": "2026-05-13T14:30:00Z",
    "llm_model": "qwen2.5-coder:32b",
    "total_iterations": 42,
    "total_runtime_seconds": 480.5,
    "best_memory_accesses": 98765432,
    "convergence_iteration": 28
  },
  "baseline_metrics": {
    "memory_accesses": 128862705,
    "memory_reads": 64431352,
    "memory_writes": 64431353
  },
  "iterations": [
    {
      "iteration": 1,
      "memory_accesses": 127000000,
      "memory_reads": 63500000,
      "memory_writes": 63500000,
      "improvement_percent": 1.45,
      "iteration_runtime_seconds": 12.3,
      "mem_score": 1.0148
    }
  ]
}
```

**Rationale:** Single JSON per experiment contains all iterations, enabling batch pandas analysis. Unified format supports future aggregation (Phase 2 adds explanations).

---

## Researcher Workflow (After Phase 1)

**Before Phase 1:**
```bash
make evolve-all           # Runs all prompts
# Results scattered across openevolve_output/{prompt}/best_program_info.json
python show_results.py    # Manual table parsing
```

**After Phase 1:**
```bash
make evolve-all           # Runs all prompts; auto-consolidates results

# Load and analyze (3 lines)
from openevolve.results_loader import load_all_results
df = load_all_results()
df.groupby('prompt').agg({'memory_accesses': 'min'})  # Best per prompt
```

**Convergence curves:**
```python
df.plot(x='iteration', y='memory_accesses', by='prompt')
# Shows how each prompt's solution evolves across iterations
```

---

## Risks & Mitigations

| Risk | Mitigation |
|------|-----------|
| Consolidation changes break existing workflows | Backward compat: show_results.py falls back to legacy format if results.json missing |
| OpenEvolve output incomplete/missing files | Graceful degradation: consolidate_experiment() handles missing best_program_info.json, logs warning, continues |
| Pandas integration adds dependency | Pandas already required by openevolve framework; no new dependency |
| Per-iteration data not available in OpenEvolve output | Fallback: use best result only; Phase 2 can enhance if detailed iteration logs available |

---

## Files Modified/Created

**New files:**
- `.planning/RESULTS_FORMAT.md` (documentation)
- `.planning/RESULTS_USAGE.md` (usage guide)
- `openevolve/consolidate_results.py` (consolidation logic)
- `openevolve/results_loader.py` (pandas integration)
- `openevolve/show_consolidated.py` (results display)
- `openevolve/test_consolidation.py` (validation)

**Modified files:**
- `openevolve/run_experiment.py` (+15 lines: consolidation integration)
- `openevolve/show_results.py` (+30 lines: dual-format support)
- `Makefile` (+5 lines: new targets)

**Total:** 6 new files, 3 modified files

---

## Acceptance Criteria (Measured After Execution)

Wave 1 (01-01):
- [ ] RESULTS_FORMAT.md documents schema with example JSON
- [ ] consolidate_results.py module importable, consolidate_experiment() works
- [ ] results_loader.py module importable, load_results() returns DataFrame
- [ ] test_consolidation.py runs without errors
- [ ] run_experiment.py integrates consolidation (non-blocking post-run)

Wave 2 (01-02):
- [ ] `make show-consolidated-results` prints table of all prompts
- [ ] show_results.py detects consolidated format, falls back to legacy
- [ ] Backward compatibility verified (existing openevolve_output/ untouched)
- [ ] Short 5-iteration baseline experiment runs, consolidates, loads into pandas
- [ ] DataFrame has columns: iteration, memory_accesses, improvement_percent, mem_score, prompt, timestamp, baseline_accesses
- [ ] `load_all_results()` combines multiple experiments into single DataFrame

---

## Next Phase (Phase 2: LLM Explanations)

**Blocked until Phase 1 complete:** Phase 2 extends results schema with `explanation` field per iteration. Requires unified format from Phase 1 to be stable.

**Timeline:** Days 4-6 (May 15-17, 2026)

---

## Success Definition (for Phase 1)

✅ **Researcher can:**
1. Run `make evolve-all` (all prompts auto-consolidate)
2. Import: `from openevolve.results_loader import load_all_results`
3. Analyze: `df = load_all_results()` → DataFrame with all iterations from all prompts
4. Plot: `df.plot(x='iteration', y='memory_accesses', by='prompt')` → convergence curves
5. Compare: `df.groupby('prompt')['memory_accesses'].min()` → best per prompt

✅ **Data is:**
- Unified (one format, not scattered)
- Complete (all iterations, not just best)
- Pandas-native (no custom parsing)
- Documented (RESULTS_FORMAT.md, RESULTS_USAGE.md)

---

## Execution Checklist

**Before starting Wave 1:**
- [ ] Read ROADMAP.md Phase 1 section (context)
- [ ] Read STATE.md implementation plan (guidance)
- [ ] Confirm LLVM memtrace built (`make memtrace_pass.so memtrace_runtime.o`)
- [ ] Confirm Ollama running (`ollama serve`)

**During Wave 1 (01-01):**
- [ ] Task 1: Create RESULTS_FORMAT.md
- [ ] Task 2: Create consolidate_results.py
- [ ] Task 3: Create results_loader.py
- [ ] Task 4: Integrate into run_experiment.py
- [ ] Task 5: Test with synthetic data, create RESULTS_USAGE.md

**During Wave 2 (01-02):**
- [ ] Task 1: Update Makefile
- [ ] Task 2: Enhance show_results.py
- [ ] Task 3: Verify backward compatibility
- [ ] Task 4: Run short baseline experiment (5 iterations)
- [ ] Task 5: Commit and document completion

**After Phase 1:**
- [ ] All files committed to git
- [ ] ROADMAP.md Phase 1 marked complete
- [ ] Ready to start Phase 2 (LLM Explanations)

---

## Questions & Notes

**Open questions:**
1. Where should per-iteration data come from? OpenEvolve may not expose full iteration history → fallback to best result for now; Phase 2 can enhance if needed.
2. Should results be written to results/ directory or stay in openevolve_output/? Decision: stay in openevolve_output/{prompt}/ for single source of truth.
3. Estimate: 1-2 seconds per consolidation (JSON write)? Acceptable; runs after experiment, non-blocking.

**Notes:**
- Backward compatibility is critical; existing workflows must work unchanged
- Consolidation is post-processing (no changes to OpenEvolve evaluation or evolution)
- Schema is extensible (Phase 2 adds explanation field without breaking existing results)

---

## Communication

- **Team:** Solo developer (you) + Claude
- **Stakeholder:** Research team (future)
- **Status reviews:** After each wave completion
- **Blockers:** None identified; all prerequisites met

---

**Plan created by:** Claude Code (GSD Planner)  
**Date:** 2026-05-13  
**Status:** Ready for Execution

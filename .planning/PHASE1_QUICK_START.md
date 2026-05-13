# Phase 1 Quick Start — What's in the Plan

**Phase:** OpenEvolve Results Consolidation (May 13-15, 2026)  
**Goal:** Unified, pandas-readable results format  
**Status:** PLANNING COMPLETE — Ready to execute

---

## What You'll Build

### The Problem
- OpenEvolve results are scattered: `openevolve_output/{prompt}/best/best_program_info.json`
- Hard to load multiple experiments into pandas for analysis
- Convergence curves and cross-prompt comparison require manual parsing

### The Solution
A unified results format + pandas loader that lets you do:
```python
from openevolve.results_loader import load_all_results
df = load_all_results()  # All prompts → one DataFrame
df.plot(x='iteration', y='memory_accesses', by='prompt')  # Convergence curves
```

---

## Plans Overview

### Plan 01 (Wave 1 — Day 1)
**5 tasks, ~4-5 hours**

Create the infrastructure:
1. **Design schema** → `.planning/RESULTS_FORMAT.md` (unified JSON format)
2. **consolidate_results.py** (transforms OpenEvolve output → results.json)
3. **results_loader.py** (pandas: `load_results()`, `load_all_results()`)
4. **Integrate into run_experiment.py** (auto-consolidate post-run)
5. **Test + document** (`test_consolidation.py`, `RESULTS_USAGE.md`)

**Output files created:**
- `.planning/RESULTS_FORMAT.md` — Schema documentation
- `.planning/RESULTS_USAGE.md` — How to use results
- `openevolve/consolidate_results.py` — Consolidation logic
- `openevolve/results_loader.py` — Pandas interface
- `openevolve/test_consolidation.py` — Validation

**Output files modified:**
- `openevolve/run_experiment.py` — Add post-run consolidation hook

---

### Plan 02 (Wave 2 — Day 2)
**5 tasks, ~3-4 hours**

Integrate + verify:
1. **Update Makefile** (add `make show-consolidated-results` target)
2. **Create show_consolidated.py** (new results display script)
3. **Enhance show_results.py** (backward-compatible dual format support)
4. **Verify backward compatibility** (existing experiments still work)
5. **Test end-to-end** (run short experiment, load, analyze)

**Output files created:**
- `openevolve/show_consolidated.py` — Unified results table

**Output files modified:**
- `Makefile` — New targets (show-consolidated-results, results-summary)
- `openevolve/show_results.py` — Dual-format support (consolidated + legacy)

---

## The Results Format

**File location:** `openevolve_output/{prompt_variant}/results.json`

**Structure:** (see RESULTS_FORMAT.md for full details)
```json
{
  "metadata": {
    "program": "cavitydetection",
    "prompt_variant": "baseline",
    "timestamp": "2026-05-13T14:30:00Z",
    "total_iterations": 42,
    "convergence_iteration": 28,
    ...
  },
  "baseline_metrics": {
    "memory_accesses": 128862705,
    ...
  },
  "iterations": [
    {
      "iteration": 1,
      "memory_accesses": 127000000,
      "improvement_percent": 1.45,
      "mem_score": 1.0148,
      ...
    },
    ...
  ]
}
```

---

## How It Works

### Workflow After Phase 1

1. **Run experiments:**
   ```bash
   make evolve-all
   ```
   Each experiment auto-consolidates results.json at end.

2. **Load into pandas:**
   ```python
   from openevolve.results_loader import load_all_results
   df = load_all_results()  # All results, all prompts, all iterations
   ```

3. **Analyze:**
   ```python
   # Convergence per prompt
   df.plot(x='iteration', y='memory_accesses', by='prompt')
   
   # Best per prompt
   df.groupby('prompt')['memory_accesses'].min()
   
   # Convergence speed
   best_iter = df.groupby('prompt').apply(
       lambda g: g[g['memory_accesses'] == g['memory_accesses'].min()]['iteration'].iloc[0]
   )
   ```

---

## Key Design Decisions

| Decision | Rationale |
|----------|-----------|
| One JSON per experiment | Enable batch analysis without downloading multiple files |
| Schema: metadata + baseline + iterations | Supports future enhancements (Phase 2 adds explanations) |
| Post-run consolidation (not during) | Non-blocking; no overhead to experiment evaluation |
| Backward compatibility | show_results.py falls back to legacy format if results.json missing |
| Pandas integration | Researchers already know pandas; no new tool to learn |

---

## Execution Checklist

**Before you start:**
- [ ] LLVM memtrace built: `make memtrace_pass.so memtrace_runtime.o`
- [ ] Ollama running: `ollama serve` (in background)
- [ ] Python venv ready: `../openevolve/.venv/bin/python`

**Plan 01 (Day 1):**
- [ ] Task 1: RESULTS_FORMAT.md (schema documentation)
- [ ] Task 2: consolidate_results.py (consolidation logic)
- [ ] Task 3: results_loader.py (pandas integration)
- [ ] Task 4: Integration in run_experiment.py
- [ ] Task 5: Test + document usage

**Plan 02 (Day 2):**
- [ ] Task 1: Makefile updates
- [ ] Task 2: show_consolidated.py
- [ ] Task 3: show_results.py enhancement
- [ ] Task 4: Backward compatibility verification
- [ ] Task 5: End-to-end test (5-iter baseline)

**After both plans:**
- [ ] Commit to git
- [ ] Ready for Phase 2 (LLM Explanations)

---

## Success Criteria

**Plan 01 success:**
- `python3 -c "from openevolve.consolidate_results import consolidate_experiment"` works
- `python3 -c "from openevolve.results_loader import load_results, load_all_results"` works
- `python3 openevolve/test_consolidation.py` passes

**Plan 02 success:**
- `make show-consolidated-results` prints table of all prompts
- `make evolve-all` auto-consolidates results (no manual step)
- Researcher can do: `load_results('openevolve_output/baseline/results.json')` → pandas DataFrame
- `make show-results` still works (backward compat)

**Phase 1 complete:**
- All files committed
- ROADMAP.md updated
- Ready for Phase 2

---

## Files You'll Create/Modify

**NEW files (6):**
- `.planning/RESULTS_FORMAT.md`
- `.planning/RESULTS_USAGE.md`
- `openevolve/consolidate_results.py`
- `openevolve/results_loader.py`
- `openevolve/show_consolidated.py`
- `openevolve/test_consolidation.py`

**MODIFIED files (3):**
- `openevolve/run_experiment.py` (~15 lines added)
- `openevolve/show_results.py` (~30 lines added)
- `Makefile` (~5 lines added)

**Total:** ~300-400 lines of code + documentation

---

## Timeline

| Phase | Days | Status |
|-------|------|--------|
| Wave 1 (Plan 01) | Day 1 | Ready |
| Wave 2 (Plan 02) | Day 2 | Blocked until Wave 1 done |
| Buffer | Day 3 | ~1 day slack for unexpected issues |

**Fits in 3-day Phase 1 window:** ✓ (uses 2.5 days, leaves 0.5 day buffer)

---

## Next Steps

1. **Read the full plans:**
   - `.planning/phases/01-consolidation/01-01-PLAN.md` (detailed task breakdown)
   - `.planning/phases/01-consolidation/01-02-PLAN.md` (integration + verification)

2. **Start Wave 1:**
   - Begin Task 1 of Plan 01 (design schema)
   - Follow task actions step-by-step

3. **Execute → Verify → Commit:**
   - After each plan completes, run verification commands
   - Commit to git when both plans done

---

## Questions?

- **How long is each plan?** 4-5 hours (Wave 1) + 3-4 hours (Wave 2) ≈ 1.5-2 days total
- **Will this break existing experiments?** No, backward compatible. show_results.py falls back to legacy format.
- **What if OpenEvolve output is missing?** Graceful degradation; consolidation logs warning and continues.
- **Can I run this without Ollama?** For testing modules: yes. For end-to-end test (Task 5 of Plan 02): no, needs a short experiment run.

---

## Files to Review Before Starting

1. `.planning/ROADMAP.md` (Phase 1 section) — context
2. `.planning/REQUIREMENTS.md` (Phase 1 requirements) — success criteria
3. `.planning/STATE.md` (implementation plan) — design guidance
4. `openevolve/run_experiment.py` (current structure) — where integration happens
5. `openevolve/show_results.py` (current results display) — pattern to follow

---

**Status:** READY TO EXECUTE  
**Date:** 2026-05-13  
**Executor:** Claude Code

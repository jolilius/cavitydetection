# Project State & Notes

**Last Updated:** 2026-05-13  
**Current Phase:** Phase 1 — Results Consolidation (In Planning)

---

## Key Decisions

1. **Incremental, working system** — Each phase ships value; system remains working
2. **Phase 1 priority: Results consolidation** — Unified format for pandas analysis
3. **Phase 2 priority: LLM explanations** — Understand what the model thought
4. **Defer multi-program + metrics** — Not in M1; add later if needed
5. **Research focus:** Prompt influence on convergence speed, quality, strategy

---

## Implementation Plan (Phase 1)

### Results Schema Design
Goal: Consolidated JSON file per experiment run (all iterations in one file)

**File structure:**
```
results/
  cavitydetection/
    baseline.json       (all iterations for "baseline" prompt variant)
    prompt1.json
    prompt2.json
    ...
```

**Format (JSON):**
```json
{
  "metadata": {
    "program": "cavitydetection",
    "prompt_variant": "baseline",
    "timestamp": "2026-05-13T10:30:00Z",
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
      "iteration_runtime_seconds": 12.3
    },
    ...
  ]
}
```

### Pandas Loader Implementation
```python
def load_results(filepath):
    """Load consolidated results into pandas DataFrame"""
    import json
    import pandas as pd
    
    with open(filepath) as f:
        data = json.load(f)
    
    meta = data['metadata']
    baseline = data['baseline_metrics']
    
    df = pd.DataFrame(data['iterations'])
    df['prompt'] = meta['prompt_variant']
    df['timestamp'] = meta['timestamp']
    df['baseline_accesses'] = baseline['memory_accesses']
    
    return df
```

### Changes to `run_experiment.py`
- After each iteration, append to consolidated JSON (not separate files)
- Track baseline metrics per program (already available)
- Record per-iteration timing
- Calculate convergence metrics at end

### Backward Compatibility
- Keep old results around (for reference)
- Use new format going forward
- Document migration if needed

---

## Phase 2 Plan (LLM Explanations)

### Explanation Capture
After each mutation evaluation:
```python
explanation = llm.generate(
    f"Explain the transformations in this code compared to baseline. "
    f"What compiler optimizations are present?\n\n{mutated_code}"
)
```

### Extended Results Schema
Add `explanation` field to each iteration:
```json
{
  "iteration": 1,
  "memory_accesses": 127000000,
  "explanation": "Reordered inner loops to improve cache locality; adjacent accesses now sequential.",
  ...
}
```

### Timing Consideration
- Estimate: 1-2 seconds per explanation (LLM inference)
- For 40 iterations: ~40-80 sec overhead per experiment
- Acceptable for research? Tune if needed.

---

## Current Confidence & Risks

| Phase | Confidence | Risk | Mitigation |
|-------|-----------|------|-----------|
| Phase 1 | **High** | Breaking existing workflow | Keep old results; implement as new output path |
| Phase 2 | **Medium** | LLM explanations slow or vague | Monitor timing; tune prompt if incoherent |

---

## Timeline Breakdown

**Phase 1 (Days 1-3):**
- Day 1: Design results schema, start refactoring `run_experiment.py`
- Day 2: Implement pandas loader, test on existing experiments
- Day 3: Verify convergence visible in pandas; finalize format

**Phase 2 (Days 4-6):**
- Day 4: Design explanation prompt, integrate into experiment loop
- Day 5: Test on short runs (10 iterations); assess quality/speed
- Day 6: Full test, documentation

**Phase 3 (Day 7):**
- Buffer for unexpected issues or polish

---

## Blockers & Dependencies

**None currently.** 
- LLVM instrumentation working ✓
- Ollama running ✓
- Existing results available for testing ✓

---

## Open Questions

1. **Explanation quality:** Will the model's explanations be accurate and useful? Plan: test on 1-2 short runs first.
2. **Explanation timing:** Is 1-2s per iteration acceptable? Plan: monitor and optimize if needed.
3. **Results aggregation:** Per-prompt JSON or one big JSON per run? Current plan: per-prompt (one file per prompt variant).

---

## Communication & Status

- **Next review:** End of Phase 1 (should have working consolidation)
- **Decision point:** If Phase 2 explanations slow or vague, adjust prompt and re-test
- **Final ship:** Both phases complete, documentation ready, sample results reviewed

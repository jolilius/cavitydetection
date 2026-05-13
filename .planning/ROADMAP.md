# OpenEvolve Results & Explanations Framework — Roadmap

**Goal:** Consolidate experiment results into a unified format; capture LLM explanations of transformations.

**Research Focus:** Understand how prompts influence search behavior (convergence speed, quality, strategy).

**Timeline:** 1 week (2026-05-13 to 2026-05-19)

---

## Phase 1: Results Consolidation (Days 1-3)
**Status:** Ready to start  
**Success:** Consolidated results loaded into pandas; convergence visible

### Deliverables
- [ ] Define unified results schema (JSON structure for all metrics, iterations, metadata)
- [ ] Refactor `run_experiment.py` to output consolidated results per experiment
- [ ] Implement pandas loader: `load_results(path) → DataFrame`
- [ ] Update `make evolve-all` to aggregate results (or keep per-prompt JSON, pre-aggregate)
- [ ] Test on existing cavitydetection experiments

### Results Schema (JSON)
```json
{
  "metadata": {
    "program": "cavitydetection",
    "prompt": "baseline",
    "timestamp": "2026-05-13T10:30:00Z",
    "total_iterations": 42,
    "total_seconds": 480,
    "convergence_iteration": 28
  },
  "iterations": [
    {
      "iteration": 1,
      "memory_reads": 123456,
      "memory_writes": 654321,
      "timing_seconds": 12.5,
      "baseline_accesses": 128862705
    }
  ]
}
```

### Definition of Done
- ✅ Existing experiment runs produce unified JSON
- ✅ `pd.read_json(results.json)` works (or custom loader if needed)
- ✅ Can plot convergence curves: iteration vs memory accesses, colored by prompt
- ✅ README documents results format and loader usage

---

## Phase 2: LLM Explanations (Days 4-6)
**Status:** Blocked until Phase 1 complete  
**Success:** Explanations captured and visible in results; prompt strategies understood

### Deliverables
- [ ] Design explanation prompt: "Explain transformations in [code] vs baseline"
- [ ] Integrate explanation capture into `run_experiment.py` post-iteration
- [ ] Extend results schema to include `explanation` field
- [ ] Update pandas loader to expose explanations
- [ ] Test on 1-2 prompt variants (short run, e.g., 10 iterations)

### Updated Results Schema
```json
{
  "iterations": [
    {
      "iteration": 1,
      "memory_reads": 123456,
      "memory_writes": 654321,
      "timing_seconds": 12.5,
      "explanation": "Reordered loops to improve cache locality; adjacent memory accesses now sequential"
    }
  ]
}
```

### Definition of Done
- ✅ Explanations are concise (1-2 sentences) and relevant
- ✅ Can read explanations from DataFrame: `df['explanation']`
- ✅ Iteration timing includes explanation generation (acceptable overhead?)
- ✅ README documents explanation prompting and interpretation

---

## Phase 3+: Future (Optional)
**Status:** Defer to next milestone  

### Possible next steps (not committed to):
- **Multi-program support:** Run same prompts on other algorithms
- **Metric plugins:** Add valgrind, energy, runtime measurements
- **Explanation grouping:** Cluster iterations by transformation type
- **Results visualization:** Generate convergence plots, strategy heatmaps

---

## Dependency Graph

```
Phase 1 (Results consolidation)
  ↓ (required by)
Phase 2 (LLM explanations)
  ↓
Phase 3+ (optional future work)
```

**No parallel work:** Phase 2 depends on Phase 1 results schema being final.

---

## Risk & Mitigation

| Risk | Mitigation |
|------|-----------|
| Explanation generation is slow (>2s/iter) | Monitor timing; accept 1-2s overhead for now; optimize prompt if needed |
| LLM explanations are incoherent/vague | Iterate prompt; fallback to showing code diffs only |
| Results format change mid-phase | Lock schema after Phase 1 complete; backfill if needed |
| Existing experiments need re-run | Keep old results for reference; use consolidated format going forward |

---

## Success Definition

✅ **Phase 1:** 
- Consolidated results in unified format
- Pandas loader functional
- Convergence curves visible (iteration vs memory accesses by prompt)

✅ **Phase 2:** 
- Explanations captured for each iteration
- Explanations are relevant and concise
- Research questions partially answered:
  - Prompt A converges faster than Prompt B (measurable)
  - Different prompts find different optima (quality comparison)
  - LLM's strategy is visible (explanation text)

---

## Ship Criteria

**After Phase 1:** 
- Commit consolidated results schema and loader
- Existing experiments runnable with new format
- Documentation complete

**After Phase 2:**
- Commit explanation integration
- Sample results with explanations for review
- Full documentation + interpretation guide

---

## Daily Standup Template

```
Date: [DATE]
Phase: [1 or 2]
Done: [what got done today]
Next: [what's next]
Blockers: [any problems?]
Confidence: [% estimate for phase completion]
```


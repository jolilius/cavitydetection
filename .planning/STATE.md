# Project State & Notes

**Last Updated:** 2026-05-13  
**Current Phase:** Framework Architecture (Phase 1 of 4)

---

## Decisions Made

1. **Multi-program from start** — Not cavitydetection-only; framework designed for 2+ programs
2. **LLM-generated explanations** — Model explains each transformation attempt in-situ
3. **Plugin system for metrics** — Extensible metric collection; memory metric built-in, future metrics pluggable
4. **Text-based results** — JSON/CSV storage; no web dashboard yet
5. **One week timeline** — M1 ships by 2026-05-19 with framework + instrumentation + basic metrics

---

## Implementation Notes

### Multi-Program Config
- Centralize program definitions in `openevolve/config.yaml`
- Each program declares: seed file, baseline access count, evaluator path, output directory
- `run_experiment.py` iterates over programs; one invocation runs all

### LLM Explanations
- After each iteration, prompt: "Explain the transformations in [mutated_code] compared to baseline. What compiler optimizations or idioms are present?"
- Store explanation in results JSON per iteration
- May need to tune prompt for clarity; have fallback to structured diffs

### Metric Plugin System
- Interface: `class MetricCollector: def collect(candidate_code: str, baseline: dict) -> dict`
- Discovery: scan `openevolve/metrics/` for `*.py` files
- Config: `metrics:` section in YAML lists which to enable
- First metric: memory accesses (read/write split) via LLVM instrumentation

### Results Format (JSON)
```json
{
  "experiment": {
    "program": "cavitydetection",
    "prompt": "baseline",
    "timestamp": "2026-05-13T10:30:00Z",
    "hardware": {
      "cpu": "Apple M1",
      "ram_gb": 16,
      "os": "macOS 14.5"
    },
    "llm_model": "qwen2.5-coder:32b",
    "iterations": [
      {
        "iteration": 1,
        "code_hash": "abc123",
        "explanation": "Reordered loops to improve cache locality...",
        "metrics": {
          "memory_reads": 123456,
          "memory_writes": 654321,
          "memory_total": 777777
        },
        "timing": {
          "iteration_seconds": 12.5,
          "cumulative_seconds": 12.5
        }
      }
    ],
    "summary": {
      "total_iterations": 42,
      "total_seconds": 480,
      "best_score": 1.05,
      "converged_at_iteration": 28
    }
  }
}
```

---

## Known Challenges

| Challenge | Status | Plan |
|-----------|--------|------|
| LLM explanation generation may be slow | Open | Monitor timing; if >2s/iter, switch to diff-only and annotate manually |
| Baseline metrics for loopoptimization1 not yet measured | Blocked on Phase 1 | Run baseline immediately after refactor |
| Prompting model to explain transformations (no prior example) | Open | Start with simple prompt; iterate based on output quality |

---

## Timeline Confidence

**Phase 1 (Framework):** High confidence — refactoring existing code, clear scope  
**Phase 2 (Instrumentation):** Medium confidence — LLM explanation may need iteration  
**Phase 3 (Metrics):** High confidence — plugin pattern is straightforward  
**Phase 4 (Validation):** High confidence — integration testing only  

**Buffer:** Built-in; can compress Phase 3 if needed.

---

## Blockers & Dependencies

- **None currently** — all prerequisites met (Ollama running, LLVM instrumentation working, OpenEvolve cloned)
- **Next blocker:** Baseline measurement for loopoptimization1 (depends on Phase 1 refactor)

---

## Communication

- **Status:** Check this file before/after each phase
- **Updates:** Brief notes here; detailed phase results in phase-specific documents
- **Review points:** End of Phase 2 (assess LLM explanation quality); end of Phase 3 (validate metrics)

# Phase 2: LLM Explanations — Planning Complete

**Date:** 2026-05-13  
**Planner:** Claude Haiku 4.5  
**Status:** Ready for Execution

---

## Overview

Phase 2 introduces LLM-generated explanations for code transformations discovered by OpenEvolve. The plan consists of **3 sequential plans** across **3 waves**, with clear task breakdowns and dependency management.

**Total Plans:** 3  
**Total Tasks:** 10  
**Estimated Effort:** 2-3 days (with Ollama running)  
**Dependencies:** Phase 1 (Results Consolidation) — COMPLETE ✓

---

## Plan Structure

### Wave 1: Explanation Infrastructure (02-01)
**Duration:** ~4-5 hours  
**Autonomy:** Fully independent (no external dependencies beyond Phase 1)

| Task | Purpose | Files |
|------|---------|-------|
| 1. Design explanation prompt | Create system message for LLM | explanation_prompt.txt, EXPLANATION_DESIGN.md |
| 2. Build explanation generator | Reusable LLM API module | explanation_generator.py |
| 3. Extend consolidation schema | Add explanations parameter | consolidate_results.py |

**Output:** Explanation infrastructure ready for integration

**Verification:** Module imports, function signatures, JSON schema validation

---

### Wave 2: Experiment Integration (02-02)
**Duration:** ~3-4 hours  
**Depends on:** Wave 1 complete

| Task | Purpose | Files |
|------|---------|-------|
| 1. Integrate into run_experiment.py | Capture explanations during experiments | run_experiment.py |
| 2. Update results_loader.py | Expose explanations in DataFrame | results_loader.py |
| 3. Add Makefile test targets | Enable short test runs with explanations | Makefile |

**Output:** Explanation generation integrated into standard workflow

**Verification:** 10-iteration test runs, results.json includes explanation field

---

### Wave 3: Documentation & Testing (02-03)
**Duration:** ~2-3 hours  
**Depends on:** Waves 1-2 complete

| Task | Purpose | Files |
|------|---------|-------|
| 1. Update RESULTS_FORMAT.md | Document explanation field schema | .planning/RESULTS_FORMAT.md |
| 2. Expand RESULTS_USAGE.md | Provide explanation analysis examples | .planning/RESULTS_USAGE.md |
| 3. Update README.md | Document Phase 2 completion | README.md |
| 4. Add test cases | Verify explanation handling | openevolve/test_consolidation.py |

**Output:** Comprehensive documentation and test coverage

**Verification:** Test suite execution, documentation accuracy

---

## Files Created vs. Modified

### Created (New Files)
- `openevolve/explanation_prompt.txt` — LLM system message (Wave 1)
- `openevolve/EXPLANATION_DESIGN.md` — Prompt design rationale (Wave 1)
- `openevolve/explanation_generator.py` — Explanation generation module (Wave 1)

### Modified (Existing Files)
- `openevolve/consolidate_results.py` — Add explanations parameter (Wave 1)
- `openevolve/run_experiment.py` — Integration point (Wave 2)
- `openevolve/results_loader.py` — DataFrame handling (Wave 2)
- `Makefile` — Test targets (Wave 2)
- `.planning/RESULTS_FORMAT.md` — Schema documentation (Wave 3)
- `.planning/RESULTS_USAGE.md` — Usage examples (Wave 3)
- `README.md` — Project documentation (Wave 3)
- `openevolve/test_consolidation.py` — Test suite (Wave 3)

**No file conflicts:** Each file is modified by exactly one plan, ensuring safe sequential execution.

---

## Key Design Features

### 1. Non-Blocking Explanations
- Experiments succeed even if LLM is unavailable or times out
- Graceful error handling with informative logging
- Optional EXPLAIN_GENERATIONS=0 flag to skip explanation generation

### 2. Backward Compatible
- Phase 1 results (without explanations) continue to work
- DataFrame handles missing explanations as NaN
- Schema supports both new and old results formats

### 3. Simple 1-2 Sentence Format
- LLM constrained to produce concise explanations
- Easy for researchers to scan while reviewing results
- Examples: "Reordered loops to improve cache locality", "Fused blur and edge detection passes"

### 4. Infrastructure-First Approach
- Explanation generator built and tested in isolation (Wave 1)
- Integration follows after infrastructure is solid (Wave 2)
- Reduces debugging effort and integration risk

---

## Task-Level Parallelization

Within each wave, some tasks can run in parallel:

**Wave 1:** Tasks 1+3 can run in parallel (Task 2 depends on Task 1)
**Wave 2:** Tasks 1+2 can run in parallel (Task 3 depends on 1+2)
**Wave 3:** Tasks 1-3 can run in parallel (Task 4 depends on all)

However, **waves are sequential** (each wave depends on previous completion).

---

## Execution Path

```
Prerequisite: Phase 1 complete ✓
             Ollama running with qwen2.5-coder model
                     │
                     ▼
         ┌───────────────────────┐
         │ Execute Wave 1 (02-01)│
         │ Infrastructure        │
         └─────────┬─────────────┘
                   │
                   ▼
         ┌───────────────────────┐
         │ Execute Wave 2 (02-02)│
         │ Integration           │
         └─────────┬─────────────┘
                   │
                   ▼
         ┌───────────────────────┐
         │ Execute Wave 3 (02-03)│
         │ Documentation         │
         └───────────────────────┘
                   │
                   ▼
             Phase 2 COMPLETE
```

---

## Verification Checklist

### Pre-Execution
- [ ] Phase 1 (Results Consolidation) fully complete
- [ ] Ollama running: `curl http://localhost:11434/api/tags`
- [ ] qwen2.5-coder or compatible model available: `ollama list`
- [ ] Python venv activated with required packages

### Post-Wave 1
- [ ] explanation_prompt.txt exists (20+ lines)
- [ ] explanation_generator.py imports cleanly
- [ ] Function signature: `generate_explanation(evolved, baseline, config, prompt) → str | None`
- [ ] consolidate_results.py accepts explanations parameter

### Post-Wave 2
- [ ] run_experiment.py includes explanation generation
- [ ] EXPLAIN_GENERATIONS environment variable works
- [ ] results_loader.py exposes explanation column
- [ ] Makefile targets created: evolve-explain-test, show-explanations
- [ ] Test run: `make evolve-explain-test` succeeds
- [ ] results.json includes explanation field: `jq '.iterations[0].explanation' openevolve_output/baseline/results.json`

### Post-Wave 3
- [ ] RESULTS_FORMAT.md documents explanation field
- [ ] RESULTS_USAGE.md includes explanation analysis examples
- [ ] README.md mentions Phase 2 completion
- [ ] Test suite passes: `cd openevolve && python3 test_consolidation.py`
- [ ] Backward compatibility verified: Phase 1 results still load as NaN for explanation

---

## Definition of Done (Phase 2)

All of the following must be true:

1. ✅ **Explanations are concise** — 1-2 sentences, 50-200 characters
2. ✅ **Accessible via DataFrame** — `df['explanation']` works
3. ✅ **Iteration timing acceptable** — ~1-2 seconds overhead per iteration
4. ✅ **Non-blocking** — Experiments succeed even if explanations fail
5. ✅ **Backward compatible** — Phase 1 results continue to work
6. ✅ **Well documented** — README, schema docs, usage examples
7. ✅ **Tested** — Unit tests for explanation handling
8. ✅ **All committed** — Changes pushed to main branch

---

## Risk Mitigation

| Risk | Likelihood | Mitigation |
|------|-----------|-----------|
| Ollama unavailable | Medium | Non-blocking; EXPLAIN_GENERATIONS=0 flag |
| Explanation quality poor | Medium | Test prompt with short runs; iterate before long experiments |
| Integration bugs | Medium | 10-iteration test runs verify integration before full runs |
| LLM timeout | Low | Handled gracefully with timeout in explanation_generator.py |
| Results format issues | Low | Backward compatibility testing; Phase 1 results unaffected |

---

## Resource Requirements

### System
- **Ollama:** Running with qwen2.5-coder:32b model (or compatible)
- **Storage:** ~10 MB per 100-iteration experiment (explanations ~50 bytes each)
- **Time:** 1-2 seconds per explanation generation (expected)

### Development
- **Python:** 3.8+ with pandas, yaml, requests libraries
- **LLM API:** Ollama endpoint (default: http://localhost:11434/v1/)

---

## What's Included in This Plan Set

1. **02-01-PLAN.md** — Explanation infrastructure (prompt + generator + schema)
2. **02-02-PLAN.md** — Experiment integration (run_experiment + loader + Makefile)
3. **02-03-PLAN.md** — Documentation and testing (docs + tests)
4. **PHASE_2_OVERVIEW.md** — Detailed breakdown and design rationale
5. **PLANNING_SUMMARY.md** — This file

---

## Getting Started

To begin Phase 2 execution:

1. **Start with Plan 02-01:** Execute all 3 tasks in Wave 1
2. **Verify Wave 1 completion** using provided verification steps
3. **Move to Plan 02-02:** Execute tasks for Wave 2
4. **Verify Wave 2 completion** with 10-iteration test run
5. **Complete Phase 2** with Plan 02-03 documentation and testing

Each PLAN.md file is self-contained and includes:
- Specific task actions (what to implement)
- Verification steps (how to confirm completion)
- Done criteria (what success looks like)

---

## Post-Phase 2

After Phase 2 completion:

1. **Run a real experiment:** `make evolve-all ITERATIONS=40` to gather explanations
2. **Analyze results:** Use examples from RESULTS_USAGE.md to understand prompt strategies
3. **Consider Phase 3:** Optional work on visualization, clustering, multi-program support

Recommended immediate next step:
```bash
# After Phase 2 is complete and you have explanation data
python3 << 'EOF'
from openevolve.results_loader import load_all_results
df = load_all_results()
print("Explanations captured:")
print(df[df['explanation'].notna()][['prompt', 'iteration', 'improvement_percent', 'explanation']].head(20))
EOF
```

---

## Questions?

See **PHASE_2_OVERVIEW.md** for detailed design rationale, architecture diagrams, and answers to common questions (Ollama unavailable, explanation accuracy, prompt customization, etc.).

---

**Planning completed:** 2026-05-13  
**Ready to execute:** Wave 1 (Plan 02-01) can start immediately

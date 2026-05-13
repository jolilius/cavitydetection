# Phase 2: LLM Explanations — Planning Documents

**Planning Complete:** 2026-05-13  
**Status:** Ready for Execution  
**Phase Duration:** 2-3 days (with Ollama running)

---

## Overview

This directory contains the complete execution plan for Phase 2 (LLM Explanations). The phase adds automatic capture of LLM-generated explanations for code transformations discovered by OpenEvolve.

**Phase Structure:**
- 3 sequential plans (02-01, 02-02, 02-03)
- 3 execution waves (wave 1 → wave 2 → wave 3)
- 10 total tasks
- Clear dependencies and parallelization opportunities

---

## Documents in This Directory

### Execution Plans (Read in Order)

1. **[02-01-PLAN.md](02-01-PLAN.md)** — Explanation Infrastructure (Wave 1)
   - Design explanation prompt system message
   - Build explanation generator module
   - Extend consolidation schema
   - Duration: ~4-5 hours
   - **Start here** for actual implementation

2. **[02-02-PLAN.md](02-02-PLAN.md)** — Experiment Integration (Wave 2)
   - Integrate explanations into run_experiment.py
   - Update results_loader.py for explanation column
   - Add Makefile test targets
   - Duration: ~3-4 hours
   - **Execute after Wave 1 complete**

3. **[02-03-PLAN.md](02-03-PLAN.md)** — Documentation & Testing (Wave 3)
   - Update RESULTS_FORMAT.md with explanation field
   - Expand RESULTS_USAGE.md with analysis examples
   - Update README.md for Phase 2
   - Add test cases for explanation handling
   - Duration: ~2-3 hours
   - **Execute after Wave 2 complete**

### Planning Reference Documents

4. **[QUICK_START.md](QUICK_START.md)** — Quick Reference
   - What to execute (high-level overview)
   - Success indicators after each wave
   - Common pitfalls and troubleshooting
   - Estimated timeline
   - **Read this first** for quick navigation

5. **[PHASE_2_OVERVIEW.md](PHASE_2_OVERVIEW.md)** — Detailed Planning
   - Complete plan breakdown by wave
   - Dependency graph (visual)
   - Task-level parallelization analysis
   - File ownership summary
   - Key design decisions
   - Risk assessment
   - **Read for architecture & design rationale**

6. **[PLANNING_SUMMARY.md](PLANNING_SUMMARY.md)** — Status & Checklist
   - Current planning status
   - File creation vs. modification summary
   - Task-level parallelization opportunities
   - Verification checklist
   - Definition of Done
   - **Read for status & acceptance criteria**

---

## How to Use This Plan Set

### For Quick Execution
1. Read **QUICK_START.md** (this gives you the gist)
2. Open corresponding PLAN.md file (02-01, 02-02, or 02-03)
3. Follow the tasks in order
4. Use the <verify> section to confirm completion

### For Understanding Architecture
1. Read **PHASE_2_OVERVIEW.md** for design decisions
2. Look at the dependency graph (visual)
3. Understand why tasks are ordered this way
4. Review "Key Design Decisions" section

### For Tracking Progress
1. Check **PLANNING_SUMMARY.md** for current status
2. Use the "Verification Checklist" (organized by wave)
3. Mark items off as you complete them
4. Refer to "Definition of Done" for acceptance criteria

---

## Quick Facts

| Aspect | Details |
|--------|---------|
| **Phase Number** | 2 (after Phase 1: Results Consolidation) |
| **Plans** | 3 (02-01, 02-02, 02-03) |
| **Waves** | 3 (sequential, each depends on previous) |
| **Total Tasks** | 10 |
| **Estimated Duration** | 2-3 days (9-12 hours effort, 6-8 with parallelization) |
| **Prerequisites** | Phase 1 complete, Ollama running |
| **Files Created** | 3 new files (explanation_prompt.txt, EXPLANATION_DESIGN.md, explanation_generator.py) |
| **Files Modified** | 8 existing files (consolidate_results.py, run_experiment.py, results_loader.py, Makefile, RESULTS_FORMAT.md, RESULTS_USAGE.md, README.md, test_consolidation.py) |

---

## Execution Path

```
Prerequisites:
  ✓ Phase 1 (Results Consolidation) complete
  • Ollama running with qwen2.5-coder model
  
                      ↓
        ┌─────────────────────────┐
        │  Wave 1: 02-01-PLAN.md  │
        │  Explanation Foundation │
        │  ~4-5 hours             │
        └────────────┬────────────┘
                     ↓
        ┌─────────────────────────┐
        │  Wave 2: 02-02-PLAN.md  │
        │  Experiment Integration │
        │  ~3-4 hours             │
        └────────────┬────────────┘
                     ↓
        ┌─────────────────────────┐
        │  Wave 3: 02-03-PLAN.md  │
        │  Documentation & Tests  │
        │  ~2-3 hours             │
        └────────────┬────────────┘
                     ↓
                Phase 2 COMPLETE
```

---

## Key Planning Features

### Clear Task Breakdown
Each PLAN.md file specifies:
- Exact files to create/modify
- Specific implementation details (not vague)
- How to verify completion
- Acceptance criteria

### Dependency Management
- Each wave depends on previous completion
- Within-wave parallelization identified
- No file conflicts (each file modified by exactly one plan)
- Explicit `depends_on` relationships

### Non-Blocking Design
- Explanation generation is optional
- Experiments succeed even if LLM unavailable
- EXPLAIN_GENERATIONS=0 flag allows opt-out
- Graceful error handling throughout

### Comprehensive Verification
- Each task has automated verification commands
- Wave-end verification checklist
- Phase-end Definition of Done
- Test suite for regression prevention

---

## What Gets Built

### Wave 1 Outputs
- `openevolve/explanation_prompt.txt` — LLM system message (20+ lines)
- `openevolve/EXPLANATION_DESIGN.md` — Design rationale document
- `openevolve/explanation_generator.py` — Reusable LLM API module
- Extended `openevolve/consolidate_results.py` — Stores explanations in JSON

### Wave 2 Outputs
- Updated `openevolve/run_experiment.py` — Generates explanations during experiments
- Enhanced `openevolve/results_loader.py` — Exposes explanation column in DataFrame
- New Makefile targets: `evolve-explain-test`, `show-explanations`
- EXPLAIN_GENERATIONS environment variable support

### Wave 3 Outputs
- Updated `.planning/RESULTS_FORMAT.md` — Documents explanation field
- Expanded `.planning/RESULTS_USAGE.md` — Explanation analysis examples
- Updated `README.md` — Phase 2 completion notes
- Enhanced `openevolve/test_consolidation.py` — Explanation test cases

---

## Success Criteria

Phase 2 is complete when:

- [x] Explanations are concise (1-2 sentences, 50-200 characters)
- [x] Accessible via DataFrame: `df['explanation']`
- [x] Iteration timing acceptable (~1-2s overhead per iteration)
- [x] Non-blocking (experiments succeed without explanations)
- [x] Backward compatible (Phase 1 results still work)
- [x] Well documented (README, schema docs, examples)
- [x] Tested (unit tests for explanation handling)
- [x] All committed (changes in git)

---

## Common Questions

**Q: Why 3 plans instead of 1?**
A: Dependency management and parallelization. Each plan is self-contained and testable. Smaller scope = lower risk and easier debugging.

**Q: Can I skip any waves?**
A: No. Each wave builds on the previous. Wave 2 needs Wave 1 infrastructure; Wave 3 needs Waves 1-2 complete.

**Q: What if Ollama is down?**
A: Explanation generation will timeout gracefully. Set EXPLAIN_GENERATIONS=0 to skip. Experiments succeed either way.

**Q: How long does explanation generation take?**
A: ~1-2 seconds per iteration. For a 40-iteration experiment: ~40-80 seconds overhead. This is acceptable for research.

**Q: Can I customize the explanation prompt?**
A: Yes. Edit `openevolve/explanation_prompt.txt` and re-run experiments. New prompt takes effect on next run.

**See PHASE_2_OVERVIEW.md for more Q&A**

---

## Next Steps

1. **Read QUICK_START.md** (2 minutes) — Get oriented
2. **Open 02-01-PLAN.md** (5 minutes) — Understand Wave 1 tasks
3. **Start implementing** Wave 1 tasks following the <action> sections
4. **Verify completion** using the <verify> sections
5. **Commit:** `feat(02-01): implement explanation infrastructure`
6. **Move to 02-02-PLAN.md** — Repeat for Wave 2
7. **Move to 02-03-PLAN.md** — Repeat for Wave 3

---

## Planning Methodology

This plan set was created using:
- **GSD Framework:** Get-Shit-Done planning methodology
- **Wave-based execution:** Maximize parallelization within dependencies
- **Interface-first design:** Clear task outputs and inputs
- **Backward compatibility:** All Phase 1 code still works
- **Non-blocking patterns:** Optional features don't block core functionality

---

## Document Locations

All Phase 2 planning documents are in this directory (`.planning/phases/02-llm-explanations/`):

```
.planning/phases/02-llm-explanations/
├── README.md                    ← You are here
├── QUICK_START.md               ← Start here for quick navigation
├── 02-01-PLAN.md               ← Wave 1: Foundation
├── 02-02-PLAN.md               ← Wave 2: Integration
├── 02-03-PLAN.md               ← Wave 3: Documentation
├── PHASE_2_OVERVIEW.md          ← Architecture & design
└── PLANNING_SUMMARY.md          ← Status & checklist
```

---

**Planning Status:** ✅ COMPLETE — Ready for Execution

**Recommended Starting Point:** [QUICK_START.md](QUICK_START.md)

**For Implementation:** [02-01-PLAN.md](02-01-PLAN.md) (Wave 1 tasks)

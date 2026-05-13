# Phase 1 Planning — OpenEvolve Results Consolidation

**Status:** PLANNING COMPLETE — Ready to Execute  
**Date:** 2026-05-13  
**Phase:** 01-consolidation  
**Timeline:** May 13-15, 2026 (3 days)

---

## Start Here

### 🚀 Quick 5-Minute Overview
**File:** `PHASE1_QUICK_START.md`
- What you'll build (problem & solution)
- Plan overview (2 pages)
- Success criteria
- Execution checklist

### 📚 Full Navigation Guide
**File:** `PHASE1_INDEX.md`
- Complete document structure
- Task breakdown with time estimates
- File inventory
- Dependency graphs
- Timeline and checklist

### 📋 Detailed Context & Design
**File:** `PLANNING_SUMMARY.md`
- Phase overview and rationale
- Results schema explanation
- Researcher workflow (before/after)
- Risks and mitigations
- Full acceptance criteria

### ✅ Execution & Deliverables
**File:** `PHASE1_DELIVERABLES.md`
- Files to create/modify
- Task-by-task deliverables
- Execution timeline (hour-by-hour)
- Verification commands
- Success checklist

---

## Executable Plans

### Wave 1: Schema Design & Module Implementation
**File:** `phases/01-consolidation/01-01-PLAN.md`

5 tasks, ~5 hours, all autonomous (no checkpoints)
1. Design unified results schema
2. Implement consolidate_results.py module
3. Implement results_loader.py module
4. Integrate into run_experiment.py
5. Test and document (test_consolidation.py, RESULTS_USAGE.md)

**Creates:** 4 new Python modules + 2 documentation files  
**Modifies:** 1 file (run_experiment.py)

### Wave 2: Integration & Verification
**File:** `phases/01-consolidation/01-02-PLAN.md`

5 tasks, ~4 hours, all autonomous (no checkpoints)
1. Update Makefile with new targets
2. Create show_consolidated.py script
3. Enhance show_results.py for dual-format support
4. Verify backward compatibility
5. End-to-end testing (5-iteration baseline)

**Creates:** 1 new Python module  
**Modifies:** 2 files (show_results.py, Makefile)

---

## What You're Building

### Problem
OpenEvolve experiment results are scattered across JSON files making batch analysis difficult.

### Solution
Unified results format + pandas loader enabling:
```python
from openevolve.results_loader import load_all_results
df = load_all_results()
df.plot(x='iteration', y='memory_accesses', by='prompt')
```

### Key Features
- **Unified Format:** One JSON per experiment with all iterations
- **Pandas Integration:** Load directly into DataFrame
- **Auto-consolidation:** Results saved automatically after each experiment
- **Backward Compatible:** Existing workflows unchanged
- **Extensible:** Phase 2 can add explanations without breaking Phase 1

---

## File Summary

### Planning Documents (Already Created)
- `PHASE1_QUICK_START.md` (7.7 KB) — Start here!
- `PHASE1_INDEX.md` (15 KB) — Full navigation
- `PLANNING_SUMMARY.md` (9.9 KB) — Design context
- `PHASE1_DELIVERABLES.md` (15 KB) — Timeline & checklist
- `README.md` (this file) — Quick index

### Executable Plans
- `phases/01-consolidation/01-01-PLAN.md` (25 KB) — Wave 1 detailed tasks
- `phases/01-consolidation/01-02-PLAN.md` (18 KB) — Wave 2 detailed tasks

### To Be Created (During Execution)
- `.planning/RESULTS_FORMAT.md` — Schema specification
- `.planning/RESULTS_USAGE.md` — Researcher usage guide
- `openevolve/consolidate_results.py` — Consolidation module
- `openevolve/results_loader.py` — Pandas integration
- `openevolve/show_consolidated.py` — Results display
- `openevolve/test_consolidation.py` — Validation tests

### To Be Modified (During Execution)
- `openevolve/run_experiment.py` — Add post-run consolidation
- `openevolve/show_results.py` — Add dual-format support
- `Makefile` — Add new targets

---

## Quick Execution Checklist

### Prerequisites
- [ ] LLVM memtrace built: `make memtrace_pass.so memtrace_runtime.o`
- [ ] Ollama running: `ollama serve` (background)
- [ ] Python venv ready: `../openevolve/.venv/bin/python`

### Wave 1 (Day 1)
- [ ] Task 1: Design schema → RESULTS_FORMAT.md
- [ ] Task 2: consolidate_results.py module
- [ ] Task 3: results_loader.py module
- [ ] Task 4: Integrate into run_experiment.py
- [ ] Task 5: Test & document
- [ ] Verify: `python3 openevolve/test_consolidation.py`

### Wave 2 (Day 2)
- [ ] Task 1: Update Makefile
- [ ] Task 2: show_consolidated.py
- [ ] Task 3: Enhance show_results.py
- [ ] Task 4: Verify backward compatibility
- [ ] Task 5: End-to-end test (5-iteration baseline)
- [ ] Verify: `make show-consolidated-results`

### Final (Day 3 Buffer)
- [ ] All files committed to git
- [ ] ROADMAP.md updated
- [ ] Ready for Phase 2

---

## Timeline

```
Day 1 (May 13): Wave 1 — Infrastructure
  09:00-09:30: Task 1 (schema design)
  09:30-11:00: Task 2 (consolidate_results.py)
  11:00-12:30: Task 3 (results_loader.py)
  12:30-13:30: Lunch
  13:30-14:00: Task 4 (integration)
  14:00-15:00: Task 5 (testing + docs)
  → Total: 5 hours

Day 2 (May 14): Wave 2 — Integration
  09:00-09:30: Task 1 (Makefile)
  09:30-10:30: Task 2 (show_consolidated.py)
  10:30-11:30: Task 3 (show_results.py)
  11:30-12:30: Lunch
  12:30-13:00: Task 4 (backward compat)
  13:00-14:30: Task 5 (end-to-end test)
  → Total: 4.5 hours

Day 3 (May 15): Buffer & Polish
  Review, final fixes, git commit, Phase 2 prep
```

---

## Success Criteria

### Wave 1 Success
- ✓ All 5 tasks completed
- ✓ consolidate_results.py and results_loader.py modules functional
- ✓ test_consolidation.py passes
- ✓ RESULTS_FORMAT.md and RESULTS_USAGE.md created
- ✓ run_experiment.py auto-consolidates results

### Wave 2 Success
- ✓ All 5 tasks completed
- ✓ make show-consolidated-results works
- ✓ show_results.py backward compatible
- ✓ Short baseline experiment runs and consolidates
- ✓ Results load into pandas DataFrame

### Phase 1 Complete
- ✓ All 10 tasks done
- ✓ All files committed to git
- ✓ Ready for Phase 2 (LLM Explanations)

---

## Document Reading Order

### First Time?
1. This README.md (you're reading it)
2. PHASE1_QUICK_START.md (5 min overview)
3. PHASE1_INDEX.md (full navigation)
4. phases/01-consolidation/01-01-PLAN.md (detailed tasks)

### Ready to Execute?
1. Review the relevant task in 01-01-PLAN.md or 01-02-PLAN.md
2. Read the `<action>` section
3. Follow the steps exactly
4. Run `<verify>` command to confirm
5. Check off the `<done>` criteria

### Need Reference?
- RESULTS_FORMAT.md — Schema specification (created during execution)
- RESULTS_USAGE.md — Code examples (created during execution)
- 01-01-PLAN.md — Wave 1 detailed spec
- 01-02-PLAN.md — Wave 2 detailed spec

---

## Total Effort Estimate

| Component | Time | Certainty |
|-----------|------|-----------|
| Wave 1 Infrastructure | 5 hours | High |
| Wave 2 Integration | 4.5 hours | High |
| Testing & Verification | 1 hour | Medium |
| Documentation | 1 hour | High |
| **Total** | **~11 hours** | **High** |
| **Timeline** | 2.5 days + 0.5 buffer | **Fits in 3 days** |

---

## Key Decisions

| Decision | Rationale |
|----------|-----------|
| One JSON per experiment | Enable batch analysis without multiple downloads |
| Post-run consolidation | Non-blocking; no experiment overhead |
| Backward compatibility | Existing workflows must not break |
| Pandas integration | Researchers already know pandas |
| Schema extensible | Phase 2 can add fields without breaking |

---

## Questions?

**How long is this really?**
- Wave 1: ~5 hours (5 tasks)
- Wave 2: ~4 hours (5 tasks)
- Total: ~9-10 hours of work (fits in 2.5 days with buffer)

**What if something breaks?**
- Verification commands after each task confirm you're on track
- Timeline includes buffer for fixes
- All changes are reversible (git)

**Can I start today?**
- Yes! Read PHASE1_QUICK_START.md first (5 min)
- Then start Wave 1, Task 1

**What's next after Phase 1?**
- Phase 2: LLM Explanations (blocked until Phase 1 complete)
- Extends results schema with explanation field per iteration
- Captures what the LLM thought at each iteration

---

## File Paths (Quick Reference)

```
/Users/jolilius/home/src/research/cavitydetection/

.planning/
├─ README.md (this file)
├─ PHASE1_QUICK_START.md ← Start here!
├─ PHASE1_INDEX.md (full navigation)
├─ PLANNING_SUMMARY.md (context & design)
├─ PHASE1_DELIVERABLES.md (timeline & checklist)
├─ RESULTS_FORMAT.md (created by Wave 1, Task 1)
├─ RESULTS_USAGE.md (created by Wave 1, Task 5)
└─ phases/
   └─ 01-consolidation/
      ├─ 01-01-PLAN.md ← Wave 1 detailed tasks
      └─ 01-02-PLAN.md ← Wave 2 detailed tasks

openevolve/ (modified/created during execution)
├─ consolidate_results.py (created)
├─ results_loader.py (created)
├─ show_consolidated.py (created)
├─ test_consolidation.py (created)
├─ run_experiment.py (modified)
└─ show_results.py (modified)

Makefile (modified)
```

---

## Getting Started

### Option 1: Quick Path (10 minutes)
1. Read PHASE1_QUICK_START.md (5 min)
2. Skim PHASE1_INDEX.md (3 min)
3. Start executing 01-01-PLAN.md Task 1
4. 2 min to get oriented

### Option 2: Full Understanding (30 minutes)
1. Read PHASE1_QUICK_START.md (5 min)
2. Read PHASE1_INDEX.md (10 min)
3. Read PLANNING_SUMMARY.md (10 min)
4. Skim 01-01-PLAN.md objectives (3 min)
5. Start executing Task 1 (2 min to get oriented)

### Option 3: Full Deep Dive (1 hour)
1. Read all navigation documents (30 min)
2. Read both full plan documents (20 min)
3. Review file inventory and timeline (5 min)
4. Start executing Task 1 (5 min to get oriented)

---

**Status:** PLANNING COMPLETE  
**Ready to Execute:** YES  
**Confidence Level:** HIGH  

**Next Step:** Read PHASE1_QUICK_START.md (5 minutes) then start Wave 1, Task 1

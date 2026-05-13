# Phase 1 Planning Index

**Phase:** 01-consolidation (OpenEvolve Results Consolidation)  
**Timeline:** May 13-15, 2026 (3 days)  
**Status:** PLANNING COMPLETE — Ready to Execute  
**Plans:** 2 (Wave 1 + Wave 2)  
**Total Tasks:** 10 (5 + 5)

---

## Documents (Start Here)

### 🚀 Quick Overview
- **`PHASE1_QUICK_START.md`** ← **START HERE** (5-min read)
  - What you'll build
  - Plan overview (2 pages)
  - Execution checklist
  - Success criteria

### 📋 Detailed Planning
- **`PLANNING_SUMMARY.md`** (comprehensive context)
  - Phase overview and rationale
  - Wave structure and dependencies
  - Results schema explanation
  - Researcher workflow before/after
  - Risks and mitigations
  - Full acceptance criteria
  - Execution checklist

### 📖 Full Specification
- **`.planning/phases/01-consolidation/01-01-PLAN.md`** (detailed Task 1-5)
  - Unified schema design (Task 1)
  - consolidate_results.py implementation (Task 2)
  - results_loader.py implementation (Task 3)
  - Integration into run_experiment.py (Task 4)
  - Testing & documentation (Task 5)
  - Threat model and verification

- **`.planning/phases/01-consolidation/01-02-PLAN.md`** (detailed Task 1-5)
  - Makefile updates (Task 1)
  - show_consolidated.py creation (Task 2)
  - show_results.py enhancement (Task 3)
  - Backward compatibility verification (Task 4)
  - End-to-end testing (Task 5)
  - Threat model and verification

### 📚 Reference Documents (Created During Execution)
- **`.planning/RESULTS_FORMAT.md`** (created by Plan 01, Task 1)
  - Results schema (JSON structure)
  - Field definitions and types
  - Example with 2 iterations
  - Consolidation rationale

- **`.planning/RESULTS_USAGE.md`** (created by Plan 01, Task 5)
  - Quick start: load + plot convergence
  - Single experiment analysis
  - Cross-prompt comparison
  - Fields reference
  - Storage location

---

## Wave Structure

```
┌─────────────────────────────────────────────────────────────────┐
│ WAVE 1 (Day 1): Infrastructure                                  │
├─────────────────────────────────────────────────────────────────┤
│ Plan 01-01: Schema Design & Module Implementation               │
│   ├─ Task 1: Design schema → RESULTS_FORMAT.md                  │
│   ├─ Task 2: consolidate_results.py module                      │
│   ├─ Task 3: results_loader.py module                           │
│   ├─ Task 4: Integrate into run_experiment.py                   │
│   └─ Task 5: Test + document (RESULTS_USAGE.md)                │
│                                                                  │
│   Status: Ready to start                                         │
│   Time: ~4-5 hours                                               │
│   Autonomous: Yes (no checkpoints)                               │
└─────────────────────────────────────────────────────────────────┘
                            ↓ depends on
┌─────────────────────────────────────────────────────────────────┐
│ WAVE 2 (Day 2): Integration & Verification                      │
├─────────────────────────────────────────────────────────────────┤
│ Plan 01-02: Integration & Verification                          │
│   ├─ Task 1: Update Makefile (new targets)                      │
│   ├─ Task 2: Create show_consolidated.py                        │
│   ├─ Task 3: Enhance show_results.py                            │
│   ├─ Task 4: Verify backward compatibility                      │
│   └─ Task 5: End-to-end test (5-iter baseline)                 │
│                                                                  │
│   Status: Blocked until 01-01 complete                          │
│   Time: ~3-4 hours                                               │
│   Autonomous: Yes (no checkpoints)                               │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│ PHASE 1 COMPLETE (Day 2-3 buffer)                               │
├─────────────────────────────────────────────────────────────────┤
│   ✓ All tasks done                                               │
│   ✓ All files committed                                          │
│   ✓ Ready for Phase 2 (LLM Explanations)                        │
└─────────────────────────────────────────────────────────────────┘
```

---

## Task Breakdown

### Plan 01-01 (Wave 1): Schema & Modules
| Task | Action | Time | Files |
|------|--------|------|-------|
| 1 | Design unified results schema | 0.5h | `.planning/RESULTS_FORMAT.md` |
| 2 | Implement consolidate_results.py | 1.5h | `openevolve/consolidate_results.py` |
| 3 | Implement results_loader.py | 1.5h | `openevolve/results_loader.py` |
| 4 | Integrate into run_experiment.py | 0.5h | `openevolve/run_experiment.py` (mod) |
| 5 | Test & document | 1h | `test_consolidation.py`, `RESULTS_USAGE.md` |
| **Total** | | **5h** | **5 new, 1 modified** |

### Plan 01-02 (Wave 2): Integration & Verify
| Task | Action | Time | Files |
|------|--------|------|-------|
| 1 | Update Makefile | 0.5h | `Makefile` (mod) |
| 2 | Create show_consolidated.py | 1h | `openevolve/show_consolidated.py` |
| 3 | Enhance show_results.py | 1h | `openevolve/show_results.py` (mod) |
| 4 | Verify backward compatibility | 0.5h | (no files) |
| 5 | End-to-end test | 1.5h | (no files) |
| **Total** | | **4.5h** | **1 new, 2 modified** |

---

## File Inventory

### Files to Create (6 new)
1. **`.planning/RESULTS_FORMAT.md`** — Schema documentation
2. **`.planning/RESULTS_USAGE.md`** — Usage guide
3. **`openevolve/consolidate_results.py`** — Consolidation logic (~80 lines)
4. **`openevolve/results_loader.py`** — Pandas integration (~100 lines)
5. **`openevolve/show_consolidated.py`** — Results display (~50 lines)
6. **`openevolve/test_consolidation.py`** — Validation (~60 lines)

### Files to Modify (3)
1. **`openevolve/run_experiment.py`** — Add post-run consolidation (~15 lines)
2. **`openevolve/show_results.py`** — Dual-format support (~30 lines)
3. **`Makefile`** — New targets (~5 lines)

### Total Changes
- 6 new files (~390 lines of code + docs)
- 3 modified files (~50 lines added)
- **~440 total lines** (including docstrings and comments)

---

## Execution Workflow

### Before Starting (Prerequisites)
```bash
# 1. Ensure LLVM memtrace built
make memtrace_pass.so memtrace_runtime.o

# 2. Start Ollama (in background or separate terminal)
ollama serve

# 3. Activate Python venv
source ../openevolve/.venv/bin/activate
```

### Wave 1 Execution (Plan 01-01)
```bash
# Follow 01-01-PLAN.md tasks in order:
# Task 1: Create .planning/RESULTS_FORMAT.md
# Task 2: Create openevolve/consolidate_results.py
# Task 3: Create openevolve/results_loader.py
# Task 4: Modify openevolve/run_experiment.py
# Task 5: Create test_consolidation.py and RESULTS_USAGE.md

# Verify Wave 1 complete:
python3 openevolve/test_consolidation.py  # Should pass
```

### Wave 2 Execution (Plan 01-02)
```bash
# Follow 01-02-PLAN.md tasks in order:
# Task 1: Update Makefile
# Task 2: Create openevolve/show_consolidated.py
# Task 3: Modify openevolve/show_results.py
# Task 4: Verify backward compatibility
# Task 5: Run short baseline experiment and test workflow

# Verify Wave 2 complete:
make show-consolidated-results  # Should print table
```

### Final Verification
```bash
# All files created/modified
ls -la .planning/RESULTS*.md
ls -la openevolve/{consolidate_results,results_loader,show_consolidated,test_consolidation}.py
grep consolidate_experiment openevolve/run_experiment.py

# All imports work
python3 -c "from openevolve.consolidate_results import consolidate_experiment"
python3 -c "from openevolve.results_loader import load_results, load_all_results"
python3 -c "from openevolve.show_consolidated import main"

# Test passes
python3 openevolve/test_consolidation.py
```

### Commit & Document
```bash
# Create .planning/phases/01-consolidation/01-01-SUMMARY.md
# Create .planning/phases/01-consolidation/01-02-SUMMARY.md
# Commit all changes
git add -A
git commit -m "feat: unified results consolidation + pandas loader (Phase 1)"
```

---

## Success Criteria

### After Wave 1 (Plan 01-01)
- [ ] RESULTS_FORMAT.md documents schema with example JSON
- [ ] consolidate_results.py module importable and functional
- [ ] results_loader.py module importable and functional
- [ ] run_experiment.py integrates consolidation (post-run, non-blocking)
- [ ] test_consolidation.py runs without errors
- [ ] RESULTS_USAGE.md documents usage with examples

### After Wave 2 (Plan 01-02)
- [ ] `make show-consolidated-results` works
- [ ] show_results.py detects consolidated format
- [ ] Backward compatibility verified
- [ ] Short 5-iteration experiment runs successfully
- [ ] Results load into pandas DataFrame
- [ ] Convergence curves plot without error

### Phase 1 Complete
- [ ] All 10 tasks done
- [ ] All files committed to git
- [ ] ROADMAP.md updated
- [ ] Ready for Phase 2 (LLM Explanations)

---

## Researcher Workflow (After Phase 1)

**Before Phase 1:** Manual results parsing  
**After Phase 1:** Unified, pandas-native analysis

```python
# Step 1: Run all experiments
make evolve-all

# Step 2: Load results (automatic consolidation happens)
from openevolve.results_loader import load_all_results
df = load_all_results()

# Step 3: Analyze
df.groupby('prompt')['memory_accesses'].min()  # Best per prompt
df.plot(x='iteration', y='memory_accesses', by='prompt')  # Convergence
```

---

## Dependency Graph

```
Phase 0 (previous): Cavitydetection + LLVM memtrace working ✓
    ↓
Phase 1, Wave 1: Schema + modules
    ├─ Task 1: Schema design
    ├─ Task 2-3: Module implementation (independent of each other)
    ├─ Task 4: Integration (depends on Task 2-3)
    └─ Task 5: Testing (depends on Task 2-3)
    ↓
Phase 1, Wave 2: Integration + verify (depends on Wave 1)
    ├─ Task 1: Makefile (independent)
    ├─ Task 2: show_consolidated.py (depends on Task 1 of Wave 1)
    ├─ Task 3: show_results.py (depends on Task 2-3 of Wave 1)
    ├─ Task 4: Backward compat (depends on Task 2-3 of Wave 1)
    └─ Task 5: End-to-end test (depends on all of Wave 1 + Wave 2 Tasks 1-4)
    ↓
Phase 1 Complete
    ↓
Phase 2: LLM Explanations (blocked until Phase 1 done)
```

---

## Key Design Decisions

| Decision | Why | Evidence |
|----------|-----|----------|
| One JSON per experiment | Batch analysis without multiple file downloads | STATE.md implementation plan |
| Consolidation post-run | Non-blocking; no experiment overhead | Aligns with Phase 1 scope (data format, not algorithm) |
| Backward compatible | Existing workflows must not break | Phase 1 requirement: "system remains working at end" |
| Pandas integration | Researchers already know pandas | No new tool to learn; simple import |
| Schema extensible | Phase 2 adds explanations without breaking Phase 1 | Design includes metadata + iterations array |

---

## Risk Mitigation

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|-----------|
| Consolidation breaks experiments | Low | Critical | Consolidation is post-processing; non-blocking |
| OpenEvolve output incomplete | Medium | Medium | Graceful degradation; fallback to best result |
| Pandas integration fails | Low | Medium | Already used by openevolve; no new dependency |
| Per-iteration data unavailable | Medium | Low | Fallback to best result; acceptable for Phase 1 |
| Backward compatibility lost | Low | Critical | show_results.py falls back to legacy format |

---

## Timeline

```
2026-05-13 (Day 1): Wave 1 execution
  ├─ Morning: Tasks 1-2 (schema + consolidation)
  ├─ Afternoon: Tasks 3-4 (loader + integration)
  └─ Evening: Task 5 (testing + documentation)

2026-05-14 (Day 2): Wave 2 execution
  ├─ Morning: Tasks 1-2 (Makefile + show_consolidated)
  ├─ Afternoon: Tasks 3-4 (show_results + compat)
  └─ Evening: Task 5 (end-to-end test)

2026-05-15 (Day 3): Buffer / Polish
  ├─ Review and finalize documentation
  ├─ Commit all changes
  └─ Prepare for Phase 2
```

---

## Next Phase (Phase 2)

**Title:** LLM Explanations  
**Timeline:** Days 4-6 (May 15-17)  
**Status:** Blocked until Phase 1 complete  
**Goal:** Capture LLM reasoning at each iteration

**Extension to results schema:**
```json
{
  "iteration": 1,
  "memory_accesses": 127000000,
  "explanation": "Reordered loops to improve cache locality; y as innermost now sequential"
}
```

**Depends on:** Phase 1 unified format being stable

---

## Navigation Guide

**First time?**
1. Read `PHASE1_QUICK_START.md` (this folder)
2. Read `PLANNING_SUMMARY.md` (context & rationale)
3. Read full plans: `01-01-PLAN.md` and `01-02-PLAN.md`

**Ready to execute?**
1. Start with Task 1 of `01-01-PLAN.md`
2. Follow action steps exactly
3. Run verification commands after each task
4. Move to next task when verification passes

**Need reference?**
1. `RESULTS_FORMAT.md` — Schema specification
2. `RESULTS_USAGE.md` — Code examples (created during execution)
3. `01-01-PLAN.md` — Detailed implementation spec for Wave 1
4. `01-02-PLAN.md` — Detailed implementation spec for Wave 2

---

## Questions During Execution

**Q: What if Task 3 fails?**  
A: Task 3 (results_loader.py) is independent of Task 2. Go back to Task 2, fix it, then redo Task 3.

**Q: Can I skip backward compatibility testing?**  
A: No. It's mandatory (Phase 1 requirement: "system remains working at end"). Task 4 of Plan 02.

**Q: How long is the end-to-end test (Task 5 of Plan 02)?**  
A: ~5-10 min including 5-iteration baseline run. Use `--iterations 5` for speed.

**Q: What if I can't run the full end-to-end test?**  
A: Run unit tests (test_consolidation.py) instead. Validates core logic without requiring OpenEvolve.

---

## Summary

- **2 Plans** (Wave 1 + Wave 2)
- **10 Tasks** (5 + 5)
- **~9-10 hours** execution (fits in 3-day window with buffer)
- **6 new files, 3 modified files**
- **All autonomous** (no external decision points)
- **Backward compatible** (no breaking changes)

**Ready to start?** → Read `PHASE1_QUICK_START.md` then start with `01-01-PLAN.md` Task 1.

---

**Index created:** 2026-05-13  
**Status:** PLANNING COMPLETE  
**Next:** Execute Wave 1 (Plan 01-01)

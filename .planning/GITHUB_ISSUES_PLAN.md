# Phase 1 GitHub Issues Structure

## Overview

Two waves of work, each with dedicated GitHub issues. Issues link to PLAN.md files for detailed execution steps.

---

## Milestone: Phase 1 - Results Consolidation

**Due:** 2026-05-15  
**Description:** Unify OpenEvolve results into pandas-readable format for analysis

---

## Wave 1: Schema & Core Implementation (Days 1-2)

### Issue #1: Design unified results schema
**Type:** Task  
**Depends on:** None  
**Assignee:** @jolilius  
**Labels:** `phase-1`, `wave-1`, `schema`  

**Description:**
Create comprehensive documentation of unified results JSON format for OpenEvolve experiments.

See `.planning/phases/01-consolidation/01-01-PLAN.md` Task 1 for detailed spec.

**Deliverable:** `.planning/RESULTS_FORMAT.md`

**Acceptance Criteria:**
- [ ] JSON schema documented with field definitions
- [ ] Example JSON with 2+ iterations
- [ ] Assumptions and constraints listed
- [ ] File naming convention specified (`results/{program}/{prompt}.json`)

---

### Issue #2: Implement consolidate_results.py module
**Type:** Task  
**Depends on:** #1  
**Assignee:** @jolilius  
**Labels:** `phase-1`, `wave-1`, `implementation`  

**Description:**
Create `openevolve/consolidate_results.py` module that transforms OpenEvolve output into unified JSON format.

See `.planning/phases/01-consolidation/01-01-PLAN.md` Task 2 for implementation details.

**Deliverable:** `openevolve/consolidate_results.py`

**Acceptance Criteria:**
- [ ] Module exports `consolidate_experiment(prompt_name, output_dir)` function
- [ ] Reads from `openevolve_output/{prompt}/` directory
- [ ] Outputs single JSON file to `results/{program}/{prompt}.json`
- [ ] Calculates improvement_percent and mem_score correctly
- [ ] Handles baseline of 128,862,705 accesses
- [ ] Unit tested on existing results

---

### Issue #3: Implement results_loader.py for pandas integration
**Type:** Task  
**Depends on:** #1  
**Assignee:** @jolilius  
**Labels:** `phase-1`, `wave-1`, `implementation`  

**Description:**
Create `openevolve/results_loader.py` module for loading consolidated results into pandas DataFrames.

See `.planning/phases/01-consolidation/01-01-PLAN.md` Task 3 for implementation details.

**Deliverable:** `openevolve/results_loader.py`

**Acceptance Criteria:**
- [ ] Exports `load_results(filepath)` → DataFrame with all iterations
- [ ] Exports `load_all_results()` → DataFrame with all prompts combined
- [ ] DataFrame has columns: iteration, memory_accesses, memory_reads, memory_writes, improvement_percent, mem_score, prompt
- [ ] Can be imported and used in Jupyter notebooks / analysis scripts
- [ ] Tested: can plot convergence curves immediately

---

### Issue #4: Integrate consolidation into run_experiment.py
**Type:** Task  
**Depends on:** #2, #3  
**Assignee:** @jolilius  
**Labels:** `phase-1`, `wave-1`, `integration`  

**Description:**
Modify `openevolve/run_experiment.py` to call consolidation after each experiment completes.

See `.planning/phases/01-consolidation/01-01-PLAN.md` Task 4 for integration details.

**Changes:**
- [ ] After experiment finishes, call `consolidate_experiment(prompt_name, openevolve_output_dir)`
- [ ] Consolidated JSON written to `results/{program}/{prompt}.json`
- [ ] No disruption to existing workflow
- [ ] Tested: running one experiment produces both old and new output

---

### Issue #5: Document results format and usage
**Type:** Documentation  
**Depends on:** #1, #3  
**Assignee:** @jolilius  
**Labels:** `phase-1`, `wave-1`, `docs`  

**Description:**
Create comprehensive usage guide for researchers analyzing consolidated results.

**Deliverable:** `.planning/RESULTS_USAGE.md`

**Acceptance Criteria:**
- [ ] Example Python code: load and plot convergence curves
- [ ] Example pandas operations: filter by prompt, compare metrics
- [ ] Explanation of each JSON field
- [ ] Troubleshooting guide (missing files, corrupted JSON, etc.)

---

## Wave 2: Integration & Testing (Days 3+)

### Issue #6: Update Makefile for consolidated results targets
**Type:** Task  
**Depends on:** #4 (Wave 1 complete)  
**Assignee:** @jolilius  
**Labels:** `phase-1`, `wave-2`, `integration`  

**Description:**
Add new Makefile targets for unified results display.

See `.planning/phases/01-consolidation/01-02-PLAN.md` Task 1 for details.

**Changes:**
- [ ] Create `openevolve/show_consolidated.py` script
- [ ] Add `make show-consolidated-results` target
- [ ] Add `make results-summary` alias
- [ ] Tested: `make show-consolidated-results` displays summary table

---

### Issue #7: End-to-end testing and validation
**Type:** Task  
**Depends on:** #6  
**Assignee:** @jolilius  
**Labels:** `phase-1`, `wave-2`, `testing`  

**Description:**
Run full experiment workflow and verify all results are properly consolidated.

See `.planning/phases/01-consolidation/01-02-PLAN.md` Task 2 for testing details.

**Acceptance Criteria:**
- [ ] Run `make evolve-all ITERATIONS=20` (short run)
- [ ] All prompt results consolidated to `results/cavitydetection/*.json`
- [ ] `make show-consolidated-results` displays all prompts in summary table
- [ ] `load_all_results()` loads data successfully
- [ ] Convergence curves plottable without errors
- [ ] Backward compat verified: old show_results.py still works

---

### Issue #8: Final commit and cleanup
**Type:** Task  
**Depends on:** #7  
**Assignee:** @jolilius  
**Labels:** `phase-1`, `wave-2`, `cleanup`  

**Description:**
Finalize Phase 1: clean up, commit, and prepare for Phase 2.

**Acceptance Criteria:**
- [ ] All code linted and formatted
- [ ] Comments added where needed
- [ ] README.md updated (if needed)
- [ ] Commit with clear message referencing Phase 1 goals
- [ ] Git tags: `phase-1-complete`

---

## Issue Workflow

**Opening:** Create all issues but mark Wave 2 as blocked (depends on Wave 1)

**During Execution:**
1. Move issue to "In Progress" when starting
2. Reference issue number in commit messages: `git commit -m "... Fixes #2"`
3. Close issue when acceptance criteria met

**Status Tracking:**
- Use GitHub project board or "Phase 1" milestone for visibility
- Wave 1 should be complete by end of 2026-05-14
- Wave 2 should be complete by end of 2026-05-15

---

## Labels to Create (if not exist)

- `phase-1` — Part of Phase 1
- `wave-1` — Wave 1 work (days 1-2)
- `wave-2` — Wave 2 work (days 3+)
- `schema` — Schema/data design
- `implementation` — Code implementation
- `integration` — Integration/glue
- `testing` — QA and validation
- `docs` — Documentation
- `cleanup` — Cleanup/finalization

---

## Quick Creation Script

If you want to create issues via GitHub CLI:

```bash
# Create milestone
gh milestone create "Phase 1 - Results Consolidation" --description "Unify OpenEvolve results for pandas analysis" --target-date 2026-05-15

# Wave 1 issues
gh issue create --title "Design unified results schema" --body "[See .planning/GITHUB_ISSUES_PLAN.md #1]" --milestone "Phase 1 - Results Consolidation" --label "phase-1,wave-1,schema"
gh issue create --title "Implement consolidate_results.py module" --body "[See .planning/GITHUB_ISSUES_PLAN.md #2]" --milestone "Phase 1 - Results Consolidation" --label "phase-1,wave-1,implementation"
# ... (repeat for #3-#5)

# Wave 2 issues
gh issue create --title "Update Makefile for consolidated results targets" --body "[See .planning/GITHUB_ISSUES_PLAN.md #6]" --milestone "Phase 1 - Results Consolidation" --label "phase-1,wave-2,integration"
# ... (repeat for #7-#8)
```

Or create them manually in GitHub UI for more control.

# Phase 2: Quick Start Guide

## What to Execute

Three plans, in order. Each plan has tasks that can be partially parallelized.

```
Wave 1 (Plan 02-01)  →  Wave 2 (Plan 02-02)  →  Wave 3 (Plan 02-03)
Foundation             Integration              Documentation
~4-5 hours            ~3-4 hours              ~2-3 hours
```

---

## Plan 02-01: Explanation Foundation

**Read:** `.planning/phases/02-llm-explanations/02-01-PLAN.md`

**Execute 3 tasks:**

1. **Design explanation prompt**
   - Create `openevolve/explanation_prompt.txt` (LLM system message)
   - Create `openevolve/EXPLANATION_DESIGN.md` (design rationale)
   - Task is independent

2. **Build explanation generator**
   - Create `openevolve/explanation_generator.py` module
   - Public API: `generate_explanation(evolved, baseline, config, prompt) → str | None`
   - Depends on Task 1 being understood (reads explanation_prompt.txt)

3. **Extend consolidation schema**
   - Modify `openevolve/consolidate_results.py` to accept `explanations` dict parameter
   - Update to store explanation field in iterations array
   - Independent of other tasks

**Parallelization:** Tasks 1+3 can run simultaneously; Task 2 after Task 1

**Verify:** All 3 artifacts created; module imports cleanly; schema extended

**Commit:** `feat(02-01): implement explanation infrastructure`

---

## Plan 02-02: Experiment Integration

**Read:** `.planning/phases/02-llm-explanations/02-02-PLAN.md`

**Execute 3 tasks:**

1. **Integrate into run_experiment.py**
   - Modify to generate explanations after OpenEvolve completes
   - Add `EXPLAIN_GENERATIONS` environment variable
   - Pass explanations to `consolidate_experiment()`

2. **Update results_loader.py**
   - Add explanation column handling
   - Utility function for analyzing explanations (optional but recommended)
   - Update docstrings

3. **Add Makefile targets**
   - `make evolve-explain-test` — 10-iteration baseline with explanations
   - `make show-explanations` — Display results with explanation column
   - `make test-explanations-disabled` — Verify toggle works

**Parallelization:** Tasks 1+2 can run simultaneously; Task 3 after both

**Verify:** Integration test with `make evolve-explain-test` (requires Ollama running)

**Commit:** `feat(02-02): integrate explanations into experiment workflow`

---

## Plan 02-03: Documentation & Testing

**Read:** `.planning/phases/02-llm-explanations/02-03-PLAN.md`

**Execute 4 tasks:**

1. **Update RESULTS_FORMAT.md**
   - Document explanation field in iterations array schema
   - Add "Explanation Field" section with examples
   - Update backward compatibility notes

2. **Expand RESULTS_USAGE.md**
   - Add "Explanation Analysis" section
   - Add "Understanding Explanations" with interpretation guidelines
   - Add "Cross-Prompt Strategy Comparison" section
   - Add advanced text analysis examples

3. **Update README.md**
   - Document Phase 2 completion
   - Add usage examples (Python code)
   - Document Makefile targets
   - Link to detailed docs

4. **Add test cases**
   - Test consolidation with explanations
   - Test consolidation without explanations (backward compat)
   - Test partial explanations
   - Test DataFrame handling with NaN
   - Test Phase 1 results loading

**Parallelization:** Tasks 1-3 can run simultaneously; Task 4 after all others

**Verify:** Test suite passes; documentation accuracy

**Commit:** `docs(02-03): complete Phase 2 documentation and testing`

---

## Key Execution Details

### Prerequisites
- [ ] Phase 1 (Results Consolidation) complete
- [ ] Ollama running: `curl http://localhost:11434/api/tags`
- [ ] Model available: `ollama list | grep qwen`
- [ ] Python venv with pandas, yaml, requests

### Files to Have Ready
- `openevolve/initial_program.c` — Baseline code for explanations
- `openevolve/config.yaml` — LLM configuration
- `openevolve/consolidate_results.py` — From Phase 1 (will be extended)
- `openevolve/run_experiment.py` — From Phase 1 (will be extended)
- `openevolve/results_loader.py` — From Phase 1 (will be extended)

### Key Environment Variables
```bash
EXPLAIN_GENERATIONS=1      # Enable explanations (default)
EXPLAIN_GENERATIONS=0      # Disable explanations (if Ollama down)
```

### Quick Test Commands

After Wave 1:
```bash
python3 -c "import sys; sys.path.insert(0, 'openevolve'); from explanation_generator import generate_explanation"
```

After Wave 2:
```bash
make evolve-explain-test     # Run 10 iterations with explanations
jq '.iterations[0]' openevolve_output/baseline/results.json | grep explanation
```

After Wave 3:
```bash
cd openevolve && python3 test_consolidation.py  # Run all tests
python3 -c "from results_loader import load_all_results; df = load_all_results(); print(df['explanation'].notna().sum())"
```

---

## Success Indicators

### After Wave 1
- ✅ `openevolve/explanation_prompt.txt` exists and is 20+ lines
- ✅ `openevolve/explanation_generator.py` imports without errors
- ✅ Function exists: `generate_explanation(...) → str | None`
- ✅ `consolidate_results.py` signature includes `explanations` parameter

### After Wave 2
- ✅ `make evolve-explain-test` completes successfully
- ✅ `openevolve_output/baseline/results.json` contains explanation field
- ✅ `make show-explanations` displays DataFrame with explanation column
- ✅ EXPLAIN_GENERATIONS=0 works: `EXPLAIN_GENERATIONS=0 make evolve-explain-test`

### After Wave 3
- ✅ `cd openevolve && python3 test_consolidation.py` passes all tests
- ✅ `grep "explanation" .planning/RESULTS_FORMAT.md` shows documentation
- ✅ `grep "Explanation Analysis" .planning/RESULTS_USAGE.md` shows examples
- ✅ `grep "Phase 2" README.md` shows Phase 2 completion

---

## Common Pitfalls

**"No explanations in results.json"**
- Check: Is Ollama running? `curl http://localhost:11434/api/tags`
- Check: Did you run with EXPLAIN_GENERATIONS=1 (or default)?
- Check: Did the LLM response timeout? Check logs in run_experiment.py

**"ImportError: No module named explanation_generator"**
- Check: Task 1.2 (explanation_generator.py) completed?
- Check: File is in `openevolve/` directory?
- Check: Python path includes `openevolve`?

**"Makefile: No rule for target 'evolve-explain-test'"**
- Check: Task 2.3 (Makefile targets) completed?
- Check: Makefile updated with new targets?

**"Test fails: test_consolidate_with_explanations"**
- Check: Wave 1 (02-01) completed successfully?
- Check: consolidate_results.py signature includes explanations parameter?

---

## Estimated Timeline

```
Wave 1: 4-5 hours     (Mostly writing and testing; some Ollama API calls)
Wave 2: 3-4 hours     (Integration; one 10-iteration test run)
Wave 3: 2-3 hours     (Documentation; test suite)
────────────────
Total:  9-12 hours    (Can be parallelized within waves)
```

With parallel execution of tasks within waves: **Effective 6-8 hours**

---

## Documentation Hierarchy

For **implementation details:** See specific PLAN.md file (02-01, 02-02, 02-03)

For **design rationale & architecture:** See `PHASE_2_OVERVIEW.md`

For **planning status & checklist:** See `PLANNING_SUMMARY.md`

For **this quick reference:** See `QUICK_START.md` (you are here)

---

## What Happens Next

After Phase 2 completion:

1. **Run a real experiment:** `make evolve-all ITERATIONS=40`
2. **Analyze explanations:** See examples in `.planning/RESULTS_USAGE.md`
3. **Consider Phase 3:** Multi-program support, visualization, clustering

---

## Need Help?

- **Task-specific details:** Read the corresponding PLAN.md (02-01, 02-02, or 02-03)
- **Design decisions:** See PHASE_2_OVERVIEW.md section "Key Design Decisions"
- **Troubleshooting:** See section "Common Pitfalls" above or refer to the PLAN files' <verify> sections
- **Questions about explanations:** See PHASE_2_OVERVIEW.md section "Questions & Clarifications"

---

**Status:** Ready to execute

**Start with:** Plan 02-01 (Explanation Foundation)

**No external dependencies besides Ollama:** ✓ (assuming Phase 1 complete)

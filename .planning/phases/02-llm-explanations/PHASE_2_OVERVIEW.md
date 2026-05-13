# Phase 2: LLM Explanations — Planning Overview

## Executive Summary

Phase 2 introduces LLM-generated explanations for code transformations discovered during OpenEvolve optimization experiments. The phase is broken into 3 sequential plans executed across 3 waves, with clear dependencies and parallel execution opportunities.

**Timeline:** Days 4-6 of the project (after Phase 1 completion)  
**Effort:** ~2-3 days of implementation  
**Dependencies:** Phase 1 (Results Consolidation) must be complete

---

## Plan Breakdown

### Wave 1: Foundation (02-01) — ~4-5 hours
**Plan 02-01: Explanation Infrastructure**

Establishes the explanation generation foundation without integrating into the experiment loop. This plan is self-contained and testable in isolation.

**What gets built:**
1. **Explanation prompt design** (openevolve/explanation_prompt.txt)
   - Refined system message guiding the LLM to generate 1-2 sentence code optimization explanations
   - Design document explaining prompt strategy, examples, and limitations

2. **Explanation generator module** (openevolve/explanation_generator.py)
   - Reusable Python module to call LLM API with code pair (evolved + baseline)
   - Public API: `generate_explanation(evolved_code, baseline_code, llm_config, prompt_text) → str | None`
   - Handles timeouts, API errors, non-blocking

3. **Schema extension** (openevolve/consolidate_results.py)
   - Updated function signature to accept optional explanations dict, explanation_prompt_text, and prompt_version
   - Results JSON now includes explanation field in iterations array
   - Results metadata now includes explanation_config section with version and hash tracking
   - Prompt versioning enables reproducibility: prompt_hash detects if prompt has changed
   - Backward compatible: Phase 1 code still works; explanations are optional

**Why first?** Infrastructure must be ready before integration; allows testing the explanation generator in isolation before wiring into run_experiment.py.

**Verification:** Module imports, function signatures, schema validation.

---

### Wave 2: Integration (02-02) — ~3-4 hours
**Plan 02-02: Experiment Integration**

Integrates explanation generation into the standard experiment workflow (run_experiment.py) and updates user-facing tools.

**What gets built:**
1. **run_experiment.py integration**
   - Captures explanations after OpenEvolve completes
   - EXPLAIN_GENERATIONS environment variable toggles capture
   - Passes explanations to consolidate_experiment() for storage
   - Non-blocking: experiments succeed even if explanations fail

2. **results_loader.py enhancement**
   - DataFrame now includes 'explanation' column
   - Handles missing explanations gracefully (NaN)
   - Utility function for analyzing explanations across prompts
   - Backward compatible with Phase 1 results

3. **Makefile test targets**
   - `make evolve-explain-test` — 10-iteration baseline with explanations
   - `make show-explanations` — Display results with explanation column
   - `make test-explanations-disabled` — Verify EXPLAIN_GENERATIONS toggle

**Why after 02-01?** Depends on explanation_generator.py module and schema from Plan 02-01.

**Verification:** Integration tests, Makefile targets, 10-iteration test runs.

---

### Wave 3: Documentation & Testing (02-03) — ~2-3 hours
**Plan 02-03: Completion & Documentation**

Ensures comprehensive documentation, test coverage, and user guidance for the new explanation feature.

**What gets built:**
1. **.planning/RESULTS_FORMAT.md extension**
   - Documents explanation field with schema, examples, limitations
   - Clarifies optional nature and backward compatibility

2. **.planning/RESULTS_USAGE.md expansion**
   - New section: "Explanation Analysis" with loading and grouping examples
   - New section: "Understanding Explanations" with interpretation guidelines
   - New section: "Cross-Prompt Strategy Comparison" for analyzing different prompts
   - Advanced text analysis examples (keyword extraction, clustering)

3. **README.md update**
   - Phase 2 completion documented
   - Usage examples (Python code)
   - Links to detailed documentation
   - Makefile targets documented

4. **Test suite (test_consolidation.py)**
   - Test with explanations
   - Test without explanations (backward compat)
   - Test partial explanations (some iterations have them, some don't)
   - Test DataFrame handling with NaN
   - Test Phase 1 results loading (no explanation field)

**Why last?** Documentation and testing depend on all implementation being complete (from 02-01 and 02-02).

**Verification:** Documentation accuracy, test suite execution, no regressions.

---

## Dependency Graph

```
        ┌─────────────────────────┐
        │  Phase 1 (COMPLETE)     │
        │  Results Consolidation  │
        └────────────┬────────────┘
                     │
                     ▼
        ┌─────────────────────────┐
        │ Plan 02-01 (Wave 1)     │
        │ Explanation Foundation  │
        │ - explanation_prompt.txt│
        │ - explanation_generator │
        │ - schema extension      │
        └────────────┬────────────┘
                     │
                     ▼
        ┌─────────────────────────┐
        │ Plan 02-02 (Wave 2)     │
        │ Experiment Integration  │
        │ - run_experiment.py     │
        │ - results_loader.py     │
        │ - Makefile targets      │
        └────────────┬────────────┘
                     │
                     ▼
        ┌─────────────────────────┐
        │ Plan 02-03 (Wave 3)     │
        │ Documentation & Testing │
        │ - RESULTS_FORMAT.md     │
        │ - RESULTS_USAGE.md      │
        │ - README.md             │
        │ - test_consolidation.py │
        └─────────────────────────┘
```

**No parallel plans:** Each wave depends on the previous one's completion. However, within each plan, tasks can run in parallel where file conflicts don't occur.

---

## Task-Level Dependency Analysis

### Wave 1 Internal Parallelization

Tasks 1-3 in Plan 02-01:
- **Task 1 (explanation prompt)** ← Independent
- **Task 2 (explanation generator)** ← Depends on Task 1 (needs prompt design done)
- **Task 3 (schema extension)** ← Independent of Tasks 1-2 (schema is just accepting explanations parameter)

**Parallel: Tasks 1+3 together, then Task 2**

### Wave 2 Internal Parallelization

Tasks 1-3 in Plan 02-02:
- **Task 1 (run_experiment.py)** ← Depends on Plan 02-01 completion
- **Task 2 (results_loader.py)** ← Independent (just adding column handling)
- **Task 3 (Makefile)** ← Depends on Tasks 1-2 being ready

**Parallel: Tasks 1+2 together, then Task 3**

### Wave 3 Internal Parallelization

Tasks 1-4 in Plan 02-03:
- **Task 1 (RESULTS_FORMAT.md)** ← Independent
- **Task 2 (RESULTS_USAGE.md)** ← Independent
- **Task 3 (README.md)** ← Independent
- **Task 4 (test_consolidation.py)** ← Depends on all implementation being complete (from Waves 1-2)

**Parallel: Tasks 1-3 together, then Task 4**

---

## File Ownership Summary

### Created Files (New)

| File | Plan | Wave |
|------|------|------|
| openevolve/explanation_prompt.txt | 02-01 | 1 |
| openevolve/EXPLANATION_DESIGN.md | 02-01 | 1 |
| openevolve/explanation_generator.py | 02-01 | 1 |

### Modified Files (Existing)

| File | Plan | Wave | Changes |
|------|------|------|---------|
| openevolve/consolidate_results.py | 02-01 | 1 | Add explanations parameter, store in JSON |
| openevolve/run_experiment.py | 02-02 | 2 | Integrate explanation generation |
| openevolve/results_loader.py | 02-02 | 2 | Handle explanation column |
| Makefile | 02-02 | 2 | Add explanation test targets |
| .planning/RESULTS_FORMAT.md | 02-03 | 3 | Document explanation field |
| .planning/RESULTS_USAGE.md | 02-03 | 3 | Add explanation analysis examples |
| README.md | 02-03 | 3 | Document Phase 2 completion |
| openevolve/test_consolidation.py | 02-03 | 3 | Add explanation tests |

**No file conflicts:** Each modified file is touched by only one plan, ensuring safe sequential execution.

---

## Key Design Decisions

### 1. Explanation Generation is Non-Blocking
If LLM is unavailable or timeout occurs, the experiment succeeds but without explanations. This prevents one service failure from blocking research.

**Trade-off:** Some iterations may lack explanations, but results are always complete.

### 2. Optional Explanations (EXPLAIN_GENERATIONS Flag)
Researchers can disable explanation generation with `EXPLAIN_GENERATIONS=0` if Ollama is not available.

**Trade-off:** More flexibility for users, but adds a configuration flag to remember.

### 3. 1-2 Sentence Format
LLM is constrained to produce concise explanations (not detailed code analysis).

**Trade-off:** Brief explanations are easy to scan, but may miss important details. Users can still review code for full understanding.

### 4. Schema: Optional Explanation Field & Prompt Versioning
Explanation field is omitted (not null) if not present; explanation_config in metadata tracks which prompt version was used.

**Trade-off:** Clean JSON structure with reproducibility; slightly more complex parsing, but enables safe prompt iteration.

**Prompt Versioning Benefits:**
- prompt_hash detects if prompt file has changed (enables reproducibility checks)
- prompt_version allows comparing explanations across prompt iterations
- Can safely change prompt and re-run experiments without losing old results

### 5. Infrastructure First (Plan 02-01)
Explanation generation module is built and tested in isolation before integration.

**Trade-off:** Slightly longer total duration, but much easier to debug integration failures.

---

## Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|-----------|
| **LLM API unavailable** | Medium | Low | Non-blocking; experiments succeed without explanations |
| **Explanation quality poor** | Medium | Low | Iterate prompt after initial test run; documentation notes limitations |
| **Explanation generation timeout** | Low | Low | Handled gracefully; timeout in explanation_generator.py |
| **Results format incompatibility** | Low | Medium | Backward compatibility testing in 02-03; Phase 1 results still valid |
| **Integration bugs in run_experiment.py** | Medium | Medium | 10-iteration test runs in 02-02 verify integration before long runs |

---

## Execution Checklist

### Pre-Phase 2 Requirements
- [ ] Phase 1 complete and committed (results consolidation working)
- [ ] Ollama running with qwen2.5-coder:32b (or compatible model) available
- [ ] Project environment set up (Python venv, dependencies)

### Plan 02-01 Execution
- [ ] Design explanation prompt (explanation_prompt.txt + EXPLANATION_DESIGN.md)
- [ ] Implement explanation_generator.py module
- [ ] Extend consolidate_results.py with explanations parameter
- [ ] Verify all three artifacts created and tested
- [ ] Commit: "feat(02-01): implement explanation infrastructure"

### Plan 02-02 Execution
- [ ] Integrate explanation generation into run_experiment.py
- [ ] Add EXPLAIN_GENERATIONS environment variable support
- [ ] Update results_loader.py to expose explanation column
- [ ] Add Makefile targets (evolve-explain-test, show-explanations)
- [ ] Run 10-iteration test: `make evolve-explain-test`
- [ ] Verify results.json includes explanation field
- [ ] Commit: "feat(02-02): integrate explanations into experiment workflow"

### Plan 02-03 Execution
- [ ] Update RESULTS_FORMAT.md with explanation field documentation
- [ ] Expand RESULTS_USAGE.md with explanation analysis examples
- [ ] Update README.md with Phase 2 completion notes
- [ ] Add explanation tests to test_consolidation.py
- [ ] Run test suite: `cd openevolve && python3 test_consolidation.py`
- [ ] Verify backward compatibility with Phase 1 results
- [ ] Commit: "docs(02-03): complete Phase 2 documentation and testing"

### Post-Phase 2 Validation
- [ ] `make show-consolidated-results` displays results from multiple prompts
- [ ] `make show-explanations` displays explanation column
- [ ] `df['explanation'].notna().sum()` shows explanations present
- [ ] Researchers can run: `make evolve-all ITERATIONS=40` with explanations
- [ ] Explanations are concise (1-2 sentences, 50-200 chars)

---

## Definition of Done (Phase 2)

**All of:**
1. ✅ Explanations are concise (1-2 sentences) and relevant to code optimization
2. ✅ Explanations can be read from DataFrame: `df['explanation']`
3. ✅ Iteration timing includes explanation generation (acceptable overhead: ~1-2s/iter)
4. ✅ README documents explanation prompting, usage, and interpretation
5. ✅ Tests verify explanation handling and backward compatibility
6. ✅ Explanations are optional and non-blocking (experiments succeed without them)

---

## Files to Review After Phase 2

1. **openevolve/EXPLANATION_DESIGN.md** — Prompt strategy rationale
2. **.planning/RESULTS_FORMAT.md** — Full schema including explanation field
3. **.planning/RESULTS_USAGE.md** — Explanation analysis examples
4. **README.md** — Phase 2 summary and usage
5. **openevolve/explanation_generator.py** — LLM integration module
6. **openevolve/run_experiment.py** — Integration point

---

## Prompt Iteration Workflow

Once Phase 2 is complete, you can safely iterate on the explanation prompt:

1. **Review initial explanations** (from first test run with v1.0)
2. **Identify gaps** (e.g., "explanations are too vague" or "missing key optimization patterns")
3. **Update explanation_prompt.txt** with refinements
4. **Bump version** in the file header and code (e.g., "1.0" → "1.1")
5. **Re-run experiments:** `make evolve-all ITERATIONS=40`
6. **Compare results:**
   ```python
   df = load_results("baseline.json")
   v1 = df[df['prompt_version'] == '1.0'][['iteration', 'explanation']].head(5)
   v1_1 = df[df['prompt_version'] == '1.1'][['iteration', 'explanation']].head(5)
   # Side-by-side comparison shows improvement
   ```

Each version is tracked, so you can run experiments with different prompt versions and compare side-by-side.

---

## Next Steps After Phase 2

**Phase 3 (Optional):**
- Multi-program support (run same prompts on other algorithms)
- Explanation grouping/clustering by transformation type
- Results visualization (convergence plots, strategy heatmaps)
- Per-iteration timing breakdown (compilation, evaluation, explanation)

**Immediate research:** Run a 40-iteration experiment to gather explanations and analyze prompt strategies:
```bash
make evolve-all ITERATIONS=40
make show-consolidated-results
python3 -c "from openevolve.results_loader import load_all_results; df = load_all_results(); print(df[df['explanation'].notna()][['prompt', 'iteration', 'explanation']].head(20))"
```

---

## Questions & Clarifications

**Q: What if Ollama is not running?**  
A: Explanation generation will timeout and fail gracefully. Set `EXPLAIN_GENERATIONS=0` to skip or run experiments without explanations. Results are still complete.

**Q: Can I regenerate explanations for old results?**  
A: The current design generates explanations during the experiment. Regenerating old results would require re-running experiments or a separate post-processing step (not included in Phase 2).

**Q: Are explanations guaranteed to be accurate?**  
A: No. LLM explanations are subjective and may contain errors. Use them as a starting point for investigation, not as ground truth. Always review actual code for verification.

**Q: Can I customize the explanation prompt?**  
A: Yes. Edit `openevolve/explanation_prompt.txt` and re-run experiments. Changes take effect in new runs.

**Q: What happens if explanation generation is slow?**  
A: Expected overhead is ~1-2 seconds per iteration. If Ollama is slow, explanations may timeout. Timeout handling is non-blocking, but you'll get fewer explanations. Optimize the Ollama instance or prompt if needed.

**Q: How do I track which prompt version was used for each result?**  
A: Every results.json includes `explanation_config.prompt_version` and `prompt_hash` in the metadata. The hash is the SHA256 of the prompt text, so you can detect if a prompt has changed. To query: `df[df['prompt_version'] == '1.0']` filters to results from version 1.0 only. Different versions can coexist in the same DataFrame for comparison.

**Q: Can I change the prompt and re-run without breaking old results?**  
A: Yes! This is the whole point of prompt versioning. Change the prompt, bump the version number (e.g., "1.0" → "1.1"), re-run experiments, and both versions' results coexist. The prompt_version and prompt_hash fields ensure reproducibility. You can compare explanations across versions side-by-side in pandas.

**Q: What if I regenerate explanations for the same experiments?**  
A: The hash will be identical if the prompt didn't change. If the prompt did change, the new hash will differ, and the new results will have a different prompt_version. Both sets of explanations are preserved for comparison.

# Retrospective

---

## Milestone: v1.0 — Results & Explanations Framework

**Shipped:** 2026-05-13
**Phases:** 2 | **Plans:** 5

### What Was Built

- Unified JSON schema per experiment + `load_results()` / `load_all_results()` pandas interface
- `run_experiment.py` auto-consolidates on every run — no manual parsing
- `explanation_generator.py` + `explanation` field in every iteration row
- `get_explanations()` utility + `make show-results` / `make show-consolidated-results` Makefile targets

### What Worked

- TDD approach (Wave 0 stubs → implementation) caught integration issues early
- Keeping `load_results()` signature stable from the start made downstream changes safe
- Makefile targets as user-facing interface kept the researcher workflow clean

### What Was Inefficient

- Explanations in v1.0 only captured the single best solution — had to be redesigned in v1.1 to be per-checkpoint. If trajectory observation had been the stated goal from the start, the per-iteration approach would not have been built.

### Key Lessons

- Define the unit of analysis before designing the schema: "per-iteration" vs "per-checkpoint" are different research primitives

---

## Milestone: v1.1 — Experiment Runs + Per-Step Analysis

**Shipped:** 2026-05-15
**Phases:** 2 (Phase 3, Phase 4) | **Plans:** 6
**Timeline:** 2 days (2026-05-13 → 2026-05-15)

### What Was Built

- Named run structure: `runs/<run_id>/<program>/<prompt>/` with `metadata.json`; `make evolve-all` stamps shared run ID
- Legacy migration: `migrate_legacy.py` moves flat dirs to `runs/legacy/cavitydetection/`
- Display scripts rewritten with glob-based discovery + `--run` filter pass-through
- Checkpoint-based consolidation: `_extract_iterations()` scans `checkpoints/checkpoint_N/` numerically, emits Phase 4 schema (6 fields per row)
- Per-checkpoint sliding-window explanation loop; integer folder-N keyed dict to match consolidation
- `--regenerate` flag + `results.json.v1` rollback backup for legacy data upgrade

### What Worked

- Strict Phase 3 before Phase 4 ordering — directory layout locked before checkpoint reads were written
- TDD wave pattern: RED tests first, then implementation, then verify. Caught pitfalls (lexicographic vs numeric sort, Pitfall 2 dict keying) before they hit real data
- Integer folder-N as the explanation dict key (not `info["iteration"]`) — correct decision, explicitly called out in PATTERNS.md
- `read-then-merge` for `metadata.json` — idempotent under repeated prompt-loop calls
- Code review + security review cycle caught three meaningful issues (CR-01 path traversal, CR-02 mem_score fallback, WR-03 temp config leak)

### What Was Inefficient

- VALIDATION.md and REQUIREMENTS.md traceability checkboxes were never updated during execution — resulted in doc debt found at audit time. Both are documentation-only, but the audit step had to do extra cross-referencing to confirm work was complete
- SUMMARY.md `requirements_addressed` vs `requirements-completed` field name inconsistency — minor but shows the template was not enforced
- `--output-root` path inconsistency between `run_experiment.py` and display scripts was identified at audit rather than during development — should be a standard integration check

### Patterns Established

- Explanation dict keys must use integer folder N (not JSON `iteration` field) — documented in PATTERNS.md and honored in both 04-01 and 04-02
- `backward-compat iteration alias`: store checkpoint_N as both `"iteration"` and `"checkpoint_iteration"` so Phase 1/2 callers keep working
- `skip-without-advance`: when `best_program.c` is missing, do NOT advance `prev_code` in the sliding window

### Key Lessons

- Mark VALIDATION.md `nyquist_compliant: true` immediately after tests pass, not after the phase summary is written — the lag caused confusion at audit
- The three-source cross-reference (VERIFICATION.md × SUMMARY frontmatter × REQUIREMENTS.md traceability) is valuable — consider making it a standard pre-close checklist item rather than a separate audit step
- Security review after code review but before verification is the right order — CR findings fed directly into WR fixes before UAT

### Cost Observations

- Model: claude-sonnet-4-6 (main executor)
- All 21 tests pass across both suites; no regressions introduced across phases

---

## Cross-Milestone Trends

| Trend | v1.0 | v1.1 |
|-------|------|------|
| TDD coverage | Partial | Full (Wave 0 stubs mandatory) |
| Security review | Not done | Full cycle (CR + WR) |
| Doc completeness at close | High | Medium (traceability + VALIDATION.md stale) |
| Phase ordering discipline | N/A | Strict (Phase 3 gated Phase 4) |
| Backward compat handling | Basic | Explicit (iteration alias, column guard) |

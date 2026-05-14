---
phase: 4
slug: per-step-data-pipeline
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-05-14
---

# Phase 4 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | Plain Python assertions (no pytest; existing tests use `python script.py` pattern) |
| **Config file** | None |
| **Quick run command** | `../openevolve/.venv/bin/python openevolve/test_consolidation.py` |
| **Full suite command** | `../openevolve/.venv/bin/python openevolve/test_consolidation.py && ../openevolve/.venv/bin/python openevolve/test_run_structure.py` |
| **Estimated runtime** | ~5 seconds |

---

## Sampling Rate

- **After every task commit:** Run `../openevolve/.venv/bin/python openevolve/test_consolidation.py`
- **After every plan wave:** Run both test files (full suite command above)
- **Before `/gsd-verify-work`:** Full suite must be green
- **Max feedback latency:** ~5 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 04-01-01 | 01 | 1 | CKPT-01 | — | N/A | unit | `../openevolve/.venv/bin/python openevolve/test_consolidation.py` | ❌ W0 | ⬜ pending |
| 04-01-02 | 01 | 1 | CKPT-02 | — | N/A | unit | `../openevolve/.venv/bin/python openevolve/test_consolidation.py` | ❌ W0 | ⬜ pending |
| 04-01-03 | 01 | 1 | CKPT-03 | — | N/A | unit | `../openevolve/.venv/bin/python openevolve/test_consolidation.py` | ❌ W0 | ⬜ pending |
| 04-02-01 | 02 | 1 | EXPLAIN-01 | — | N/A | unit | `../openevolve/.venv/bin/python openevolve/test_consolidation.py` | ❌ W0 | ⬜ pending |
| 04-02-02 | 02 | 1 | EXPLAIN-02 | — | N/A | unit | `../openevolve/.venv/bin/python openevolve/test_consolidation.py` | ❌ W0 | ⬜ pending |
| 04-03-01 | 03 | 2 | CKPT-01/02 | — | N/A | unit | `../openevolve/.venv/bin/python openevolve/test_run_structure.py` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

New test functions to add to existing test files before implementation tasks:

- [ ] `test_checkpoint_based_consolidation()` in `openevolve/test_consolidation.py` — creates synthetic `checkpoints/checkpoint_N/` tree (2–3 checkpoint dirs with minimal `best_program.c` and `best_program_info.json`), runs `consolidate_experiment()`, asserts one row per checkpoint with correct `checkpoint_iteration`, `best_found_at_iteration`, `code`, `combined_score`, `time_score` fields (CKPT-01, CKPT-02)
- [ ] `test_checkpoint_load_results()` in `openevolve/test_consolidation.py` — passes synthetic `results.json` through `load_results()`, asserts all new columns present and one row per checkpoint (CKPT-03)
- [ ] `test_checkpoint_explanation_threading()` in `openevolve/test_consolidation.py` — passes explanations dict keyed by checkpoint N through `consolidate_experiment()`, asserts `df['explanation']` populated per row (EXPLAIN-01, EXPLAIN-02)
- [ ] `test_regenerate_flag()` in `openevolve/test_run_structure.py` — creates synthetic experiment dir with existing `results.json`, calls `migrate_legacy --regenerate`, asserts `results.json.v1` backup exists and `results.json` updated from checkpoints (D-09, D-10)

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| LLM explanation quality | EXPLAIN-01 | LLM output is non-deterministic; correctness is semantic | Run `EXPLAIN_GENERATIONS=3 ../openevolve/.venv/bin/python openevolve/run_experiment.py baseline --iterations 5`; inspect `df['explanation']` — should mention loop transformations |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 10s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending

---
phase: 4
slug: per-step-data-pipeline
status: complete
nyquist_compliant: true
wave_0_complete: true
created: 2026-05-14
validated: 2026-05-15
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
| 04-01-01 | 01 | 1 | CKPT-01 | — | N/A | unit | `../openevolve/.venv/bin/python openevolve/test_consolidation.py` | ✅ | ✅ green |
| 04-01-02 | 01 | 1 | CKPT-02 | — | N/A | unit | `../openevolve/.venv/bin/python openevolve/test_consolidation.py` | ✅ | ✅ green |
| 04-01-03 | 01 | 1 | CKPT-03 | — | N/A | unit | `../openevolve/.venv/bin/python openevolve/test_consolidation.py` | ✅ | ✅ green |
| 04-02-01 | 02 | 1 | EXPLAIN-01 | — | N/A | unit | `../openevolve/.venv/bin/python openevolve/test_consolidation.py` | ✅ | ✅ green |
| 04-02-02 | 02 | 1 | EXPLAIN-02 | — | N/A | unit | `../openevolve/.venv/bin/python openevolve/test_consolidation.py` | ✅ | ✅ green |
| 04-03-01 | 03 | 2 | CKPT-01/02 | — | N/A | unit | `../openevolve/.venv/bin/python openevolve/test_run_structure.py` | ✅ | ✅ green |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

New test functions to add to existing test files before implementation tasks:

- [x] `test_checkpoint_based_consolidation()` in `openevolve/test_consolidation.py` — PASSES
- [x] `test_checkpoint_load_results()` in `openevolve/test_consolidation.py` — PASSES
- [x] `test_checkpoint_explanation_threading()` in `openevolve/test_consolidation.py` — PASSES
- [x] `test_regenerate_flag()` in `openevolve/test_run_structure.py` — PASSES
- [x] `test_regenerate_no_legacy_dir()` in `openevolve/test_run_structure.py` — PASSES (bonus: graceful no-op path)

*Wave 0 complete. Full suite: test_consolidation.py 9/9 + test_run_structure.py 12/12 (1 pre-existing warning: test_consolidation returns bool instead of asserting — not a failure).*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Result |
|----------|-------------|------------|--------|
| LLM explanation quality | EXPLAIN-01 | LLM output is non-deterministic; correctness is semantic | ✅ VERIFIED 2026-05-15 — live run with qwen3-coder:30b (10 iterations, 2 checkpoints). `df['explanation'].notna().all()` = True. Explanations populated; "No optimization detected" for zero-improvement run is correct behaviour. Sliding-window mechanism confirmed. |

---

## Validation Sign-Off

- [x] All tasks have automated verify
- [x] Sampling continuity: all 6 tasks have automated tests
- [x] Wave 0 covers all MISSING references
- [x] No watch-mode flags
- [x] Feedback latency < 10s (9 tests in 0.15s)
- [x] `nyquist_compliant: true` set in frontmatter

**Approval:** 2026-05-15 — retroactive audit, 0 gaps found, 9/9 tests green

---

## Validation Audit 2026-05-15

| Metric | Count |
|--------|-------|
| Gaps found | 0 |
| Resolved | 0 |
| Escalated | 0 |
| Tests green | 9/9 (test_consolidation.py) + 12/12 (test_run_structure.py) |
| Manual-only resolved | 1 (LLM quality — live UAT 2026-05-15) |

---
phase: 3
slug: experiment-run-structure
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-05-14
---

# Phase 3 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest (openevolve venv) |
| **Config file** | none — run directly |
| **Quick run command** | `../openevolve/.venv/bin/python -m pytest openevolve/test_run_structure.py -x` |
| **Full suite command** | `../openevolve/.venv/bin/python -m pytest openevolve/ -x` |
| **Estimated runtime** | ~10 seconds |

---

## Sampling Rate

- **After every task commit:** Run `../openevolve/.venv/bin/python -m pytest openevolve/test_run_structure.py -x`
- **After every plan wave:** Run `../openevolve/.venv/bin/python -m pytest openevolve/ -x`
- **Before `/gsd-verify-work`:** Full suite must be green
- **Max feedback latency:** ~10 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 3-01-01 | 01 | 1 | RUNORG-01 | — | run_id sanitized: no `/` or `..` | unit | `pytest openevolve/test_run_structure.py::test_run_id_format -x` | ❌ W0 | ⬜ pending |
| 3-01-02 | 01 | 1 | RUNORG-01 | — | `--run` override accepted | unit | `pytest openevolve/test_run_structure.py::test_run_arg_override -x` | ❌ W0 | ⬜ pending |
| 3-01-03 | 01 | 1 | RUNORG-01 | — | `--output-root` overrides default | unit | `pytest openevolve/test_run_structure.py::test_output_root_override -x` | ❌ W0 | ⬜ pending |
| 3-01-04 | 01 | 1 | RUNORG-03 | — | metadata.json has all required fields | unit | `pytest openevolve/test_run_structure.py::test_metadata_fields -x` | ❌ W0 | ⬜ pending |
| 3-02-01 | 02 | 1 | MIGRATE-01 | — | migration moves all non-runs dirs | unit | `pytest openevolve/test_run_structure.py::test_migration_moves -x` | ❌ W0 | ⬜ pending |
| 3-02-02 | 02 | 1 | MIGRATE-01 | — | migration idempotent on re-run | unit | `pytest openevolve/test_run_structure.py::test_migration_idempotent -x` | ❌ W0 | ⬜ pending |
| 3-03-01 | 03 | 2 | DISPLAY-01 | — | show_results --run filters to one run | unit | `pytest openevolve/test_run_structure.py::test_show_results_run_filter -x` | ❌ W0 | ⬜ pending |
| 3-03-02 | 03 | 2 | DISPLAY-01 | — | show_results no args shows all runs | unit | `pytest openevolve/test_run_structure.py::test_show_results_all -x` | ❌ W0 | ⬜ pending |
| 3-03-03 | 03 | 2 | DISPLAY-01 | — | show_consolidated --run filters to one run | unit | `pytest openevolve/test_run_structure.py::test_show_consolidated_run_filter -x` | ❌ W0 | ⬜ pending |
| 3-04-01 | 03 | 2 | RUNORG-02 | — | evolve-all prompts share same run_id dir | integration | `pytest openevolve/test_run_structure.py::test_evolve_all_shared_run -x` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `openevolve/test_run_structure.py` — stubs for RUNORG-01, RUNORG-02, RUNORG-03, MIGRATE-01, DISPLAY-01
- [ ] Shared fixtures: tmp dir, mock `config.yaml`, mock experiment output directories (baseline/, prompt1/)

*Wave 0 must be complete before any other task in Wave 1 begins.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| `make evolve-all` runs and creates run directory in new layout | RUNORG-02 | Requires actual OpenEvolve subprocess execution | Run `ITERATIONS=1 make evolve-all`; verify `openevolve_output/runs/<id>/cavitydetection/<prompt>/` exists |
| `make show-results RUN=<id>` shows only that run | DISPLAY-01 | Integration with actual filesystem state | Run migration, then `make show-results RUN=legacy`; confirm only legacy prompts shown |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 10s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending

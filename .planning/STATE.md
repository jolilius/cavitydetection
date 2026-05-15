---
gsd_state_version: 1.0
milestone: v1.1
milestone_name: Experiment Runs + Per-Step Analysis
current_phase: 04
status: milestone_archived
last_updated: "2026-05-15"
last_activity: 2026-05-15 -- v1.1 milestone archived
progress:
  total_phases: 4
  completed_phases: 4
  total_plans: 6
  completed_plans: 6
  percent: 100
---

# Project State & Notes

**Last Updated:** 2026-05-15
**Status:** ✅ v1.1 ARCHIVED — ready for next milestone

---

## Project Reference

See: .planning/PROJECT.md (updated 2026-05-15 after v1.1)

**Core value:** Trajectory observation — every checkpoint queryable with code + explanation, not just the final best solution
**Current focus:** Planning next milestone (v1.2)

---

## Key Decisions (summary)

1. **v1.0 complete (Phases 1–2):** Unified JSON, pandas loader, per-iteration explanations shipped
2. **v1.1 research goal: trajectory observation** — checkpoints are the unit of analysis, not iterations
3. **Phase 3 first:** Directory restructure and legacy migration must land before Phase 4 reads from new paths
4. **Run grouping** — `make evolve-all` stamps a single run ID; all prompts share it
5. **Checkpoint granularity** — `results.json` rebuilt from `checkpoints/checkpoint_N/` directories; `best/`-only approach dropped
6. **Per-checkpoint explanation** — compares checkpoint N to checkpoint N-1 (or initial_program.c for checkpoint 0)
7. **Defer multi-program support** — not in v1.1; next milestone candidate

Full decision log: `.planning/PROJECT.md → Key Decisions`

---

## Deferred Items (acknowledged at v1.1 close)

| Area | Item | Severity |
|------|------|----------|
| Makefile | `--output-root` path inconsistency (W-1) | Medium |
| Makefile | Stale `evolve-explain-test`/`test-explanations-disabled` targets (W-2) | Low |
| Display | `show-explanations` scope inconsistency vs other display targets (W-3) | Low |
| Operations | `migrate_legacy.py` not yet run on real data | Low |

---

## Archives

- `.planning/milestones/v1.1-ROADMAP.md` — full phase details
- `.planning/milestones/v1.1-REQUIREMENTS.md` — all 10 requirements marked complete
- `.planning/milestones/v1.1-MILESTONE-AUDIT.md` — 3-source coverage audit
- `.planning/milestones/v1.1-phases/` — phase execution artifacts (plans, summaries, verifications)

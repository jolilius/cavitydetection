# OpenEvolve Results & Explanations Framework — Roadmap

**Goal:** Consolidate experiment results into a unified format; capture LLM explanations of transformations; enable per-step trajectory analysis.

**Research Focus:** Understand how prompts influence search behavior (convergence speed, quality, strategy).

---

## Milestones

- ✅ **v1.0 — Results & Explanations Framework** — Phases 1–2 (shipped 2026-05-13)
- ✅ **v1.1 — Experiment Runs + Per-Step Analysis** — Phases 3–4 (shipped 2026-05-15)

---

## Phases

<details>
<summary>✅ v1.0 — Results & Explanations Framework (Phases 1–2) — SHIPPED 2026-05-13</summary>

- [x] Phase 1: Results Consolidation — Unified JSON schema per experiment; pandas loader functional
- [x] Phase 2: LLM Explanations — Per-iteration explanation capture; `explanation` field in DataFrame

See: `.planning/milestones/v1.0-ROADMAP.md` *(or ROADMAP.md git history prior to v1.0 tag)*

</details>

<details>
<summary>✅ v1.1 — Experiment Runs + Per-Step Analysis (Phases 3–4) — SHIPPED 2026-05-15</summary>

- [x] Phase 3: Experiment Run Structure — Named runs grouping all prompts; legacy data migrated
- [x] Phase 4: Per-Step Data Pipeline — Checkpoint-based consolidation with code field; per-checkpoint explanations

See: `.planning/milestones/v1.1-ROADMAP.md`

</details>

---

## Progress

| Phase | Milestone | Plans Complete | Status | Completed |
|-------|-----------|---------------|--------|-----------|
| 1. Results Consolidation | v1.0 | — | Complete | 2026-05-13 |
| 2. LLM Explanations | v1.0 | — | Complete | 2026-05-13 |
| 3. Experiment Run Structure | v1.1 | 3/3 | Complete | 2026-05-14 |
| 4. Per-Step Data Pipeline | v1.1 | 3/3 | Complete | 2026-05-15 |

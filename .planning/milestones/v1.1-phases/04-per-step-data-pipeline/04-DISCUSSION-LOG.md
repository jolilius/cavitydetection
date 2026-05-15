# Phase 4: Per-Step Data Pipeline - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-05-14
**Phase:** 04-per-step-data-pipeline
**Areas discussed:** Missing time_score field, Explanation timing, Legacy results.json compat, consolidate_results.py approach

---

## Missing time_score field

| Option | Description | Selected |
|--------|-------------|----------|
| null / None | Store null for time_score in every row. Schema stays forward-compatible when OpenEvolve adds real timing. | ✓ |
| Omit from schema | Drop time_score from CKPT-02 entirely — update the requirement. | |
| Derive from iteration_runtime_seconds | Compute a synthetic time_score from per-iteration timing metadata. | |

**User's choice:** null / None — store null as placeholder
**Notes:** User wants to add real time measurement as a feature in a later phase. The null slot keeps the schema forward-compatible without inventing a synthetic value.

### combined_score sub-question

| Option | Description | Selected |
|--------|-------------|----------|
| Copy mem_score value | combined_score = mem_score in every row — keeps field for future multi-objective scoring. | ✓ |
| Omit combined_score | Drop it alongside time_score. | |

**User's choice:** Copy mem_score value (Recommended)

---

## Explanation timing

### When to generate

| Option | Description | Selected |
|--------|-------------|----------|
| Post-run, separate command | run_experiment.py writes null explanations; separate 'make explain' fills them in. | |
| Inline during run | Maintain Phase 2 behavior: generated at end of run. | ✓ |

**User's choice:** Inline during run

### Skippability

| Option | Description | Selected |
|--------|-------------|----------|
| Yes, generate all at end of run | All checkpoints explained in one batch post-run (~30-60s added). | |
| No, make it skippable | Add EXPLAIN=0 flag for fast iteration runs. | ✓ |

**Notes:** Explanation generation adds ~30s for 10 checkpoints. User wants it skippable.

### Which flag

| Option | Description | Selected |
|--------|-------------|----------|
| Reuse EXPLAIN_GENERATIONS=0 | Existing Phase 2 flag. No new flag needed. | ✓ |
| New EXPLAIN_CHECKPOINTS=0 flag | Separate control for checkpoint vs iteration explanations. | |

**User's choice:** Reuse EXPLAIN_GENERATIONS=0 (Recommended)

---

## Legacy results.json compat

### Handling strategy

| Option | Description | Selected |
|--------|-------------|----------|
| Regenerate on migrate | Add --regenerate flag to migrate_legacy.py; rebuilds results.json from checkpoints. | ✓ |
| Dual-format loader | load_results() normalizes both old and new schema permanently. | |
| Ignore legacy files | load_results() only handles new format; old data inaccessible. | |

**User's choice:** Regenerate on migrate (Recommended)

### Backup strategy

| Option | Description | Selected |
|--------|-------------|----------|
| Keep backup as results.json.v1 | Rename before overwriting — easy rollback. | ✓ |
| No backup, overwrite directly | Trust new consolidation; simpler. | |

**User's choice:** Keep backup as results.json.v1 (Recommended)

---

## consolidate_results.py approach

### File structure

| Option | Description | Selected |
|--------|-------------|----------|
| Replace _extract_iterations() in-place | Rewrite private function; same public API. Minimal diff. | ✓ |
| New checkpoint_consolidator.py module | Separate file; consolidate_results.py untouched. Cleaner but more surface area. | |

**User's choice:** Replace _extract_iterations() in-place (Recommended)

### JSON key name

| Option | Description | Selected |
|--------|-------------|----------|
| Keep 'iterations' key | Backward compat with analysis code that reads results.json directly. | ✓ |
| Rename to 'checkpoints' | More semantically accurate. | |

**User's choice:** Keep 'iterations' key (Recommended)

---

## Claude's Discretion

- Numeric sort implementation for checkpoint directories
- Whether explanation generation reuses `_generate_explanations_for_experiment()` or calls `generate_explanation()` directly per checkpoint
- Error handling for incomplete checkpoint directories (missing files → skip with warning)

## Deferred Ideas

- **Real time measurement / time_score** — User wants this added in a future phase once the definition of "time score" is clear (wall time? CPU time? normalized?). The `null` placeholder in Phase 4 keeps the door open.

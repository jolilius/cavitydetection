# Phase 3: Experiment Run Structure - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-05-14
**Phase:** 03-experiment-run-structure
**Areas discussed:** Run ID collision handling, Migration: move or copy?, show-results default view, Standalone run_experiment.py without --run

---

## Run ID Collision Handling

| Option | Description | Selected |
|--------|-------------|----------|
| Full datetime (YYYY-MM-DD_HHMM_model) | Include HH-MM in the ID. Unique by default, no collision logic needed. | ✓ |
| Date + counter suffix | Start at YYYY-MM-DD_model, increment to _002 on collision. | |
| Date + short UUID | Append 6-char random suffix. Always unique but noisy. | |

**User's choice:** Full datetime — `2026-05-14_1430_qwen25-32b`
**Notes:** No collision detection needed; the minute-level timestamp makes each auto-ID unique.

---

| Option | Description | Selected |
|--------|-------------|----------|
| Collapse to alphanumeric + dashes | `qwen2.5-coder:32b` → `qwen25-coder-32b` | ✓ |
| Replace only `:` with `-` | Minimal changes, keeps dots | |
| You decide | Leave sanitization to planner | |

**User's choice:** Collapse to alphanumeric + dashes — any non-`[a-zA-Z0-9-]` replaced with `-`, consecutive dashes collapsed.

---

## Migration: Move or Copy?

| Option | Description | Selected |
|--------|-------------|----------|
| Move (os.rename) | Atomic on same filesystem, original paths gone after | ✓ |
| Copy then verify then delete originals | Safer but slower, doubles disk temporarily | |
| Copy and leave originals | Copy to new location, originals stay as safety net | |

**User's choice:** Move (os.rename)
**Notes:** Atomic rename on the same filesystem; fast, no extra disk space.

---

| Option | Description | Selected |
|--------|-------------|----------|
| Idempotent: migrate only unmigrated dirs | Skip dirs already in runs/legacy/ | ✓ |
| Error if legacy already exists | Fail loudly if runs/legacy/ already present | |
| Always overwrite | Re-migrate everything each time | |

**User's choice:** Idempotent — migration script skips already-migrated directories.

---

## show-results Default View

| Option | Description | Selected |
|--------|-------------|----------|
| All runs merged, flat by prompt | Same as today — one row per prompt, best across all runs | ✓ |
| Most recent run only | Only the latest run is shown without filter | |
| Grouped by run | One section per run, per-prompt rows | |

**User's choice:** All runs merged flat by prompt — backward-compatible with current output.

---

| Option | Description | Selected |
|--------|-------------|----------|
| Same flat table filtered to that run | Per-prompt summary for prompts in that run | ✓ |
| Full per-checkpoint rows for that run | Every checkpoint row — better for Phase 4 | |
| You decide | Leave filtered display to planner | |

**User's choice:** Same flat table filtered to that run only.

---

## Standalone run_experiment.py without --run

| Option | Description | Selected |
|--------|-------------|----------|
| Auto-create a solo run with its own ID | Output to `runs/<auto-id>/cavitydetection/<prompt>/` | ✓ |
| Fall back to legacy path | Keep old `openevolve_output/<prompt>/` for direct invocations | |
| Require --run always (error without it) | Force explicit run naming | |

**User's choice:** Auto-create a solo run — new layout always used after this phase.

---

| Option | Description | Selected |
|--------|-------------|----------|
| Always relative to SCRIPT_DIR | Output stays at `openevolve/openevolve_output/runs/...` | |
| Accept --output-root flag to override | Researcher can point results at any directory | ✓ |
| You decide | Leave output root handling to planner | |

**User's choice:** Accept `--output-root` flag to override the default base directory.

---

## Claude's Discretion

- `metadata.json` field ordering and JSON formatting details
- Whether `make evolve-all` generates the run ID in shell or via a Python helper
- Config snapshot format in `metadata.json` (inline dict vs. raw YAML string)

## Deferred Ideas

None — discussion stayed within phase scope.

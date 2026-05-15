---
phase: 03-experiment-run-structure
plan: "02"
subsystem: testing
tags: [python, filesystem, migration, os.rename, idempotent, pytest]

# Dependency graph
requires:
  - phase: 03-experiment-run-structure/03-01
    provides: test_run_structure.py with fixture style, generate_run_id, write_run_metadata
provides:
  - openevolve/migrate_legacy.py — standalone idempotent migration script using os.rename
  - test_migration_moves and test_migration_idempotent tests in test_run_structure.py
affects: [03-experiment-run-structure/03-03, display scripts, any future migration consumers]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "os.rename() with shutil.move() EXDEV fallback for same-filesystem moves"
    - "Idempotency via os.path.exists(dst) check before rename"
    - "skip = {'runs'} set filter to exclude the runs/ dir itself from migration"
    - "Sentinel file pattern in idempotency tests (write data → migrate → verify read)"

key-files:
  created:
    - openevolve/migrate_legacy.py
  modified:
    - openevolve/test_run_structure.py

key-decisions:
  - "Migration uses os.rename() (atomic on same filesystem) with shutil.move() EXDEV fallback for cross-device case"
  - "Skip set is {'runs'} — all other top-level subdirs including orphans (best/, checkpoints/, logs/) are migrated"
  - "Idempotency: dst existence check with print message, no error raised on skip"

patterns-established:
  - "Pattern: standalone migration script with --output-root arg and sys.exit validation"
  - "Pattern: idempotency test uses sentinel file to verify data preservation across re-runs"

requirements-completed: [MIGRATE-01]

# Metrics
duration: 2min
completed: 2026-05-14
---

# Phase 3 Plan 02: Migration Script for Legacy Flat Experiment Directories Summary

**Idempotent os.rename()-based migration script moving all non-runs/ subdirs under openevolve_output/ to runs/legacy/cavitydetection/, with sentinel-file data-preservation tests**

## Performance

- **Duration:** 2 min
- **Started:** 2026-05-14T13:45:30Z
- **Completed:** 2026-05-14T13:47:45Z
- **Tasks:** 2
- **Files modified:** 2

## Accomplishments

- Created `openevolve/migrate_legacy.py`: scans all non-`runs/` subdirectories in `openevolve_output/` and moves each to `runs/legacy/cavitydetection/<name>/` via `os.rename()`, with `shutil.move()` fallback for cross-device (EXDEV errno 18)
- Implemented idempotency: destination existence check before each rename; prints skip message and continues on second run without error
- Added `test_migration_moves` and `test_migration_idempotent` to `test_run_structure.py`; both pass alongside existing 10-test suite (12 total green)

## Task Commits

Each task was committed atomically:

1. **Task 1: Create migrate_legacy.py** - `c6cd6d4` (feat)
2. **Task 2: Implement migration tests in test_run_structure.py** - `fce7c19` (test)

**Plan metadata:** (docs commit follows)

## Files Created/Modified

- `openevolve/migrate_legacy.py` — standalone migration script; callable as `python openevolve/migrate_legacy.py [--output-root PATH]`
- `openevolve/test_run_structure.py` — added `test_migration_moves` and `test_migration_idempotent` plus `__main__` runner entries

## Decisions Made

- Migration scans `os.listdir()` with `skip = {"runs"}` rather than hard-coding the two known names (`baseline/`, `prompt1/`); this handles all five actual top-level dirs including orphans (`best/`, `checkpoints/`, `logs/`)
- Used errno 18 (EXDEV) check rather than blanket `OSError` catch for the `shutil.move` fallback, so other OS errors propagate correctly
- `--output-root` validated with `sys.exit()` before any filesystem operations, matching plan's T-03-05 threat mitigation

## Deviations from Plan

None — plan executed exactly as written.

## Issues Encountered

None.

## User Setup Required

None — no external service configuration required. Migration is a standalone script run manually by the researcher.

## Next Phase Readiness

- `migrate_legacy.py` is ready for one-shot use against real `openevolve_output/` when researcher decides to migrate
- Full test suite (12 tests) green; no regressions in consolidation or run structure tests
- Plan 03-03 (show_results / display filtering) can proceed independently

---
*Phase: 03-experiment-run-structure*
*Completed: 2026-05-14*

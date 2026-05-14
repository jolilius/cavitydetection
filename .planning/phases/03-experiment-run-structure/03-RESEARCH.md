# Phase 3: Experiment Run Structure - Research

**Researched:** 2026-05-14
**Domain:** Python filesystem restructuring, argparse CLI, shell Makefile variable passing, JSON metadata, data migration
**Confidence:** HIGH

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

- **D-01:** Run ID format: `YYYY-MM-DD_HHMM_<model>` (e.g., `2026-05-14_1430_qwen25-32b`). Date-only IDs rejected — two runs on the same day must be distinguishable.
- **D-02:** Model sanitization: replace all `[^a-zA-Z0-9-]` with `-`; collapse consecutive dashes. `qwen2.5-coder:32b` → `qwen2-5-coder-32b`. `qwen3-coder:30b` → `qwen3-coder-30b`.
- **D-03:** Migration uses `os.rename()` (move, not copy). Atomic on same filesystem. Legacy paths gone after migration.
- **D-04:** Migration is idempotent. Already-migrated directories under `runs/legacy/cavitydetection/` are skipped without error.
- **D-05:** `make show-results` with no `RUN=` arg — all runs merged, flat by prompt. Best result across all runs per prompt. Backward-compatible.
- **D-06:** `make show-results RUN=<id>` — same flat per-prompt table, filtered to prompts in that specific run only.
- **D-07:** `run_experiment.py` without `--run` auto-generates solo run ID in `YYYY-MM-DD_HHMM_<model>` format. Results go to `openevolve_output/runs/<auto-id>/cavitydetection/<prompt>/`. No fallback to legacy flat path.
- **D-08:** `run_experiment.py` accepts `--output-root` flag to override default output base (`openevolve/openevolve_output/`).

### Claude's Discretion

- How `metadata.json` is written (fields order, JSON formatting) — follow REQUIREMENTS.md spec for field list.
- Whether `make evolve-all` generates the run ID in shell or calls a Python helper.
- Config snapshot format in `metadata.json` — inline YAML-as-dict vs. raw YAML string.

### Deferred Ideas (OUT OF SCOPE)

None — discussion stayed within phase scope.
</user_constraints>

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| RUNORG-01 | Researcher can identify an experiment as a named run; auto-generates from timestamp + model; overridable with `--run <name>` | Run ID generation logic verified; argparse pattern in existing code confirmed |
| RUNORG-02 | `make evolve-all` creates one run directory before invoking individual prompt runs; all prompts share same run ID | Makefile `evolve-all` target structure analyzed; shell `date`/Python helper approaches both viable |
| RUNORG-03 | Each run directory contains `metadata.json` with model name, total iterations, programs, prompts, config snapshot, start timestamp | `config.yaml` loading pattern confirmed in existing code; YAML-as-dict approach ready to use |
| MIGRATE-01 | `baseline/` and `prompt1/` migrated to `runs/legacy/cavitydetection/` with no data loss; `os.rename()` + idempotency | Actual directory structure verified; two dirs confirmed; `os.rename()` is cross-dir atomic on same filesystem |
| DISPLAY-01 | `make show-results` and `make show-consolidated-results` work with new run structure; accept optional `RUN=<id>` | Both scripts analyzed; `load_all_results()` already uses `os.walk()` — adapts to new depth automatically |
</phase_requirements>

---

## Summary

Phase 3 is a pure structural and CLI refactoring phase. The codebase (Python scripts + Makefile) is well-understood from direct inspection. No new third-party libraries are needed. The key changes touch four files: `run_experiment.py` (CLI flags + output path logic), `Makefile` (run ID generation + `RUN=` pass-through), `show_results.py` and `show_consolidated.py` (filter by run). A new migration script and a `metadata.json` writer are needed.

The most important discovery is that `load_all_results()` in `results_loader.py` already uses `os.walk()` recursively and finds any `results.json` at any depth — meaning the new `runs/<run_id>/cavitydetection/<prompt>/results.json` layout will be discovered automatically without changes to the loader. This is the single biggest re-use win.

The second important discovery is that `show_results.py` scans `os.listdir(OUTPUT_ROOT)` and expects top-level entries to be prompt names — this will break when `OUTPUT_ROOT` contains a `runs/` directory. The `show_results.py` discovery logic must be updated to walk the new `runs/` structure, not the flat top-level list.

There is an existing v1.0 milestone audit that flagged pandas as not installed in the openevolve venv. Direct verification confirms pandas 3.0.3 **is** installed at `/home/jolilius/home/src/openevolve/.venv/` (the correct path). The audit path notation was off. `make show-results` works correctly from the project root right now.

**Primary recommendation:** Implement run ID generation as a small Python helper function (callable from both `run_experiment.py` and via subprocess from the Makefile) to avoid duplicating the sanitization regex in shell and Python.

---

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Run ID generation (timestamp + sanitize) | Python (`run_experiment.py`) | Shell (Makefile) | Logic is in Python; Makefile calls subprocess to get ID |
| Output path construction | Python (`run_experiment.py`) | — | Centralizes path logic; Makefile receives `--run` flag |
| `metadata.json` write | Python (`run_experiment.py`) | — | Has access to config, model, prompts, start time |
| Legacy migration | Python (new `migrate_legacy.py`) | — | `os.rename()` is Python stdlib; needs idempotency logic |
| Results discovery (load_all_results) | Python (`results_loader.py`) | — | Already `os.walk()` — auto-adapts to new depth |
| Display filtering by run | Python (`show_results.py`, `show_consolidated.py`) | — | `--run` arg added to both scripts |
| Run ID coordination across prompts | Shell (`Makefile` `evolve-all`) | Python helper | Makefile generates run ID once, passes to each invocation |

---

## Standard Stack

### Core (all already in use — no new installs)

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Python stdlib `os`, `os.path`, `shutil` | 3.12.3 | Filesystem ops, path construction, migration | Already in use throughout codebase |
| Python stdlib `argparse` | 3.12.3 | CLI flag parsing (`--run`, `--output-root`) | Already used in `run_experiment.py` |
| Python stdlib `json` | 3.12.3 | `metadata.json` read/write | Already used everywhere |
| Python stdlib `re` | 3.12.3 | Model name sanitization regex | Lightweight, no dependency |
| Python stdlib `datetime` | 3.12.3 | Run ID timestamp generation | Already used in `consolidate_results.py` |
| `yaml` (PyYAML) | 6.0.3 | Config snapshot read for `metadata.json` | Already used in `run_experiment.py` |
| `pandas` | 3.0.3 | DataFrame aggregation for display scripts | Confirmed installed in venv |

[VERIFIED: direct venv inspection `/home/jolilius/home/src/openevolve/.venv/bin/python -c "import pandas; print(pandas.__version__)"`]

### No New Dependencies Required

All libraries needed for this phase are already present in the openevolve venv. No `uv pip install` step needed.

---

## Architecture Patterns

### System Architecture Diagram

```
make evolve-all
    │
    ├─ generate RUN_ID (via Python helper or shell date + sanitize)
    │       YYYY-MM-DD_HHMM_<sanitized-model>
    │
    ├─ for each prompt in PROMPT_NAMES:
    │       run_experiment.py <prompt> --run $RUN_ID --iterations N
    │           │
    │           ├─ parse --run, --output-root, --iterations
    │           ├─ construct output_dir = <output_root>/runs/<run_id>/cavitydetection/<prompt>/
    │           ├─ write metadata.json to <output_root>/runs/<run_id>/metadata.json
    │           ├─ run OpenEvolve subprocess (--output output_dir)
    │           ├─ generate explanations
    │           └─ consolidate_experiment(output_dir=...) → results.json
    │
    └─ done

make show-results [RUN=<id>]
    │
    ├─ show_results.py [--run <id>]
    │       └─ walk runs/<run_id>/cavitydetection/<prompt>/results.json
    │               filter by run if --run provided
    │               display flat per-prompt table (best row per prompt)

make show-consolidated-results [RUN=<id>]
    │
    └─ show_consolidated.py [--run <id>]
            └─ load_all_results(runs_root)   ← os.walk finds all results.json
                    filter by run_id if arg provided
                    display flat per-prompt table

migrate_legacy.py (standalone, run once)
    │
    ├─ for each top-level dir in openevolve_output/ (excluding 'runs/'):
    │       target = openevolve_output/runs/legacy/cavitydetection/<dirname>/
    │       if target exists: skip (idempotent)
    │       else: os.rename(src, target)
    └─ also handle top-level orphan dirs: best/, checkpoints/, logs/
```

### Recommended Project Structure (new files only)

```
openevolve/
├── run_experiment.py       # MODIFIED: --run, --output-root args; metadata.json write
├── show_results.py         # MODIFIED: --run filter; new path traversal
├── show_consolidated.py    # MODIFIED: --run filter arg
├── migrate_legacy.py       # NEW: one-shot migration script
└── openevolve_output/
    └── runs/
        ├── legacy/
        │   └── cavitydetection/
        │       ├── baseline/   (moved from openevolve_output/baseline/)
        │       └── prompt1/    (moved from openevolve_output/prompt1/)
        └── 2026-05-14_1430_qwen3-coder-30b/
            ├── metadata.json
            └── cavitydetection/
                ├── baseline/
                │   ├── best/
                │   ├── checkpoints/
                │   ├── logs/
                │   └── results.json
                └── prompt1/
                    └── ...
```

### Pattern 1: Run ID Generation

**What:** Generates a deterministic, filesystem-safe run identifier.
**When to use:** At the start of `run_experiment.py` when `--run` is not provided; at the start of `make evolve-all` before the prompt loop.

```python
# Source: [ASSUMED] standard Python pattern
import re
from datetime import datetime
import yaml

def generate_run_id(config_path: str) -> str:
    """Generate run ID from current timestamp and model name from config."""
    ts = datetime.now().strftime("%Y-%m-%d_%H%M")
    # Load model from config
    try:
        with open(config_path) as f:
            config = yaml.safe_load(f)
        model = config.get("llm", {}).get("primary_model", "unknown")
    except Exception:
        model = "unknown"
    sanitized = re.sub(r"[^a-zA-Z0-9-]+", "-", model)
    sanitized = re.sub(r"-+", "-", sanitized).strip("-")
    return f"{ts}_{sanitized}"
```

**Verified output:** `qwen3-coder:30b` → `qwen3-coder-30b`; `qwen2.5-coder:32b` → `qwen2-5-coder-32b` [VERIFIED: Python 3.12.3 regex test in session]

### Pattern 2: Output Path Construction

**What:** Derives the per-prompt output directory from run ID, program name, and prompt name.
**When to use:** In `run_experiment.py` after run ID is resolved.

```python
# Source: [VERIFIED: existing SCRIPT_DIR/PROJECT_ROOT pattern in run_experiment.py]
output_root = args.output_root or os.path.join(SCRIPT_DIR, "openevolve_output")
run_id = args.run or generate_run_id(config_path)
output_dir = os.path.join(output_root, "runs", run_id, "cavitydetection", args.prompt)
os.makedirs(output_dir, exist_ok=True)
```

### Pattern 3: metadata.json Write

**What:** Writes run-level metadata once per run, before or after each prompt's experiment.
**When to use:** In `run_experiment.py`; write on first invocation (if file absent), or overwrite/update prompts list on each invocation.

```python
# Source: [ASSUMED] standard json + yaml pattern
import json, yaml, os
from datetime import datetime, timezone

def write_run_metadata(run_dir: str, config: dict, args, start_time: str, prompts_so_far: list):
    meta_path = os.path.join(run_dir, "metadata.json")
    # Load existing to merge prompts list (for partial runs)
    existing = {}
    if os.path.isfile(meta_path):
        with open(meta_path) as f:
            existing = json.load(f)
    metadata = {
        "run_id": os.path.basename(run_dir),
        "model": config.get("llm", {}).get("primary_model", "unknown"),
        "total_iterations": args.iterations,
        "programs": ["cavitydetection"],
        "prompts": prompts_so_far,
        "config_snapshot": config,   # full config dict (YAML loaded as dict)
        "start_timestamp": existing.get("start_timestamp", start_time),
    }
    os.makedirs(run_dir, exist_ok=True)
    with open(meta_path, "w") as f:
        json.dump(metadata, f, indent=2)
```

**Note:** `config_snapshot` stored as a dict (YAML already deserialized). This avoids YAML string quoting edge cases and is directly JSON-serializable. [ASSUMED — discretion area from CONTEXT.md]

### Pattern 4: Migration Script

**What:** Moves legacy flat directories to the new nested structure.
**When to use:** One-shot; idempotent so safe to re-run.

```python
# Source: [VERIFIED: os.rename semantics; same filesystem confirmed via df output]
import os

def migrate_legacy(output_root: str):
    """Move top-level experiment dirs to runs/legacy/cavitydetection/."""
    runs_dir = os.path.join(output_root, "runs")
    legacy_dir = os.path.join(runs_dir, "legacy", "cavitydetection")
    os.makedirs(legacy_dir, exist_ok=True)

    skip = {"runs"}  # don't move the runs/ dir itself
    for name in os.listdir(output_root):
        if name in skip:
            continue
        src = os.path.join(output_root, name)
        if not os.path.isdir(src):
            continue
        dst = os.path.join(legacy_dir, name)
        if os.path.exists(dst):
            print(f"Skip (already migrated): {dst}")
            continue
        os.rename(src, dst)
        print(f"Moved: {src} → {dst}")
```

**Important:** The top-level `openevolve_output/` directory contains: `baseline/`, `prompt1/`, `best/`, `checkpoints/`, `logs/`. All five are orphan directories from v1.0 and early test runs. All five should be migrated — not just `baseline/` and `prompt1/`. [VERIFIED: `ls openevolve_output/` output]

### Pattern 5: show_results.py Adaptation for New Path Layout

**Current behavior:** Scans `os.listdir(OUTPUT_ROOT)` — expects direct children to be prompt dirs.
**Problem after migration:** `OUTPUT_ROOT` will contain only `runs/`; `os.listdir` would return `["runs"]` and no prompts would be found.
**Fix:** Change discovery to walk `runs/*/cavitydetection/*/results.json` pattern.

```python
# Source: [VERIFIED: current show_results.py line 95 os.listdir(OUTPUT_ROOT)]
import glob

def discover_prompt_results(output_root: str, run_filter: str = None) -> list:
    """Find all results under runs/ structure. Optionally filter to one run."""
    pattern = os.path.join(output_root, "runs", "**", "results.json")
    paths = glob.glob(pattern, recursive=True)
    results = []
    for path in paths:
        # Parse run_id from path: runs/<run_id>/cavitydetection/<prompt>/results.json
        parts = path.replace(output_root, "").split(os.sep)
        # parts: ['', 'runs', '<run_id>', 'cavitydetection', '<prompt>', 'results.json']
        if len(parts) >= 6:
            run_id = parts[2]
            prompt = parts[4]
            if run_filter and run_id != run_filter:
                continue
            results.append({"path": path, "run_id": run_id, "prompt": prompt})
    return results
```

**Alternative:** Keep `load_all_results()` from `results_loader.py` (which already uses `os.walk()`) and add a `run_id` column to the DataFrame by parsing the path. This is the cleaner approach for `show_consolidated.py` which already uses `load_all_results()`.

### Pattern 6: Makefile RUN_ID Generation

**What:** The Makefile must generate the run ID once before the prompt loop and pass it to each `run_experiment.py` invocation.

Two approaches:

**Option A — Shell date + sed (no Python):**
```makefile
evolve-all:
    @RUN_ID=$$(date '+%Y-%m-%d_%H%M')_$$(grep 'primary_model:' openevolve/config.yaml | head -1 | sed "s/.*: '//;s/'.*//;s/[^a-zA-Z0-9-]/-/g;s/-\+/-/g"); \
    echo "Run ID: $$RUN_ID"; \
    for p in $(PROMPT_NAMES); do \
        $(OPENEVOLVE_PYTHON) openevolve/run_experiment.py $$p --run $$RUN_ID --iterations $${ITERATIONS:-80}; \
    done
```

**Option B — Python helper (recommended):**
```makefile
evolve-all:
    @RUN_ID=$$($(OPENEVOLVE_PYTHON) -c "import sys; sys.path.insert(0,'openevolve'); from run_experiment import generate_run_id; print(generate_run_id('openevolve/config.yaml'))"); \
    echo "Run ID: $$RUN_ID"; \
    for p in $(PROMPT_NAMES); do \
        $(OPENEVOLVE_PYTHON) openevolve/run_experiment.py $$p --run $$RUN_ID --iterations $${ITERATIONS:-80}; \
    done
```

Option B is preferred because it centralizes sanitization logic in Python where it's testable, avoids shell sed quoting pitfalls, and keeps the regex in one place. [ASSUMED — discretion area from CONTEXT.md]

### Pattern 7: Makefile RUN= Variable Pass-Through

```makefile
show-results:
    $(OPENEVOLVE_PYTHON) openevolve/show_results.py $(if $(RUN),--run $(RUN),)

show-consolidated-results:
    $(OPENEVOLVE_PYTHON) openevolve/show_consolidated.py $(if $(RUN),--run $(RUN),)
```

The `$(if $(RUN),--run $(RUN),)` pattern expands to `--run <value>` when `RUN=<value>` is set, and to nothing when unset. [VERIFIED: standard GNU Make pattern]

### Anti-Patterns to Avoid

- **Copying instead of moving in migration:** `shutil.copytree` + delete is non-atomic and wastes disk space. Use `os.rename()` which is atomic on same-filesystem moves on Linux. [VERIFIED: same filesystem confirmed]
- **Hard-coding `"baseline"` and `"prompt1"` in migration:** The script scans `os.listdir()` so new legacy dirs added later are also migrated on re-run (idempotency).
- **Generating run ID inside the per-prompt loop:** Each `run_experiment.py` call would produce a different timestamp. Run ID must be generated once before the loop.
- **Storing config_snapshot as raw YAML string:** PyYAML dumps can produce multi-line strings that require careful JSON escaping. Store as deserialized dict — already available in memory when config is loaded.
- **Updating metadata.json per-prompt with only the current prompt's name:** Write the full prompts list each time, read-then-merge pattern, so partial failures don't lose already-recorded prompts.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Recursive results.json discovery | Custom walker | `os.walk()` in existing `load_all_results()` | Already works at any depth; adding `runs/` nesting requires only updating the root path argument |
| Config file parsing | Custom YAML parser | `yaml.safe_load()` (already imported in `run_experiment.py`) | Handles anchors, multiline strings, edge cases |
| Filesystem path construction | String concatenation | `os.path.join()` | Cross-platform separators, handles trailing slashes |
| Glob-based path discovery | Regex on os.walk output | `glob.glob(pattern, recursive=True)` | Cleaner syntax, well-tested |

---

## Runtime State Inventory

> This phase renames/moves directories. The inventory is required.

| Category | Items Found | Action Required |
|----------|-------------|-----------------|
| Stored data | `openevolve_output/baseline/` and `openevolve_output/prompt1/` — directories with checkpoints and best/ subdirs; no `results.json` exists yet | `os.rename()` move in migration script |
| Stored data (orphan) | `openevolve_output/best/`, `openevolve_output/checkpoints/`, `openevolve_output/logs/` — top-level dirs from early test runs, not associated with a named prompt | Move to `runs/legacy/cavitydetection/` under the same names (or a special `_root_run/` subdirectory if preferred) |
| Live service config | None — no external services reference these directory paths | None |
| OS-registered state | None — no cron jobs, systemd units, or Task Scheduler entries reference `openevolve_output/` paths | None |
| Secrets/env vars | `EXPLAIN_GENERATIONS`, `ITERATIONS`, `MEMTRACE_LOG` — env vars that control run behavior, not paths | No change needed; env var names unchanged |
| Build artifacts | `openevolve/__pycache__/` — will auto-regenerate after code edits | None |

**Key finding:** The five top-level orphan directories (`best/`, `checkpoints/`, `logs/` at `openevolve_output/` level plus `baseline/` and `prompt1/`) must all be migrated. The migration script in CONTEXT.md mentions only `baseline/` and `prompt1/`; the planner must ensure the migration handles all non-`runs/` subdirectories in `openevolve_output/`. [VERIFIED: `ls openevolve_output/` output]

---

## Common Pitfalls

### Pitfall 1: os.rename() Fails Across Filesystems

**What goes wrong:** `os.rename()` raises `OSError: [Errno 18] Invalid cross-device link` if source and destination are on different filesystems.
**Why it happens:** `os.rename()` uses the `rename(2)` syscall which does not support cross-device moves.
**How to avoid:** `openevolve_output/` and its `runs/` subdirectory are siblings on the same filesystem (confirmed: both on `/dev/nvme0n1p2`). The migration script creates `runs/legacy/cavitydetection/` inside `openevolve_output/` — same device. Safe.
**Warning signs:** If a user specifies `--output-root` pointing to a different mount, `os.rename()` will fail. Add a fallback to `shutil.move()` which handles cross-device by copy+delete. [VERIFIED: filesystem check]

### Pitfall 2: show_results.py Finds No Results After Migration

**What goes wrong:** `show_results.py` currently iterates `os.listdir(OUTPUT_ROOT)` and treats each entry as a prompt name. After migration, `OUTPUT_ROOT` contains only `runs/` — no prompts at the top level.
**Why it happens:** The script was written for the flat `openevolve_output/<prompt>/` layout.
**How to avoid:** Replace `os.listdir(OUTPUT_ROOT)` with a traversal that walks `runs/*/cavitydetection/*/` or uses `load_all_results()` with path parsing to extract run_id.
**Warning signs:** `make show-results` returns "No completed experiments found." immediately after migration. [VERIFIED: show_results.py source]

### Pitfall 3: run_id Collision Within One Minute

**What goes wrong:** Two `make evolve-all` runs started within the same minute produce identical run IDs (`YYYY-MM-DD_HHMM`).
**Why it happens:** The timestamp resolution is minutes, not seconds.
**How to avoid:** The collision risk is low in practice (researcher workflow). If needed, the planner could add seconds to the format, but D-01 locked the `HHMM` precision. Document the limitation.
**Warning signs:** Second run's `metadata.json` overwrites first run's metadata. Prompt output dirs within the same run ID get merged.

### Pitfall 4: metadata.json Prompts List Partial on Failure

**What goes wrong:** If the third prompt in a five-prompt `evolve-all` run fails, `metadata.json` only lists the first two prompts.
**Why it happens:** Each `run_experiment.py` invocation updates `metadata.json`; a crash mid-loop leaves it incomplete.
**How to avoid:** Use a read-then-merge pattern in `write_run_metadata()` so each invocation appends its prompt to the existing list rather than overwriting.
**Warning signs:** `metadata.json` shows fewer prompts than actually ran.

### Pitfall 5: consolidate_results.py output_dir Mismatch

**What goes wrong:** `consolidate_experiment(output_dir=output_dir)` writes `results.json` to `output_dir` — that must be the prompt-specific dir (`runs/<run_id>/cavitydetection/<prompt>/`), not the run root.
**Why it happens:** The function derives `prompt_variant` from `os.path.basename(output_dir)`. If `output_dir` points to the run root, `prompt_variant` would be the run ID, not the prompt name.
**How to avoid:** Ensure `output_dir` passed to `consolidate_experiment()` is always the prompt-level directory. [VERIFIED: consolidate_results.py line 71]

### Pitfall 6: Legacy Orphan Directories Not Migrated

**What goes wrong:** `openevolve_output/best/`, `openevolve_output/checkpoints/`, `openevolve_output/logs/` remain after migration, causing `show_results.py` path traversal or future confusion.
**Why it happens:** REQUIREMENTS.md and CONTEXT.md mention only `baseline/` and `prompt1/` as migration targets.
**How to avoid:** Migration script must scan all directories in `openevolve_output/` (excluding `runs/`) rather than hard-coding the two known names. [VERIFIED: `ls openevolve_output/` shows 5 subdirs total]

---

## Code Examples

### Full run_experiment.py argparse Changes

```python
# Source: [VERIFIED: existing argparse pattern in run_experiment.py:115-118]
parser.add_argument("prompt", help="Prompt name (must match prompts/<name>.txt)")
parser.add_argument("--iterations", type=int, default=80)
parser.add_argument("--run", default=None,
    help="Run ID to group results (default: auto-generated from timestamp + model)")
parser.add_argument("--output-root", default=None,
    help="Override output base directory (default: openevolve/openevolve_output/)")
```

### Output Path Construction in run_experiment.py

```python
# Source: [VERIFIED: SCRIPT_DIR pattern from run_experiment.py:23,40]
output_root = args.output_root or os.path.join(SCRIPT_DIR, "openevolve_output")
config_path = os.path.join(SCRIPT_DIR, "config.yaml")
run_id = args.run or generate_run_id(config_path)
run_dir = os.path.join(output_root, "runs", run_id)
output_dir = os.path.join(run_dir, "cavitydetection", args.prompt)
os.makedirs(output_dir, exist_ok=True)
```

### load_all_results() — No Changes Needed

```python
# Source: [VERIFIED: results_loader.py:249 — os.walk already recursive]
for root, dirs, files in os.walk(results_root):
    if "results.json" in files:
        results_files.append(os.path.join(root, "results.json"))
# With results_root = openevolve_output/runs/, this finds:
# runs/legacy/cavitydetection/baseline/results.json
# runs/2026-05-14_1430_qwen3-coder-30b/cavitydetection/baseline/results.json
# etc.
```

The only change to `load_all_results()` needed is: callers pass `os.path.join(SCRIPT_DIR, "openevolve_output", "runs")` as `results_root` instead of just `openevolve_output`. Alternatively, the function's internal default can be updated.

### Adding run_id Column to DataFrame

```python
# Source: [ASSUMED] — needed for RUN= filtering in display scripts
# Parse run_id from file path: runs/<run_id>/cavitydetection/<prompt>/results.json
def load_results_with_run(filepath: str) -> pd.DataFrame:
    df = load_results(filepath)
    # Extract run_id from path
    parts = filepath.split(os.sep)
    try:
        runs_idx = parts.index("runs")
        run_id = parts[runs_idx + 1]
    except (ValueError, IndexError):
        run_id = "unknown"
    df["run_id"] = run_id
    return df
```

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Flat `openevolve_output/<prompt>/` | `openevolve_output/runs/<run_id>/cavitydetection/<prompt>/` | Phase 3 | Enables run grouping, filtering, experiment organization |
| `os.listdir()` discovery in show_results.py | Walk `runs/*/cavitydetection/*/results.json` | Phase 3 | Handles nested structure |
| No run-level metadata | `metadata.json` per run directory | Phase 3 | Single file summary of what ran |

---

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | Config snapshot stored as dict (not YAML string) in metadata.json | Pattern 3, Discretion | Low — either format is valid JSON; choice affects readability only |
| A2 | Makefile RUN_ID generated via Python helper (not shell sed) | Pattern 6, Discretion | Low — both produce correct output; shell approach avoids Python subprocess overhead |
| A3 | Legacy orphan dirs (best/, checkpoints/, logs/ at top-level) should be migrated alongside baseline/ and prompt1/ | Pitfall 6 | Medium — if left unmigrated, they remain as confusing entries; show_results.py could still trip over them |
| A4 | `load_all_results()` root path updated to `openevolve_output/runs/` rather than `openevolve_output/` | Code Examples | Medium — if root stays as `openevolve_output/`, legacy + new results still found, but run_id parsing from path is harder |

**If A3 is wrong:** Restrict migration to only `baseline/` and `prompt1/` as REQUIREMENTS.md specifies. Orphan dirs remain and can be cleaned manually.

---

## Open Questions

1. **Orphan top-level directories**
   - What we know: `openevolve_output/best/`, `openevolve_output/checkpoints/`, `openevolve_output/logs/` exist at the top level and were not created by named experiments
   - What's unclear: Should they be moved to `runs/legacy/cavitydetection/` (mixing them with experiment data) or to a separate `runs/legacy/_root_orphans/` directory?
   - Recommendation: Move all non-`runs/` directories to `runs/legacy/cavitydetection/` for simplicity. The `best/`, `checkpoints/`, `logs/` names won't conflict with any prompt name.

2. **metadata.json: write-once vs. append**
   - What we know: Each `run_experiment.py` invocation in `evolve-all` runs one prompt; only the last knows all prompts
   - What's unclear: Should `metadata.json` be written once by the Makefile (knowing all PROMPT_NAMES) or incrementally by each Python invocation?
   - Recommendation: Write from `run_experiment.py` using read-then-merge (appends current prompt to list). Simpler than coordinating from Makefile, and handles standalone `run_experiment.py` calls correctly.

3. **run_id for standalone run_experiment.py (D-07)**
   - What we know: Solo invocations auto-generate a run ID and create `runs/<auto-id>/cavitydetection/<prompt>/`
   - What's unclear: `metadata.json` would list only one prompt, but `programs` and `total_iterations` can still be accurate
   - Recommendation: Write `metadata.json` in all cases, whether solo or group run. Consistent behavior.

---

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Python 3.12 | All scripts | ✓ | 3.12.3 | — |
| pandas | show_consolidated.py, results_loader.py | ✓ | 3.0.3 | — |
| PyYAML | config loading, metadata.json write | ✓ | 6.0.3 | — |
| openevolve venv | All experiment scripts | ✓ | `/home/jolilius/home/src/openevolve/.venv/` | — |

[VERIFIED: direct venv inspection]

**All dependencies available.** No install steps needed for this phase.

---

## Validation Architecture

> `workflow.nyquist_validation` not set in config.json — treating as enabled.

### Test Framework

| Property | Value |
|----------|-------|
| Framework | pytest (via openevolve venv) or Python unittest |
| Config file | None present — run directly |
| Quick run command | `../openevolve/.venv/bin/python -m pytest openevolve/test_consolidation.py -x` |
| Full suite command | `../openevolve/.venv/bin/python -m pytest openevolve/ -x` |

Existing `openevolve/test_consolidation.py` provides a test baseline for this phase.

### Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| RUNORG-01 | `generate_run_id()` produces `YYYY-MM-DD_HHMM_<sanitized-model>` format | unit | `pytest openevolve/test_run_structure.py::test_run_id_format -x` | ❌ Wave 0 |
| RUNORG-01 | `--run <name>` accepted; overrides auto-generated ID | unit | `pytest openevolve/test_run_structure.py::test_run_arg_override -x` | ❌ Wave 0 |
| RUNORG-01 | `--output-root` overrides default output base | unit | `pytest openevolve/test_run_structure.py::test_output_root_override -x` | ❌ Wave 0 |
| RUNORG-02 | All prompts within one `evolve-all` share the same run_id directory | integration | `pytest openevolve/test_run_structure.py::test_evolve_all_shared_run -x` | ❌ Wave 0 |
| RUNORG-03 | `metadata.json` written with all required fields | unit | `pytest openevolve/test_run_structure.py::test_metadata_fields -x` | ❌ Wave 0 |
| MIGRATE-01 | Migration moves baseline/ and prompt1/ to runs/legacy/cavitydetection/ | unit | `pytest openevolve/test_run_structure.py::test_migration_moves -x` | ❌ Wave 0 |
| MIGRATE-01 | Migration is idempotent (re-run skips existing dirs) | unit | `pytest openevolve/test_run_structure.py::test_migration_idempotent -x` | ❌ Wave 0 |
| DISPLAY-01 | `show_results.py --run <id>` filters to one run only | unit | `pytest openevolve/test_run_structure.py::test_show_results_run_filter -x` | ❌ Wave 0 |
| DISPLAY-01 | `show_results.py` with no args shows all runs merged | unit | `pytest openevolve/test_run_structure.py::test_show_results_all -x` | ❌ Wave 0 |

### Sampling Rate

- **Per task commit:** `../openevolve/.venv/bin/python -m pytest openevolve/test_run_structure.py -x`
- **Per wave merge:** `../openevolve/.venv/bin/python -m pytest openevolve/ -x`
- **Phase gate:** Full suite green before `/gsd-verify-work`

### Wave 0 Gaps

- [ ] `openevolve/test_run_structure.py` — covers RUNORG-01 through MIGRATE-01 and DISPLAY-01
- [ ] Shared fixtures (tmp dir, mock config.yaml, mock experiment output dirs)

---

## Security Domain

> `security_enforcement` not set in config.json — treating as enabled. Reviewed for ASVS applicability.

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | No | Not applicable — local CLI tool, no auth |
| V3 Session Management | No | Not applicable |
| V4 Access Control | No | Local filesystem only |
| V5 Input Validation | Yes (limited) | `--run` and `--output-root` args from CLI; validate no path traversal in run ID |
| V6 Cryptography | No | Not applicable |

### Known Threat Patterns

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| Path traversal via `--run` arg (e.g., `--run ../../etc`) | Tampering | Validate run ID matches `[a-zA-Z0-9_-]+` pattern; reject if it contains `/` or `..` |
| Path traversal via `--output-root` | Tampering | `os.path.abspath()` + confirm within expected tree; researcher-only tool so risk is very low |

**Risk assessment:** Very low. This is a single-researcher local tool. Validation is a best practice, not a hard security requirement.

---

## Sources

### Primary (HIGH confidence)

- [VERIFIED: run_experiment.py] — Current CLI args, output path, consolidate call pattern
- [VERIFIED: Makefile] — `evolve-all` target structure, `show-results` target, OPENEVOLVE_PYTHON variable
- [VERIFIED: consolidate_results.py] — `consolidate_experiment()` signature, output_dir semantics
- [VERIFIED: results_loader.py] — `load_all_results()` uses `os.walk()` recursively
- [VERIFIED: show_results.py] — `os.listdir(OUTPUT_ROOT)` discovery pattern (the part that breaks with new layout)
- [VERIFIED: show_consolidated.py] — uses `load_all_results()` with SCRIPT_DIR-based path
- [VERIFIED: config.yaml] — current `primary_model: "qwen3-coder:30b"`, `checkpoint_interval: 5`
- [VERIFIED: filesystem check] — `openevolve_output/` on `/dev/nvme0n1p2`; `os.rename()` is atomic
- [VERIFIED: venv check] — pandas 3.0.3, PyYAML 6.0.3 installed in `/home/jolilius/home/src/openevolve/.venv/`
- [VERIFIED: Python regex test] — model sanitization produces expected output
- [VERIFIED: `ls openevolve_output/`] — five subdirectories: `baseline/`, `best/`, `checkpoints/`, `logs/`, `prompt1/`

### Secondary (MEDIUM confidence)

- [VERIFIED: v1.0-MILESTONE-AUDIT.md] — known integration bugs from previous milestone; confirmed pandas issue was an audit path error, not a real gap

### Tertiary (LOW confidence)

- None

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — all verified by direct inspection
- Architecture: HIGH — all source files read and analyzed
- Pitfalls: HIGH — sourced from actual code behavior observed during research
- Migration scope: HIGH — actual directory listing confirmed

**Research date:** 2026-05-14
**Valid until:** 2026-06-14 (stable Python stdlib + no new dependency churn)

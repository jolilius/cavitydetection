# Phase 3: Experiment Run Structure - Pattern Map

**Mapped:** 2026-05-14
**Files analyzed:** 5 (4 modified + 1 new)
**Analogs found:** 5 / 5

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|-------------------|------|-----------|----------------|---------------|
| `openevolve/run_experiment.py` | utility/runner | request-response (CLI → subprocess → filesystem) | `openevolve/run_experiment.py` (self — extend) | self |
| `openevolve/show_results.py` | utility/display | batch (filesystem walk → table) | `openevolve/show_consolidated.py` | exact role+flow |
| `openevolve/show_consolidated.py` | utility/display | batch (filesystem walk → table) | `openevolve/show_results.py` | exact role+flow |
| `openevolve/migrate_legacy.py` | utility/migration | batch (filesystem rename) | `openevolve/test_consolidation.py` (tempdir + os ops) | partial |
| `openevolve/test_run_structure.py` | test | batch (tmpdir fixtures + assertions) | `openevolve/test_consolidation.py` | exact |
| `Makefile` | config | event-driven (shell targets) | `Makefile` (self — extend) | self |

---

## Pattern Assignments

### `openevolve/run_experiment.py` (extend — CLI runner)

**Analog:** `openevolve/run_experiment.py` (current file, lines 1–219)

**Imports pattern** (lines 1–22):
```python
#!/usr/bin/env python3
import argparse
import json
import os
import subprocess
import sys
import tempfile
import time

import yaml

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
```

**New imports to add** (after existing imports):
```python
import re
from datetime import datetime
```

**SCRIPT_DIR / path construction pattern** (lines 23, 40–41):
```python
SCRIPT_DIR   = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
OPENEVOLVE   = os.path.join(PROJECT_ROOT, "..", "openevolve")
```

**argparse pattern** (lines 114–118) — copy and extend:
```python
def main():
    parser = argparse.ArgumentParser(description="Run one prompt experiment")
    parser.add_argument("prompt", help="Prompt name (must match prompts/<name>.txt)")
    parser.add_argument("--iterations", type=int, default=80)
    args = parser.parse_args()
```
Add `--run` and `--output-root` after `--iterations` following the same `add_argument()` style.

**Output dir construction pattern** (line 132–133) — replace with new path logic:
```python
# CURRENT (replace this):
output_dir = os.path.join(SCRIPT_DIR, "openevolve_output", args.prompt)
os.makedirs(output_dir, exist_ok=True)
```
New pattern follows the same `os.path.join()` + `os.makedirs(..., exist_ok=True)` idiom.

**Config load pattern** (lines 127–130) — keep verbatim, reuse `config` dict for metadata:
```python
with open(os.path.join(SCRIPT_DIR, "config.yaml")) as f:
    config = yaml.safe_load(f)
config["prompt"]["system_message"] = prompt_text
```

**Error handling / non-blocking pattern** (lines 195–212):
```python
try:
    result = consolidate_experiment(
        output_dir=output_dir,
        ...
    )
    ...
except Exception as e:
    print(f"Warning: Could not consolidate results: {e}")
    # Non-blocking; experiment succeeded even if consolidation fails
```
Use the same try/except + `print(f"Warning: ...")` + non-blocking pattern for `write_run_metadata()` call.

**New function: `generate_run_id`** — place before `main()`, same style as `_generate_explanations_for_experiment()`:
```python
def generate_run_id(config_path: str) -> str:
    """Generate run ID from current timestamp and model name from config."""
    ts = datetime.now().strftime("%Y-%m-%d_%H%M")
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

**New function: `write_run_metadata`** — place before `main()`, same docstring style as existing helpers:
```python
def write_run_metadata(run_dir: str, config: dict, run_id: str,
                       iterations: int, prompt: str) -> None:
    """Write (or merge) metadata.json in the run directory."""
    meta_path = os.path.join(run_dir, "metadata.json")
    existing = {}
    if os.path.isfile(meta_path):
        with open(meta_path) as f:
            existing = json.load(f)
    prompts_so_far = existing.get("prompts", [])
    if prompt not in prompts_so_far:
        prompts_so_far.append(prompt)
    start_ts = existing.get("start_timestamp",
                            datetime.now(timezone.utc).isoformat())
    metadata = {
        "run_id": run_id,
        "model": config.get("llm", {}).get("primary_model", "unknown"),
        "total_iterations": iterations,
        "programs": ["cavitydetection"],
        "prompts": prompts_so_far,
        "config_snapshot": config,
        "start_timestamp": start_ts,
    }
    os.makedirs(run_dir, exist_ok=True)
    with open(meta_path, "w") as f:
        json.dump(metadata, f, indent=2)
```

---

### `openevolve/show_results.py` (modify — display script)

**Analog:** `openevolve/show_consolidated.py` (lines 1–68) + self (lines 1–131)

**Imports and SCRIPT_DIR pattern** (show_results.py lines 19–26):
```python
import argparse
import json
import os
import sys

SCRIPT_DIR         = os.path.dirname(os.path.abspath(__file__))
OUTPUT_ROOT        = os.path.join(SCRIPT_DIR, "openevolve_output")
REFERENCE_ACCESSES = 128_862_705
```

**argparse pattern — add `--run`** (lines 85–88):
```python
def main():
    parser = argparse.ArgumentParser(description="Show experiment results (best per prompt)")
    parser.add_argument("--verbose", action="store_true", help="Show data format used")
    args = parser.parse_args()
```
Add `parser.add_argument("--run", default=None, help="Filter to a specific run ID")` before `parse_args()`.

**Discovery pattern to replace** (lines 90–98 — the `os.listdir` loop that breaks after migration):
```python
# CURRENT — replace entirely:
for name in sorted(os.listdir(OUTPUT_ROOT)):
    result = load_result(name)
    if result:
        rows.append(result)
```
Replacement uses `glob.glob` or a walk over `runs/*/cavitydetection/*/results.json`. Import `glob` at the top.

**`load_consolidated_result` pattern** (lines 29–47) — the path-based result loader to adapt for new nested path:
```python
def load_consolidated_result(prompt_name: str) -> dict | None:
    """Try to load consolidated results.json"""
    try:
        from results_loader import load_results
        results_path = os.path.join(OUTPUT_ROOT, prompt_name, "results.json")
        if os.path.isfile(results_path):
            df = load_results(results_path)
            ...
    except Exception:
        pass
    return None
```
New version receives `(results_path, prompt_name, run_id)` or equivalent; path is now passed in rather than constructed from `OUTPUT_ROOT + prompt_name`.

**Table printing pattern** (lines 106–121) — keep verbatim:
```python
rows.sort(key=lambda r: r["mem_score"], reverse=True)
col_w = max(len(r["prompt"]) for r in rows)
col_w = max(col_w, 6)
header = f"{'prompt':<{col_w}}  {'mem_score':>9}  {'iter_found':>10}  {'accesses':>13}  {'reduction':>9}"
print(header)
print("-" * len(header))
for r in rows:
    ...
    print(f"{r['prompt']:<{col_w}}  {r['mem_score']:>9.4f}  ...")
```

**Error guard pattern** (lines 90–92):
```python
if not os.path.isdir(OUTPUT_ROOT):
    print("No results yet — run  make evolve-all  first.")
    return
```
Keep this guard; also add a guard for when `runs/` subdirectory does not exist yet.

---

### `openevolve/show_consolidated.py` (modify — display script)

**Analog:** `openevolve/show_consolidated.py` (self, lines 1–68)

**Imports and SCRIPT_DIR pattern** (lines 17–24):
```python
import os
import sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SCRIPT_DIR)

from results_loader import load_all_results
```
Add `import argparse` and `import re` (for path parsing).

**`load_all_results` call pattern** (lines 28–30):
```python
results_root = os.path.join(SCRIPT_DIR, "openevolve_output")
df = load_all_results(results_root)
```
After migration the root passed should be `openevolve_output/runs/` so `os.walk` finds all `results.json` under the new nested layout. Update `results_root` to `os.path.join(SCRIPT_DIR, "openevolve_output", "runs")`.

**`run_id` column extraction** — new helper to add before `main()`, follows the `load_all_results` call:
```python
# Parse run_id from filepath: runs/<run_id>/cavitydetection/<prompt>/results.json
def extract_run_id(filepath: str) -> str:
    parts = filepath.replace("\\", "/").split("/")
    try:
        runs_idx = parts.index("runs")
        return parts[runs_idx + 1]
    except (ValueError, IndexError):
        return "unknown"
```
After `load_all_results()`, add a `df["run_id"]` column by mapping each source filepath through this helper. Since `load_all_results` does not expose filepaths in the returned DataFrame, the simplest approach is to extend `load_all_results` or load results manually at the call site in `show_consolidated.py`.

**Groupby and table pattern** (lines 36–60) — keep verbatim:
```python
for prompt in sorted(df['prompt'].unique()):
    subset = df[df['prompt'] == prompt]
    best_row = subset[subset['memory_accesses'] == subset['memory_accesses'].min()].iloc[0]
    results.append({...})
results.sort(key=lambda r: r['improvement_percent'], reverse=True)
header = f"{'prompt':<15}  {'best_accesses':>13}  ..."
print(header)
print("-" * len(header))
for r in results:
    print(f"{r['prompt']:<15}  {r['best_accesses']:>13,}  ...")
```
Add `--run` filter as a `df = df[df['run_id'] == args.run]` step after the DataFrame is loaded and `run_id` column is present.

**Error handling pattern** (lines 62–64):
```python
except Exception as e:
    print(f"Error: {e}", file=sys.stderr)
    sys.exit(1)
```
Keep verbatim.

---

### `openevolve/migrate_legacy.py` (new file — migration script)

**Analog:** `openevolve/test_consolidation.py` (for os + tempfile + path patterns, lines 1–30)

**File header and SCRIPT_DIR pattern** (test_consolidation.py lines 1–27):
```python
#!/usr/bin/env python3
"""
<docstring>
"""

import json
import os
import sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
```
Follow the same shebang + triple-quote module docstring + stdlib imports pattern.

**Imports for migrate_legacy.py** — stdlib only:
```python
#!/usr/bin/env python3
"""
Migrate legacy flat experiment directories to the new runs/ structure.

Usage (from project root):
    ../openevolve/.venv/bin/python openevolve/migrate_legacy.py [--output-root PATH]

Idempotent: already-migrated directories are skipped without error.
"""

import argparse
import os
import sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
```

**Migration core pattern** — from RESEARCH.md Pattern 4 (no existing code analog, use stdlib os.rename):
```python
def migrate_legacy(output_root: str) -> None:
    """Move top-level experiment dirs to runs/legacy/cavitydetection/."""
    legacy_dir = os.path.join(output_root, "runs", "legacy", "cavitydetection")
    os.makedirs(legacy_dir, exist_ok=True)

    skip = {"runs"}
    for name in sorted(os.listdir(output_root)):
        if name in skip:
            continue
        src = os.path.join(output_root, name)
        if not os.path.isdir(src):
            continue
        dst = os.path.join(legacy_dir, name)
        if os.path.exists(dst):
            print(f"Skip (already migrated): {name}")
            continue
        os.rename(src, dst)
        print(f"Moved: {name} -> runs/legacy/cavitydetection/{name}")
```

**argparse `--output-root` pattern** — mirrors `run_experiment.py` new `--output-root` arg:
```python
def main():
    parser = argparse.ArgumentParser(description="Migrate legacy experiment output")
    parser.add_argument(
        "--output-root",
        default=os.path.join(SCRIPT_DIR, "openevolve_output"),
        help="Base output directory to migrate (default: openevolve/openevolve_output/)",
    )
    args = parser.parse_args()
    migrate_legacy(args.output_root)

if __name__ == "__main__":
    main()
```

---

### `openevolve/test_run_structure.py` (new file — test suite)

**Analog:** `openevolve/test_consolidation.py` (lines 1–403) — exact role and flow match

**File header pattern** (lines 1–17):
```python
#!/usr/bin/env python3
"""
<one-line summary of what is tested>

Usage:
    python openevolve/test_run_structure.py
    # or via pytest:
    ../openevolve/.venv/bin/python -m pytest openevolve/test_run_structure.py -x
"""

import json
import os
import sys
import tempfile

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SCRIPT_DIR)
```

**Synthetic data + tempdir pattern** (lines 29–57):
```python
def test_<name>():
    """<one-line description>."""
    from <module> import <function>

    with tempfile.TemporaryDirectory() as tmpdir:
        # Setup: create minimal directory/file structure
        os.makedirs(os.path.join(tmpdir, "subdir"), exist_ok=True)
        with open(os.path.join(tmpdir, "subdir", "file.json"), "w") as f:
            json.dump({...}, f)

        # Exercise
        result = <function>(tmpdir, ...)

        # Assert
        assert "field" in result, "Missing field"
        assert result["field"] == expected_value
        print("✓ test_<name> passed")
```

**`__main__` runner pattern** (lines 379–402):
```python
if __name__ == "__main__":
    try:
        test_one()
        test_two()
        ...
        print("\n✅ All tests passed")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Test failed: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)
```

**Mock config.yaml pattern** — new fixture not in existing test, but follows json.dump style:
```python
def _write_mock_config(tmpdir: str, model: str = "qwen3-coder:30b") -> str:
    """Write a minimal config.yaml for testing."""
    import yaml
    config = {"llm": {"primary_model": model}, "prompt": {"system_message": ""}}
    config_path = os.path.join(tmpdir, "config.yaml")
    with open(config_path, "w") as f:
        yaml.dump(config, f)
    return config_path
```

---

### `Makefile` (modify — build config)

**Analog:** `Makefile` (self, lines 152–198)

**Variable definitions pattern** (lines 152–155):
```makefile
OPENEVOLVE_PYTHON = ../openevolve/.venv/bin/python
OPENEVOLVE_RUN    = ../openevolve/openevolve-run.py
PROMPTS           = $(wildcard openevolve/prompts/*.txt)
PROMPT_NAMES      = $(basename $(notdir $(PROMPTS)))
```
No change to these. New `evolve-all` needs to read `OPENEVOLVE_PYTHON` and `PROMPT_NAMES`.

**`evolve-all` current pattern** (lines 163–172):
```makefile
evolve-all:
	@echo "Running all prompt variants (explanations enabled by default)..."
	@echo "Running experiments for prompts: $(PROMPT_NAMES)"
	@for p in $(PROMPT_NAMES); do \
		echo ""; \
		echo "=== Experiment: $$p ==="; \
		$(OPENEVOLVE_PYTHON) openevolve/run_experiment.py $$p \
			--iterations $${ITERATIONS:-80}; \
	done
```
Replace with a version that generates `RUN_ID` once before the loop using the Python helper approach (Option B from RESEARCH.md). The `$$` shell escaping and `$${VAR:-default}` syntax are established in this Makefile — keep consistent.

**`show-results` current pattern** (lines 190–191):
```makefile
show-results:
	$(OPENEVOLVE_PYTHON) openevolve/show_results.py
```
Extend with `$(if $(RUN),--run $(RUN),)` — same GNU Make conditional expansion as is already used elsewhere in Makefile recipes.

**`show-consolidated-results` current pattern** (lines 193–194):
```makefile
show-consolidated-results:
	$(OPENEVOLVE_PYTHON) openevolve/show_consolidated.py
```
Same `$(if $(RUN),--run $(RUN),)` addition.

**`.PHONY` pattern** (line 198):
```makefile
.PHONY: all clean run profile memtrace evolve evolve-all show-results show-consolidated-results ...
```
Add any new make targets to `.PHONY`.

---

## Shared Patterns

### SCRIPT_DIR / Path Construction
**Source:** `openevolve/run_experiment.py` lines 23, 40–41; `openevolve/show_results.py` lines 24–25
**Apply to:** All Python files (run_experiment.py, show_results.py, show_consolidated.py, migrate_legacy.py, test_run_structure.py)
```python
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
# Derived paths always use os.path.join(SCRIPT_DIR, ...)
```

### Config Loading
**Source:** `openevolve/run_experiment.py` lines 127–130
**Apply to:** `run_experiment.py` (already present), `test_run_structure.py` (mock version)
```python
with open(os.path.join(SCRIPT_DIR, "config.yaml")) as f:
    config = yaml.safe_load(f)
```

### Non-Blocking Warning Pattern
**Source:** `openevolve/run_experiment.py` lines 195–212
**Apply to:** `run_experiment.py` for `write_run_metadata()` call
```python
try:
    <operation>
except Exception as e:
    print(f"Warning: <description>: {e}", file=sys.stderr)
    # Non-blocking; experiment succeeded even if <operation> fails
```

### JSON Read + Write Pattern
**Source:** `openevolve/run_experiment.py` lines 84–87, 205–209; `openevolve/results_loader.py` lines 127–128
**Apply to:** `run_experiment.py` (metadata.json write), `migrate_legacy.py` (none needed), `test_run_structure.py` (fixture setup)
```python
# Read
with open(path) as f:
    data = json.load(f)
# Write
with open(path, "w") as f:
    json.dump(data, f, indent=2)
```

### os.makedirs + exist_ok Pattern
**Source:** `openevolve/run_experiment.py` line 133; `openevolve/test_consolidation.py` line 36
**Apply to:** All files that create directories (run_experiment.py, migrate_legacy.py, test_run_structure.py)
```python
os.makedirs(some_dir, exist_ok=True)
```

### argparse Pattern
**Source:** `openevolve/run_experiment.py` lines 114–118; `openevolve/show_results.py` lines 86–88
**Apply to:** run_experiment.py (add `--run`, `--output-root`), show_results.py (add `--run`), show_consolidated.py (add `--run`), migrate_legacy.py (add `--output-root`)
```python
parser = argparse.ArgumentParser(description="...")
parser.add_argument("--flag", default=None, help="Description (default: ...)")
args = parser.parse_args()
```

### `load_all_results()` — No Change
**Source:** `openevolve/results_loader.py` lines 249–251
**Apply to:** `show_consolidated.py` — call site changes root path; function body unchanged
```python
for root, dirs, files in os.walk(results_root):
    if "results.json" in files:
        results_files.append(os.path.join(root, "results.json"))
```
After the run layout change, callers pass `openevolve_output/runs/` as `results_root` and `os.walk` automatically descends into `<run_id>/cavitydetection/<prompt>/` without any changes to the function.

---

## No Analog Found

All files in this phase have close analogs within the codebase. No files require falling back to RESEARCH.md patterns exclusively.

---

## Metadata

**Analog search scope:** `openevolve/` directory (all `.py` files), `Makefile`
**Files scanned:** 6 (run_experiment.py, show_results.py, show_consolidated.py, results_loader.py, test_consolidation.py, Makefile)
**Pattern extraction date:** 2026-05-14

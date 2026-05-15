---
phase: 04-per-step-data-pipeline
audit_mode: RETROACTIVE-STRIDE
asvs_level: L1
block_on: critical
audited_at: 2026-05-15
status: OPEN_THREATS
threats_total: 10
threats_closed: 7
threats_open: 3
---

# Phase 04 — Security Audit Report

**Mode:** RETROACTIVE-STRIDE (no pre-existing threat model; register built from implementation)
**ASVS Level:** L1
**Block On:** critical
**Result:** OPEN_THREATS — 2 BLOCKERS, 1 WARNING open

---

## STRIDE Threat Register

Threats derived from implementation analysis of: `consolidate_results.py`, `results_loader.py`, `run_experiment.py`, `migrate_legacy.py`, and their test suites.

---

## Closed Threats

| Threat ID | STRIDE | Category | Disposition | Evidence |
|-----------|--------|----------|-------------|----------|
| T-01 | Tampering | Checkpoint dir name injection via non-integer suffix | mitigate | `consolidate_results.py:203` — `int(d.replace("checkpoint_", ""))` raises `ValueError` on non-integer suffix; directory is skipped by the `startswith("checkpoint_")` filter at line 200. No un-sanitized directory name reaches the filesystem as a path component beyond `checkpoints_dir`. |
| T-03 | Tampering | `results.json` overwritten without rollback option | mitigate | `migrate_legacy.py:87` — `shutil.copy2(results_path, backup_path)` executes before `consolidate_experiment()` call at line 91. D-10 disposition honored. Byte-for-byte fidelity verified by `test_regenerate_flag` in `test_run_structure.py:412-414`. |
| T-04 | Tampering | Checkpoint dirs without required files cause pipeline crash | mitigate | `consolidate_results.py:213-224` — `isfile` guard skips incomplete checkpoints with stderr warning; `try/except (IOError, json.JSONDecodeError)` wraps both file reads. Same pattern in `run_experiment.py:104-114`. |
| D-01 | DoS | Malformed checkpoint JSON crashes consolidation | mitigate | `consolidate_results.py:217-224` — `json.load` wrapped in `try/except (IOError, json.JSONDecodeError)`, prints warning to stderr and `continue`s. |
| I-02 | Info Disclosure | LLM API endpoint leaks via results.json (config snapshot in metadata.json) | accept | `metadata.json` written by `write_run_metadata` at `run_experiment.py:149-176` includes `config_snapshot` which contains the full YAML config including `llm.api_base`. This is local-only data; no network export path exists. Accepted: internal research tool with no multi-user or remote-access surface. |
| R-01 | Repudiation | Regeneration overwrites experiment history without audit trail | mitigate | `migrate_legacy.py:84-88` — `results.json.v1` backup created via `shutil.copy2` before any overwrite. Backup name is fixed (not timestamped), so only one generation of backup is retained. Accepted limitation documented in Plan 04-03. |
| S-01 | Spoofing | No authentication boundary | accept | This is a local CLI tool with no network endpoints, no authentication, and no multi-user model. Spoofing is not a relevant threat at this trust boundary. |

---

## Open Threats (BLOCKERS)

### OPEN-01 — CR-01: `--run` path traversal bypasses `runs/` containment

| Field | Value |
|-------|-------|
| **Threat ID** | OPEN-01 |
| **STRIDE** | Tampering / Elevation |
| **Severity** | BLOCKER |
| **File** | `openevolve/run_experiment.py:207-209` |
| **Mitigation Expected** | `--run` value validated to alphanumeric+underscore+hyphen, OR path guard checks `startswith(output_root/runs/)` |
| **Evidence of Mitigation** | ABSENT |

**Proof of absence:**

Line 189 applies the alphanumeric regex only to `args.prompt`:
```
if not re.match(r'^[a-zA-Z0-9_-]+$', args.prompt):
```

No equivalent validation exists for `args.run`. The guard at line 208:
```python
if not os.path.abspath(run_dir).startswith(os.path.abspath(output_root)):
```
checks against `output_root`, NOT `output_root/runs/`. With `--run ../evil`:
- `run_dir` = `output_root/runs/../evil` = `output_root/evil` (after abspath)
- `output_root/evil`.startswith(`output_root`) = **True** — guard passes
- Experiment data is written to `output_root/evil/`, escaping the `runs/` tree

**Impact:** An operator running `run_experiment.py baseline --run ../../somewhere` can cause `metadata.json`, `results.json`, and checkpoint data to be written to arbitrary paths within the filesystem subtree that `output_root` is a prefix of (including sibling directories). On a shared workstation this could overwrite other users' data.

**Required fix before ship:** Apply the same regex to `args.run` when provided, or change the guard to `startswith(os.path.abspath(output_root) + os.sep + "runs" + os.sep)`.

---

### OPEN-02 — CR-02: Falsy `or`-chain silently replaces `mem_score=0.0` with `1.0`

| Field | Value |
|-------|-------|
| **Threat ID** | OPEN-02 |
| **STRIDE** | Tampering (data integrity) |
| **Severity** | BLOCKER |
| **File** | `openevolve/consolidate_results.py:227` |
| **Mitigation Expected** | `None`-aware fallback chain that preserves `0.0` as a valid score |
| **Evidence of Mitigation** | ABSENT |

**Proof of absence:**

Line 227 reads:
```python
mem_score = metrics.get("mem_score") or metrics.get("combined_score") or 1.0
```

Python's `or` operator treats `0.0` as falsy. When `metrics["mem_score"] == 0.0` (valid: candidate instrumented binary reported zero accesses, e.g., compilation failure with exit 0), the chain skips to `metrics.get("combined_score")`, then to `1.0`. The checkpoint is recorded as scoring `1.0` (baseline performance) rather than `0.0` (catastrophic failure), silently discarding a meaningful data point.

**Impact:** A failing candidate is indistinguishable from the baseline in `results.json`. Convergence analysis, best-result selection, and comparison reports are silently corrupted for any run that produces a zero-score checkpoint.

**Required fix before ship:** Replace with a `None`-aware check:
```python
mem_score = (
    metrics.get("mem_score")
    if metrics.get("mem_score") is not None
    else metrics.get("combined_score")
    if metrics.get("combined_score") is not None
    else 1.0
)
```

---

## Open Threats (WARNINGS — not blockers at `block_on: critical`)

### OPEN-03 — WR-03: Temp config YAML placed in source tree; leaks on `yaml.dump` failure

| Field | Value |
|-------|-------|
| **Threat ID** | OPEN-03 |
| **STRIDE** | Information Disclosure |
| **Severity** | WARNING |
| **File** | `openevolve/run_experiment.py:235-241` |
| **Mitigation Expected** | Temp file written to `tempfile.gettempdir()`, and its creation covered by the `try/finally` cleanup block |
| **Evidence of Mitigation** | ABSENT |

**Proof of absence:**

Line 236: `dir=SCRIPT_DIR` places `.tmp_config_*.yaml` inside `openevolve/` (the source tree).
The `with tempfile.NamedTemporaryFile(...)` block at lines 235-239 is **outside** the `try/finally` block which begins at line 241. If `yaml.dump` raises (e.g., non-serializable config value), the temp file exists on disk in `SCRIPT_DIR` and is never unlinked. The `finally: os.unlink(tmp_config)` at line 298 never executes because `yaml.dump` failure raises before `try:` on line 241 is reached.

**Impact:** Config YAML containing `llm.api_base` (Ollama endpoint URL, potentially an authenticated remote host) leaks into `openevolve/` as `.tmp_config_*.yaml`, appears in `git status`, and persists until manual cleanup. On a shared machine, readable by other local users.

**Recommended fix:** Use `tempfile.gettempdir()` for `dir=`, and wrap the `NamedTemporaryFile` creation inside the `try` block so `finally` covers cleanup.

---

## Unregistered Flags

The following items were flagged in `04-02-SUMMARY.md ## Threat Flags`:

> "None — this plan modifies only the explanation generation helper function... No new network endpoints, auth paths, file access patterns, or schema changes at trust boundaries were introduced."

No unregistered flags from `## Threat Flags` sections in any SUMMARY.md.

Additional threats surfaced during audit (not present in any SUMMARY.md Threat Flags):

| Flag ID | Source | Description | Mapping |
|---------|--------|-------------|---------|
| UF-01 | `run_experiment.py:236` (WR-03) | Temp config file in source tree | Registered as OPEN-03 above |
| UF-02 | `consolidate_results.py:99` (WR-01) | `convergence_iteration` uses backward-compat alias instead of `best_found_at_iteration` — semantic metadata error, not a security threat | INFO only; no security impact |
| UF-03 | `run_experiment.py:125` (WR-02) | Empty-string explanations stored inconsistently vs. `None` explanations | INFO only; data quality, not a security threat |
| UF-04 | `test_run_structure.py:220-235` (IN-03) | Test helper `_write_minimal_results_json` writes invalid schema (list, not dict) | Test code; no production impact |

---

## Accepted Risks Log

| Risk ID | Description | Rationale | Accepted By |
|---------|-------------|-----------|-------------|
| S-01 | No authentication — local CLI only | Tool has no network listener, no multi-user model, and no remote API surface. Authentication is out of scope. | Architecture (local-only tool) |
| I-02 | `config_snapshot` in `metadata.json` contains LLM API endpoint URL | File is written to local experiment output directory. No network export path. Operator controls the directory. | Local research context |
| R-01 | `results.json.v1` backup retains only one generation (no timestamp rotation) | Sufficient for the single-upgrade-path use case described in Plan 04-03. Multi-generation history is a future enhancement. | Plan 04-03 design decision |

---

## Verification Evidence

All grep matches confirmed against implementation files as of audit date 2026-05-15.

**CR-01 path traversal — confirmed exploitable:**
```
python3 -c "
import os
output_root = '/home/user/openevolve_output'
run_id = '../evil'
run_dir = os.path.join(output_root, 'runs', run_id)
print(os.path.abspath(run_dir).startswith(os.path.abspath(output_root)))  # True
"
# Outputs: True — guard passes for traversal input
```

**CR-02 falsy or-chain — confirmed present:**
`consolidate_results.py:227`: `mem_score = metrics.get("mem_score") or metrics.get("combined_score") or 1.0`
No `is not None` guard. Confirmed unchanged from code review finding.

**D-10 backup-before-overwrite — confirmed present:**
`migrate_legacy.py:87`: `shutil.copy2(results_path, backup_path)` precedes `consolidate_experiment()` at line 91.

**EXPLAIN_GENERATIONS gate — confirmed present:**
`run_experiment.py:256`: `explanations_enabled = os.environ.get("EXPLAIN_GENERATIONS", "1") != "0"`

**Checkpoint numeric sort — confirmed present:**
`consolidate_results.py:203`: `dirs.sort(key=lambda d: int(d.replace("checkpoint_", "")))`
`run_experiment.py:91`: `key=lambda d: int(d.replace("checkpoint_", ""))`

---

## Next Steps

1. **OPEN-01 (BLOCKER):** Add `if args.run is not None and not re.match(r'^[a-zA-Z0-9_-]+$', args.run): sys.exit(...)` at `run_experiment.py` before line 207. Then re-audit.
2. **OPEN-02 (BLOCKER):** Replace falsy `or`-chain at `consolidate_results.py:227` with `None`-aware check. Then re-audit.
3. **OPEN-03 (WARNING):** Move `dir=SCRIPT_DIR` to `tempfile.gettempdir()` and restructure the `NamedTemporaryFile` + `try/finally` to ensure cleanup on all failure paths.
4. Re-run `/gsd-secure-phase` after implementing mitigations.

---
phase: 04-per-step-data-pipeline
audit_mode: RETROACTIVE-STRIDE
asvs_level: L1
block_on: critical
audited_at: 2026-05-15
reaudited_at: 2026-05-15
status: SECURED
threats_total: 10
threats_closed: 10
threats_open: 0
---

# Phase 04 — Security Audit Report

**Mode:** RETROACTIVE-STRIDE (no pre-existing threat model; register built from implementation)
**ASVS Level:** L1
**Block On:** critical
**Result:** SECURED — all 10 threats closed; 0 open

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
| CR-01 | Tampering/Elevation | `--run` path traversal bypasses `runs/` containment | mitigate | `run_experiment.py:205` — `re.match(r'^[a-zA-Z0-9_-]+$', args.run)` rejects traversal chars. `run_experiment.py:211-213` — guard constructs `runs_dir = os.path.join(os.path.abspath(output_root), "runs") + os.sep` and checks `os.path.abspath(run_dir).startswith(runs_dir)`, binding containment to `runs/` with trailing separator. Both conditions of declared fix verified present. Re-audit 2026-05-15. |
| CR-02 | Tampering (data integrity) | Falsy `or`-chain silently replaces `mem_score=0.0` with `1.0` | mitigate | `consolidate_results.py:227-229` — falsy or-chain replaced by explicit `None`-check: `_ms = metrics.get("mem_score"); _cs = metrics.get("combined_score"); mem_score = _ms if _ms is not None else (_cs if _cs is not None else 1.0)`. `0.0` is preserved as a valid score. Re-audit 2026-05-15. |
| WR-03 | Info Disclosure | Temp config YAML placed in source tree; leaks on `yaml.dump` failure | mitigate | `run_experiment.py:239` — `tempfile.mkstemp(suffix=".yaml", prefix=".tmp_config_")` with no `dir=` argument (uses system tmpdir, not `SCRIPT_DIR`). `tmp_config` bound before `try:` at line 240; `yaml.dump` executes inside try; `finally` at lines 299-301 guards `os.path.exists(tmp_config)` before `os.unlink`. All failure paths covered. Re-audit 2026-05-15. |

---

## Formerly Open Threats — CLOSED by re-audit 2026-05-15

All three threats that were OPEN in the original audit (2026-05-15) have been remediated and verified closed in the re-audit (2026-05-15).

### CR-01 — `--run` path traversal (was OPEN-01, BLOCKER) — NOW CLOSED

**Commits fixing this:** fa3f3a1

**Verification (re-audit 2026-05-15):**

`run_experiment.py:205`: `if args.run is not None and not re.match(r'^[a-zA-Z0-9_-]+$', args.run):` — regex rejects traversal characters (`..`, `/`, etc.) in `--run` value. `sys.exit` called on violation.

`run_experiment.py:211-213`:
```python
runs_dir = os.path.join(os.path.abspath(output_root), "runs") + os.sep
if not os.path.abspath(run_dir).startswith(runs_dir):
    sys.exit(f"Error: --run value escapes the runs/ directory: {run_id}")
```
Guard now checks against `output_root/runs/` with trailing `os.sep` — the previously exploitable `../evil` bypass is eliminated. With the regex gate, no `..` characters can reach the path guard anyway. Defense in depth: both layers present.

**Status: CLOSED**

---

### CR-02 — Falsy `or`-chain replacing `mem_score=0.0` (was OPEN-02, BLOCKER) — NOW CLOSED

**Commits fixing this:** 2fa6fb8

**Verification (re-audit 2026-05-15):**

`consolidate_results.py:227-229`:
```python
_ms = metrics.get("mem_score")
_cs = metrics.get("combined_score")
mem_score = _ms if _ms is not None else (_cs if _cs is not None else 1.0)
```
Falsy `or`-chain entirely removed. Explicit `is not None` guards preserve `0.0` as a valid score distinct from absent key. Pattern applied to both `mem_score` and `combined_score` fallback.

**Status: CLOSED**

---

### WR-03 — Temp config in source tree / cleanup gap (was OPEN-03, WARNING) — NOW CLOSED

**Commits fixing this:** cb1e2d2

**Verification (re-audit 2026-05-15):**

`run_experiment.py:239`: `tmp_fd, tmp_config = tempfile.mkstemp(suffix=".yaml", prefix=".tmp_config_")` — `mkstemp` with no `dir=` argument; resolves to `tempfile.gettempdir()` (system tmpdir), not `SCRIPT_DIR`.

`run_experiment.py:239-301` structure: `tmp_config` binding at line 239 precedes `try:` at line 240. `yaml.dump` executes inside `try` at line 242. `finally:` at lines 299-301 guards `os.path.exists(tmp_config)` before `os.unlink(tmp_config)`. All failure paths (including `yaml.dump` exception) result in cleanup.

**Status: CLOSED**

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

All previously-open threats are now closed. No outstanding required actions for this phase.

Future hardening (optional, non-blocking):
- UF-02: Align `convergence_iteration` alias with `best_found_at_iteration` field name for schema consistency.
- UF-03: Standardize empty-string vs. `None` explanation storage for consistent downstream handling.
- R-01: Rotate `results.json.v1` backups with timestamps if multi-generation history becomes a requirement.

---

## Re-Audit Trail

### Re-audit 2026-05-15 — Verify fixes for CR-01, CR-02, WR-03

**Auditor:** gsd-security-auditor (claude-sonnet-4-6)
**Scope:** Re-verification of 3 previously-open threats only. All other threats unchanged from original audit.
**Commits reviewed:** fa3f3a1 (CR-01), 2fa6fb8 (CR-02), cb1e2d2 (WR-03)
**Files read:** `openevolve/run_experiment.py`, `openevolve/consolidate_results.py`

| Threat ID | Prior Status | New Status | Verification Method |
|-----------|-------------|------------|---------------------|
| CR-01 (OPEN-01) | OPEN / BLOCKER | CLOSED | Grep confirmed `re.match(r'^[a-zA-Z0-9_-]+$', args.run)` at line 205 and `startswith(runs_dir)` with `runs_dir` containing `os.sep` suffix at lines 211-213 |
| CR-02 (OPEN-02) | OPEN / BLOCKER | CLOSED | Grep confirmed `_ms if _ms is not None else` pattern at lines 227-229; falsy or-chain absent |
| WR-03 (OPEN-03) | OPEN / WARNING | CLOSED | Grep confirmed `tempfile.mkstemp` at line 239 with no `dir=` argument; `try/finally` structure at lines 240-301 covers all paths |

**Result:** All 10/10 threats closed. Phase 04 cleared for ship.

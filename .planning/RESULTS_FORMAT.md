# Unified Results Format Specification

## Overview

OpenEvolve experiments produce a unified JSON results file that consolidates all iterations from an experiment into a single, self-contained document. This format enables batch analysis in pandas without parsing multiple scattered checkpoint files.

## File Naming & Location

Results are stored at:
```
openevolve_output/{prompt_variant}/results.json
```

Example: `openevolve_output/baseline/results.json`, `openevolve_output/prompt1/results.json`

## JSON Schema

The results file has three top-level sections: `metadata`, `baseline_metrics`, and `iterations`.

### Metadata Section

```json
{
  "metadata": {
    "program": "string",           // Program name (e.g., "cavitydetection")
    "prompt_variant": "string",    // Prompt name (from filename)
    "timestamp": "string",         // ISO 8601 format: YYYY-MM-DDTHH:MM:SSZ
    "llm_model": "string",         // LLM model name (e.g., "qwen2.5-coder:32b")
    "total_iterations": "integer", // Number of iterations completed
    "total_runtime_seconds": "number", // Total wall-clock time for experiment
    "best_memory_accesses": "integer", // Memory accesses in best solution found
    "convergence_iteration": "integer", // Iteration number when best was first found
    "explanation_config": {object}  // Metadata about LLM explanations (see section below)
  }
}
```

**Field Definitions:**
- `program`: Name of the program being optimized (string, lowercase)
- `prompt_variant`: Name of the prompt file without extension; derives from output directory basename
- `timestamp`: Start time of the experiment in UTC (ISO 8601 format for sorting and filtering)
- `llm_model`: Full model identifier from Ollama (e.g., `qwen2.5-coder:32b`)
- `total_iterations`: Total number of iterations the experiment ran
- `total_runtime_seconds`: Sum of all iteration runtimes (float, in seconds)
- `best_memory_accesses`: Integer count of memory accesses in the best-scoring solution
- `convergence_iteration`: Iteration number (1-indexed) at which the best solution was first discovered

### Baseline Metrics Section

```json
{
  "baseline_metrics": {
    "memory_accesses": 128862705,  // Total unoptimized baseline (integer)
    "memory_reads": 64431352,      // Estimated read accesses (≈ baseline / 2)
    "memory_writes": 64431353      // Estimated write accesses (≈ baseline / 2)
  }
}
```

**Field Definitions:**
- `memory_accesses`: Reference baseline from unoptimized program (integer, constant: 128,862,705 for cavitydetection)
- `memory_reads`: Estimated load count (baseline / 2, rounded)
- `memory_writes`: Estimated store count (baseline / 2, rounded, accounting for odd total)

The split between reads and writes is derived from the baseline and applies uniformly to all iterations.

### Explanation Config Section

```json
{
  "explanation_config": {
    "enabled": boolean,             // Whether explanations were generated
    "prompt_file": "string",        // Source prompt file name (if enabled)
    "prompt_version": "string",     // Semantic version of prompt (e.g., "1.0")
    "prompt_hash": "string",        // SHA256 (first 16 chars) for change detection
    "prompt_changed_after_run": boolean  // True if prompt was modified after experiment
  }
}
```

**Field Definitions:**
- `enabled`: Boolean flag indicating whether LLM explanations were generated for this experiment
- `prompt_file`: Source filename for reference (always "explanation_prompt.txt" if enabled)
- `prompt_version`: Semantic version of the explanation prompt used (e.g., "1.0", "1.1", "2.0")
- `prompt_hash`: SHA256 hash (first 16 hexadecimal characters) of the prompt text; enables detection if prompt file was modified
- `prompt_changed_after_run`: Boolean flag set to true if the prompt file was modified after the experiment completed (data integrity warning)

When `enabled` is false (no explanations generated), only the `enabled` field is present.

### Iterations Array

```json
{
  "iterations": [
    {
      "iteration": 1,
      "memory_accesses": 127000000,
      "memory_reads": 63500000,
      "memory_writes": 63500000,
      "improvement_percent": 1.45,
      "iteration_runtime_seconds": 12.3,
      "mem_score": 1.0148,
      "explanation": "Reordered loops to improve cache locality..."
    },
    {
      "iteration": 2,
      "memory_accesses": 126500000,
      "memory_reads": 63250000,
      "memory_writes": 63250000,
      "improvement_percent": 1.95,
      "iteration_runtime_seconds": 12.8,
      "mem_score": 1.0198
    }
  ]
}
```

Note: The `explanation` field is optional and present only if explanations were generated for that iteration.

**Field Definitions:**

| Field | Type | Description |
|-------|------|-------------|
| `iteration` | integer | Iteration number (1-indexed) |
| `memory_accesses` | integer | Total loads + stores in evolved pipeline for this iteration |
| `memory_reads` | integer | Estimated read count (derived from memory_accesses * 0.5) |
| `memory_writes` | integer | Estimated write count (derived from memory_accesses * 0.5) |
| `improvement_percent` | float | Percentage reduction vs baseline: `(baseline - accesses) / baseline * 100` |
| `iteration_runtime_seconds` | float | Wall-clock time spent evaluating this iteration candidate (seconds) |
| `mem_score` | float | Memory score: `baseline / accesses` (>1.0 means better than baseline) |
| `explanation` | string (optional) | LLM-generated description of optimization strategy; omitted if not available |
| `prompt_version` | string (optional) | Version of explanation prompt used; present if explanation field exists |

## Derived Fields

The following fields are computed during consolidation and included in every iteration record:

### improvement_percent

```
improvement_percent = (baseline_memory_accesses - memory_accesses) / baseline_memory_accesses * 100
```

Example: If baseline is 128,862,705 and accesses are 127,000,000:
```
improvement = (128,862,705 - 127,000,000) / 128,862,705 * 100 = 1.45%
```

### mem_score

```
mem_score = baseline_memory_accesses / memory_accesses
```

Example: With baseline 128,862,705 and accesses 127,000,000:
```
mem_score = 128,862,705 / 127,000,000 = 1.0148
```

Used for backward compatibility with existing `show_results.py` reports. A score > 1.0 indicates fewer accesses than the baseline.

### memory_reads and memory_writes

Estimated by splitting memory_accesses uniformly:
```
memory_reads = memory_accesses / 2  (rounded down)
memory_writes = memory_accesses / 2 (rounded up if total is odd)
```

This is a placeholder for Phase 2, which may extract actual read/write counts from LLVM instrumentation.

## Complete Example JSON (With Explanations)

```json
{
  "metadata": {
    "program": "cavitydetection",
    "prompt_variant": "baseline",
    "timestamp": "2026-05-13T14:30:00Z",
    "llm_model": "qwen2.5-coder:32b",
    "total_iterations": 42,
    "total_runtime_seconds": 480.5,
    "best_memory_accesses": 98765432,
    "convergence_iteration": 28,
    "explanation_config": {
      "enabled": true,
      "prompt_file": "explanation_prompt.txt",
      "prompt_version": "1.0",
      "prompt_hash": "a3b2c1f5e8d9a2b3",
      "prompt_changed_after_run": false
    }
  },
  "baseline_metrics": {
    "memory_accesses": 128862705,
    "memory_reads": 64431352,
    "memory_writes": 64431353
  },
  "iterations": [
    {
      "iteration": 1,
      "memory_accesses": 127000000,
      "memory_reads": 63500000,
      "memory_writes": 63500000,
      "improvement_percent": 1.45,
      "iteration_runtime_seconds": 12.3,
      "mem_score": 1.0148,
      "explanation": "Reordered loops from (x outer, y inner) to (y outer, x inner) to improve cache locality."
    },
    {
      "iteration": 2,
      "memory_accesses": 126500000,
      "memory_reads": 63250000,
      "memory_writes": 63250000,
      "improvement_percent": 1.95,
      "iteration_runtime_seconds": 12.8,
      "mem_score": 1.0198
    }
  ]
}
```

## Complete Example JSON (No Explanations — Backward Compatible)

```json
{
  "metadata": {
    "program": "cavitydetection",
    "prompt_variant": "baseline",
    "timestamp": "2026-05-13T14:30:00Z",
    "llm_model": "qwen2.5-coder:32b",
    "total_iterations": 42,
    "total_runtime_seconds": 480.5,
    "best_memory_accesses": 98765432,
    "convergence_iteration": 28,
    "explanation_config": {
      "enabled": false
    }
  },
  "baseline_metrics": {
    "memory_accesses": 128862705,
    "memory_reads": 64431352,
    "memory_writes": 64431353
  },
  "iterations": [
    {
      "iteration": 1,
      "memory_accesses": 127000000,
      "memory_reads": 63500000,
      "memory_writes": 63500000,
      "improvement_percent": 1.45,
      "iteration_runtime_seconds": 12.3,
      "mem_score": 1.0148
    },
    {
      "iteration": 2,
      "memory_accesses": 126500000,
      "memory_reads": 63250000,
      "memory_writes": 63250000,
      "improvement_percent": 1.95,
      "iteration_runtime_seconds": 12.8,
      "mem_score": 1.0198
    }
  ]
}
```

## Design Rationale

### Single File per Experiment

Each experiment produces one `results.json` file containing the complete iteration history. This approach:

- **Simplifies batch loading:** Researchers load one file per prompt variant; no iteration hunting
- **Preserves history:** All iterations (not just the best) are available for convergence analysis
- **Enables comparison:** Concatenating multiple results.json files (via pandas) compares prompt strategies
- **Self-contained:** Each file includes metadata and baseline for reproducibility and portability

### Field Types

- **Integer fields:** Memory access counts are integers (no fractional accesses)
- **Float fields:** Percentages, scores, and timings are floats (allow fractional representation)
- **Strings:** Timestamps in ISO 8601 for standard sorting; identifiers as lowercase strings
- **ISO 8601 timestamps:** `YYYY-MM-DDTHH:MM:SSZ` format for UTC; sortable and comparable across timezones

### Baseline Constant

The baseline (128,862,705 accesses) is hardcoded in the consolidation script, not in every results.json, to:
- Reduce file size and redundancy
- Centralize the reference metric (easier to audit)
- Prevent transcription errors per file

### Backward Compatibility

The `mem_score` field is derived from the baseline and memory_accesses to maintain compatibility with existing `show_results.py`, which uses this metric for ranking.

## Assumptions & Constraints

1. **One experiment, one file:** Each `results.json` represents a single experiment run (single prompt variant, single model, single start time)
2. **All numeric accesses are large integers:** No overflow risk with Python int type (arbitrary precision)
3. **Per-iteration data:** If OpenEvolve outputs per-iteration checkpoints, consolidate reads all; if only the best is available (fallback), create a synthetic single-iteration record
4. **Timestamps in UTC:** All `timestamp` and `iteration_runtime_seconds` are in UTC or wall-clock seconds (not CPU time)
5. **Immutable after creation:** Results files are written once at experiment end; not updated by subsequent experiments

## Prompt Reproducibility & Versioning

When LLM explanations are enabled, the `explanation_config` metadata section ensures reproducibility:

### Version Tracking
- `prompt_version`: Semantic versioning (e.g., "1.0", "1.1", "2.0") tracks prompt evolution
- `prompt_hash`: SHA256 digest (first 16 chars) of prompt text enables change detection
- **Comparison across versions**: Filter results by `prompt_version` to compare explanation quality across prompt iterations
- **Safety**: Old and new results coexist; changing the prompt does not invalidate past results

### Change Detection
- If `prompt_hash` differs from the current `explanation_prompt.txt`, the prompt has been modified
- Set `prompt_changed_after_run` to true if modification detected after experiment completion (data integrity warning)

### Iteration Workflow
When the explanation prompt is updated:

1. Edit `explanation_prompt.txt`
2. Increment `prompt_version` in the file header
3. Commit to git with message: `prompt(02-llm): bump explanation prompt to v{version}`
4. Re-run experiments to capture explanations with new prompt version
5. Compare old vs new results: filter by `prompt_version` field in pandas

### Guidance for Analysis
- **Explanation quality analysis**: Group results by `prompt_version`; compare descriptions for style/accuracy changes
- **Version stability**: Expect mostly similar explanations for minor bumps (v1.0 → v1.1)
- **Major rewrites**: Major version bumps (v1.0 → v2.0) indicate conceptual changes; results not directly comparable

## Migration & Version Control

- **Current OpenEvolve output** (scattered best_program_info.json) remains for backward compatibility
- **New results.json** is the authoritative consolidated format going forward
- **show_results.py** continues to work from best_program_info.json
- **Loaders (results_loader.py)** read the new format exclusively

If OpenEvolve is upgraded and output structure changes, consolidate_results.py must be updated to parse the new format.

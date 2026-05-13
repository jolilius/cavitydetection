# Using Consolidated Results

This document describes how to load, analyze, and visualize OpenEvolve experiment results using the consolidated JSON format and pandas loader.

## Installation

The loader requires pandas. Install it in the OpenEvolve virtual environment:

```bash
cd ../openevolve
uv pip install pandas
```

## Quick Start

Load all consolidated results and plot convergence curves:

```python
from openevolve.results_loader import load_all_results
import matplotlib.pyplot as plt

df = load_all_results()
for prompt in df['prompt'].unique():
    subset = df[df['prompt'] == prompt].sort_values('iteration')
    plt.plot(subset['iteration'], subset['memory_accesses'], label=prompt)

plt.xlabel('Iteration')
plt.ylabel('Memory Accesses')
plt.legend()
plt.title('Convergence Curves by Prompt')
plt.show()
```

## Single Experiment Analysis

Load and analyze a single prompt's results:

```python
from openevolve.results_loader import load_results

df = load_results('openevolve_output/baseline/results.json')
print(df[['iteration', 'memory_accesses', 'improvement_percent']].head(10))

# Find convergence point (iteration at which best solution was found)
best_iter = df[df['memory_accesses'] == df['memory_accesses'].min()]['iteration'].iloc[0]
print(f"Converged at iteration {best_iter}")

# Summary statistics
print(f"Best memory accesses: {df['memory_accesses'].min():,}")
print(f"Best improvement: {df['improvement_percent'].max():.2f}%")
```

## Compare Prompts

Compare performance across multiple prompt variants:

```python
from openevolve.results_loader import load_all_results

df = load_all_results()

# Summary statistics by prompt
comparison = df.groupby('prompt').agg({
    'memory_accesses': ['min', 'max', 'mean'],
    'improvement_percent': ['max', 'mean'],
    'iteration': 'count',  # number of iterations per prompt
})
print(comparison)

# Find best prompt (lowest best memory accesses)
best_prompt = df.groupby('prompt')['memory_accesses'].min().idxmin()
print(f"\nBest prompt: {best_prompt}")

# Convergence speed (iteration at which best was found)
convergence_speed = df.groupby('prompt').apply(
    lambda g: g[g['memory_accesses'] == g['memory_accesses'].min()]['iteration'].iloc[0]
)
print(f"\nConvergence speed (iteration to best):\n{convergence_speed}")
```

## Advanced Analysis

### Memory Access Breakdown

```python
df = load_all_results()

# Compare reads vs writes (estimated split)
df['read_to_write_ratio'] = df['memory_reads'] / df['memory_writes']

# Analyze improvement over baseline
df['absolute_improvement'] = df['baseline_accesses'] - df['memory_accesses']

# Group by prompt and iteration range
early_iterations = df[df['iteration'] <= 10].groupby('prompt')['memory_accesses'].mean()
late_iterations = df[df['iteration'] > 30].groupby('prompt')['memory_accesses'].mean()

print("Early iterations (1-10) average accesses:")
print(early_iterations)
print("\nLate iterations (>30) average accesses:")
print(late_iterations)
```

### Time-to-Convergence Analysis

```python
df = load_all_results()

# Find iteration where best was achieved
convergence_data = []
for prompt in df['prompt'].unique():
    subset = df[df['prompt'] == prompt]
    best_iter = subset[subset['memory_accesses'] == subset['memory_accesses'].min()]['iteration'].iloc[0]
    
    # Sum runtime up to convergence
    runtime_to_convergence = subset[subset['iteration'] <= best_iter]['iteration_runtime_seconds'].sum()
    
    convergence_data.append({
        'prompt': prompt,
        'convergence_iteration': best_iter,
        'total_runtime_to_convergence': runtime_to_convergence,
    })

import pandas as pd
convergence_df = pd.DataFrame(convergence_data)
print("Time-to-convergence summary:")
print(convergence_df)
```

### Improvement Trajectory

Plot how improvement increases over iterations:

```python
from openevolve.results_loader import load_all_results
import matplotlib.pyplot as plt

df = load_all_results()

fig, axes = plt.subplots(1, 2, figsize=(14, 5))

# Plot 1: Improvement percent over time
for prompt in df['prompt'].unique():
    subset = df[df['prompt'] == prompt].sort_values('iteration')
    axes[0].plot(subset['iteration'], subset['improvement_percent'], marker='o', label=prompt)

axes[0].set_xlabel('Iteration')
axes[0].set_ylabel('Improvement %')
axes[0].set_title('Improvement Over Baseline')
axes[0].legend()
axes[0].grid(True, alpha=0.3)

# Plot 2: Memory accesses over time
for prompt in df['prompt'].unique():
    subset = df[df['prompt'] == prompt].sort_values('iteration')
    axes[1].plot(subset['iteration'], subset['memory_accesses'], marker='s', label=prompt)

axes[1].set_xlabel('Iteration')
axes[1].set_ylabel('Memory Accesses')
axes[1].set_title('Convergence Curves')
axes[1].legend()
axes[1].grid(True, alpha=0.3)

plt.tight_layout()
plt.show()
```

## Analyzing Explanations

Load explanations and compare transformation strategies across prompts:

```python
from openevolve.results_loader import load_all_results
import pandas as pd

df = load_all_results()

# Filter to rows with explanations only
explained_df = df[df['explanation'].notna()]

# Group by prompt and show unique explanations
for prompt in sorted(df['prompt'].unique()):
    subset = explained_df[explained_df['prompt'] == prompt]
    print(f"\n{prompt}:")
    for _, row in subset.head(3).iterrows():
        print(f"  Iter {row['iteration']}: {row['explanation'][:100]}...")
```

## Understanding Explanations

Explanations describe the high-level optimization strategy. Look for patterns:

**Common optimization patterns:**
- **Loop reordering:** "Changed loop order from for(x) for(y) to for(y)..."
  - Indicates cache locality improvement (sequential memory access)
- **Loop fusion:** "Fused blur and edge detection into single pass"
  - Indicates reduced intermediate buffer allocations
- **Ring buffers:** "Used ring buffer to keep only N rows in memory"
  - Indicates reduced total memory footprint
- **Scalar replacement:** "Computed values inline instead of storing intermediate arrays"
  - Indicates reduced memory traffic

**Limitations:**
- Explanations are generated by LLM; may be subjective or incomplete
- LLM may hallucinate transformations not actually present in code
- Explanations do not replace code review for understanding actual changes
- Use as starting point for deeper investigation, not ground truth

## Cross-Prompt Strategy Comparison

Compare how different prompts discover different optimization strategies:

```python
df = load_all_results()
explained = df[df['explanation'].notna()]

# Show explanations for iteration 1 across all prompts (what did each prompt try first?)
iter1 = explained[explained['iteration'] == 1][['prompt', 'memory_accesses', 'explanation']]
print("Iteration 1 strategies across prompts:")
print(iter1.to_string(index=False))

# Show convergence patterns
for prompt in explained['prompt'].unique():
    subset = explained[explained['prompt'] == prompt].sort_values('iteration')
    print(f"\n{prompt} convergence:")
    first = subset.iloc[0]
    best = subset.iloc[subset['memory_accesses'].idxmin()]
    print(f"  First: {first['explanation']}")
    print(f"  Best (iter {int(best['iteration'])}): {best['explanation']}")
```

## Text Analysis of Explanations (Advanced)

Cluster explanations by transformation type:

```python
from openevolve.results_loader import load_all_results
import re

df = load_all_results()
explained = df[df['explanation'].notna()]

# Extract transformation keywords
def extract_keywords(text):
    keywords = []
    patterns = {
        'loop_order': r'loop order|for\(.*\).*for\(',
        'fusion': r'fus|combin|merge',
        'buffer': r'buffer|array|allocat',
        'cache': r'cache|locality|sequential',
    }
    for key, pattern in patterns.items():
        if re.search(pattern, text, re.IGNORECASE):
            keywords.append(key)
    return keywords

explained['keywords'] = explained['explanation'].apply(extract_keywords)

# Count keyword frequency by prompt
for prompt in explained['prompt'].unique():
    subset = explained[explained['prompt'] == prompt]
    all_keywords = []
    for kw_list in subset['keywords']:
        all_keywords.extend(kw_list)
    from collections import Counter
    freq = Counter(all_keywords)
    print(f"{prompt}: {dict(freq)}")
```

## Fields Reference

The DataFrame includes the following columns:

### Iteration Metrics
- **iteration** (int): Iteration number (1-indexed)
- **memory_accesses** (int): Total loads + stores in the evolved pipeline
- **memory_reads** (int): Estimated read count (≈ memory_accesses / 2)
- **memory_writes** (int): Estimated write count (≈ memory_accesses / 2)

### Performance Metrics
- **improvement_percent** (float): Percentage reduction vs baseline
  - Calculated as: `(baseline - accesses) / baseline * 100`
  - Positive values indicate improvement (fewer accesses than baseline)
  - Example: 5.0% = 5% fewer accesses than baseline
- **mem_score** (float): Score > 1.0 means better than baseline
  - Calculated as: `baseline / accesses`
  - Example: 1.05 = 5% better (1.05× speedup in memory accesses)
- **iteration_runtime_seconds** (float): Wall-clock time to evaluate this iteration

### Metadata Columns
- **prompt** (str): Prompt variant name (from filename)
- **timestamp** (str): Experiment start time (ISO 8601 format)
- **baseline_accesses** (int): Baseline reference (128,862,705 for cavitydetection)
- **program** (str): Program name (e.g., "cavitydetection")
- **explanation** (str, optional): LLM-generated description of the optimization strategy. NaN if not available (Phase 1 results or LLM timeout)

## Results Storage

Consolidated results are stored at:
```
openevolve_output/{prompt_variant}/results.json
```

Each file is self-contained and can be:
- Analyzed independently: `load_results('path/to/results.json')`
- Combined with others: `load_all_results()`
- Shared, archived, or migrated without external dependencies

## Understanding Memory Score

The `mem_score` is the primary comparison metric:

| Score | Interpretation |
|-------|---|
| < 1.0 | Worse than baseline (more accesses) |
| 1.0 | Same as baseline |
| > 1.0 | Better than baseline (fewer accesses) |
| 1.1 | 10% fewer accesses than baseline |
| 1.5 | 50% fewer accesses than baseline |

**Formula:** `mem_score = baseline_accesses / candidate_accesses`

**Example:**
- Baseline: 128,862,705 accesses
- Candidate: 120,000,000 accesses
- mem_score = 128,862,705 / 120,000,000 = 1.074
- Improvement: 7.4% better than baseline

## Performance Interpretation

Typical convergence patterns:

- **Early plateau** (improvement stalls quickly): Prompt explores local optima
- **Gradual decline** (steady improvement): Prompt balances exploration and refinement
- **Late jumps** (sudden improvements): Prompt discovers major transformations late

Monitor `improvement_percent` and `mem_score` trends to understand prompt effectiveness.

## Limitations & Known Stubs

The current implementation (Phase 1):

- **Read/write split is estimated** (not measured from instrumentation)
  - Assumes uniform split (≈50% reads, ≈50% writes)
  - Phase 2 will extract actual counts from LLVM instrumentation
- **Iteration runtime is estimated** (placeholder value from best_program_info.json)
  - Does not include consolidation overhead
  - Will be improved when OpenEvolve outputs per-iteration timing
- **LLM model** is extracted from config.yaml
  - May show "unknown" if config not found
  - Phase 2 will ensure model is recorded in results

## Troubleshooting

### No results found

```
Warning: No results.json files found in openevolve_output/
```

**Solution:** Run an experiment first:
```bash
../openevolve/.venv/bin/python openevolve/run_experiment.py baseline --iterations 10
```

### Module not found errors

```
ModuleNotFoundError: No module named 'pandas'
```

**Solution:** Install pandas:
```bash
cd ../openevolve
uv pip install pandas
```

### Empty DataFrame

If a results.json file exists but the DataFrame is empty, check:
1. Results file has valid JSON syntax: `python3 -c "import json; json.load(open('results.json'))"`
2. File contains the required schema sections: `metadata`, `baseline_metrics`, `iterations`
3. Iterations array is not empty: `grep -c '"iteration"' results.json`

### Missing explanations

If `explanation` column is NaN for all or most rows:
- Phase 1 results don't have explanations; run new experiments with Phase 2
- EXPLAIN_GENERATIONS=0 was set; re-run with EXPLAIN_GENERATIONS=1
- LLM API was unavailable; explanations timed out during experiment

Check explanation field presence:
```python
df['explanation'].notna().sum()  # count non-NaN explanations
```

## Next Steps

After analyzing results:

1. **Identify best prompts** — Which prompt variants show best convergence?
2. **Analyze strategies** — What code transformations emerge?
3. **Refine prompts** — Phase 2 will add LLM-generated explanations
4. **Run longer experiments** — Increase `--iterations` to find global optima
5. **Compare across programs** — Phase 3 will support multiple target programs


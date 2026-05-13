# Phase 2 — LLM Explanations: Quick Start Guide

**Phase 2 is complete and ready to use!** 🚀

This guide will help you get started with the new explanation generation feature that was just implemented.

---

## What's New (Phase 2)

OpenEvolve experiments now **automatically generate LLM-powered explanations** for code transformations:

```
Before (Phase 1):
  Iteration 5: 127,000,000 memory accesses, 1.45% improvement

After (Phase 2):
  Iteration 5: 127,000,000 memory accesses, 1.45% improvement
  Explanation: "Reordered loops to access memory sequentially; 
                converted stride-512 misses to adjacent prefetch."
```

You can:
- ✅ Run experiments and get explanations automatically
- ✅ Load explanations into pandas DataFrames
- ✅ Analyze what optimizations the LLM discovered
- ✅ Compare strategies across different prompts
- ✅ Iterate on the prompt and re-run safely (with full version tracking)

---

## Quick Start (5 minutes)

### 1. Test With 10 Iterations

Run a quick test to see explanations in action:

```bash
make evolve-explain-test
```

This runs the baseline prompt variant with 10 iterations and auto-captures explanations.

### 2. View Results with Explanations

```bash
make show-explanations
```

Shows a table of results including the explanation column.

### 3. Load Into Python

```python
from openevolve.results_loader import load_results
import pandas as pd

# Load the baseline results
df = load_results("openevolve_output/baseline/results.json")

# View first 5 iterations with explanations
print(df[['iteration', 'memory_accesses', 'improvement_percent', 'explanation']].head())
```

Output:
```
   iteration  memory_accesses  improvement_percent                      explanation
0          1       127000000                  1.45  Reordered loops to access memory...
1          2       126500000                  1.95  Fused horizontal and vertical bl...
2          3       126100000                  2.31  Added intermediate buffer to con...
3          4       125800000                  2.52  Eliminated redundant memory reads...
4          5       125200000                  3.15  Simplified loop bounds to avoid ...
```

---

## Run Full Experiments

### 40-Iteration Baseline

```bash
EXPLAIN_GENERATIONS=1 make evolve-all ITERATIONS=40
```

This runs the baseline prompt variant for 40 iterations and captures explanations.

### 10 Iterations (Faster Test)

```bash
make evolve-explain-test
```

---

## Analyze Explanations

### Basic Loading

```python
from openevolve.results_loader import load_results

df = load_results("openevolve_output/baseline/results.json")

# Show all explanations
print(df[['iteration', 'explanation']].to_string())

# Count how many have explanations
print(f"Explanations captured: {df['explanation'].notna().sum()}/{len(df)}")
```

### Filter by Improvement

```python
# Show explanations for best improvements (top 5)
best = df.nlargest(5, 'improvement_percent')[['iteration', 'explanation', 'improvement_percent']]
print(best.to_string())
```

### Keyword Analysis

```python
# Find explanations mentioning specific optimization types
loop_reorder = df[df['explanation'].str.contains('loop', case=False, na=False)]
print(f"Loop-related optimizations: {len(loop_reorder)}")
print(loop_reorder[['iteration', 'explanation']].head())
```

### Cross-Prompt Comparison

```python
# Load multiple prompt variants
baseline = load_results("openevolve_output/baseline/results.json")
variant1 = load_results("openevolve_output/prompt1/results.json")

# Compare explanations for iteration 10
print("Baseline iteration 10:")
print(baseline.loc[baseline['iteration'] == 10, 'explanation'].values[0])

print("\nVariant 1 iteration 10:")
print(variant1.loc[variant1['iteration'] == 10, 'explanation'].values[0])

# Which variant converged faster?
print(f"\nBaseline convergence: iteration {baseline['convergence_iteration'].iloc[0]}")
print(f"Variant 1 convergence: iteration {variant1['convergence_iteration'].iloc[0]}")
```

---

## Understanding Explanations

Explanations focus on **code transformation techniques**, not performance numbers:

### Good Explanations (What You'll See)
- "Reordered loops to improve cache locality; sequential access instead of striding."
- "Fused multiple passes into single loop to reduce memory traffic."
- "Added intermediate buffer to convert 2D random access to 1D sequential."
- "Eliminated redundant bounds checking in inner loop."
- "Transformed loop to enable vectorization; aligned memory accesses."

### Not Explanations (What You Won't See)
- "This optimization is amazing!" ← Too vague
- "Changed lines 23-27 in GaussBlur" ← Too specific
- "Improved cache hit rate by 40%" ← Performance, not transformation
- "My transformer learned this pattern" ← Speculation about intent

---

## Prompt Versioning & Iteration

### Review Initial Results (v1.0)

The prompt was created in v1.0. Run a quick test:

```bash
make evolve-explain-test
```

Examine the explanations:
```python
df = load_results("baseline.json")
print(df[['iteration', 'explanation']].head(10))
```

### If You Want to Improve the Prompt

The prompt file is at: `openevolve/explanation_prompt.txt`

**Improve it if:**
- Explanations are too vague or generic
- Important optimization patterns are missing
- Explanations don't match the actual code changes

**Example improvement:**
```
# Original (v1.0):
"Explain the key optimization strategy in 1-2 sentences"

# Improved (v1.1):
"Explain the key optimization strategy in 1-2 sentences.
Focus on: loop order, memory layout, access patterns, prefetching, vectorization, bounds.
Be specific about WHAT changed, not WHY the model did it."
```

**Then re-run:**
```bash
# Edit openevolve/explanation_prompt.txt

# Bump version in code and re-run
# Version number is tracked automatically; old and new results coexist

make evolve-all ITERATIONS=40
```

**Compare versions:**
```python
df = load_results("baseline.json")

# v1.0 explanations
v1_0 = df[df['prompt_version'] == '1.0'][['iteration', 'explanation']]
print("Version 1.0:")
print(v1_0.head())

# v1.1 explanations (if you re-ran)
v1_1 = df[df['prompt_version'] == '1.1'][['iteration', 'explanation']]
print("\nVersion 1.1:")
print(v1_1.head())

# Compare quality, specificity, coverage
```

---

## Environment Variables

Control explanation generation with:

```bash
# Enable (default)
EXPLAIN_GENERATIONS=1 make evolve-all ITERATIONS=40

# Disable (experiments run, no explanations captured)
EXPLAIN_GENERATIONS=0 make evolve-all ITERATIONS=40

# Default is enabled if not specified
make evolve-all ITERATIONS=40  # Same as EXPLAIN_GENERATIONS=1
```

Use `EXPLAIN_GENERATIONS=0` if:
- Ollama is not running
- You want faster iteration on code without waiting for explanations
- You're testing integration and don't need explanations yet

---

## Results Schema

Every result includes metadata about which prompt was used:

```json
{
  "metadata": {
    "program": "cavitydetection",
    "prompt_variant": "baseline",
    "explanation_config": {
      "enabled": true,
      "prompt_file": "explanation_prompt.txt",
      "prompt_version": "1.0",
      "prompt_hash": "a3b2c1f5e8d9a2b3"
    }
  },
  "iterations": [
    {
      "iteration": 1,
      "memory_accesses": 127000000,
      "explanation": "Reordered loops to..."
    }
  ]
}
```

**Key fields:**
- `prompt_version` — Which version of the prompt (1.0, 1.1, 2.0, etc.)
- `prompt_hash` — SHA256 of the prompt text; changes if prompt was modified
- `enabled` — Whether explanation generation was on for this run

---

## Common Tasks

### Task 1: See What Optimizations the LLM Found

```python
from openevolve.results_loader import load_results

df = load_results("baseline.json")

# Show all explanations in a readable format
for idx, row in df[['iteration', 'explanation']].iterrows():
    if pd.notna(row['explanation']):
        print(f"Iteration {row['iteration']}: {row['explanation']}")
```

### Task 2: Find the Most Common Optimization Pattern

```python
from collections import Counter

df = load_results("baseline.json")
explanations = df['explanation'].dropna().tolist()

# Extract optimization keywords
keywords = []
for exp in explanations:
    if 'loop' in exp.lower():
        keywords.append('loop reordering')
    if 'buffer' in exp.lower() or 'intermediate' in exp.lower():
        keywords.append('buffering')
    if 'fus' in exp.lower():
        keywords.append('loop fusion')
    if 'cache' in exp.lower() or 'locality' in exp.lower():
        keywords.append('cache optimization')

counts = Counter(keywords)
print("Most common optimizations:")
for pattern, count in counts.most_common():
    print(f"  {pattern}: {count}")
```

### Task 3: Compare Two Prompts

```python
from openevolve.results_loader import load_results

baseline = load_results("openevolve_output/baseline/results.json")
variant = load_results("openevolve_output/prompt1/results.json")

print("Baseline prompt (v1.0):")
print("  Convergence iteration:", baseline['convergence_iteration'].iloc[0])
print("  Best improvement:", baseline['improvement_percent'].max())
print("  Sample explanation:")
print("  ", baseline[baseline['explanation'].notna()]['explanation'].iloc[0])

print("\nVariant prompt (v1.0):")
print("  Convergence iteration:", variant['convergence_iteration'].iloc[0])
print("  Best improvement:", variant['improvement_percent'].max())
print("  Sample explanation:")
print("  ", variant[variant['explanation'].notna()]['explanation'].iloc[0])
```

### Task 4: Check Explanation Quality

```python
df = load_results("baseline.json")

# Count explanations (should be high if Ollama was running)
explanation_count = df['explanation'].notna().sum()
total = len(df)
coverage = 100 * explanation_count / total

print(f"Explanation coverage: {explanation_count}/{total} ({coverage:.1f}%)")

# Check lengths (should be 1-2 sentences, ~50-200 chars)
lengths = df['explanation'].dropna().str.len()
print(f"Explanation lengths: min={lengths.min()}, max={lengths.max()}, avg={lengths.mean():.0f}")

# Sample explanations
print("\nSample explanations:")
for exp in df['explanation'].dropna().head(5):
    print(f"  - {exp}")
```

---

## Troubleshooting

### "No explanations captured" (all NaN)

**Cause:** Ollama wasn't running or LLM wasn't available

**Fix:**
1. Start Ollama: `ollama serve` (in a separate terminal)
2. Verify model is loaded: `ollama pull qwen2.5-coder:32b`
3. Re-run: `make evolve-explain-test`

### "Explanations are too vague"

**Cause:** Prompt needs refinement

**Fix:**
1. Edit `openevolve/explanation_prompt.txt`
2. Add more specific examples or constraints
3. Bump version (e.g., "1.0" → "1.1")
4. Re-run: `make evolve-all ITERATIONS=40`
5. Compare v1.0 vs v1.1 explanations

### "Explanation generation is too slow"

**Cause:** LLM is slow or network latency

**Fix:**
1. Use `EXPLAIN_GENERATIONS=0` to skip explanations
2. Or reduce timeout in code and accept some missing explanations
3. Or optimize Ollama instance (reduce context, use smaller model)

### "Results file is missing explanation field"

**Cause:** Running old code that doesn't support explanations

**Fix:**
1. Ensure you're on the latest main branch: `git pull`
2. Results from Phase 1 won't have explanations; Phase 2 results will

---

## Files & Documentation

### Core Implementation
- `openevolve/explanation_prompt.txt` — The LLM system prompt
- `openevolve/explanation_generator.py` — LLM API client
- `openevolve/run_experiment.py` — Integration point
- `openevolve/results_loader.py` — Pandas utilities

### Design Documents
- `openevolve/EXPLANATION_DESIGN.md` — Prompt philosophy & versioning strategy
- `.planning/RESULTS_FORMAT.md` — Full schema specification
- `.planning/RESULTS_USAGE.md` — Detailed pandas examples
- `.planning/PHASE2_COMPLETE.md` — Full completion report

### Test Suite
- `openevolve/test_consolidation.py` — 6 tests covering explanation handling

---

## Next Steps

**Now:**
1. Run `make evolve-explain-test` and see explanations
2. Load results: `python3 -c "from openevolve.results_loader import load_results; df = load_results('baseline.json'); print(df[['iteration', 'explanation']].head())"`
3. Play with the data!

**Longer experiments:**
- `make evolve-all ITERATIONS=40` for full run with explanations
- Analyze patterns, refine prompt if needed

**Research questions you can now answer:**
- What optimization patterns does the LLM discover?
- Do different prompts find different strategies?
- How consistent are the explanations?
- Can we cluster optimizations by type?

---

## Commands Cheat Sheet

```bash
# Quick test (10 iterations with explanations)
make evolve-explain-test

# View results table with explanations
make show-explanations

# Full experiment (40 iterations)
EXPLAIN_GENERATIONS=1 make evolve-all ITERATIONS=40

# Run without explanations (faster)
EXPLAIN_GENERATIONS=0 make evolve-all ITERATIONS=40

# Run tests
cd openevolve && python3 test_consolidation.py

# View consolidated results
python3 -c "from openevolve.show_consolidated import main; main()"
```

---

## Python Snippets

```python
# Load results
from openevolve.results_loader import load_results
df = load_results("openevolve_output/baseline/results.json")

# View explanations
df[['iteration', 'explanation']].head()

# Filter high improvements
df[df['improvement_percent'] > 5][['iteration', 'explanation']]

# Count by prompt version
df['prompt_version'].value_counts()

# Export to CSV
df[['iteration', 'memory_accesses', 'explanation']].to_csv('results.csv', index=False)
```

---

**Everything is on GitHub and ready to go!** Enjoy exploring. 🚀

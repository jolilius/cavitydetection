# LLM Explanation Infrastructure Design

## Objective

Establish a reusable, testable infrastructure for generating LLM-based explanations of code optimization strategies. This document specifies the prompt design, expected output quality, and versioning strategy for sustainable evolution of explanation prompts.

## Prompt Structure & Rationale

### Design Philosophy

Explanations are **researcher-facing narrative descriptions** of optimization strategies applied by evolved code. They serve three purposes:

1. **Research insight**: Help researchers understand what optimization strategies the LLM explores
2. **Convergence analysis**: Enable correlation between explanation type and solution quality
3. **Prompt tuning feedback**: Identify patterns in high-quality vs. low-quality explanations

The prompt is intentionally **specific to this domain** (image-processing pipeline, 512×512 arrays, cache locality, memory-bounded optimization) to maximize accuracy and minimize hallucination.

### Prompt Components

**Section 1: Task Definition**
- Clearly states the input (baseline vs. evolved code) and output (1-2 sentence explanation)
- Emphasizes "WHAT was changed" over "WHY" to ground responses in observable code differences

**Section 2: Domain Context**
- Describes the pipeline stages (Gaussian blur → edge detection → root detection)
- Explains array indexing and its impact on cache locality
- Lists common optimization techniques specific to this domain

**Section 3: Output Format Requirements**
- Hard constraints: exactly 1-2 sentences, plain text only
- Specificity requirement: name actual techniques ("loop fusion", not "improved performance")
- Edge case: guidance for unchanged code ("No optimization detected")

**Section 4: Examples**
- Three realistic examples showing desired explanation quality
- Each example demonstrates a different optimization category
- Examples are grounded in actual techniques possible in the domain

### Addressing Hallucination

The prompt mitigates hallucination through:
- **Domain grounding**: Lists concrete techniques before asking for explanation
- **Format constraints**: Tight output bounds reduce rambling or invented claims
- **Specificity requirement**: Forces reference to actual code structures
- **Negative example**: Shows what NOT to do ("avoid generic phrases")

Remaining hallucination risk is acceptable because:
- Explanations are advisory, not authoritative
- Researchers review explanations alongside actual optimized code
- Results schema includes a versioning system to track prompt iterations

## What Makes a "Good" Explanation

### Quality Criteria

A good explanation has these properties:

1. **Specificity**: Names concrete optimization techniques (loop fusion, bounds elimination, tiling, etc.) rather than generic terms like "optimized"
2. **Accuracy**: Describes observable changes in code, not speculation about internal LLM reasoning
3. **Brevity**: Conveys the key insight in 1-2 sentences; forces prioritization
4. **Grounding**: Uses domain vocabulary (buffer, ring buffer, cache locality, stride, etc.)
5. **Negative precision**: Correctly identifies lack of optimization ("No optimization detected") when appropriate

### Anti-Patterns

Explanations to avoid:

- **Generic praise**: "Improved memory efficiency" — too vague to be useful
- **Speculation**: "The LLM likely realized..." — focuses on process, not outcome
- **Invented techniques**: "Implemented quantum cache optimization" — hallucination
- **Incomplete descriptions**: "Reorganized loops" without specifying how or why
- **Vague metrics**: "Reduced memory accesses" without stating the mechanism

## Example Explanations

### Example 1: Loop Fusion

**Baseline (reference pipeline):**
```c
// Four separate loop nests, four full 256 KB arrays
for (int y = 0; y < M; ++y)
    for (int x = 0; x < N; ++x)
        gx[x][y] = blur_horizontal(in[x][y]);

for (int y = 0; y < M; ++y)
    for (int x = 0; x < N; ++x)
        gxy[x][y] = blur_vertical(gx[x][y]);

// ... edge detection and root detection follow
```

**Evolved version:**
```c
// Single pass combining blur and edge detection via strip processing
for (int y = 0; y < M; ++y) {
    for (int x = 0; x < N; ++x) {
        int g = blur_horizontal(...); // One row of blur
        int e = edge_detect(g, neighbors);  // Direct edge detection
        ce[x][y] = e;
    }
}
```

**Good explanation:**
"Fused Gaussian blur and edge detection into a single loop nest using strip processing through row buffers, eliminating the intermediate gx array (256 KB) and improving cache reuse."

**Why it's good:**
- Specific technique names: "fused", "strip processing", "row buffers"
- Observable change: eliminated gx array
- Benefit clearly stated: cache reuse
- Concise and technical

---

### Example 2: Loop Reordering

**Baseline:**
```c
for (int x = 0; x < N; ++x)
    for (int y = 0; y < M; ++y)
        out[x][y] = process(in[x][y]);
```
(Stride pattern: x varies in outer loop → 512-byte strides in L1 cache, thrashing)

**Evolved:**
```c
for (int y = 0; y < M; ++y)
    for (int x = 0; x < N; ++x)
        out[x][y] = process(in[x][y]);
```
(Stride pattern: y varies in inner loop → sequential bytes, L1 cache friendly)

**Good explanation:**
"Reordered loops from (x outer, y inner) to (y outer, x inner), converting 512-byte strides to sequential cache-line accesses in the image processing loops."

**Why it's good:**
- Precise before/after loop structure
- Explains memory access pattern consequence
- Technical detail without speculation

---

### Example 3: Bounds Check Elimination

**Baseline:**
```c
for (int y = 0; y < M; ++y)
    for (int x = 0; x < N; ++x) {
        int max_diff = 0;
        for (int dy = -1; dy <= 1; ++dy)
            for (int dx = -1; dx <= 1; ++dx) {
                int nx = x + dx, ny = y + dy;
                if (nx >= 0 && nx < N && ny >= 0 && ny < M)  // Redundant in interior
                    max_diff = max(max_diff, abs(...));
            }
    }
```

**Evolved:**
```c
// Interior: skip bounds checks (x,y are guaranteed safe)
for (int y = 1; y < M-1; ++y)
    for (int x = 1; x < N-1; ++x)
        max_diff = max(max_diff, 8-neighbor max);

// Edges: handle with bounds checks
for edges: ...
```

**Good explanation:**
"Separated interior and edge pixels; interior pixels skip bounds checks, reducing branch misprediction in the hot loop by ~85%."

**Why it's good:**
- Identifies the optimization: splitting logic
- Quantifies benefit: specific improvement metric
- Addresses both code and performance

---

## Known Limitations

Explanations have inherent limitations that researchers should be aware of:

### LLM Hallucination
The LLM may generate plausible-sounding but inaccurate explanations, especially if:
- Code changes are subtle (refactoring vs. optimization)
- The evolved code contains bugs or dead code
- Optimization is indirect (e.g., enabling compiler optimizations via restructuring)

**Mitigation**: Always verify explanations against the actual evolved code.

### Subjectivity
Different researchers may legitimately disagree on the "primary" optimization strategy in a solution. The LLM response is one interpretation, not canonical truth.

**Mitigation**: Use explanations as a starting point for discussion, not a final judgment.

### Domain Specificity
The prompt is tuned for this image-processing pipeline. Applying it to other domains (matrix multiplication, sort algorithms, etc.) requires re-tuning.

**Mitigation**: When applying to new domains, test the prompt on known examples and iterate.

### Inference Costs
Generating explanations adds latency to experiments. The baseline suggests 1-2 seconds per explanation via Ollama.

**Mitigation**: Explanations are optional; experiments can run without them (backward compatible).

## Prompt Versioning Strategy

### Goals

- **Reproducibility**: Track which prompt version generated which explanations
- **Iteration safety**: Change prompts without losing or invalidating old results
- **Comparison**: Enable analysis across prompt versions (did v2.0 produce better explanations?)
- **Accountability**: Git history shows all prompt changes and rationale

### Version Numbering

Use semantic versioning: `MAJOR.MINOR`

- **MAJOR**: Conceptual change in how explanations are framed (e.g., v1 → v2: shift from optimization techniques to code transformation categories)
- **MINOR**: Refinement within the same framing (e.g., v1.0 → v1.1: added examples, clarified wording)

**Current version**: 1.0 (baseline prompt)

### Tracking Mechanism

Two levels of tracking ensure reproducibility:

**1. Human-readable header** (in `explanation_prompt.txt`):
```
# Explanation Prompt v1.0
# Last modified: 2026-05-13
# SHA256: [computed at runtime]
```
- Purpose: Git history shows version at a glance
- Not parsed by code; purely for human reference

**2. Structured metadata** (in `results.json`):
```json
{
  "metadata": {
    "explanation_config": {
      "prompt_version": "1.0",
      "prompt_hash": "a3b2c1f5e8d9a2b3",
      "prompt_changed_after_run": false
    }
  }
}
```
- Purpose: Reproducibility verification; detect if prompt file was modified after experiment
- `prompt_hash`: SHA256 of prompt text (first 16 chars) for change detection
- `prompt_changed_after_run`: If true, prompt was modified after experiment finished (indicates data integrity issue)

### When to Increment Version

**Minor bump (e.g., v1.0 → v1.1):**
- Wording clarification (grammar, examples)
- Added examples (same concepts, better illustration)
- Constraint clarification (same intent, clearer wording)
- Decision: Can re-run old experiments with new prompt for comparison; expect mostly similar explanations

**Major bump (e.g., v1.0 → v2.0):**
- Fundamentally different explanation category (e.g., shift from "techniques" to "code transformations")
- Different output format constraints (e.g., 1-2 sentences → bullet list)
- Different domain focus (e.g., "this pipeline" → "general C optimizations")
- Decision: Old and new results cannot be directly compared; must analyze separately

### Safe Iteration Workflow

When the prompt is updated:

1. **Edit `explanation_prompt.txt`**
2. **Increment version** in the header:
   ```
   # Explanation Prompt v1.1
   # Last modified: 2026-05-14
   ```
3. **Document the change** in this file (`EXPLANATION_DESIGN.md`):
   ```markdown
   ### v1.1 → v1.2 (2026-05-15)
   - Clarified examples to emphasize actual loop structures
   - Added explicit instruction: avoid speculating about branch behavior
   ```
4. **Commit to git**:
   ```bash
   git add openevolve/explanation_prompt.txt openevolve/EXPLANATION_DESIGN.md
   git commit -m "prompt(02-llm): bump explanation prompt to v1.1 — clarified examples"
   ```
5. **Re-run experiments** to capture explanations with the new prompt:
   ```bash
   make evolve-all  # Generates results.json with explanation_config.prompt_version = "1.1"
   ```
6. **Analyze comparison**:
   - Load results.json from old and new versions
   - Filter by `prompt_version` field
   - Compare explanation quality metrics

### Detecting Prompt Changes

If a researcher manually edits `explanation_prompt.txt` without incrementing the version header:

1. During experiment run, compute `prompt_hash = SHA256(prompt_text)[:16]`
2. Store in `results.json` as `explanation_config.prompt_hash`
3. Later, compute hash of current prompt file
4. If hashes differ, set `explanation_config.prompt_changed_after_run = true` in results
5. Tool (e.g., `show_results.py`) can warn: "Prompt changed after this experiment; results may not be reproducible"

### Git Commit Message Guidance

When changing the prompt, use this format:

```
prompt({phase}): {action} explanation prompt to v{version}

- {change 1}
- {change 2}

Rationale: {why the change improves explanation quality or accuracy}
```

**Example:**
```
prompt(02-llm): bump explanation prompt to v1.1 — clarified loop reordering examples

- Added explicit before/after loop structures to illustrate cache effect
- Clarified: "y outer, x inner = sequential; x outer, y inner = strides"
- Removed ambiguous "compiler optimizer" terminology

Rationale: Initial experiments showed confusion about loop ordering in evolved code;
specific examples reduce hallucination and improve explanation accuracy.
```

## Integration Points

### Phase 2 Wave 1: Infrastructure
- `explanation_generator.py`: Loads prompt, calls LLM API, returns explanations
- `consolidate_results.py`: Stores explanations and `explanation_config` metadata

### Phase 2 Wave 2: Integration
- `run_experiment.py`: Calls `generate_explanation()` after each iteration
- `show_results.py`: Displays explanations alongside optimization metrics

### Future Phases
- Multi-prompt comparison: load results across versions, analyze explanation quality trends
- Prompt optimization: use MAP-Elites on the prompt itself (meta-optimization)
- Domain generalization: adapt prompt for other domains (matrix operations, sorting, etc.)

## Summary

The explanation infrastructure enables systematic investigation of:
- What optimization strategies the LLM discovers
- How prompt design influences explanation quality
- Whether certain explanation patterns correlate with solution quality

The versioning system ensures that:
- Each result is reproducible (prompt version + hash stored)
- Prompts can evolve safely (old and new results coexist)
- Researchers can compare explanations across prompt versions
- Git history provides full audit trail of prompt changes

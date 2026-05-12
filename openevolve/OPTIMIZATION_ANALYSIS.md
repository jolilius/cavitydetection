# Optimization Ceiling Analysis

Analysis of how much reduction in memory accesses (IR-level loads + stores,
measured by the LLVM memtrace pass at `-O0`) is theoretically achievable for
the cavity-detection pipeline.

## Baseline and current best

| Program | Total accesses | mem_score |
|---------|---------------|-----------|
| Initial (`initial_program.c`) | 128,862,705 | 1.00 |
| Best evolved (iteration 83) | 58,187,247 | 2.21 |

Per-function breakdown:

| Function | Baseline | Best evolved | Improvement |
|----------|----------|-------------|-------------|
| GaussBlur | 19,894,278 | 14,569,478 | 1.37× |
| ComputeEdges | 67,604,444 | 32,492,490 | 2.08× |
| DetectRoots | 41,363,979 | 11,125,273 | 3.72× |
| run_pipeline | 4 | 6 | — |
| **Total** | **128,862,705** | **58,187,247** | **2.21×** |

## What the best evolved program actually did

1. **ComputeEdges** — interior/border separation plus explicit unrolling of the
   inner `dy/dx` loop into 8 hardcoded reads, eliminating inner loop overhead
   and bounds-check conditionals for the 510×510 interior region.

2. **DetectRoots** — eliminated the `rev[512][512]` intermediate array by
   computing `maxval - ce[x][y]` inline.  `maxval` is now returned from
   `ComputeEdges`, removing the separate scan pass that found it.

3. **GaussBlur** — 4× loop unrolling in both passes, but the full `gx[512][512]`
   intermediate array is still written and read back, and the H-blur still
   evaluates `(x >= 1 ? ... : 0)` ternaries for every pixel including interior
   ones.

## Why loop order does not help this metric

**Loop order changes do not reduce IR-level access counts.**  The LLVM pass
counts `LoadInst` / `StoreInst` instructions executed, which is the same
regardless of traversal order.  Swapping `for(x) for(y)` to `for(y) for(x)`
improves cache behaviour and wall-clock time, but leaves the instruction count
unchanged.  Only algorithmic changes that remove operations help the memtrace
score.

## Where the remaining accesses are going

At `-O0`, every named C variable is a stack allocation.  Every assignment is a
`StoreInst`; every use is a `LoadInst`.  The 124 accesses/pixel reported for
ComputeEdges is not just 9 array reads: it includes loads/stores of the 8 named
neighbor variables (`left_up`, `up`, `right_up`, …), the `diff` and `max_diff`
temporaries, and the loop counters `x` and `y` reloaded on every inner
iteration.

Accesses per pixel in the best evolved program:

| Stage | Accesses/pixel | Main cost |
|-------|---------------|-----------|
| GaussBlur | 55.7 | Ternary conditions in H-blur interior; full `gx` array |
| ComputeEdges | 123.9 | `-O0` stack traffic for 8 named temporaries |
| DetectRoots | 42.4 | Bounds-check loads for every pixel including interior |

## The three remaining opportunities

### 1. Interior/border split for GaussBlur, H-blur pass  (~4–5M savings)

The unrolled H-blur evaluates `(x >= 2 ? image_in[x-2][y] : 0)` for every
pixel, including the 96% that are interior (x: 2..509) where the guard is
always true.  At `-O0` each ternary generates a load of `x`, a comparison, a
branch, and then the array load — four instructions instead of one.  A
dedicated interior loop with the guards removed cuts this to a single direct
load per neighbor.  With four such guards per interior pixel per pass, the
savings are roughly 3–5 M accesses.

Note: replacing `gx[512][512]` with a ring buffer does **not** reduce the
IR-level instruction count — it substitutes one set of stores/loads for
another of equal size.  Ring buffers help cache efficiency (wall-clock time)
but not the memtrace score.  See `STREAMING_BUFFERS.md` for details.

### 2. Interior/border split for GaussBlur  (~5–7M savings)

The unrolled H-blur still evaluates `(x >= 1 ? image_in[x-1][y]*4 : 0)` for
every pixel.  For interior rows (x: 2..509, 96% of the image) these guards are
always true.  A dedicated interior loop with no conditionals would cut the
per-pixel cost roughly in half for those rows.

### 3. Tighten ComputeEdges and DetectRoots  (~5–8M combined)

ComputeEdges already has the interior/border split.  The remaining overhead is
almost entirely `-O0` stack noise from the 8 named neighbor variables and
diff/max temporaries — hard to eliminate without restructuring into a
pure-expression style.  DetectRoots can gain from a similar interior/border
split, removing the bounds-check loads for the 510×510 interior region.

## Practical ceiling estimate

A carefully written implementation (ring-buffer GaussBlur, interior/border
split throughout, still idiomatic C at `-O0`):

| Stage | Minimum realistic | Basis |
|-------|------------------|-------|
| GaussBlur (ring-buffer + interior split) | 3–5M | ~12–15 accesses/pixel |
| ComputeEdges (current structure, tightened) | 18–22M | ~70–85 accesses/pixel |
| DetectRoots (interior split) | 7–9M | ~27–34 accesses/pixel |
| **Total** | **28–36M** | |
| **mem_score** | **~4–5×** | |

A more aggressive fully-fused single-pass implementation that also eliminates
`gxy[512][512]` and `ce[512][512]` (processing all four stages with a shared
row-strip ring buffer) could push to **6–8×**, but requires complex streaming
C that LLMs have historically struggled to keep pixel-exact.

## Summary

The current best (2.21×) is roughly halfway to the practical ceiling (~4–5×),
with the bulk of the remaining gain concentrated in **GaussBlur** — the one
stage that was not properly restructured by the best evolved program.

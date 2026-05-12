# Experiment Results: baseline vs prompt1

Comparison of the best programs found by the two prompt experiments against
the unoptimised initial program.  All access counts are IR-level loads +
stores measured by the LLVM memtrace pass at `-O0`, `BENCH_RUNS=1`.

## Scores at a glance

| Experiment | mem_score | Total accesses | Reduction | Best at iter |
|------------|-----------|----------------|-----------|-------------|
| Initial program | 1.000 | 128,862,705 | — | — |
| baseline | 1.155 | 111,572,927 | 13.4% | 5 |
| prompt1 | 1.287 | 100,154,018 | 22.3% | 52 |

## Prompts used

**baseline** — detailed guidance listing six specific transformations
(single-pass fusion, loop-order swap, strip tiling, buffer elimination,
redundancy removal, free restructuring) plus hard constraints.

**prompt1** — minimal guidance: "minimise memory accesses", "restructure
freely", hard constraints only.  No transformation hints.

## Access counts by function

| Function | Initial | baseline best | prompt1 best |
|----------|---------|---------------|--------------|
| GaussBlur | 19,894,278 | *(inlined)* | 19,894,278 |
| ComputeEdges | 67,604,444 | *(inlined)* | — |
| DetectRoots | 41,363,979 | *(inlined)* | — |
| ComputeEdgesAndDetectRoots | — | — | 80,259,736 |
| run_pipeline | 4 | 111,572,927 | 4 |
| **Total** | **128,862,705** | **111,572,927** | **100,154,018** |

The baseline best inlined all four stages into a single `run_pipeline`;
the per-stage breakdown is therefore not available for that program.

## What prompt1's best program changed

### GaussBlur — unchanged

The code is identical to the initial program: same loop order
(`for y { for x {...} }`), same boundary conditionals, same `gx[512][512]`
intermediate array.  19,894,278 accesses in both.

### ComputeEdges + DetectRoots → fused `ComputeEdgesAndDetectRoots`

Three concrete changes inside the fused function account for the 28.7M
reduction (108,968,423 → 80,259,736):

**1. Eliminated the standalone maxval scan pass.**
The initial `DetectRoots` begins with a dedicated loop over all 262,144
pixels solely to find the maximum edge value.  The fused function tracks
`maxval` as a running maximum during the edge-computation loop itself,
removing one full pass over `ce[]`.

**2. Eliminated the `rev[512][512]` intermediate array.**
The initial program writes `rev[x][y] = maxval - ce[x][y]` for every pixel
(262K stores), then reads `rev` in the local-maxima loop.  The fused function
computes `maxval - ce[x][y]` inline wherever `rev` was read, removing both
the write pass and the array reads.

**3. Fixed the outer-loop early exit in the local-maxima check.**
The initial `DetectRoots` breaks out of the inner `dx` loop when a larger
neighbour is found, but the outer `dy` loop has no guard — it keeps iterating
after the answer is already known.  The fused function adds
`if (!is_maximum) break;` after the inner loop, so both levels exit as soon
as a larger neighbour is found.  For the majority of pixels (which are not
local maxima) this terminates the search after 1–3 neighbour checks rather
than exhausting all nine.

## What the baseline best program changed

The baseline best inlined all four stages into a single `run_pipeline`,
applied the same double-loop early-exit fix, and tracked `maxval` during
edge computation — but **kept the `rev[512][512]` array**.  This is a
strictly weaker version of prompt1's insight: same structural changes minus
the intermediate-array elimination.  It reached its best score at iteration 5
and never improved further.

The detailed transformation hints in the baseline prompt did not lead to a
better result.  The model found a quick shallow optimisation early and
converged, while the simpler prompt1 explored longer and found a deeper one.

## Why neither run approached the previous best (2.21×)

A longer 200-iteration run (different models, starting from a checkpoint)
previously found a program that separated interior pixels from border pixels
and replaced the inner `dy`/`dx` loops with eight hardcoded neighbour reads.
That eliminated the loop-counter loads and address-computation overhead for
96% of the image — the dominant cost in `ComputeEdges`.

Neither of the short experiments here found that transformation.  The
`ComputeEdgesAndDetectRoots` inner loop in the prompt1 best still uses
`for (ny = start_y; ny <= end_y)` / `for (nx = start_x; nx <= end_x)` with
an `if (nx != x || ny != y)` guard — structurally the same overhead as the
original, just with neater variable names.

## Remaining headroom

Based on the analysis in `OPTIMIZATION_ANALYSIS.md`, the practical ceiling
for the memtrace score is approximately **4–5×** (25–32M accesses).  The
largest untouched opportunity is the interior/border split in `ComputeEdges`
and the removal of boundary conditionals in `GaussBlur`, which together
could save another 30–50M accesses.

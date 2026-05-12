# Streaming Ring Buffers — Concept and Relevance to the Memtrace Metric

## The concept

A streaming ring buffer is a small circular array that holds only the last K
elements needed for a computation.  Instead of materialising a full N-element
intermediate array, writing it in one pass and reading it back in the next, you
keep K elements in a tiny buffer and process the pipeline in a single sweep.

### Simple example: 1D blur applied twice

Consider 8 values processed by a 3-tap blur `[1,2,1]/4` applied twice — a
direct analogue of the separable Gaussian blur in `GaussBlur`.

```
Input:  [a, b, c, d, e, f, g, h]
Pass 1: B[i] = (in[i-1] + 2*in[i] + in[i+1]) / 4
Pass 2: C[i] = (B[i-1] + 2*B[i] + B[i+1]) / 4
```

#### Traditional two-pass approach

```c
int B[8];

// Pass 1: compute and store all of B
for (int i = 0; i < 8; i++)
    B[i] = blur(in, i);            // 8 stores to B

// Pass 2: read B to compute C
for (int i = 0; i < 8; i++)
    C[i] = (B[i-1] + 2*B[i] + B[i+1]) / 4;   // ~3 loads from B per step

// Total accesses to B: 8 stores + ~22 reads = 30
```

#### Streaming approach with a ring of 3

To compute `C[i]` you only ever need `B[i-1]`, `B[i]`, and `B[i+1]` — three
consecutive values.  Everything older can be discarded:

```c
int ring[3];

ring[0] = blur(in, 0);   // pre-fill two slots
ring[1] = blur(in, 1);

for (int i = 0; i < 8; i++) {
    ring[(i+2) % 3] = blur(in, i+2);                      // 1 store to ring
    C[i] = (ring[(i-1+3)%3] + 2*ring[i%3] + ring[(i+1)%3]) / 4;  // 3 reads
}
// Total accesses to ring: 8 stores + ~22 reads = 30
```

**The load/store count is identical.**  What changed is only the size of the
intermediate storage: `ring[3]` = 3 elements instead of `B[8]` = 8 elements.

---

## What actually differs: cache efficiency vs instruction count

| | Two-pass (`B[8]`) | Streaming (`ring[3]`) |
|--|--|--|
| Load/store instruction count | 30 | 30 |
| Working set | 8 elements | 3 elements |
| Cache behaviour (large N) | B is evicted and reloaded across passes | ring stays permanently hot |

For N = 8 neither matters.  For N = 512, `B[512]` = 512 bytes that spill out
of cache between passes; the ring always fits in a handful of registers.  This
is the real gain — and it directly reduces wall-clock time and cache-miss
counts.

The **LLVM memtrace score counts IR-level `LoadInst` / `StoreInst`
instructions**, not cache events.  The streaming version executes the same
number of memory instructions as the full-array version.  Streaming ring
buffers therefore **do not improve the memtrace score directly**.

---

## Correction to OPTIMIZATION_ANALYSIS.md

`OPTIMIZATION_ANALYSIS.md` incorrectly states:

> Eliminate `gx[512][512]` in GaussBlur (~4–5M savings)
> … eliminating ~524K array stores and ~524K array reads.
> At -O0 overhead that translates to roughly 3–5M fewer accesses.

This claim holds for a cache-miss metric (e.g. valgrind D-refs) but not for
the IR-level instruction count.  Replacing `gx[512][512]` with a ring buffer
substitutes one set of stores/loads for another of equal size; the total
instruction count does not change.

### What does reduce the memtrace count for GaussBlur

The genuine remaining opportunity is **eliminating the ternary conditionals for
interior pixels**.  The current unrolled H-blur contains expressions like:

```c
(x >= 2 ? image_in[x-2][y] : 0)
```

For interior rows (x: 2..509, covering 96% of the image) the guard is always
true.  At `-O0` each ternary generates:

- 1 load of `x`
- 1 comparison
- conditional branch
- 1 load of `image_in[x-2][y]` (taken branch)

A dedicated interior loop with the guards removed replaces those four
operations with a single direct load.  With four such guards per pixel per
pass, across 508 interior rows × 512 columns × 2 passes, the savings are on
the order of **3–5 M accesses** — the same figure as before, but from a
different and correct source.

### Revised ceiling for GaussBlur

| Approach | Estimated accesses | Basis |
|----------|-------------------|-------|
| Current best | 14,569,478 | 4× unrolled, ternaries present |
| Interior/border split, no ternaries | ~4–6 M | ~8–12 accesses/pixel for interior |

The overall ceiling estimate in `OPTIMIZATION_ANALYSIS.md` (~4–5× total
mem_score) remains roughly correct, but the mechanism for GaussBlur is
interior/border separation and direct reads — not streaming ring buffers.

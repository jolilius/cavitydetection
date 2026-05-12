# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Build commands

```sh
make                      # build cavitydetection (requires SDL2)
make run                  # build and run the main binary
make loopoptimization1    # build the standalone loop-optimization example
make run-loopoptimization1
make profile              # build with gprof, run, write gprof_report.txt
make memtrace             # build LLVM-instrumented binary and run it
MEMTRACE_LOG=1 ./cavitydetection_traced   # full per-access trace → memtrace.log
make clean
```

The Makefile auto-detects LLVM via `brew --prefix llvm`; override with `LLVM_PREFIX=/path/to/llvm make memtrace`.

## Architecture

This project is an image-processing pipeline for cavity/edge detection, with a separate LLVM instrumentation subsystem for memory-access profiling.

### Detection pipeline (`cavitydetection.c`, `render.c`, `testimage.c`)

All pipeline stages operate on fixed-size `unsigned char image[512][512]` arrays (dimensions defined as `N`/`M = 512`). The pipeline runs sequentially in `main`:

1. `GenerateTestImage` (`testimage.c`) — random-walk blob with interior shading, producing a synthetic grayscale image.
2. `GaussBlur` — separable 5-tap Gaussian (`[1,4,6,4,1]/16`) applied horizontally then vertically.
3. `ComputeEdges` — replaces each pixel with its maximum absolute difference across all 8 neighbors.
4. `DetectRoots` — calls `Reverse` (invert relative to max value), then marks pixels that are local maxima in the reversed image as 255, others as 0.

After each stage, `DisplayImage` (`render.c`) opens an SDL2 window showing the intermediate result. The user presses any key or closes the window to advance to the next stage.

**Array layout note**: arrays are indexed `[x][y]` (x is the outer dimension), which is column-major in memory. This is significant when reasoning about cache behavior, which is a primary purpose of this codebase.

### LLVM memory-tracing subsystem (`memtrace_pass.cpp`, `memtrace_runtime.c`)

A two-part LLVM instrumentation system used to count and optionally log every load/store in the pipeline functions:

- `memtrace_pass.cpp` — a new-pass-manager module plugin (LLVM 15+, opaque pointers) that walks every non-intrinsic, non-runtime function and inserts calls to `__memtrace_load` / `__memtrace_store` before each load/store instruction, passing the pointer, access size, function name, and source line.
- `memtrace_runtime.c` — the runtime callbacks. By default (count-only mode) they accumulate per-function load/store counters and print a summary table on exit. With `MEMTRACE_LOG=1` they additionally append every access to `memtrace.log` in the format `<L|S> <func> <line> <addr> <size_bytes>`.

The build pipeline for memtrace: compile the pass plugin as a `.dylib` → emit LLVM bitcode for `cavitydetection.c` → run `opt` with the plugin to instrument the bitcode → compile instrumented bitcode to an object → link with the runtime and existing `render.o`/`testimage.o`.

### `loopoptimization1.c`

A standalone, self-contained program (no SDL2 dependency) used as a study case for loop optimization. It demonstrates two sequential loops (initialization and computation) and is independently buildable via `make loopoptimization1`.

## OpenEvolve integration (`openevolve/`)

Uses [OpenEvolve](../openevolve) to evolve cache-efficient versions of the pipeline functions via LLM-guided mutation.

**Files:**
- `openevolve/initial_program.c` — self-contained seed (no SDL2): all four pipeline functions inside `EVOLVE-BLOCK` markers, plus frozen reference implementations for pixel-exact correctness checking.
- `openevolve/evaluator.py` — compiles with `gcc -O0`, checks correctness, measures wall-clock time (20 bench runs, median of 3) and D1 cache misses via `valgrind --tool=cachegrind` (1 bench run). Score 1.0 = unoptimised baseline.
- `openevolve/config.yaml` — Anthropic API (reads `$ANTHROPIC_API_KEY`), 80 iterations, diff-based evolution.

**Running:**

```sh
# Ollama must be running (ollama serve)
../openevolve/.venv/bin/python ../openevolve/openevolve-run.py \
    openevolve/initial_program.c openevolve/evaluator.py \
    --config openevolve/config.yaml --iterations 80
```

To resume from a checkpoint:

```sh
... --checkpoint <output_dir> --iterations 20
```

**Calibration:** baseline scores ~1.0 (`time_ms ≈ 420`, `d1_misses ≈ 7.7M`). The primary opportunity is swapping the `for(y) for(x)` loop order to `for(x) for(y)` throughout, which turns stride-512 cache misses into sequential byte accesses and should yield ~5× fewer D1 misses.

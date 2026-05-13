# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Prerequisites

### System packages

**Linux (Ubuntu/Debian):**
```sh
sudo apt install gcc make libsdl2-dev llvm clang
```

**macOS:**
```sh
brew install llvm sdl2
```

The Makefile auto-detects LLVM versions 15–20 via `brew --prefix llvm`; override with `LLVM_PREFIX=/path/to/llvm make memtrace`.

### Ollama (for OpenEvolve experiments)

Install from https://ollama.com, then pull a 30B-class coding model (smaller models produce invalid C):

```sh
ollama pull qwen2.5-coder:32b
```

Start the server before running experiments: `ollama serve`.

### OpenEvolve

Clone as a sibling directory:

```sh
git clone https://github.com/codelion/openevolve ../openevolve
cd ../openevolve
python3 -m venv .venv
.venv/bin/pip install -e .
cd -
```

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

**Array layout and cache optimization**: Arrays are indexed `[x][y]` where x is the outer (row) dimension. In row-major memory layout, `image[x][y]` is at offset `x*512 + y`, so an inner loop over `y` accesses sequential bytes while an inner loop over `x` strides 512 bytes per step. **Swapping loop order from `for(x) for(y)` to `for(y) for(x)` is the single most impactful cache optimization available** — converting stride-512 cache misses into sequential accesses can reduce D1 misses by ~5×. This is the primary optimization opportunity explored in OpenEvolve experiments.

### LLVM memory-tracing subsystem (`memtrace_pass.cpp`, `memtrace_runtime.c`)

A two-part LLVM instrumentation system used to count and optionally log every load/store in the pipeline functions:

- `memtrace_pass.cpp` — a new-pass-manager module plugin (LLVM 15+, opaque pointers) that walks every non-intrinsic, non-runtime function and inserts calls to `__memtrace_load` / `__memtrace_store` before each load/store instruction, passing the pointer, access size, function name, and source line.
- `memtrace_runtime.c` — the runtime callbacks. By default (count-only mode) they accumulate per-function load/store counters and print a summary table on exit. With `MEMTRACE_LOG=1` they additionally append every access to `memtrace.log` in the format `<L|S> <func> <line> <addr> <size_bytes>`.

The build pipeline for memtrace: compile the pass plugin as a `.dylib` → emit LLVM bitcode for `cavitydetection.c` → run `opt` with the plugin to instrument the bitcode → compile instrumented bitcode to an object → link with the runtime and existing `render.o`/`testimage.o`.

### `loopoptimization1.c`

A standalone, self-contained program (no SDL2 dependency) used as a study case for loop optimization. It demonstrates two sequential loops (initialization and computation) and is independently buildable via `make loopoptimization1`.

## OpenEvolve integration (`openevolve/`)

Uses [OpenEvolve](../openevolve) to evolve cache-efficient versions of the pipeline functions via LLM-guided mutation. An LLM proposes code mutations; each candidate is evaluated for correctness and memory-access efficiency (measured via LLVM instrumentation).

**Key files:**
- `openevolve/initial_program.c` — self-contained seed (no SDL2): the pipeline functions to evolve, wrapped in `EVOLVE-BLOCK` markers, plus frozen reference implementations for pixel-exact correctness checks.
- `openevolve/evaluator.py` — compiles with `gcc -O0`, verifies correctness, and measures memory accesses via the LLVM memtrace instrumentation. Score formula: `mem_score = 128,862,705 / accesses` (scores > 1.0 = better than baseline).
- `openevolve/config.yaml` — OpenEvolve settings (model names, iteration limits, early stopping, population size).
- `openevolve/prompts/` — system message variants; each `.txt` file is treated as a separate experiment.

### Baseline metrics

The unoptimized baseline (initial_program.c, gcc -O0) makes **128,862,705** total memory accesses:

| Function      | Accesses    |
|---------------|-------------|
| GaussBlur     | 19,894,278  |
| ComputeEdges  | 67,604,444  |
| DetectRoots   | 41,363,979  |
| run_pipeline  | 4           |

### One-time setup

Before running experiments, compile the LLVM pass plugin and runtime:

```sh
make memtrace_pass.so memtrace_runtime.o
```

### Running experiments

Run a single prompt variant (80 iterations, writes to `openevolve_output/<name>/`):

```sh
../openevolve/.venv/bin/python openevolve/run_experiment.py <prompt_name> --iterations 80
```

Run all prompt variants in `openevolve/prompts/`:

```sh
make evolve-all                 # 80 iterations per prompt
ITERATIONS=200 make evolve-all  # override iteration count
```

View ranked results:

```sh
make show-results
```

Output shows `mem_score`, iteration where best was found (convergence speed), total accesses, and % reduction from baseline.

### Configuration

Edit `openevolve/config.yaml` to adjust:

| Key | Purpose |
|-----|---------|
| `llm.primary_model` | Ollama model name (e.g. `qwen2.5-coder:32b`) |
| `llm.api_base` | Ollama endpoint (default `http://localhost:11434/v1/`) |
| `database.population_size` | MAP-Elites population size |
| `early_stopping_patience` | Iterations without improvement before stopping |

The `prompt.system_message` in `config.yaml` is overridden at runtime by the prompt file; editing the file directly only affects bare `make evolve` runs.

### Adding a new prompt variant

1. Copy `openevolve/prompts/baseline.txt` to `openevolve/prompts/<name>.txt`
2. Edit the system message
3. Run `make evolve-all` or `run_experiment.py <name>` for that variant alone

## Remote infrastructure (mandelbrot)

Experiments run on **mandelbrot.abo.fi** at `100.89.90.6` (Tailscale). Ollama is bound to `0.0.0.0:11434` on that machine.

When running OpenEvolve locally, set `llm.api_base` in `config.yaml` to:

```
http://100.89.90.6:11434/v1/
```

SSH access: `jolilius@100.89.90.6`

## Python packages

Always use `uv` instead of `pip` or `pip3` when installing packages.

## Session summaries

When Johan says **"save session"** (or any close variant: "log session", "save this session"), immediately write a summary note to the Obsidian vault at:

```
/Users/jolilius/home/doc/vaults/Projects2024-2025/1 Projects/openevolve/sessions/YYYY-MM-DD-HHMM-summary.md
```

Use this frontmatter and structure:

```markdown
---
title: "openevolve session — YYYY-MM-DD"
type: projectnote
project: oe
date: YYYY-MM-DD
---

# Session summary — YYYY-MM-DD HH:MM

## What was done
[2–5 bullet points — concrete actions taken]

## What worked
[findings, successful approaches]

## What didn't work / open questions
[failures, surprises, unresolved issues]

## Next steps
[concrete next actions]
```

Create the `sessions/` folder if it doesn't exist. Use the actual session start time for the filename timestamp. Write the file immediately when the trigger phrase is used — do not wait to be asked twice.

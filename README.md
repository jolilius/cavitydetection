# Cavity Detection — Pipeline Optimisation Study

An image-processing pipeline for cavity/edge detection, used as a benchmark for
studying how LLM-guided evolutionary search finds cache-efficient C code.  The
central experiment measures how much an LLM can reduce the raw number of memory
accesses in the pipeline, and how the wording of the prompt affects convergence
speed.

---

## Repository layout

```
cavitydetection/
├── cavitydetection.c       Main pipeline (SDL2 display after each stage)
├── render.c / render.h     SDL2 window helper
├── testimage.c / testimage.h  Synthetic test-image generator
├── loopoptimization1.c     Standalone loop-order study (no SDL2)
├── memtrace_pass.cpp       LLVM instrumentation pass (counts every load/store)
├── memtrace_runtime.c      Runtime callbacks: per-function counters + log
├── Makefile
└── openevolve/
    ├── initial_program.c   Self-contained seed (no SDL2); the code to evolve
    ├── evaluator.py        OpenEvolve evaluator: compile → correctness → memtrace
    ├── config.yaml         OpenEvolve settings (models, database, prompt template)
    ├── run_experiment.py   Launcher: run one named-prompt experiment
    ├── show_results.py     Print a ranked table of all completed experiments
    └── prompts/
        └── baseline.txt    The starting system-message; copy to add variants
```

---

## Prerequisites

### System packages

**Linux (Ubuntu/Debian):**
```sh
sudo apt install gcc make libsdl2-dev llvm clang
```
The Makefile auto-detects LLVM versions 17–20.  LLVM 15 or later is required
(new-pass-manager plugin API).

**macOS:**
```sh
brew install llvm sdl2
```
Override the LLVM prefix if needed: `LLVM_PREFIX=/opt/homebrew/opt/llvm make memtrace`.

### Ollama (local LLM server)

The OpenEvolve runs use Ollama-served models.  Install from https://ollama.com,
then pull the two models referenced in `config.yaml`:

```sh
ollama pull qwen3-coder:30b
ollama pull qwen2.5-coder:32b
```

Smaller models (e.g. `phi3`, `qwen3:4b`) work but produce mostly invalid C and
stall the search.  30B-class coding models are the practical minimum.

### OpenEvolve

Clone the framework as a **sibling** of this repository:

```sh
git clone https://github.com/codelion/openevolve ../openevolve
cd ../openevolve
python3 -m venv .venv
.venv/bin/pip install -e .
cd -
```

The scripts in `openevolve/` expect `../openevolve/.venv/bin/python` to exist.

---

## Building and running

```sh
make                  # build cavitydetection (requires SDL2)
make run              # build and run — SDL2 window shows each pipeline stage
make loopoptimization1
make run-loopoptimization1
make clean
```

The SDL2 app pauses at each stage; press any key or close the window to advance.

---

## LLVM memory tracing

The memtrace subsystem instruments every load and store in the pipeline and
prints a per-function count on exit.

```sh
make memtrace                        # build and run; prints summary table
MEMTRACE_LOG=1 ./cavitydetection_traced   # also write per-access log → memtrace.log
```

**How it works:**

1. `memtrace_pass.cpp` — an LLVM module pass that walks the IR and inserts a
   call to `__memtrace_load` / `__memtrace_store` before every load/store
   instruction, recording the pointer, size, function name, and source line.
2. `memtrace_runtime.c` — accumulates per-function counters and prints a
   summary on program exit.  With `MEMTRACE_LOG=1` it additionally writes
   every individual access to `memtrace.log`.

The pass is compiled as a shared-library plugin and loaded by `opt` at build
time, so the runtime overhead is only present in the `_traced` binary.

**Why this instead of Valgrind cachegrind:**  the LLVM pass counts IR-level
loads and stores in the evolved pipeline functions only.  Valgrind works on
the finished binary and counts the entire process including the reference
pipeline run and the C runtime.  The LLVM count reflects the algorithm's
memory-access structure directly, independent of cache topology.

---

## OpenEvolve prompt study

### How it works

OpenEvolve uses a MAP-Elites evolutionary algorithm to search for C
implementations of `run_pipeline` that score higher than the unoptimised
baseline.  An LLM proposes mutations; each candidate is evaluated by
`evaluator.py`, which:

1. Compiles with `gcc -O0` and checks correctness (pixel-exact match against
   the frozen reference implementation).
2. Builds an LLVM-instrumented binary and counts memory accesses for a single
   pipeline run.
3. Returns `mem_score = 128,862,705 / accesses` — scores above 1.0 mean fewer
   accesses than the baseline.

The baseline (initial program, `gcc -O0`) makes **128,862,705** loads and stores:

| Function      | Accesses    |
|---------------|-------------|
| GaussBlur     | 19,894,278  |
| ComputeEdges  | 67,604,444  |
| DetectRoots   | 41,363,979  |
| run_pipeline  | 4           |
| **Total**     | **128,862,705** |

### One-time build step

The pass plugin and runtime object must be compiled before running evolution:

```sh
make memtrace_pass.so memtrace_runtime.o
```

This is needed once per machine (or after `make clean`).

### Running a single experiment

```sh
../openevolve/.venv/bin/python openevolve/run_experiment.py baseline --iterations 80
```

Results are written to `openevolve/openevolve_output/baseline/`.

### Running all prompt experiments

```sh
make evolve-all                      # 80 iterations per prompt (default)
ITERATIONS=200 make evolve-all       # override iteration count
```

Every `.txt` file in `openevolve/prompts/` is treated as one experiment.
Experiments run sequentially; each starts fresh from `initial_program.c`.

### Viewing results

```sh
make show-results
```

Example output:

```
prompt           mem_score   iter_found       accesses  reduction
-----------------------------------------------------------------
loop_order_only     2.4500           41     52,597,022     59.2%
baseline            2.2146           83     58,187,247     54.8%
```

`iter_found` is the iteration at which the best program was first discovered —
the primary measure of convergence speed.

### Adding a new prompt variant

1. Copy `openevolve/prompts/baseline.txt` to `openevolve/prompts/<name>.txt`.
2. Edit the new file.
3. Run `make evolve-all` (or `run_experiment.py <name>` for just that variant).

No other files need to change.

### Configuration

`openevolve/config.yaml` controls everything except the system message:

| Key | Purpose |
|-----|---------|
| `llm.primary_model` / `secondary_model` | Ollama model names |
| `llm.api_base` | Ollama endpoint (default `http://localhost:11434/v1/`) |
| `database.population_size` | MAP-Elites population |
| `early_stopping_patience` | Iterations without improvement before stopping |
| `early_stopping_metric` | Must be `mem_score` to match the evaluator |

The `prompt.system_message` in `config.yaml` is overridden at runtime by
`run_experiment.py` from the prompt file; editing it directly only affects
the bare `make evolve` command.

---

## Phase 2: LLM Explanations (COMPLETE)

Experiments now capture LLM-generated explanations for each iteration, describing the optimization strategy employed by the LLM.

**Features:**
- Automatic explanation generation for code transformations
- Explanations stored in results.json and accessible via pandas DataFrame
- Optional: disable with `EXPLAIN_GENERATIONS=0` if LLM is unavailable
- Non-blocking: experiments succeed even if explanation generation fails

**Usage:**
```python
from openevolve.results_loader import load_all_results
df = load_all_results()

# View explanations alongside results
explained = df[df['explanation'].notna()]
print(explained[['iteration', 'prompt', 'improvement_percent', 'explanation']])
```

See `.planning/RESULTS_USAGE.md` for detailed explanation analysis examples.

### Quick Start: Testing with Explanations

Test explanation generation with a 10-iteration run:
```bash
make evolve-explain-test    # Run baseline prompt with explanations
make show-explanations      # View results with explanations
```

Disable explanations if LLM is unavailable:
```bash
EXPLAIN_GENERATIONS=0 make evolve-all
```

See `.planning/RESULTS_FORMAT.md` for the unified results schema and explanation field documentation.

---

## The detection pipeline

All stages operate on `unsigned char image[512][512]` arrays (`N = M = 512`).

| Stage | Function | What it does |
|-------|----------|-------------|
| 1 | `GaussBlur` | Separable 5-tap Gaussian `[1,4,6,4,1]/16` — horizontal pass then vertical |
| 2 | `ComputeEdges` | Each pixel ← max absolute difference across all 8 neighbours |
| 3 | `DetectRoots` | Invert relative to max value; mark local maxima as 255, others as 0 |

**Array layout:** arrays are indexed `[x][y]` where `x` is the outer (row)
dimension.  In C row-major layout `image[x][y]` is at offset `x*512 + y`, so
an inner loop over `y` is sequential in memory while an inner loop over `x`
strides 512 bytes per step.  Swapping loop order from `for(x) for(y)` to
`for(y) for(x)` is the single most impactful cache optimisation available.

---

## Profiling (gprof)

```sh
make profile          # build with -pg, run, write gprof_report.txt
```

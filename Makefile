CC = gcc
CFLAGS = -Wall -Wextra -std=c99 -O2 -D_THREAD_SAFE

# ── LLVM memory-access tracing ──────────────────────────────────────────────
# Detect platform and find LLVM.
# Override with: LLVM_PREFIX=/path/to/llvm make memtrace
UNAME_S := $(shell uname -s)

ifeq ($(UNAME_S),Darwin)
  LLVM_PREFIX ?= $(shell \
    BREW_PFX=$$(brew --prefix llvm 2>/dev/null); \
    if [ -n "$$BREW_PFX" ] && [ -d "$$BREW_PFX/bin" ]; then \
      echo "$$BREW_PFX"; \
    elif [ -d /usr/local/opt/llvm/bin ]; then \
      echo /usr/local/opt/llvm; \
    else \
      echo LLVM_NOT_FOUND; \
    fi)
  PASS_EXT      = dylib
  PASS_LDFLAGS  = -dynamiclib -Wl,-undefined,dynamic_lookup
else
  # Linux: prefer the highest versioned LLVM that has clang
  LLVM_PREFIX ?= $(shell \
    for v in 20 19 18 17; do \
      if [ -x /usr/lib/llvm-$$v/bin/clang ]; then \
        echo /usr/lib/llvm-$$v; exit; \
      fi; \
    done; \
    echo LLVM_NOT_FOUND)
  PASS_EXT      = so
  PASS_LDFLAGS  = -shared -fPIC
endif

ifeq ($(LLVM_PREFIX),LLVM_NOT_FOUND)
  $(error LLVM not found. On Linux: sudo apt install llvm clang)
endif

LLVM_CONFIG     = $(LLVM_PREFIX)/bin/llvm-config
LLVM_CLANG      = $(LLVM_PREFIX)/bin/clang
LLVM_CLANGXX    = $(LLVM_PREFIX)/bin/clang++
LLVM_OPT        = $(LLVM_PREFIX)/bin/opt
LLVM_CXXFLAGS   = $(shell $(LLVM_CONFIG) --cxxflags 2>/dev/null) \
                  $(if $(filter Linux,$(UNAME_S)),-I/usr/include/$(notdir $(LLVM_PREFIX)))
MEMTRACE_PASS   = memtrace_pass.$(PASS_EXT)
MEMTRACE_RT_OBJ = memtrace_runtime.o
MEMTRACE_BC     = cavitydetection_memtrace.bc
MEMTRACE_IOBJ   = cavitydetection_memtrace.o
MEMTRACE_BIN    = cavitydetection_traced
LDFLAGS =
GPROF_CFLAGS = -Wall -Wextra -std=c99 -pg -D_THREAD_SAFE

# SDL2 flags are only needed for the render/display target and the main program
ifeq ($(UNAME_S),Darwin)
  SDL_CFLAGS  = $(shell sdl2-config --cflags 2>/dev/null || echo -I/opt/homebrew/include/SDL2)
  SDL_LDFLAGS = $(shell sdl2-config --libs   2>/dev/null || echo -L/opt/homebrew/lib -lSDL2)
else
  SDL_CFLAGS  = $(shell sdl2-config --cflags 2>/dev/null || pkg-config --cflags sdl2 2>/dev/null)
  SDL_LDFLAGS = $(shell sdl2-config --libs   2>/dev/null || pkg-config --libs   sdl2 2>/dev/null)
endif
TARGET = cavitydetection
TARGET_GPROF = cavitydetection_gprof
SRC = cavitydetection.c render.c testimage.c
OBJ = cavitydetection.o render.o testimage.o
OBJ_GPROF = cavitydetection_gprof.o render_gprof.o testimage_gprof.o
LOOP_SRC = loopoptimization1.c
LOOP_OBJ = loopoptimization1.o
LOOP_GPROF_OBJ = loopoptimization1_gprof.o
GPROF_OUT = gmon.out

all: $(TARGET)

$(TARGET): $(OBJ)
	$(CC) $(CFLAGS) -o $(TARGET) $(OBJ) $(LDFLAGS) $(SDL_LDFLAGS)

# Standalone target to build loopoptimization1 tool
loopoptimization1: $(LOOP_OBJ)
	$(CC) $(CFLAGS) -o loopoptimization1 $(LOOP_OBJ) $(LDFLAGS)

loopoptimization1_gprof: $(LOOP_GPROF_OBJ)
	$(CC) $(GPROF_CFLAGS) -o loopoptimization1_gprof $(LOOP_GPROF_OBJ) $(LDFLAGS)

cavitydetection.o: cavitydetection.c
	$(CC) $(CFLAGS) -c cavitydetection.c

loopoptimization1.o: loopoptimization1.c
	$(CC) $(CFLAGS) -c loopoptimization1.c

render.o: render.c
	$(CC) $(CFLAGS) $(SDL_CFLAGS) -c render.c

$(TARGET_GPROF): $(OBJ_GPROF)
	$(CC) $(GPROF_CFLAGS) -o $(TARGET_GPROF) $(OBJ_GPROF) $(LDFLAGS)

cavitydetection_gprof.o: cavitydetection.c
	$(CC) $(GPROF_CFLAGS) -c cavitydetection.c -o cavitydetection_gprof.o

render_gprof.o: render.c
	$(CC) $(GPROF_CFLAGS) $(SDL_CFLAGS) -c render.c -o render_gprof.o

loopoptimization1_gprof.o: loopoptimization1.c
	$(CC) $(GPROF_CFLAGS) -c loopoptimization1.c -o loopoptimization1_gprof.o

testimage_gprof.o: testimage.c
	$(CC) $(GPROF_CFLAGS) -c testimage.c -o testimage_gprof.o

# ── memtrace build rules ────────────────────────────────────────────────────
# 1. Compile the pass plugin
$(MEMTRACE_PASS): memtrace_pass.cpp
	$(LLVM_CLANGXX) $(PASS_LDFLAGS) $(LLVM_CXXFLAGS) -o $@ $<

# 2. Compile the runtime callbacks
$(MEMTRACE_RT_OBJ): memtrace_runtime.c
	$(LLVM_CLANG) -O0 -c -o $@ $<

# 3. Emit LLVM bitcode for cavitydetection.c (no SDL needed here)
$(MEMTRACE_BC): cavitydetection.c render.h testimage.h
	$(LLVM_CLANG) -O0 -g -emit-llvm -c -o $@ $<

# 4. Run the instrumentation pass, then compile the resulting bitcode to an object
$(MEMTRACE_IOBJ): $(MEMTRACE_BC) $(MEMTRACE_PASS)
	$(LLVM_OPT) -load-pass-plugin ./$(MEMTRACE_PASS) -passes=memtrace \
	            $(MEMTRACE_BC) -o cavitydetection_instr.bc
	$(LLVM_CLANG) -O0 -c cavitydetection_instr.bc -o $@

# 5. Link instrumented object + runtime + existing render/testimage objects
$(MEMTRACE_BIN): $(MEMTRACE_IOBJ) $(MEMTRACE_RT_OBJ) render.o testimage.o
	$(LLVM_CLANG) -O0 -o $@ $^ $(SDL_LDFLAGS)

memtrace: $(MEMTRACE_BIN)
	./$(MEMTRACE_BIN)
	@echo ""
	@echo "Tip: run  MEMTRACE_LOG=1 ./$(MEMTRACE_BIN)  for a full per-line trace in memtrace.log"

profile: $(TARGET_GPROF)
	./$(TARGET_GPROF)
	gprof $(TARGET_GPROF) $(GPROF_OUT) > gprof_report.txt
	@echo "Profile report saved to gprof_report.txt"

clean:
	rm -f $(OBJ) $(OBJ_GPROF) $(TARGET) $(TARGET_GPROF) $(GPROF_OUT) gprof_report.txt \
		$(LOOP_OBJ) $(LOOP_GPROF_OBJ) loopoptimization1 loopoptimization1_gprof \
		memtrace_pass.so memtrace_pass.dylib \
		$(MEMTRACE_RT_OBJ) $(MEMTRACE_BC) $(MEMTRACE_IOBJ) \
		cavitydetection_instr.bc $(MEMTRACE_BIN) memtrace.log

run-loopoptimization1: loopoptimization1
	./loopoptimization1

run: $(TARGET)
	./$(TARGET)

OPENEVOLVE_PYTHON = ../openevolve/.venv/bin/python
OPENEVOLVE_RUN    = ../openevolve/openevolve-run.py
PROMPTS           = $(wildcard openevolve/prompts/*.txt)
PROMPT_NAMES      = $(basename $(notdir $(PROMPTS)))

evolve:
	$(OPENEVOLVE_PYTHON) $(OPENEVOLVE_RUN) \
		openevolve/initial_program.c openevolve/evaluator.py \
		--config openevolve/config.yaml \
		--iterations $${ITERATIONS:-10}

evolve-all:
	@echo "Running all prompt variants (explanations enabled by default)..."
	@echo "To skip explanation generation, use: EXPLAIN_GENERATIONS=0 make evolve-all"
	@echo "Running experiments for prompts: $(PROMPT_NAMES)"
	@for p in $(PROMPT_NAMES); do \
		echo ""; \
		echo "=== Experiment: $$p ==="; \
		$(OPENEVOLVE_PYTHON) openevolve/run_experiment.py $$p \
			--iterations $${ITERATIONS:-80}; \
	done

evolve-explain-test:
	@echo "Running baseline prompt with explanation generation (10 iterations)..."
	$(OPENEVOLVE_PYTHON) openevolve/run_experiment.py baseline --iterations 10
	@echo "✓ Results written to openevolve_output/baseline/results.json"
	@echo "View results:"
	@echo "  make show-consolidated-results"

show-explanations:
	$(OPENEVOLVE_PYTHON) -c "import sys; sys.path.insert(0, 'openevolve'); from results_loader import load_all_results; df = load_all_results(); import pandas as pd; print(df[df['explanation'].notna()][['iteration', 'prompt', 'improvement_percent', 'explanation']].to_string(index=False) if len(df) > 0 and 'explanation' in df.columns else 'No results or no explanation column found')"

test-explanations-disabled:
	@echo "Testing with EXPLAIN_GENERATIONS=0..."
	EXPLAIN_GENERATIONS=0 $(OPENEVOLVE_PYTHON) openevolve/run_experiment.py baseline --iterations 5
	@echo "✓ Experiment completed without explanations"
	@grep -q "explanation" openevolve_output/baseline/results.json && echo "⚠ Explanation field found in results" || echo "✓ No explanations in results (as expected)"

show-results:
	$(OPENEVOLVE_PYTHON) openevolve/show_results.py

show-consolidated-results:
	$(OPENEVOLVE_PYTHON) openevolve/show_consolidated.py

results-summary: show-consolidated-results

.PHONY: all clean run profile memtrace evolve evolve-all show-results show-consolidated-results results-summary evolve-explain-test show-explanations test-explanations-disabled

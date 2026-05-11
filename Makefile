CC = gcc
CFLAGS = -Wall -Wextra -std=c99 -O2 -D_THREAD_SAFE

# ── LLVM memory-access tracing ──────────────────────────────────────────────
# Resolve the real LLVM prefix: prefer an explicit override, then a Homebrew
# install that actually exists on disk, then fall back to /usr/local.
LLVM_PREFIX    ?= $(shell \
  BREW_PFX=$$(brew --prefix llvm 2>/dev/null); \
  if [ -n "$$BREW_PFX" ] && [ -d "$$BREW_PFX/bin" ]; then \
    echo "$$BREW_PFX"; \
  elif [ -d /usr/local/opt/llvm/bin ]; then \
    echo /usr/local/opt/llvm; \
  else \
    echo LLVM_NOT_FOUND; \
  fi)

ifeq ($(LLVM_PREFIX),LLVM_NOT_FOUND)
$(error LLVM not found. Install it with: brew install llvm)
endif

LLVM_CONFIG     = $(LLVM_PREFIX)/bin/llvm-config
LLVM_CLANG      = $(LLVM_PREFIX)/bin/clang
LLVM_CLANGXX    = $(LLVM_PREFIX)/bin/clang++
LLVM_OPT        = $(LLVM_PREFIX)/bin/opt
LLVM_CXXFLAGS   = $(shell $(LLVM_CONFIG) --cxxflags 2>/dev/null)
MEMTRACE_PASS   = memtrace_pass.dylib
MEMTRACE_RT_OBJ = memtrace_runtime.o
MEMTRACE_BC     = cavitydetection_memtrace.bc
MEMTRACE_IOBJ   = cavitydetection_memtrace.o
MEMTRACE_BIN    = cavitydetection_traced
LDFLAGS =
GPROF_CFLAGS = -Wall -Wextra -std=c99 -pg -D_THREAD_SAFE

# SDL2 flags are only needed for the render/display target and the main program
SDL_CFLAGS = -I/opt/homebrew/include/SDL2
SDL_LDFLAGS = -L/opt/homebrew/lib -lSDL2
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
# On macOS, -undefined dynamic_lookup lets LLVM symbols resolve from the
# host `opt` binary at load time (standard practice for pass plugins).
$(MEMTRACE_PASS): memtrace_pass.cpp
	$(LLVM_CLANGXX) -dynamiclib $(LLVM_CXXFLAGS) \
	    -Wl,-undefined,dynamic_lookup \
	    -o $@ $<

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
		$(MEMTRACE_PASS) $(MEMTRACE_RT_OBJ) $(MEMTRACE_BC) $(MEMTRACE_IOBJ) \
		cavitydetection_instr.bc $(MEMTRACE_BIN) memtrace.log

run-loopoptimization1: loopoptimization1
	./loopoptimization1

run: $(TARGET)
	./$(TARGET)

.PHONY: all clean run profile memtrace

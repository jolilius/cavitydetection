"""
Evaluator for cavity-detection pipeline optimisation.

Compiles the evolved C program with gcc -O0 (correctness gate), then builds
an LLVM-instrumented binary via memtrace_pass.so and counts every load/store
in the evolved pipeline functions.  Score = REFERENCE_ACCESSES / accesses;
values above 1.0 mean fewer memory accesses than the unoptimised baseline.

Baseline (initial_program.c, gcc -O0, BENCH_RUNS=1):
  run_pipeline + helper functions: 128,862,705 memory accesses (loads + stores)

Pre-requisites (built once from the project root):
  make memtrace_pass.so memtrace_runtime.o
"""

import os
import re
import subprocess
import tempfile

from openevolve.evaluation_result import EvaluationResult

REFERENCE_ACCESSES = 128_862_705

FIXED_FUNCTIONS = {"main", "GenerateTestImage", "ref_run_pipeline"}

COMPILE_TIMEOUT  = 15
RUN_TIMEOUT      = 30

SCRIPT_DIR   = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
PASS_PLUGIN  = os.path.join(PROJECT_ROOT, "memtrace_pass.so")
RUNTIME_OBJ  = os.path.join(PROJECT_ROOT, "memtrace_runtime.o")


def _find_llvm_bin() -> str | None:
    for v in [20, 19, 18, 17]:
        clang = f"/usr/lib/llvm-{v}/bin/clang"
        if os.path.isfile(clang) and os.access(clang, os.X_OK):
            return f"/usr/lib/llvm-{v}/bin"
    return None


LLVM_BIN = _find_llvm_bin()


def evaluate(program_path: str) -> EvaluationResult:
    if not os.path.isfile(PASS_PLUGIN):
        return _fail("memtrace_pass.so not found",
                     f"Run  make memtrace_pass.so  from {PROJECT_ROOT}")
    if not os.path.isfile(RUNTIME_OBJ):
        return _fail("memtrace_runtime.o not found",
                     f"Run  make memtrace_runtime.o  from {PROJECT_ROOT}")
    if LLVM_BIN is None:
        return _fail("LLVM clang not found",
                     "Install with: sudo apt install llvm clang")

    with open(program_path) as f:
        source = f.read()

    with tempfile.TemporaryDirectory() as tmp:
        src  = os.path.join(tmp, "program.c")
        exe  = os.path.join(tmp, "program")
        bc   = os.path.join(tmp, "program.bc")
        ibc  = os.path.join(tmp, "program_instr.bc")
        iobj = os.path.join(tmp, "program_instr.o")
        texe = os.path.join(tmp, "program_traced")

        with open(src, "w") as f:
            f.write(source)

        # ── Stage 1: compile with gcc (fast correctness gate) ───────────────
        r = subprocess.run(
            ["gcc", "-O0", "-std=c99", "-o", exe, src, "-lm"],
            capture_output=True, text=True, timeout=COMPILE_TIMEOUT,
        )
        if r.returncode != 0:
            return _fail("Compilation failed", r.stderr[:4096])

        # ── Stage 2: correctness check ───────────────────────────────────────
        r = subprocess.run(
            [exe], env={**os.environ, "BENCH_RUNS": "1"},
            capture_output=True, text=True, timeout=RUN_TIMEOUT,
        )
        if r.returncode != 0 or "PASS" not in r.stdout:
            return _fail("Correctness check failed",
                         f"stdout: {r.stdout[:512]}\nstderr: {r.stderr[:512]}")

        # ── Stage 3: build instrumented binary ──────────────────────────────
        clang = os.path.join(LLVM_BIN, "clang")
        opt   = os.path.join(LLVM_BIN, "opt")

        r = subprocess.run(
            [clang, "-O0", "-std=c99", "-g", "-emit-llvm", "-c", "-o", bc, src],
            capture_output=True, text=True, timeout=COMPILE_TIMEOUT,
        )
        if r.returncode != 0:
            return _fail("Clang bitcode emission failed", r.stderr[:2048])

        r = subprocess.run(
            [opt, f"--load-pass-plugin={PASS_PLUGIN}",
             "-passes=memtrace", bc, "-o", ibc],
            capture_output=True, text=True, timeout=COMPILE_TIMEOUT,
        )
        if r.returncode != 0:
            return _fail("Instrumentation pass failed", r.stderr[:2048])

        r = subprocess.run(
            [clang, "-O0", "-c", "-o", iobj, ibc],
            capture_output=True, text=True, timeout=COMPILE_TIMEOUT,
        )
        if r.returncode != 0:
            return _fail("Instrumented object compilation failed", r.stderr[:2048])

        r = subprocess.run(
            [clang, "-O0", "-o", texe, iobj, RUNTIME_OBJ, "-lm"],
            capture_output=True, text=True, timeout=COMPILE_TIMEOUT,
        )
        if r.returncode != 0:
            return _fail("Instrumented link failed", r.stderr[:2048])

        # ── Stage 4: memtrace run ────────────────────────────────────────────
        r = subprocess.run(
            [texe], env={**os.environ, "BENCH_RUNS": "1"},
            capture_output=True, text=True, timeout=RUN_TIMEOUT,
        )
        if r.returncode != 0 or "PASS" not in r.stdout:
            return _fail("Traced run failed",
                         f"stdout: {r.stdout[:512]}\nstderr: {r.stderr[:512]}")

        accesses, per_func = _parse_summary(r.stdout)
        if accesses is None:
            return _fail("Could not parse memtrace summary", r.stdout[:512])

    score = REFERENCE_ACCESSES / max(accesses, 1)

    artifacts = {"accesses": str(accesses), "compilation": "OK", "correctness": "PASS"}
    artifacts.update({f"accesses_{fn}": str(cnt) for fn, cnt in per_func.items()})

    return EvaluationResult(
        metrics={"mem_score": score},
        artifacts=artifacts,
    )


# ── helpers ──────────────────────────────────────────────────────────────────

def _parse_summary(stdout: str) -> tuple[int | None, dict[str, int]]:
    """
    Parse the memtrace summary block.  Returns (total_evolved_accesses, per_func_dict).
    Excludes FIXED_FUNCTIONS and the TOTAL row.
    """
    in_summary = False
    total = 0
    per_func: dict[str, int] = {}

    for line in stdout.splitlines():
        if "=== memtrace summary ===" in line:
            in_summary = True
            continue
        if not in_summary:
            continue
        parts = line.split()
        if len(parts) < 4:
            continue
        name = parts[0]
        if name in ("function", "--------", "TOTAL"):
            continue
        if name in FIXED_FUNCTIONS:
            continue
        try:
            accesses = int(parts[3])
        except (ValueError, IndexError):
            continue
        per_func[name] = accesses
        total += accesses

    if not in_summary:
        return None, {}
    return total, per_func


def _fail(msg: str, detail: str = "") -> EvaluationResult:
    arts: dict = {"error": msg}
    if detail:
        arts["detail"] = detail
    return EvaluationResult(
        metrics={"mem_score": 0.0},
        artifacts=arts,
    )


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print(f"Usage: python {sys.argv[0]} <program.c>")
        sys.exit(1)
    result = evaluate(sys.argv[1])
    print(f"mem_score: {result.metrics['mem_score']:.4f}")
    if result.artifacts:
        print("\nArtifacts:")
        for k, v in result.artifacts.items():
            print(f"  {k}: {str(v)[:200]}")

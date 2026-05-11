/* memtrace_runtime.c — callbacks inserted by memtrace_pass.cpp
 *
 * Two modes selected by the MEMTRACE_LOG environment variable:
 *
 *   (default / MEMTRACE_LOG=0)
 *     Count-only: at program exit a summary table is printed to stdout.
 *
 *   MEMTRACE_LOG=1
 *     Full trace: every access is appended to memtrace.log, and the summary
 *     is appended at the end of that file.
 *     Format: <L|S> <func> <line> <addr> <size_bytes>
 *
 * Because the traced loops can generate tens of millions of accesses, full
 * logging is intentionally opt-in.
 */

#include <stdio.h>
#include <stdint.h>
#include <stdlib.h>
#include <string.h>

/* ── per-function counters (dynamic — handles any function names) ─────────── */

#define MAX_FUNCS 128

typedef struct {
    char     name[64];
    uint64_t loads;
    uint64_t stores;
} FuncStats;

static FuncStats g_stats[MAX_FUNCS];
static int       g_nstats = 0;

static FILE *g_fp = NULL;  /* log file handle (NULL when count-only) */

/* ── helpers ────────────────────────────────────────────────────────────────── */

static FuncStats *find_or_create_stats(const char *func)
{
    for (int i = 0; i < g_nstats; i++)
        if (strcmp(g_stats[i].name, func) == 0)
            return &g_stats[i];
    if (g_nstats < MAX_FUNCS) {
        strncpy(g_stats[g_nstats].name, func, 63);
        g_stats[g_nstats].name[63] = '\0';
        g_stats[g_nstats].loads    = 0;
        g_stats[g_nstats].stores   = 0;
        return &g_stats[g_nstats++];
    }
    return NULL;   /* table full — access still counted in TOTAL */
}

/* ── constructor / destructor ──────────────────────────────────────────────── */

__attribute__((constructor))
static void memtrace_init(void)
{
    const char *env = getenv("MEMTRACE_LOG");
    if (env && strcmp(env, "1") == 0) {
        g_fp = fopen("memtrace.log", "w");
        if (!g_fp) {
            perror("memtrace: fopen(memtrace.log)");
            g_fp = stderr;
        }
        fprintf(g_fp, "# TYPE FUNC LINE ADDR SIZE_BYTES\n");
    }
}

__attribute__((destructor))
static void memtrace_fini(void)
{
    FILE *out = g_fp ? g_fp : stdout;

    fprintf(out, "\n=== memtrace summary ===\n");
    fprintf(out, "%-14s %14s %14s %14s\n",
            "function", "loads", "stores", "total");
    fprintf(out, "%-14s %14s %14s %14s\n",
            "--------", "-----", "------", "-----");

    uint64_t tl = 0, ts = 0;
    for (int i = 0; i < g_nstats; i++) {
        uint64_t tot = g_stats[i].loads + g_stats[i].stores;
        fprintf(out, "%-14s %14llu %14llu %14llu\n",
                g_stats[i].name,
                (unsigned long long)g_stats[i].loads,
                (unsigned long long)g_stats[i].stores,
                (unsigned long long)tot);
        tl += g_stats[i].loads;
        ts += g_stats[i].stores;
    }
    fprintf(out, "%-14s %14llu %14llu %14llu\n",
            "TOTAL",
            (unsigned long long)tl,
            (unsigned long long)ts,
            (unsigned long long)(tl + ts));

    if (g_fp && g_fp != stderr && g_fp != stdout) {
        fclose(g_fp);
        fprintf(stdout, "Full trace written to memtrace.log\n");
    }
}

/* ── instrumentation callbacks ──────────────────────────────────────────────── */

void __memtrace_load(void *addr, uint64_t size, const char *func, int line)
{
    FuncStats *s = find_or_create_stats(func);
    if (s) s->loads++;

    if (g_fp)
        fprintf(g_fp, "L %s %d %p %llu\n",
                func, line, addr, (unsigned long long)size);
}

void __memtrace_store(void *addr, uint64_t size, const char *func, int line)
{
    FuncStats *s = find_or_create_stats(func);
    if (s) s->stores++;

    if (g_fp)
        fprintf(g_fp, "S %s %d %p %llu\n",
                func, line, addr, (unsigned long long)size);
}

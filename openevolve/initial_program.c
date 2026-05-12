/* initial_program.c — OpenEvolve seed for cavity-detection pipeline optimisation.
 *
 * Self-contained (no SDL2).
 *
 * CONTRACT for the evolved code
 * ─────────────────────────────
 * main() calls exactly one function:
 *
 *   void run_pipeline(unsigned char in[N][M], unsigned char out[N][M]);
 *
 * Everything inside the EVOLVE-BLOCK may be restructured freely:
 *   - Merge all four stages into a single loop.
 *   - Split or rename helper functions however you like.
 *   - Change internal data structures (e.g. transpose, tiled, flat arrays).
 *   - Remove intermediate buffers, fuse passes, whatever reduces memory traffic.
 *
 * The ONLY invariant that must hold: for a given input image, out[x][y] must
 * equal the reference output pixel-for-pixel (verified by main()).
 *
 * IMPORTANT: intermediate arrays of 512×512 bytes are 256 KB each.
 * Declare them  static  (or use malloc/free) to avoid stack overflow.
 *
 * Compiled with:  gcc -O0 -std=c99 -o program program.c -lm
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>

#ifndef M_PI
#define M_PI 3.14159265358979323846
#endif

#define N 512
#define M 512

/* ── test-image generator (fixed seed — never change this) ───────────────── */

static void GenerateTestImage(unsigned char image[N][M])
{
    int cx = N / 2, cy = M / 2;
    unsigned char mask[N][M];
    memset(mask, 0, sizeof mask);
    srand(12345u);

    int target = (int)(M_PI * 50.0 * 50.0);
    if (target < 1000) target = 1000;

    int x = cx, y = cy;
    mask[x][y] = 1;
    int filled = 1, steps = 0;

    while (filled < target && steps < N * M * 10) {
        int r = rand() & 3;
        if      (r == 0 && x > 0)     --x;
        else if (r == 1 && x < N - 1) ++x;
        else if (r == 2 && y > 0)     --y;
        else if (r == 3 && y < M - 1) ++y;
        if (!mask[x][y]) { mask[x][y] = 1; ++filled; }
        if ((rand() % 100) < 12) {
            int bx = x + (rand() % 7) - 3;
            int by = y + (rand() % 7) - 3;
            if (bx >= 0 && bx < N && by >= 0 && by < M && !mask[bx][by])
                { mask[bx][by] = 1; ++filled; }
        }
        ++steps;
    }

    for (int pass = 0; pass < 2; ++pass) {
        unsigned char tmp[N][M];
        memcpy(tmp, mask, sizeof tmp);
        for (int yy = 1; yy < M - 1; ++yy)
            for (int xx = 1; xx < N - 1; ++xx)
                if (!tmp[xx][yy]) {
                    int n = 0;
                    for (int dy = -1; dy <= 1; ++dy)
                        for (int dx = -1; dx <= 1; ++dx)
                            if (dx || dy) n += tmp[xx+dx][yy+dy];
                    if (n >= 4) mask[xx][yy] = 1;
                }
    }

    double maxd = 0;
    for (int yy = 0; yy < M; ++yy)
        for (int xx = 0; xx < N; ++xx)
            if (mask[xx][yy]) {
                double ddx = xx - cx, ddy = yy - cy;
                double d = sqrt(ddx*ddx + ddy*ddy);
                if (d > maxd) maxd = d;
            }
    if (maxd < 1.0) maxd = 1.0;

    for (int yy = 0; yy < M; ++yy)
        for (int xx = 0; xx < N; ++xx)
            if (mask[xx][yy]) {
                double ddx = xx - cx, ddy = yy - cy;
                double t = sqrt(ddx*ddx + ddy*ddy) / maxd;
                int v = 18 + (rand() % 24) + (int)(t * 40.0) + (rand() % 15) - 7;
                if (v < 0) v = 0; if (v > 140) v = 140;
                image[xx][yy] = (unsigned char)v;
            } else {
                int v = 180 + (rand() % 40) + (rand() % 20) - 10;
                if (v < 120) v = 120; if (v > 255) v = 255;
                image[xx][yy] = (unsigned char)v;
            }
}

/* ── reference pipeline (frozen — used only for correctness checking) ───── */

static void ref_run_pipeline(unsigned char in[N][M], unsigned char out[N][M])
{
    /* Horizontal Gaussian pass */
    static unsigned char gx[N][M];
    for (int y = 0; y < M; ++y)
        for (int x = 0; x < N; ++x) {
            int s = in[x][y] * 6;
            if (x >= 1) s += in[x-1][y] * 4;
            if (x >= 2) s += in[x-2][y];
            if (x < N-1) s += in[x+1][y] * 4;
            if (x < N-2) s += in[x+2][y];
            gx[x][y] = (unsigned char)(s / 16);
        }

    /* Vertical Gaussian pass → gxy */
    static unsigned char gxy[N][M];
    for (int y = 0; y < M; ++y)
        for (int x = 0; x < N; ++x) {
            int s = gx[x][y] * 6;
            if (y >= 1) s += gx[x][y-1] * 4;
            if (y >= 2) s += gx[x][y-2];
            if (y < M-1) s += gx[x][y+1] * 4;
            if (y < M-2) s += gx[x][y+2];
            gxy[x][y] = (unsigned char)(s / 16);
        }

    /* Edge detection → ce */
    static unsigned char ce[N][M];
    for (int y = 0; y < M; ++y)
        for (int x = 0; x < N; ++x) {
            unsigned char cur = gxy[x][y], md = 0;
            for (int dy = -1; dy <= 1; ++dy)
                for (int dx = -1; dx <= 1; ++dx) {
                    if (!dx && !dy) continue;
                    int nx = x+dx, ny = y+dy;
                    if (nx < 0 || nx >= N || ny < 0 || ny >= M) continue;
                    unsigned char d = cur > gxy[nx][ny] ? cur-gxy[nx][ny] : gxy[nx][ny]-cur;
                    if (d > md) md = d;
                }
            ce[x][y] = md;
        }

    /* Reverse + local-maxima detection */
    unsigned char maxv = 0;
    for (int y = 0; y < M; ++y)
        for (int x = 0; x < N; ++x)
            if (ce[x][y] > maxv) maxv = ce[x][y];

    static unsigned char rev[N][M];
    for (int y = 0; y < M; ++y)
        for (int x = 0; x < N; ++x)
            rev[x][y] = maxv - ce[x][y];

    for (int y = 0; y < M; ++y)
        for (int x = 0; x < N; ++x) {
            unsigned char cur = rev[x][y];
            int ismax = 1;
            for (int dy = -1; dy <= 1 && ismax; ++dy)
                for (int dx = -1; dx <= 1 && ismax; ++dx) {
                    if (!dx && !dy) continue;
                    int nx = x+dx, ny = y+dy;
                    if (nx >= 0 && nx < N && ny >= 0 && ny < M && rev[nx][ny] > cur)
                        ismax = 0;
                }
            out[x][y] = ismax ? 255 : 0;
        }
}

/* ═══════════════════════════════════════════════════════════════════════════
   EVOLVE-BLOCK — everything between the markers may be freely restructured.

   REQUIRED: define  void run_pipeline(unsigned char in[N][M], unsigned char out[N][M])
   All other functions are optional; add, remove, or merge them as you see fit.
   ═══════════════════════════════════════════════════════════════════════════ */

// # EVOLVE-BLOCK-START

static void GaussBlur(unsigned char image_in[N][M], unsigned char gxy[N][M])
{
    static unsigned char gx[N][M];
    int sum;

    for (int y = 0; y < M; ++y)
        for (int x = 0; x < N; ++x) {
            sum = image_in[x][y] * 6;
            if (x >= 2) sum += image_in[x-2][y];
            if (x >= 1) sum += image_in[x-1][y] * 4;
            if (x < N-1) sum += image_in[x+1][y] * 4;
            if (x < N-2) sum += image_in[x+2][y];
            gx[x][y] = (unsigned char)(sum / 16);
        }

    for (int y = 0; y < M; ++y)
        for (int x = 0; x < N; ++x) {
            sum = gx[x][y] * 6;
            if (y >= 2) sum += gx[x][y-2];
            if (y >= 1) sum += gx[x][y-1] * 4;
            if (y < M-1) sum += gx[x][y+1] * 4;
            if (y < M-2) sum += gx[x][y+2];
            gxy[x][y] = (unsigned char)(sum / 16);
        }
}

static void ComputeEdges(unsigned char gxy[N][M], unsigned char ce[N][M])
{
    for (int y = 0; y < M; ++y)
        for (int x = 0; x < N; ++x) {
            unsigned char current = gxy[x][y], max_diff = 0;
            for (int dy = -1; dy <= 1; ++dy)
                for (int dx = -1; dx <= 1; ++dx) {
                    if (dx == 0 && dy == 0) continue;
                    int nx = x+dx, ny = y+dy;
                    if (nx >= 0 && nx < N && ny >= 0 && ny < M) {
                        unsigned char diff = current > gxy[nx][ny]
                            ? current - gxy[nx][ny] : gxy[nx][ny] - current;
                        if (diff > max_diff) max_diff = diff;
                    }
                }
            ce[x][y] = max_diff;
        }
}

static void DetectRoots(unsigned char ce[N][M], unsigned char image_out[N][M])
{
    unsigned char maxval = 0;
    for (int y = 0; y < M; ++y)
        for (int x = 0; x < N; ++x)
            if (ce[x][y] > maxval) maxval = ce[x][y];

    static unsigned char ce_rev[N][M];
    for (int y = 0; y < M; ++y)
        for (int x = 0; x < N; ++x)
            ce_rev[x][y] = maxval - ce[x][y];

    for (int y = 0; y < M; ++y)
        for (int x = 0; x < N; ++x) {
            unsigned char current = ce_rev[x][y];
            int is_maximum = 1;
            for (int dy = -1; dy <= 1; ++dy)
                for (int dx = -1; dx <= 1; ++dx) {
                    if (dx == 0 && dy == 0) continue;
                    int nx = x+dx, ny = y+dy;
                    if (nx >= 0 && nx < N && ny >= 0 && ny < M)
                        if (ce_rev[nx][ny] > current) { is_maximum = 0; break; }
                }
            image_out[x][y] = is_maximum ? 255 : 0;
        }
}

void run_pipeline(unsigned char image_in[N][M], unsigned char image_out[N][M])
{
    static unsigned char gxy[N][M];
    static unsigned char ce[N][M];

    GaussBlur(image_in, gxy);
    ComputeEdges(gxy, ce);
    DetectRoots(ce, image_out);
}

// # EVOLVE-BLOCK-END

/* ── driver ──────────────────────────────────────────────────────────────── */

int main(void)
{
    const char *env = getenv("BENCH_RUNS");
    int runs = env ? atoi(env) : 20;
    if (runs < 1) runs = 1;

    static unsigned char image_in[N][M];
    static unsigned char ref_out[N][M];
    static unsigned char image_out[N][M];

    GenerateTestImage(image_in);

    ref_run_pipeline(image_in, ref_out);

    for (int k = 0; k < runs; ++k)
        run_pipeline(image_in, image_out);

    for (int y = 0; y < M; ++y)
        for (int x = 0; x < N; ++x)
            if (image_out[x][y] != ref_out[x][y]) {
                printf("FAIL [%d][%d] got=%d expected=%d\n",
                       x, y, (int)image_out[x][y], (int)ref_out[x][y]);
                return 1;
            }

    printf("PASS\n");
    return 0;
}

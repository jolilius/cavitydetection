#include <stdlib.h>
#include <math.h>
#include <time.h>
#include "testimage.h"

#define N 512
#define M 512

/*
 * Generate test image: create an irregular, connected dark shape
 * The shape is created by a random-walk blob (connected) and gets
 * interior shading that is darker than the outside.
 */
void GenerateTestImage(unsigned char image_in[N][M])
{
    int center_x = N / 2;
    int center_y = M / 2;

    /* Mask for shape presence (0 = outside, 1 = inside) */
    unsigned char mask[N][M];
    for (int y = 0; y < M; ++y)
        for (int x = 0; x < N; ++x)
            mask[x][y] = 0;

    srand((unsigned int)time(NULL));

    /*
     * Create a connected blob using a random walk starting at center.
     * Continue until we reach approximately the target area.
     */
    int target_area = (int)(M_PI * 50.0 * 50.0); /* ~7850 */
    if (target_area < 1000) target_area = 1000;

    int x = center_x, y = center_y;
    mask[x][y] = 1;
    int filled = 1;
    int steps = 0;

    while (filled < target_area && steps < N * M * 10) {
        /* Move randomly to one of 4 neighbors (4-connectivity) */
        int r = rand() & 3;
        if (r == 0 && x > 0) x--;
        else if (r == 1 && x < N - 1) x++;
        else if (r == 2 && y > 0) y--;
        else if (r == 3 && y < M - 1) y++;

        if (!mask[x][y]) {
            mask[x][y] = 1;
            filled++;
        }

        /* Occasionally branch out to create irregular lobes */
        if ((rand() % 100) < 12) {
            int bx = x + (rand() % 7) - 3;
            int by = y + (rand() % 7) - 3;
            if (bx >= 0 && bx < N && by >= 0 && by < M && !mask[bx][by]) {
                mask[bx][by] = 1;
                filled++;
            }
        }

        steps++;
    }

    /* Small smoothing pass to fill tiny holes and make silhouette nicer */
    for (int pass = 0; pass < 2; ++pass) {
        unsigned char tmp[N][M];
        for (int yy = 0; yy < M; ++yy) for (int xx = 0; xx < N; ++xx) tmp[xx][yy] = mask[xx][yy];

        for (int yy = 1; yy < M - 1; ++yy) {
            for (int xx = 1; xx < N - 1; ++xx) {
                if (!tmp[xx][yy]) {
                    int neigh = 0;
                    for (int dy = -1; dy <= 1; ++dy)
                        for (int dx = -1; dx <= 1; ++dx)
                            if (dx != 0 || dy != 0)
                                neigh += tmp[xx + dx][yy + dy];

                    if (neigh >= 4) mask[xx][yy] = 1;
                }
            }
        }
    }

    /* Compute maximum distance inside mask (for shading) */
    double maxd = 0.0;
    for (int yy = 0; yy < M; ++yy) {
        for (int xx = 0; xx < N; ++xx) {
            if (mask[xx][yy]) {
                double dx = xx - center_x;
                double dy = yy - center_y;
                double d = sqrt(dx * dx + dy * dy);
                if (d > maxd) maxd = d;
            }
        }
    }
    if (maxd < 1.0) maxd = 1.0;

    /* Fill image: outside is light with some noise; inside is darker with shading */
    for (int yy = 0; yy < M; ++yy) {
        for (int xx = 0; xx < N; ++xx) {
            if (mask[xx][yy]) {
                /* Interior shading: darker near center, lighter near blob boundary */
                double dx = xx - center_x;
                double dy = yy - center_y;
                double d = sqrt(dx * dx + dy * dy);
                double t = d / maxd; /* 0..1 */

                int inside_base = 18 + (rand() % 24);      /* 18..41 */
                int inside_shade = (int)(inside_base + t * 40.0); /* up to ~80 */
                /* Add small local noise */
                inside_shade += (rand() % 15) - 7;
                if (inside_shade < 0) inside_shade = 0;
                if (inside_shade > 140) inside_shade = 140;

                image_in[xx][yy] = (unsigned char)inside_shade;
            } else {
                /* Outside: lighter background with noise */
                int outside_base = 180 + (rand() % 40); /* 180..219 */
                outside_base += (rand() % 20) - 10;     /* jitter +/-10 */
                if (outside_base < 120) outside_base = 120;
                if (outside_base > 255) outside_base = 255;
                image_in[xx][yy] = (unsigned char)outside_base;
            }
        }
    }
}

#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <time.h>
#include "render.h"
#include "testimage.h"

#define N 512  // Image width
#define M 512  // Image height

/**
 * Perform horizontal and vertical Gauss blurring on each pixel
 */
void GaussBlur(unsigned char image_in[N][M], unsigned char gxy[N][M])
{
    unsigned char gx[N][M];
    int sum;

    // Apply horizontal Gauss blurring (5-tap kernel: [1, 4, 6, 4, 1] / 16)
    for (int y = 0; y < M; ++y) {
        for (int x = 0; x < N; ++x) {
            sum = 0;
            
            // Left neighbors
            if (x >= 2) sum += image_in[x-2][y] * 1;
            if (x >= 1) sum += image_in[x-1][y] * 4;
            
            // Center pixel
            sum += image_in[x][y] * 6;
            
            // Right neighbors
            if (x < N-1) sum += image_in[x+1][y] * 4;
            if (x < N-2) sum += image_in[x+2][y] * 1;
            
            gx[x][y] = (unsigned char)(sum / 16);
        }
    }

    // Apply vertical Gauss blurring (5-tap kernel: [1, 4, 6, 4, 1] / 16)
    for (int y = 0; y < M; ++y) {
        for (int x = 0; x < N; ++x) {
            sum = 0;
            
            // Top neighbors
            if (y >= 2) sum += gx[x][y-2] * 1;
            if (y >= 1) sum += gx[x][y-1] * 4;
            
            // Center pixel
            sum += gx[x][y] * 6;
            
            // Bottom neighbors
            if (y < M-1) sum += gx[x][y+1] * 4;
            if (y < M-2) sum += gx[x][y+2] * 1;
            
            gxy[x][y] = (unsigned char)(sum / 16);
        }
    }
}

/**
 * Replace every pixel with the maximum difference with its neighbors
 */
void ComputeEdges(unsigned char gxy[N][M], unsigned char ce[N][M])
{
    for (int y = 0; y < M; ++y) {
        for (int x = 0; x < N; ++x) {
            // Replace pixel with the maximum difference with its neighbors
            unsigned char current = gxy[x][y];
            unsigned char max_diff = 0;
            
            // Check all 8 neighbors
            for (int dy = -1; dy <= 1; ++dy) {
                for (int dx = -1; dx <= 1; ++dx) {
                    if (dx == 0 && dy == 0) continue;  // Skip center pixel
                    
                    int nx = x + dx;
                    int ny = y + dy;
                    
                    // Check bounds and compute difference
                    if (nx >= 0 && nx < N && ny >= 0 && ny < M) {
                        unsigned char diff = (current > gxy[nx][ny]) ? 
                                           (current - gxy[nx][ny]) : 
                                           (gxy[nx][ny] - current);
                        
                        if (diff > max_diff) {
                            max_diff = diff;
                        }
                    }
                }
            }
            
            ce[x][y] = max_diff;
        }
    }
}

/**
 * Reverse the image by subtracting each pixel from the maximum value
 */
void Reverse(unsigned char ce[N][M], unsigned char ce_rev[N][M])
{
    unsigned char maxval = 0;

    // Compute maximum value
    for (int y = 0; y < M; ++y) {
        for (int x = 0; x < N; ++x) {
            if (ce[x][y] > maxval) {
                maxval = ce[x][y];
            }
        }
    }

    // Subtract every pixel value from the maximum value
    for (int y = 0; y < M; ++y) {
        for (int x = 0; x < N; ++x) {
            ce_rev[x][y] = maxval - ce[x][y];
        }
    }
}

/**
 * Detect local maxima (roots) - pixels with no neighbors larger than themselves
 */
void DetectRoots(unsigned char ce[N][M], unsigned char image_out[N][M])
{
    unsigned char ce_rev[N][M];

    // Reverse image
    Reverse(ce, ce_rev);

    // image_out[x][y] is true if no neighbors are bigger than ce_rev[x][y]
    for (int y = 0; y < M; ++y) {
        for (int x = 0; x < N; ++x) {
            // Is true if no neighbors are bigger than current pixel
            unsigned char current = ce_rev[x][y];
            int is_maximum = 1;  // Assume it's a local maximum
            
            // Check all 8 neighbors
            for (int dy = -1; dy <= 1; ++dy) {
                for (int dx = -1; dx <= 1; ++dx) {
                    if (dx == 0 && dy == 0) continue;  // Skip center pixel
                    
                    int nx = x + dx;
                    int ny = y + dy;
                    
                    // Check bounds
                    if (nx >= 0 && nx < N && ny >= 0 && ny < M) {
                        if (ce_rev[nx][ny] > current) {
                            is_maximum = 0;  // Found a neighbor that's bigger
                            break;
                        }
                    }
                }
                if (!is_maximum) break;
            }
            
            image_out[x][y] = is_maximum ? 255 : 0;  // 255 for local max, 0 otherwise
        }
    }
}

/* GenerateTestImage moved to `testimage.c` */

/**
 * Main function
 */
int main(void)
{
    unsigned char image_in[N][M], gxy[N][M], ce[N][M], image_out[N][M];

    // Generate test image with noise and circle
    GenerateTestImage(image_in);
    DisplayImage(image_in, "Original Test Image");

    GaussBlur(image_in, gxy);
    DisplayImage(gxy, "After Gaussian Blur");
    
    ComputeEdges(gxy, ce);
    DisplayImage(ce, "After Edge Detection");
    
    DetectRoots(ce, image_out);
    DisplayImage(image_out, "Final Root Detection");

    return 0;
}
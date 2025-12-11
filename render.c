#include <stdio.h>
#include <stdlib.h>
#include <SDL.h>
#include "render.h"

#define N 512  // Image width
#define M 512  // Image height

/**
 * Display image in an SDL2 window
 * Creates a window and displays the grayscale image
 */
void DisplayImage(unsigned char image[512][512], const char *title)
{
    SDL_Window *window = NULL;
    SDL_Renderer *renderer = NULL;
    SDL_Texture *texture = NULL;
    int window_width = 512 * WINDOW_SCALE;
    int window_height = 512 * WINDOW_SCALE;
    
    // Convert grayscale to ARGB8888 format for SDL2
    Uint32 *rgb_data = (Uint32 *)malloc(512 * 512 * sizeof(Uint32));
    if (rgb_data == NULL) {
        printf("Memory allocation failed\n");
        return;
    }
    
    // Fill with grayscale data in ARGB8888 format
    for (int y = 0; y < 512; ++y) {
        for (int x = 0; x < 512; ++x) {
            unsigned char gray = image[x][y];
            // ARGB8888: 0xAARRGGBB (A=255 for opaque, R=G=B=gray)
            rgb_data[y * 512 + x] = (0xFF << 24) | (gray << 16) | (gray << 8) | gray;
        }
    }
    
    // Initialize SDL
    if (SDL_Init(SDL_INIT_VIDEO) < 0) {
        printf("SDL initialization failed: %s\n", SDL_GetError());
        free(rgb_data);
        return;
    }
    
    // Create window
    window = SDL_CreateWindow(
        title,
        SDL_WINDOWPOS_CENTERED,
        SDL_WINDOWPOS_CENTERED,
        window_width,
        window_height,
        SDL_WINDOW_SHOWN
    );
    
    if (window == NULL) {
        printf("Window creation failed: %s\n", SDL_GetError());
        SDL_Quit();
        free(rgb_data);
        return;
    }
    
    // Create renderer
    renderer = SDL_CreateRenderer(window, -1, SDL_RENDERER_ACCELERATED | SDL_RENDERER_PRESENTVSYNC);
    if (renderer == NULL) {
        printf("Renderer creation failed: %s\n", SDL_GetError());
        SDL_DestroyWindow(window);
        SDL_Quit();
        free(rgb_data);
        return;
    }
    
    // Create texture for the image (use ARGB8888 format)
    texture = SDL_CreateTexture(
        renderer,
        SDL_PIXELFORMAT_ARGB8888,
        SDL_TEXTUREACCESS_STATIC,
        512,
        512
    );
    
    if (texture == NULL) {
        printf("Texture creation failed: %s\n", SDL_GetError());
        SDL_DestroyRenderer(renderer);
        SDL_DestroyWindow(window);
        SDL_Quit();
        free(rgb_data);
        return;
    }
    
    // Copy image data to texture
    SDL_UpdateTexture(texture, NULL, (void *)rgb_data, 512 * sizeof(Uint32));
    
    // Event loop - display until user closes window
    int quit = 0;
    SDL_Event event;
    while (!quit) {
        while (SDL_PollEvent(&event)) {
            if (event.type == SDL_QUIT) {
                quit = 1;
            } else if (event.type == SDL_KEYDOWN) {
                quit = 1;  // Close on any key press
            }
        }
        
        // Clear and render
        SDL_RenderClear(renderer);
        SDL_Rect dest_rect = {0, 0, window_width, window_height};
        SDL_RenderCopy(renderer, texture, NULL, &dest_rect);
        SDL_RenderPresent(renderer);
    }
    
    // Cleanup
    SDL_DestroyTexture(texture);
    SDL_DestroyRenderer(renderer);
    SDL_DestroyWindow(window);
    SDL_Quit();
    free(rgb_data);
}

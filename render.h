#ifndef RENDER_H
#define RENDER_H

#include <stddef.h>

#define WINDOW_SCALE 2  // Scale factor for window display

/**
 * Display image in an SDL2 window
 * Creates a window and displays the grayscale image
 */
void DisplayImage(unsigned char image[512][512], const char *title);

#endif // RENDER_H

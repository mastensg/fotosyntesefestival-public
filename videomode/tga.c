#include <err.h>
#include <inttypes.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include "tga.h"

void
tga_write(FILE *file, uint8_t *pixels, const uint16_t width, const uint16_t height)
{
    struct tga_header h;
    uint8_t *p;
    int i;

    memset(&h, 0, sizeof(struct tga_header));
    h.image_type = 2;
    h.y_origin = height;
    h.image_width = width;
    h.image_height = height;
    h.pixel_depth = 24;
    h.image_descriptor = 0;

    if(fwrite(&h, sizeof(struct tga_header), 1, file) == -1)
        err(EXIT_FAILURE, "fwrite header");

    p = pixels;

    for(i = 0; i < width * height; ++i)
    {
        if(fwrite(p + 2, 1, 1, file) == -1)
            err(EXIT_FAILURE, "fwrite pixels");

        if(fwrite(p + 1, 1, 1, file) == -1)
            err(EXIT_FAILURE, "fwrite pixels");

        if(fwrite(p + 0, 1, 1, file) == -1)
            err(EXIT_FAILURE, "fwrite pixels");

        p += 3;
    }
}

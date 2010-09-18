#include <stdlib.h>
#include <stdio.h>
#include "SDL.h"
void
write_bmp_header (FILE * f, SDL_Surface * screen)
{
    Uint32 w32, size;
    Uint16 w16;
    Uint8 s = 3;
    int w = screen->w, h = screen->h;
    fputs ("BM", f);
    size = w * h * s;
    if ((w * s) % 4) {
        size += h * (4 - (w * s) % 4);
    }
    w32 = 54 + size;            /* Size of the file */
    fwrite (&w32, sizeof w32, 1, f);
    w32 = 0;
    fwrite (&w32, sizeof w32, 1, f);    /* App specific */
    w32 = 54;
    fwrite (&w32, sizeof w32, 1, f);    /* Offset of the data */
    w32 = 40;
    fwrite (&w32, sizeof w32, 1, f);    /* Size of the header from this point on */
    w32 = w;
    fwrite (&w32, sizeof w32, 1, f);
    w32 = h;
    fwrite (&w32, sizeof w32, 1, f);
    w16 = 1;
    fwrite (&w16, sizeof w16, 1, f);    /* Number of color planes */
    w16 = s * 8;
    fwrite (&w16, sizeof w16, 1, f);    /* bpp */
    w32 = 0;
    fwrite (&w32, sizeof w32, 1, f);    /* no compression */
    w32 = size;
    fwrite (&w32, sizeof w32, 1, f);    /* size of the data */

    /* pixels per meters in both direction (assuming 166 dpi) */
    w32 = 6535;
    fwrite (&w32, sizeof w32, 1, f);
    fwrite (&w32, sizeof w32, 1, f);
    w32 = 0;
    fwrite (&w32, sizeof w32, 1, f);    /* Number of colors in the palette */
    w32 = 0;
    fwrite (&w32, sizeof w32, 1, f);    /* Number of important colors */
}

void
write_bmp_data (FILE * f, SDL_Surface * screen)
{
    int x, y, pad = 0, w = screen->w, h = screen->h;
    Uint8 r, g, b, dummy = 0;
    Uint32 *pixel, p, temp;
    SDL_PixelFormat *fmt;
    fmt = screen->format;
    if ((w * 3) % 4) {
        pad = 4 - (w * 3) % 4;
    }
    SDL_LockSurface (screen);
    for (y = h - 1; y >= 0; y--) {
        pixel = (Uint32 *) (screen->pixels) + (y * w);
        for (x = 0; x < w; x++) {
            p = *(pixel++);
            temp = p & fmt->Rmask;      /* Isolate red component */
            temp = temp >> fmt->Rshift; /* Shift it down to 8-bit */
            temp = temp << fmt->Rloss;  /* Expand to a full 8-bit number */
            r = (Uint8) temp;
            temp = p & fmt->Gmask;      /* Isolate green component */
            temp = temp >> fmt->Gshift; /* Shift it down to 8-bit */
            temp = temp << fmt->Gloss;  /* Expand to a full 8-bit number */
            g = (Uint8) temp;
            temp = p & fmt->Bmask;      /* Isolate blue component */
            temp = temp >> fmt->Bshift; /* Shift it down to 8-bit */
            temp = temp << fmt->Bloss;  /* Expand to a full 8-bit number */
            b = (Uint8) temp;
            fwrite (&b, sizeof b, 1, f);
            fwrite (&g, sizeof b, 1, f);
            fwrite (&r, sizeof b, 1, f);
        }
        for (x = 0; x < pad; x++) {
            fwrite (&dummy, sizeof dummy, 1, f);
        }
    }
    SDL_UnlockSurface (screen);
}

void
write_bmp (SDL_Surface * screen)
{
    FILE *f;
    char name[] = "dump.bmp";   /* Need to create a unique name someday... */
    if ((f = fopen (name, "wb")) == NULL) {
        fprintf (stderr, "Unable to open file %s to  dump BMP\n", name);
        return;
    }
    write_bmp_header (f, screen);
    write_bmp_data (f, screen);
    fclose (f);
}

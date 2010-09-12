/* 
 * This program is free software; you can redistribute it and/or modify 
 * it under the terms of the GNU General Public License as published by 
 * the Free Software Foundation; either version 3 of the License, or 
 * (at your option) any later version.
 * 
 * This program is distributed in the hope that it will be useful, but 
 * WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY 
 * or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License 
 * for more details.
 * 
 * You should have received a copy of the GNU General Public License along 
 * with this program; if not, write to the Free Software Foundation, Inc., 
 * 59 Temple Place, Suite 330, Boston, MA 02111-1307 USA
 */
/* Colorization code copied from David Madore's site: http://www.madore.org/~david/programs/#prog_mandel */
#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <time.h>
#include <getopt.h>
#include "SDL/SDL.h"
#include "SDL/SDL_gfxPrimitives.h"
#include "prec.h"

#define VERSION_STRING "2.0"

typedef struct
{
    mpfr_t x;
    mpfr_t y;
} point_t;

typedef enum
{ MANDELBROT = 0, JULIA
} algo_t;

typedef enum
{ MU = 0, INV_MU = 1, MAX_PAR = 2
} parametrization_t;

typedef struct
{
    int n;                      /* Iteration number */
    mpfr_t modulus;             /* Modulus of the point */
    Uint32 color;               /* Color of the point */
} mpoint_t;

typedef struct
{
    int nmax;                   /* Number of iterations to perform before assuming divergence */
    point_t julia_c;            /* Point on which to compute Julia set */
    algo_t algo;                /* Mandelbrot or Julia */
    parametrization_t para;     /* Normal or inverted */
    mpoint_t *t;                /* Table containing the fractal data */
    int current_alloc;          /* Current allocated memory for t */
    mpfr_prec_t prec;           /* Precision for floats */
    mpfr_rnd_t round;           /* Rounding for floats */
} fractal_settings_t;

typedef struct
{
    unsigned long int w;        /* width of current window (in pixels) */
    unsigned long int h;        /* height of current window (in pixels) */
    int screen_w;               /* Width of the screen (in pixels) */
    int screen_h;               /* Height of thr screen (in pixels) */
    int fullscreen;             /* Are we drawing fullscreen or not */
    Uint32 *colormap;           /* The colormap */
    Uint32 coef[3];             /* Coefficients for coloring */
    Sint32 smooth;              /* Color smoothing used ? */
} display_settings_t;

static fractal_settings_t fset;
static display_settings_t dset;

#ifdef HAS_MPFR
const char *WINDOW_TITLE = "Mandelbrot explorer (MPFR build)";
#else
const char *WINDOW_TITLE = "Mandelbrot explorer";
#endif

void
usage (char *prog_name, FILE * stream)
{
    fprintf (stream, "%s (version %s):\n", prog_name, VERSION_STRING);
    fprintf (stream,
             "\t--version                | -v  : show program version\n");
    fprintf (stream, "\t--help                   | -h  : show this help\n");
    fprintf (stream,
             "\t--n_iterations           | -n  : number of iterations to perform before assuming divergence\n");
    fprintf (stream,
             "\t--geometry=<geo>         | -g  : sets the window geometry.\n");
    fprintf (stream,
             "\t--parametrization=<para> | -p  : sets initial parametrization. Valid values are mu and mu_inv.\n");
    fprintf (stream,
             "\t--smooth                 | -s  : performs color smoothing.\n");
    fprintf (stream,
             "\t--fullscreen             | -f  : runs in fullscreen.\n");
#ifdef HAS_MPRF
    fprintf (stream,
             "\t--prec=<prec>            | -r  : set precision to <prec> bits.\n");
#endif
    fprintf (stream,
             "\t--coef=<r>,<g>,<b>       | -c  : coefficients for coloring.\n\n");
}

void
default_settings (void)
{
    fset.nmax = 128;
    fset.prec = 64;
    fset.round = GMP_RNDZ;
    dset.w = 640;
    dset.h = 480;
    fset.algo = MANDELBROT;
    mpfr_set_ui (fset.julia_c.x, 0, fset.round);
    mpfr_set_ui (fset.julia_c.y, 0, fset.round);
    fset.para = MU;
    fset.current_alloc = dset.w * dset.h * 2;
    dset.screen_w = 640;
    dset.screen_h = 480;
    dset.fullscreen = 0;
    dset.smooth = 0;
    dset.coef[0] = dset.coef[1] = dset.coef[2] = 1;
}

int
isnumber (char c)
{
    if (c < '0' || c > '9') {
        return 0;
    }
    return 1;
}

int
set_geometry (char *s)
{
    int l, i, spos = -1;
    l = strlen (s);
    if (l == 0) {
        fprintf (stderr, "Missing geometry definition\n");
        return -1;
    }
    if (!isnumber (s[l - 1])) {
        fprintf (stderr,
                 "Badly formed geometry definition (expecting <w>x<h)>\n");
        return -1;
    }
    for (i = 0; i < l; i++) {
        if (!isnumber (s[i]) && (s[i] != 'x')) {
            fprintf (stderr,
                     "Wrong character found in geometry definition at position %d: %c\n",
                     i, s[i]);
            return -1;
        }
        if (s[i] == 'x') {
            if (spos != -1) {
                fprintf (stderr,
                         "Bad geometry definition string (contains at least two 'x')\n");
                return -1;
            }
            if (i == 0) {
                fprintf (stderr,
                         "Bad geometry definition string (missing x dimension)\n");
                return -1;
            }
            s[i] = '\0';
            spos = i;
        }
    }
    if (spos == -1) {
        fprintf (stderr, "Bad geometry definition\n");
        return -1;
    }
    dset.w = atoi (s);
    dset.h = atoi (s + spos + 1);
    return 0;
}

int
get_coef (char *c)
{
    int l, i, spos[2] = { -1, -1 }, p = 0;

    l = strlen (c);
    if (l == 0) {
        fprintf (stderr, "Missing coef definition (expecting <r>,<g>,<b>)\n");
        return -1;
    }

    if (!isnumber (c[l - 1])) {
        fprintf (stderr,
                 "Badly formed coef definition (expecting <r>,<g>,<b>)\n");
        return -1;
    }

    for (i = 0; i < l; i++) {
        if (!isnumber (c[i]) && (c[i] != ',')) {
            fprintf (stderr,
                     "Wrong character found in coef definition at position %d: %c\n",
                     i, c[i]);
            return -1;
        }
        if (c[i] == ',') {
            if (p > 1) {
                fprintf (stderr,
                         "Bad coef definition string (contains at least three ',')\n");
                return -1;
            }
            if (i == 0) {
                fprintf (stderr,
                         "Bad coef definition string (missing coef)\n");
                return -1;
            }
            c[i] = '\0';
            spos[p++] = i;
        }
    }

    if (spos[0] == -1 || spos[1] == -1) {
        fprintf (stderr, "Bad coef definition\n");
        return -1;
    }
    dset.coef[0] = atoi (c);
    dset.coef[1] = atoi (c + spos[0] + 1);
    dset.coef[2] = atoi (c + spos[1] + 1);
    return 0;

}

void
parse_options (int argc, char **argv)
{
    int c;
    while (1) {
        static struct option long_options[] = {
            /* These options set a flag. */
            {"coef", required_argument, 0, 'c'},
            {"geometry", required_argument, 0, 'g'},
            {"help", no_argument, 0, 'h'},
            {"n_iterations", required_argument, 0, 'n'},
            {"parametrization", required_argument, 0, 'p'},
            {"precision", required_argument, 0, 'r'},
            {"version", no_argument, 0, 'v'},
            {"fullscreen", no_argument, &dset.fullscreen, 1},
            {"smooth", no_argument, &dset.smooth, 1},
            {0, 0, 0, 0}
        };

        /* getopt_long stores the option index here. */
        int option_index = 0;
        c = getopt_long (argc, argv, "vhn:g:p:c:r:", long_options,
                         &option_index);

        /* Detect the end of the options. */
        if (c == -1)
            break;
        switch (c) {
        case 0:
            break;
        case 'h':
            usage (argv[0], stdout);
            exit (EXIT_SUCCESS);
        case 'v':
            fprintf (stdout, "%s\n", VERSION_STRING);
            exit (EXIT_SUCCESS);
        case 'n':
            fset.nmax = atoi (optarg);
            if ((fset.nmax < 1) || (fset.nmax > 2 * 65536))
                fset.nmax = 1024;
            break;
        case 'g':
            if (set_geometry (optarg))
                exit (EXIT_FAILURE);
            break;
        case 'p':
            if (strcmp (optarg, "mu") == 0) {
                fset.para = MU;
                break;
            }
            if (strcmp (optarg, "mu_inv") == 0) {
                fset.para = INV_MU;
                break;
            }
            fprintf (stderr, "Bad parametrization parameter\n");
            usage (argv[0], stderr);
            exit (EXIT_FAILURE);
        case 'c':
            if (get_coef (optarg)) {
                exit (EXIT_FAILURE);
            }
            break;
        case 'r':
#ifndef HAS_MPFR
            fprintf (stderr,
                     "MPFR support not compiled in - ignoring precision setting\n");
#else
            fset.prec = atoi (optarg);
            if (fset.prec < MPFR_PREC_MIN || fset.prec > MPFR_PREC_MAX) {
                fprintf (stderr,
                         "Invalid value (too high or too low) for precision. Falling back to 64 bits.\n");
                fset.prec = 64;
            }
#endif
            break;
        case '?':
            /* getopt_long already printed an error message. */
            break;
        default:
            abort ();
        }
    }

    /* Print any remaining command line arguments (not options). */
    if (optind < argc) {
        while (optind < argc)
            fprintf (stderr,
                     "%s is not recognized as a valid option or argument\n",
                     argv[optind++]);
        usage (argv[0], stderr);
    }
}


/* Maps an integer between 0-511 to a 0-255 integer using a triangular function */
inline int
periodic_color (int x)
{
    if (x < 128) {
        return 128 + x;
    }
    if (x < 384) {
        return 383 - x;
    }
    return x - 384;
}


/* Return a color associated to a convergence value */
inline Uint32
colorize_pixel (SDL_Surface * screen, int n)
{
    if (n >= fset.nmax) {
        return SDL_MapRGB (screen->format, 16, 16, 16);
    }
    else {
        long double a = 8 * sqrt (n + 2);
        return SDL_MapRGB (screen->format,
                           periodic_color ((int) (floor (a * dset.coef[0])) %
                                           512),
                           periodic_color ((int) (floor (a * dset.coef[1])) %
                                           512),
                           periodic_color ((int) (floor (a * dset.coef[2])) %
                                           512));
}}

void
colorize (SDL_Surface * screen)
{
    int i, imax = dset.w * dset.h;

    if (dset.smooth == 0) {
        Uint32 *colormap;
        if ((colormap =
             malloc ((fset.nmax + 1) * (sizeof *colormap))) == NULL) {
            fprintf (stderr, "Unable to allocate memory for colormap\n");
            exit (EXIT_FAILURE);
        }
        for (i = 0; i <= fset.nmax; i++) {
            colormap[i] = colorize_pixel (screen, i);
        }
        for (i = 0; i < imax; i++) {
            fset.t[i].color = colormap[fset.t[i].n];
        }
        free (colormap);
    }
    else {
        double v, m;

        for (i = 0; i < imax; i++) {
            m = mpfr_get_d (fset.t[i].modulus, fset.round);
            v = ((double) fset.t[i].n - log2 (log2 (sqrt (m)))) / fset.nmax;    /* Down to the continuous 0->1 interval */
            v *= 511;
            if (fset.t[i].n >= fset.nmax) {
                fset.t[i].color = SDL_MapRGB (screen->format, 16, 16, 16);
            }
            else {
                fset.t[i].color = SDL_MapRGB (screen->format,
                                              periodic_color ((int)
                                                              (floor
                                                               (v *
                                                                dset.coef[0]))
                                                              % 512),
                                              periodic_color ((int)
                                                              (floor
                                                               (v *
                                                                dset.coef[1]))
                                                              % 512),
                                              periodic_color ((int)
                                                              (floor
                                                               (v *
                                                                dset.coef[2]))
                                                              % 512));
            }
        }
    }
    return;
}

inline void
parametrize (mpfr_t * x, mpfr_t * y)
{
    switch (fset.para) {
    case INV_MU:
        {
            mpfr_t a, b, m, a2, b2, n;

#ifdef HAS_MPFR
            mpfr_inits2 (fset.prec, a, b, a2, b2, n, m, NULL);
#endif
            mpfr_set (a, *x, fset.round);
            mpfr_set (b, *y, fset.round);
            mpfr_sqr (a2, a, fset.round);
            mpfr_sqr (b2, b, fset.round);
            mpfr_add (m, a2, b2, fset.round);
            mpfr_neg (n, b, fset.round);
            mpfr_div (*x, a, m, fset.round);
            mpfr_div (*y, n, m, fset.round);

#ifdef HAS_MPFR
            mpfr_clears (a, b, a2, b2, n, m, NULL);
#endif
        }
        break;
    default:
        break;
    }
}

void
mandelbrot (point_t * center, mpfr_t width)
{
    mpfr_t a, b, x, y, c, xmin, ymax, step, w2, w3, b2, x2, x3, x4, y2,
        y3, modulus;
    unsigned long int i, j, n;

#ifdef HAS_MPFR
    mpfr_inits2 (fset.prec, a, b, x, y, c, xmin, ymax, step, w2, w3, b2,
                 x2, x3, x4, y2, y3, modulus, NULL);
#endif

    mpfr_div_ui (w2, width, 2, fset.round);
    mpfr_mul_d (w3, w2, (double) dset.h / (double) dset.w, fset.round);
    mpfr_sub (xmin, center->x, w2, fset.round);
    mpfr_add (ymax, center->y, w3, fset.round);
    mpfr_div_ui (step, width, dset.w, fset.round);

    for (j = 0; j < dset.h; j++) {
        mpfr_mul_ui (b2, step, j, fset.round);
        mpfr_sub (b, ymax, b2, fset.round);
        for (i = 0; i < dset.w; i++) {
            mpfr_set (c, b, fset.round);
            mpfr_mul_ui (a, step, i, fset.round);
            mpfr_add (a, a, xmin, fset.round);
            parametrize (&a, &c);
            mpfr_set_ui (x, 0, fset.round);
            mpfr_set_ui (y, 0, fset.round);
            n = 0;

            do {
                mpfr_sqr (x2, x, fset.round);
                mpfr_sqr (y2, y, fset.round);
                mpfr_add (modulus, x2, y2, fset.round);
                if ((mpfr_cmp_ui (modulus, 4) >= 0) && (n > 0)) {
                    break;
                }
                mpfr_add (y3, x2, a, fset.round);
                mpfr_mul_ui (x3, x, 2, fset.round);
                mpfr_mul (x4, x3, y, fset.round);
                mpfr_add (y, x4, c, fset.round);
                mpfr_sub (x, y3, y2, fset.round);
            } while (++n < fset.nmax);
            mpfr_set (fset.t[j * dset.w + i].modulus, modulus, fset.round);
            fset.t[j * dset.w + i].n = n;
        }
    }
#ifdef HAS_MPFR
    mpfr_clears (a, b, x, y, c, xmin, ymax, step, w2, w3, b2, x2, x3, x4,
                 y2, y3, modulus, NULL);
#endif
}

void
julia (point_t * center, mpfr_t width, point_t * c)
{
    mpfr_t a, b, x, y, xmin, ymax, step, w2, w3, b2, s2, x2, y2, x3, x4,
        y3, modulus;
    int i, j, n;
    point_t c1;

#ifdef HAS_MPFR
    mpfr_inits2 (fset.prec, c1.x, c1.y, x, y, xmin, ymax, step, w2, b2,
                 s2, w3, a, b, x2, y2, x3, x4, y3, modulus, NULL);
#endif

    mpfr_set (c1.x, c->x, fset.round);
    mpfr_set (c1.y, c->y, fset.round);

    mpfr_div_ui (w2, width, 2, fset.round);
    mpfr_mul_d (w3, w2, (double) dset.h / (double) dset.w, fset.round);
    mpfr_sub (xmin, center->x, w2, fset.round);
    mpfr_add (ymax, center->y, w3, fset.round);
    mpfr_div_ui (step, width, dset.w, fset.round);

    parametrize (&(c1.x), &(c1.y));

    for (j = 0; j < dset.h; j++) {
        mpfr_mul_ui (b2, step, j, fset.round);
        mpfr_sub (b, ymax, b2, fset.round);
        for (i = 0; i < dset.w; i++) {
            mpfr_mul_ui (s2, step, i, fset.round);
            mpfr_add (a, s2, xmin, fset.round);
            mpfr_set (x, a, fset.round);
            mpfr_set (y, b, fset.round);
            n = 0;

            do {
                mpfr_sqr (x2, x, fset.round);
                mpfr_sqr (y2, y, fset.round);
                mpfr_add (modulus, x2, y2, fset.round);
                if ((mpfr_cmp_ui (modulus, 4) >= 0) && (n > 0)) {
                    break;
                }
                mpfr_add (y3, x2, c1.x, fset.round);
                mpfr_mul_ui (x3, x, 2, fset.round);
                mpfr_mul (x4, x3, y, fset.round);
                mpfr_add (y, x4, c1.y, fset.round);
                mpfr_sub (x, y3, y2, fset.round);
            } while (++n < fset.nmax);
            fset.t[j * dset.w + i].n = n;
            mpfr_set (fset.t[j * dset.w + i].modulus, modulus, fset.round);
        }
    }
#ifdef HAS_MPFR
    mpfr_clears (c1.x, c1.y, x, y, xmin, ymax, step, w2, b2, s2, w3, a, b,
                 x2, y2, x3, x4, y3, modulus, NULL);
#endif
}

SDL_Surface *
init_SDL (void)
{
    SDL_Surface *s;
    SDL_VideoInfo *vinfo;
    SDL_Init (SDL_INIT_VIDEO);
    vinfo = (SDL_VideoInfo *) SDL_GetVideoInfo ();
    dset.screen_w = vinfo->current_w;
    dset.screen_h = vinfo->current_h;
    if (dset.fullscreen == 0) {
        s = SDL_SetVideoMode (dset.w, dset.h, 0,
                              SDL_HWSURFACE | SDL_DOUBLEBUF | SDL_RESIZABLE);
    }

    else {
        dset.w = dset.screen_w;
        dset.h = dset.screen_h;
        fset.current_alloc = dset.w * dset.h;
        s = SDL_SetVideoMode (dset.w, dset.h, 0,
                              SDL_HWSURFACE | SDL_DOUBLEBUF | SDL_FULLSCREEN);
    }
    SDL_WM_SetCaption (WINDOW_TITLE, 0);
    return s;
}

void
display_screen (SDL_Surface * screen)
{
    int i, imax = dset.w * dset.h;
    switch (screen->format->BytesPerPixel) {
    case 1:                    // 8-bpp
        {
            Uint8 *bufp;
            for (i = 0; i < imax; i++) {
                bufp = (Uint8 *) screen->pixels + i;
                *bufp = fset.t[i].color;
            }
        }
        break;
    case 2:                    // 15-bpp or 16-bpp
        {
            Uint16 *bufp;
            for (i = 0; i < imax; i++) {
                bufp = (Uint16 *) screen->pixels + i;
                *bufp = fset.t[i].color;
            }
        }
        break;
    case 3:                    // 24-bpp mode, usually not used
        {
            Uint8 *bufp;
            for (i = 0; i < imax; i++) {
                bufp = (Uint8 *) screen->pixels + i * 3;
                if (SDL_BYTEORDER == SDL_LIL_ENDIAN) {
                    bufp[0] = fset.t[i].color;
                    bufp[1] = fset.t[i].color >> 8;
                    bufp[2] = fset.t[i].color >> 16;
                }
                else {
                    bufp[2] = fset.t[i].color;
                    bufp[1] = fset.t[i].color >> 8;
                    bufp[0] = fset.t[i].color >> 16;
                }
            }
        }
        break;
    case 4:                    // 32-bpp
        {
            Uint32 *bufp;
            for (i = 0; i < imax; i++) {
                bufp = (Uint32 *) screen->pixels + i;
                *bufp = fset.t[i].color;
            }
        }
        break;
    }
}

void
compute (point_t * p, mpfr_t width, SDL_Surface * screen)
{
    switch (fset.algo) {
    case MANDELBROT:
        mandelbrot (p, width);
        colorize (screen);
        break;
    case JULIA:
        julia (p, width, &fset.julia_c);
        colorize (screen);
        break;
    default:
        break;
    }
}

void
screen_to_real (mpfr_t width, point_t * center, point_t * p)
{
    mpfr_t r, rm, r2;

#ifdef HAS_MPFR
    mpfr_inits2 (fset.prec, r, rm, r2, NULL);
#endif

    mpfr_div_ui (r, width, dset.w, fset.round);

    mpfr_mul (rm, p->x, r, fset.round);
    mpfr_add (p->x, center->x, rm, fset.round);
    mpfr_mul_d (r2, r, (double) dset.w / 2, fset.round);
    mpfr_sub (p->x, p->x, r2, fset.round);

    mpfr_mul (rm, p->y, r, fset.round);
    mpfr_sub (p->y, center->y, rm, fset.round);
    mpfr_mul_d (r2, r, (double) dset.h / 2, fset.round);
    mpfr_add (p->y, p->y, r2, fset.round);

#ifdef HAS_MPFR
    mpfr_clears (r, rm, r2, NULL);
#endif
}

void
reset_video_mode (SDL_Surface * screen, int w, int h, Uint32 flag)
{
    dset.w = w;
    dset.h = h;
    if (dset.w * dset.h > fset.current_alloc) {
        while (dset.w * dset.h > fset.current_alloc)
            fset.current_alloc *= 2;
        if ((fset.t =
             realloc (fset.t,
                      fset.current_alloc * (sizeof *fset.t))) == NULL) {
            fprintf (stderr, "Unable to allocate memory for screen buffer\n");
            exit (EXIT_FAILURE);
        }
    }
    screen = SDL_SetVideoMode (dset.w, dset.h, 0, flag);
    if (screen == NULL) {
        fprintf (stderr, "Unable to change video mode. Exiting...\n");
        exit (EXIT_FAILURE);
    }
}

int
main (int argc, char **argv)
{
    int prog_running = 1, zooming = 0, coloring = 0, cw = 640, ch = 480;
    point_t p;
    mpfr_t width, r;
    SDL_Surface *screen;
    SDL_Event event;
    SDL_Rect zoom;

    srand (time (NULL));
    default_settings ();
    parse_options (argc, argv);
    screen = init_SDL ();

#ifdef HAS_MPFR
    mpfr_inits2 (fset.prec, width, r, p.x, p.y, fset.julia_c.x,
                 fset.julia_c.y, NULL);
#endif

    mpfr_set_ui (width, 3, fset.round);

    if ((fset.t = malloc (fset.current_alloc * (sizeof *fset.t))) == NULL) {
        fprintf (stderr, "Unable to allocate memory for screen buffer\n");
        exit (EXIT_FAILURE);
    }

    switch (fset.para) {
    case MU:
        mpfr_set_d (p.x, -0.75, fset.round);
        mpfr_set_ui (p.y, 0, fset.round);
        mpfr_set_d (width, 3.5, fset.round);
        break;
    case INV_MU:
        mpfr_set_d (p.x, 1.0 / .75, fset.round);
        mpfr_set_ui (p.y, 0, fset.round);
        mpfr_set_ui (width, 6, fset.round);
        break;
    default:
        break;
    }
    compute (&p, width, screen);
    while (prog_running) {
        display_screen (screen);
        if (zooming)
            rectangleColor (screen, zoom.x, zoom.y, zoom.w, zoom.h,
                            0xFFFFFFFF);
        SDL_Flip (screen);
        if (SDL_PollEvent (&event)) {
            switch (event.type) {
            case SDL_VIDEORESIZE:
                reset_video_mode (screen, event.resize.w, event.resize.h,
                                  SDL_HWSURFACE | SDL_DOUBLEBUF |
                                  SDL_RESIZABLE);
                compute (&p, width, screen);
                break;
            case SDL_KEYDOWN:
                switch (event.key.keysym.sym) {

                case SDLK_ESCAPE:
                    if (!zooming && !coloring) {
                        prog_running = 0;
                    }
                    if (zooming) {
                        zooming = 0;
                    }
                    if (coloring) {
                        coloring = 0;
                    }
                    break;

                case SDLK_EQUALS:
                    fset.nmax *= 2;
                    compute (&p, width, screen);
                    break;

                case SDLK_MINUS:
                    fset.nmax /= 2;
                    if (fset.nmax < 1)
                        fset.nmax = 1;
                    compute (&p, width, screen);
                    break;

                case SDLK_UP:
                    if (coloring) {
                        dset.coef[coloring - 1]++;
                        colorize (screen);
                        break;
                    }

                    mpfr_mul_ui (width, width, 2, fset.round);
                    compute (&p, width, screen);
                    break;

                case SDLK_DOWN:
                    if (coloring) {
                        if (dset.coef[coloring - 1] > 0) {
                            dset.coef[coloring - 1]--;
                            colorize (screen);
                        }
                        break;
                    }
                    mpfr_div_ui (width, width, 2, fset.round);
                    compute (&p, width, screen);
                    break;

                case SDLK_RETURN:
                    if (dset.fullscreen == 0) {
                        cw = dset.w;
                        ch = dset.h;
                        reset_video_mode (screen, dset.screen_w,
                                          dset.screen_h,
                                          SDL_HWSURFACE | SDL_DOUBLEBUF |
                                          SDL_FULLSCREEN);
                        dset.fullscreen = 1;
                    }

                    else {
                        reset_video_mode (screen, cw, ch,
                                          SDL_HWSURFACE | SDL_DOUBLEBUF |
                                          SDL_RESIZABLE);
                        dset.fullscreen = 0;
                    }
                    compute (&p, width, screen);
                    break;

                case SDLK_1:
                case SDLK_2:
                case SDLK_3:
                    coloring = event.key.keysym.sym - SDLK_1 + 1;
                    break;

                case SDLK_c:
                    {
                        int x, y;
                        point_t tmp;

                        mpfr_init2 (tmp.x, fset.prec);
                        mpfr_init2 (tmp.y, fset.prec);

                        SDL_GetMouseState (&x, &y);
                        mpfr_set_ui (tmp.x, x, fset.round);
                        mpfr_set_ui (tmp.y, y, fset.round);
                        screen_to_real (width, &p, &tmp);
                        mpfr_set (p.x, tmp.x, fset.round);
                        mpfr_set (p.y, tmp.y, fset.round);
                        compute (&p, width, screen);
                        mpfr_clear (tmp.x);
                        mpfr_clear (tmp.y);
                    }
                    break;

                case SDLK_j:
                    if (fset.algo == MANDELBROT) {
                        int x, y;
                        SDL_GetMouseState (&x, &y);
                        mpfr_set_ui (fset.julia_c.x, x, fset.round);
                        mpfr_set_ui (fset.julia_c.y, y, fset.round);
                        screen_to_real (width, &p, &fset.julia_c);
                        mpfr_set_ui (p.x, 0, fset.round);
                        mpfr_set_ui (p.y, 0, fset.round);
                        mpfr_set_d (width, 3.5, fset.round);
                        fset.algo = JULIA;
                        compute (&p, width, screen);
                    }
                    break;

                case SDLK_p:
                    fset.para = (fset.para + 1) % MAX_PAR;

                case SDLK_r:
                    fset.algo = MANDELBROT;
                    switch (fset.para) {
                    case MU:
                        mpfr_set_d (p.x, -0.75, fset.round);
                        mpfr_set_ui (p.y, 0, fset.round);
                        mpfr_set_d (width, 3.5, fset.round);
                        break;
                    case INV_MU:
                        mpfr_set_d (p.x, 1.0 / .75, fset.round);
                        mpfr_set_ui (p.y, 0, fset.round);
                        mpfr_set_ui (width, 6, fset.round);
                        break;
                    default:
                        break;
                    }
                    compute (&p, width, screen);
                    break;

                case SDLK_s:
                    dset.smooth = abs (dset.smooth - 1);
                    colorize (screen);
                    break;

                default:
                    break;
                }
                break;

            case SDL_MOUSEMOTION:
                if (zooming) {
                    zoom.w = event.motion.x;
                    zoom.h = event.motion.y;
                }
                break;

            case SDL_MOUSEBUTTONDOWN:
                if (zooming) {
                    mpfr_t r2, r3;
                    mpfr_init2 (r2, fset.prec);
                    mpfr_init2 (r3, fset.prec);
                    zooming = 0;

                    mpfr_div_ui (r, width, dset.w, fset.round);
                    mpfr_mul_d (r2, r, (double) dset.w / 2, fset.round);
                    mpfr_mul_d (r3, r, (double) (zoom.x + zoom.w) / 2,
                                fset.round);
                    mpfr_add (p.x, p.x, r3, fset.round);
                    mpfr_sub (p.x, p.x, r2, fset.round);

                    mpfr_mul_d (r2, r, (double) dset.h / 2, fset.round);
                    mpfr_mul_d (r3, r, (double) (zoom.y + zoom.h) / 2,
                                fset.round);
                    mpfr_add (p.y, p.y, r2, fset.round);
                    mpfr_sub (p.y, p.y, r3, fset.round);
                    mpfr_mul_ui (width, r, abs (zoom.w - zoom.x), fset.round);
                    compute (&p, width, screen);

                    mpfr_clear (r2);
                    mpfr_clear (r3);
                }
                else {
                    zooming = 1;
                    zoom.x = event.button.x;
                    zoom.w = event.button.x;
                    zoom.y = event.button.y;
                    zoom.h = event.button.y;
                }
                break;
            case SDL_QUIT:
                prog_running = 0;
                break;
            default:
                break;
            }
        }
    }

#ifdef HAS_MPFR
    mpfr_clears (width, r, p.x, p.y, fset.julia_c.x, fset.julia_c.y, NULL);
#endif
    SDL_Quit ();
    return EXIT_SUCCESS;
}

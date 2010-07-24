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
#include <time.h>
#include <getopt.h>
#include "SDL/SDL.h"
#include "SDL/SDL_gfxPrimitives.h"

#define VERSION_STRING "2.0"

typedef struct
{
    long double x;
    long double y;
} point_t;

typedef enum
{ MANDELBROT = 0, JULIA
} algo_t;

typedef enum
{ MU = 0, INV_MU = 1, MAX_PAR = 2
} parametrization_t;

typedef struct
{
    int nmax;                   /* Number of iterations to perform before assuming divergence */
    point_t julia_c;            /* Point on which to compute Julia set */
    algo_t algo;                /* Mandelbrot or Julia */
    parametrization_t para;     /* Normal or inverted */
    int *t;                     /* Table containing the fractal data */
    int current_alloc;          /* Current allocated memory for t */
} fractal_settings_t;

typedef struct
{
    int w;                      /* width of current window (in pixels) */
    int h;                      /* height of current window (in pixels) */
    int screen_w;               /* Width of the screen (in pixels) */
    int screen_h;               /* Height of thr screen (in pixels) */
    int fullscreen;             /* Are we drawing fullscreen or not */
    Uint32 *colormap;           /* The colormap */
    Uint32 coef[3];             /* Coefficients for coloring */
} display_settings_t;

static fractal_settings_t fset;
static display_settings_t dset;
const char *WINDOW_TITLE = "Mandelbrot explorer";

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
             "\t--fullscreen             | -f  : runs in fullscreen.\n");
    fprintf (stream,
             "\t--coef=<r>,<g>,<b>       | -c  : coefficients for coloring.\n\n");
}

void
default_settings (void)
{
    fset.nmax = 128;
    dset.w = 640;
    dset.h = 480;
    fset.algo = MANDELBROT;
    fset.julia_c.x = 0;
    fset.julia_c.y = 0;
    fset.para = MU;
    fset.current_alloc = dset.w * dset.h * 2;
    dset.screen_w = 640;
    dset.screen_h = 480;
    dset.fullscreen = 0;
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
            {"version", no_argument, 0, 'v'},
            {"fullscreen", no_argument, &dset.fullscreen, 1},
            {0, 0, 0, 0}
        };

        /* getopt_long stores the option index here. */
        int option_index = 0;
        c = getopt_long (argc, argv, "vhn:g:p:c:", long_options,
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


/* Maps an integer between 0-512 to a 0-256 integer using a triangular function */
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
    if (n == fset.nmax) {
        return SDL_MapRGB (screen->format, 64, 64, 64);
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

Uint32 *
create_colormap (SDL_Surface * screen, Uint32 * colormap, int nmax)
{
    int i;
    if (colormap != NULL)
        free (colormap);
    if ((colormap = (Uint32 *) malloc ((nmax + 1) * sizeof (Uint32))) == NULL) {
        fprintf (stderr, "Unable to allocate memory for colormap\n");
        exit (EXIT_FAILURE);
    }
    for (i = 0; i <= nmax; i++) {
        colormap[i] = colorize_pixel (screen, i);
    }
    return colormap;
}

inline void
parametrize (long double *x, long double *y)
{
    switch (fset.para) {
    case INV_MU:
        {
            long double a = *x, b = *y, m;
            m = a * a + b * b;
            *x = a / m;
            *y = -b / m;
        } break;
    default:
        break;
    }
}

void
mandelbrot (point_t * center, long double width)
{
    long double a, b, x, y, x1, xmin, ymax, step;
    int i, j, n;
    xmin = center->x - width / 2;
    ymax = center->y + width / 2 * dset.h / dset.w;
    step = width / dset.w;
    for (j = 0; j < dset.h; j++) {
        b = ymax - j * step;
        for (i = 0; i < dset.w; i++) {
            long double c = b;
            a = i * step + xmin;
            parametrize (&a, &c);
            x = 0;
            y = 0;
            n = 0;

            do {
                x1 = x * x - y * y + a;
                y = 2 * x * y + c;
                x = x1;
            } while (((x * x + y * y) < 4) && (++n < fset.nmax));
            fset.t[j * dset.w + i] = n;
        }
    }
}

void
julia (point_t * center, long double width, point_t * c)
{
    long double a, b, x, y, x1, xmin, ymax, step;
    int i, j, n;
    point_t c1;
    c1.x = c->x;
    c1.y = c->y;
    xmin = center->x - width / 2;
    ymax = center->y + width / 2 * dset.h / dset.w;
    step = width / dset.w;
    parametrize (&(c1.x), &(c1.y));
    for (j = 0; j < dset.h; j++) {
        b = ymax - j * step;
        for (i = 0; i < dset.w; i++) {
            a = i * step + xmin;
            x = a;
            y = b;
            n = 0;

            do {
                x1 = x * x - y * y + c1.x;
                y = 2 * x * y + c1.y;
                x = x1;
            } while (((x * x + y * y) < 4) && (++n < fset.nmax));
            fset.t[j * dset.w + i] = n;
        }
    }
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
                *bufp = dset.colormap[fset.t[i]];
            }
        }
        break;
    case 2:                    // 15-bpp or 16-bpp
        {
            Uint16 *bufp;
            for (i = 0; i < imax; i++) {
                bufp = (Uint16 *) screen->pixels + i;
                *bufp = dset.colormap[fset.t[i]];
            }
        }
        break;
    case 3:                    // 24-bpp mode, usually not used
        {
            Uint8 *bufp;
            for (i = 0; i < imax; i++) {
                bufp = (Uint8 *) screen->pixels + i * 3;
                if (SDL_BYTEORDER == SDL_LIL_ENDIAN) {
                    bufp[0] = dset.colormap[fset.t[i]];
                    bufp[1] = dset.colormap[fset.t[i]] >> 8;
                    bufp[2] = dset.colormap[fset.t[i]] >> 16;
                }
                else {
                    bufp[2] = dset.colormap[fset.t[i]];
                    bufp[1] = dset.colormap[fset.t[i]] >> 8;
                    bufp[0] = dset.colormap[fset.t[i]] >> 16;
                }
            }
        }
        break;
    case 4:                    // 32-bpp
        {
            Uint32 *bufp;
            for (i = 0; i < imax; i++) {
                bufp = (Uint32 *) screen->pixels + i;
                *bufp = dset.colormap[fset.t[i]];
            }
        }
        break;
    }
}

void
compute (point_t * p, long double width)
{
    switch (fset.algo) {
    case MANDELBROT:
        mandelbrot (p, width);
        break;
    case JULIA:
        julia (p, width, &fset.julia_c);
        break;
    default:
        break;
    }
}

void
screen_to_real (long double width, point_t * center, point_t * p)
{
    long double r;
    r = width / dset.w;
    p->x = center->x - r * dset.w / 2 + p->x * r;
    p->y = center->y + r * dset.h / 2 - p->y * r;
} void

reset_video_mode (SDL_Surface * screen, int w, int h, Uint32 flag)
{
    dset.w = w;
    dset.h = h;
    if (dset.w * dset.h > fset.current_alloc) {
        while (dset.w * dset.h > fset.current_alloc)
            fset.current_alloc *= 2;
        if ((fset.t =
             (int *) realloc (fset.t,
                              fset.current_alloc * sizeof (int))) == NULL) {
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
    int prog_running = 1, zooming = 0, cw = 640, ch = 480;
    point_t p;
    long double width, r;
    SDL_Surface *screen;
    SDL_Event event;
    SDL_Rect zoom;
    srand (time (NULL));
    default_settings ();
    parse_options (argc, argv);
    screen = init_SDL ();
    dset.colormap = create_colormap (screen, dset.colormap, fset.nmax);
    width = 3;
    if ((fset.t = (int *) malloc (fset.current_alloc * sizeof (int))) == NULL) {
        fprintf (stderr, "Unable to allocate memory for screen buffer\n");
        exit (EXIT_FAILURE);
    }
    switch (fset.para) {
    case MU:
        p.x = -0.75;
        p.y = 0;
        width = 3.5;
        break;
    case INV_MU:
        p.x = 1 / .75;
        p.y = 0;
        width = 6;
        break;
    default:
        break;
    }
    compute (&p, width);
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
                compute (&p, width);
                break;
            case SDL_KEYDOWN:
                switch (event.key.keysym.sym) {
                case SDLK_ESCAPE:
                    if (zooming)
                        zooming = 0;

                    else
                        prog_running = 0;
                    break;
                case SDLK_EQUALS:
                    fset.nmax *= 2;
                    dset.colormap =
                        create_colormap (screen, dset.colormap, fset.nmax);
                    compute (&p, width);
                    break;
                case SDLK_MINUS:
                    fset.nmax /= 2;
                    if (fset.nmax < 1)
                        fset.nmax = 1;
                    dset.colormap =
                        create_colormap (screen, dset.colormap, fset.nmax);
                    compute (&p, width);
                    break;
                case SDLK_j:
                    if (fset.algo == MANDELBROT) {
                        int x, y;
                        SDL_GetMouseState (&x, &y);
                        fset.julia_c.x = x;
                        fset.julia_c.y = y;
                        screen_to_real (width, &p, &fset.julia_c);
                        p.x = 0;
                        p.y = 0;
                        width = 3.5;
                        fset.algo = JULIA;
                        compute (&p, width);
                    }
                    break;
                case SDLK_c:
                    {
                        int x, y;
                        point_t tmp;
                        SDL_GetMouseState (&x, &y);
                        tmp.x = x;
                        tmp.y = y;
                        screen_to_real (width, &p, &tmp);
                        p.x = tmp.x;
                        p.y = tmp.y;
                        compute (&p, width);
                    } break;
                case SDLK_o:
                    width *= 2;
                    compute (&p, width);
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
                    compute (&p, width);
                    break;
                case SDLK_p:
                    fset.para = (fset.para + 1) % MAX_PAR;
                case SDLK_r:
                    fset.algo = MANDELBROT;
                    switch (fset.para) {
                    case MU:
                        p.x = -0.75;
                        p.y = 0;
                        width = 3.5;
                        break;
                    case INV_MU:
                        p.x = 1 / .75;
                        p.y = 0;
                        width = 6;
                        break;
                    default:
                        break;
                    }
                    compute (&p, width);
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
                    zooming = 0;
                    r = width / dset.w;
                    p.x = p.x - r * dset.w / 2 + (zoom.x + zoom.w) / 2 * r;
                    p.y = p.y + r * dset.h / 2 - (zoom.y + zoom.h) / 2 * r;
                    width = r * abs (zoom.w - zoom.x);
                    compute (&p, width);
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
    SDL_Quit ();
    return EXIT_SUCCESS;
}

/*
 * This program is free software; you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation; either version 3 of the License, or
 * (at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful, but
 * WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY
 * or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License
 * for more details
 *
 * You should have received a copy of the GNU General Public License along
 * with this program; if not, write to the Free Software Foundation, Inc.,
 * 59 Temple Place, Suite 330, Boston, MA 02111-1307 USA
 */
#include <stdio.h>
#include <math.h>
#include <time.h>
#include <getopt.h>

#ifdef __MINGW__
#include <windows.h>
#endif
#include <GL/glut.h>
#include "attractors.h"

#define VERSION_STRING "Polynomial strange attractors - version 1.0"
#define DEFAULT_X 800
#define DEFAULT_Y 600
#define DEFAULT_POINTS 65536
#define DEFAULT_ITER 8192
#define DEFAULT_ORDER 2
#define DEFAULT_DIM 3

typedef struct
{
    unsigned int numPoints;
    unsigned int convergenceIterations;
    unsigned int order;
    unsigned int dimension;
} fractal_settings_t;

typedef struct
{
    unsigned long int w;        /* width of current window (in pixels) */
    unsigned long int h;        /* height of current window (in pixels) */
    int fullscreen;
} display_settings_t;

static fractal_settings_t fset;
static display_settings_t dset;

const char *WINDOW_TITLE = "Strange Attractors";

static struct attractor *at;
static float angle = 3.0;
static double r = 0;

void
usage (char *prog_name, FILE * stream)
{
}

int
numbers_from_string (long *num, char *s, char separator, int n)
{
    int i;
    char *ss = s, *p = NULL;

    for (i = 0; i < n; i++) {
        num[i] = strtol (ss, &p, 0);
        if ((num[i] == 0) && (p == ss)) {
            return -1;
        }
        if (i == n - 1) {
            break;
        }
        if (*p++ != separator) {
            return -1;
        }
        ss = p;
    }
    return 0;
}

void
parse_options (int argc, char **argv)
{
    int c;

    while (1) {
        static struct option long_options[] = {
            {"conviter", required_argument, 0, 'c'},
            {"dimension", required_argument, 0, 'd'},
            {"fullscreen", no_argument, &dset.fullscreen, 1},
            {"geometry", required_argument, 0, 'g'},
            {"npoints", required_argument, 0, 'n'},
            {"order", required_argument, 0, 'o'},
            {"version", no_argument, 0, 'v'},
            {0, 0, 0, 0}
        };

        /* getopt_long stores the option index here. */
        int option_index = 0;
        c = getopt_long (argc, argv, "c:d:fg:n:o:v", long_options,
                         &option_index);

        /* Detect the end of the options. */
        if (c == -1)
            break;
        switch (c) {
        case 0:
            break;
        case 'g':{
                long n[2];
                if (numbers_from_string (n, optarg, 'x', 2) == -1) {
                    fprintf (stderr, "Bad geometry string\n");
                    exit (EXIT_FAILURE);
                }
                dset.w = n[0];
                dset.h = n[1];
                break;
            }

        case 'h':
            usage (argv[0], stdout);
            exit (EXIT_SUCCESS);

        case 'v':
            fprintf (stdout, "%s\n", VERSION_STRING);
            exit (EXIT_SUCCESS);
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

void
default_settings (void)
{
    dset.w = DEFAULT_X;
    dset.h = DEFAULT_Y;
    dset.fullscreen = 0;
    fset.numPoints = DEFAULT_POINTS;
    fset.convergenceIterations = DEFAULT_ITER;
    fset.order = DEFAULT_ORDER;
    fset.dimension = DEFAULT_DIM;
}

void
initDisplay ()
{
    int i;

    glClearColor (0.0f, 0.0f, 0.0f, 1.0f);
    glColor4f (1.0f, 1.0f, 1.0f, 0.02f);
    glViewport (0, 0, dset.w, dset.h);

    glMatrixMode (GL_PROJECTION);
    glLoadIdentity ();

    /* The square of the diagonal length */
    for (i = 0; i < MDIM; i++) {
        r += (at->bound[1][i] - at->bound[0][i]) * (at->bound[1][i] -
                                                    at->bound[0][i]);
    }
    /* Add 2% to move the clipping planes a bit further */
    r = 0.51 * sqrt (r);
    glOrtho (-r, r, -r, r, -r, r);

    glMatrixMode (GL_MODELVIEW);
    glLoadIdentity ();

#if (MDIM == 2)
    glEnable (GL_BLEND);
    glBlendFunc (GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA);
#endif

    glEnable (GL_POINT_SMOOTH);
    glPointSize (1.0f);
}

void
display ()
{
    int i;

    glClear (GL_COLOR_BUFFER_BIT);
    glMatrixMode (GL_MODELVIEW);
    glLoadIdentity ();
    glRotatef (angle, 1.0, 1.0, 1.0);

    glBegin (GL_POINTS);
    for (i = 0; i < at->numPoints; i++) {
#if (MDIM == 2)
        glVertex2f (at->array[i][0], at->array[i][1]);
#else
        glVertex3f (at->array[i][0], at->array[i][1], at->array[i][2]);
#endif
    }
    glEnd ();

    glutSwapBuffers ();
    angle += 1.0;
}

/* Keep aspect ratio */
void
reshape (int w, int h)
{
    GLdouble ar;

    glViewport (0, 0, w, h);
    ar = (GLdouble) w / (GLdouble) h;

    glMatrixMode (GL_PROJECTION);
    glLoadIdentity ();

    if (ar < 1.0) {
        glOrtho (-r, r, -r / ar, r / ar, -r, r);
    }
    else {
        glOrtho (-r * ar, r * ar, -r, r, -r, r);
    }
    glMatrixMode (GL_MODELVIEW);
    glLoadIdentity ();
}

void
key (unsigned char mychar, int x, int y)
{
    // exit the program when the Esc key is pressed
    if (mychar == 27) {
        exit (0);
    }
}

void
animate (int argc, char **argv)
{
    glutInit (&argc, argv);
    glutInitDisplayMode (GLUT_RGBA | GLUT_DOUBLE | GLUT_ALPHA | GLUT_DEPTH);

    glutInitWindowSize (dset.w, dset.h);
    glutCreateWindow (WINDOW_TITLE);

    /* Even if there are no events, redraw our gl scene. */
    glutIdleFunc (display);
    glutDisplayFunc (display);
    glutKeyboardFunc (key);
    glutReshapeFunc (reshape);

    initDisplay ();
    glutMainLoop ();
}

int
main (int argc, char **argv)
{
#ifdef __MINGW__
    freopen ("CON", "w", stdout);
    freopen ("CON", "w", stderr);
#endif

    srand (time (NULL));
    default_settings ();
    parse_options (argc, argv);
    at = newAttractor ();
    animate (argc, argv);
    freeAttractor (at);
    return EXIT_SUCCESS;
}

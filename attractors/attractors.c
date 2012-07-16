/*
 * This program is free software; you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation; either version 3 of the License, or
 * (at your option) any later version
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
#include <stdlib.h>
#include <math.h>
#include <time.h>
#include <sys/time.h>
#include <getopt.h>

#ifdef __MINGW__
#include <windows.h>
#endif
#include <GL/glut.h>

#define VERSION_STRING "Polynomial strange attractors - version 1.0"
#define DEFAULT_X 800
#define DEFAULT_Y 600
#define DEFAULT_POINTS 65536
#define DEFAULT_ITER 8192
#define DEFAULT_ORDER 2
#define DEFAULT_DIM 3
#define NUM_CONVERGENCE_POINTS 128
#define AT_INFINITY 1000000
#define LYAPU_DELTA 0.000001

/* Looks like minGW defines min and max macros somewhere */
#ifndef __MINGW__
#define min(x, y) (x)<(y)?(x):(y)
#define max(x, y) (x)>(y)?(x):(y)
#endif

typedef GLdouble *point;

struct lyapu
{
    GLdouble lsum;
    int n;
    GLdouble ly;
};

struct polynom
{
    double **p;
    int length;
    int order;
};

struct attractor
{
    struct polynom *polynom;
    struct lyapu *lyapunov;
    point *array;
    int convergenceIterations;
    int numPoints;
    GLdouble r;
    point bound[2];
    char *code;
    int dimension;
};

struct fractal_settings
{
    unsigned int numPoints;
    unsigned int convergenceIterations;
    unsigned int order;
    unsigned int dimension;
    char *code;
};

struct display_settings
{
    unsigned long int w;        /* width of current window (in pixels) */
    unsigned long int h;        /* height of current window (in pixels) */
    int fullscreen;
};

const char *WINDOW_TITLE = "Strange Attractors";
const char codelist[] = { 48, 49, 50, 51, 52, 53, 54, 55, 56, 57, 65, 66, 67,
    68, 69, 70, 71, 72, 73, 74, 75, 76, 77, 78, 79, 80, 81, 82, 83, 84,
    85, 86, 87,
    88, 89, 90, 97, 98, 99, 100, 101, 102, 103, 104, 105, 106, 107, 108,
    109, 110,
    111, 112, 113, 114, 115, 116, 117, 118, 119, 120, 121, 122
};

const int lc = (sizeof codelist) / (sizeof codelist[0]);
static struct fractal_settings fset;
static struct display_settings dset;
static struct attractor *at;
static GLfloat angle = 3.0;

void
diffTime (const char *caption, struct timeval *t1, struct timeval *t2)
{
    GLfloat td =
        (GLfloat) (t2->tv_sec - t1->tv_sec) * 1000 + ((GLfloat) t2->tv_usec -
                                                      (GLfloat) t1->tv_usec) /
        1000;
    fprintf (stdout, "%s took %.3f milliseconds\n", caption, td);
}

/* Probably best algo as we are dealing with low exponents here (typically < 5)
     so no need to bother with exponentation by squaring */
inline GLdouble
power (GLdouble base, unsigned int exp)
{
    int i;
    GLdouble result = 1.0;

    for (i = 0; i < exp; i++)
        result *= base;
    return result;
}

inline point
newPoint (void)
{
    point p;

    if ((p = malloc (fset.dimension * (sizeof *p))) == NULL) {
        fprintf (stderr, "Unable to allocate memory for point.\n");
        fprintf (stderr,
                 "I'm trying to go on, but expect a crash pretty soon :-)\n");
    }
    return p;
}

inline point
_scalar_mul (point p, GLdouble m)
{
    int i;

    for (i = 0; i < fset.dimension; i++)
        p[i] *= m;

    return p;
}

inline GLdouble
_modulus (point p)
{
    GLdouble m = 0;
    int i;

    for (i = 0; i < fset.dimension; i++)
        m += p[i] * p[i];

    return m;
}

inline GLdouble
_abs (point p)
{
    GLdouble a = 0;
    int i;

    for (i = 0; i < fset.dimension; i++)
        a += fabsl (p[i]);

    return a;
}

inline point
_sub (point a, point b)
{
    point c = newPoint ();
    int i;

    for (i = 0; i < fset.dimension; i++)
        c[i] = a[i] - b[i];

    return c;
}

inline point
_middle (point a, point b)
{
    point c = newPoint ();
    int i;

    for (i = 0; i < fset.dimension; i++)
        c[i] = (a[i] + b[i]) / 2;

    return c;
}

point
fastEval (point p, struct polynom * polynom)
{                               /* For polynoms of order 2 */
    point pe = newPoint ();
    GLfloat x2 = p[0] * p[0];
    GLfloat y2 = p[1] * p[1];
    GLfloat xy = p[0] * p[1];

    if (fset.dimension == 2) {
        pe[0] =
            polynom->p[0][0] + polynom->p[0][1] * p[0] +
            polynom->p[0][2] * p[1] + polynom->p[0][3] * x2 +
            polynom->p[0][4] * y2 + polynom->p[0][5] * xy;
        pe[1] =
            polynom->p[1][0] + polynom->p[1][1] * p[0] +
            polynom->p[1][2] * p[1] + polynom->p[1][3] * x2 +
            polynom->p[1][4] * y2 + polynom->p[1][5] * xy;
    }
    else {
        GLfloat z2 = p[2] * p[2];
        GLfloat xz = p[0] * p[2];
        GLfloat yz = p[1] * p[2];
        pe[0] =
            polynom->p[0][0] + polynom->p[0][1] * p[0] +
            polynom->p[0][2] * p[1] + polynom->p[0][3] * p[2] +
            polynom->p[0][4] * x2 + polynom->p[0][5] * y2 +
            polynom->p[0][6] * z2 + polynom->p[0][7] * xy +
            polynom->p[0][8] * xz + polynom->p[0][9] * yz;
        pe[1] =
            polynom->p[1][0] + polynom->p[1][1] * p[0] +
            polynom->p[1][2] * p[1] + polynom->p[1][3] * p[2] +
            polynom->p[1][4] * x2 + polynom->p[1][5] * y2 +
            polynom->p[1][6] * z2 + polynom->p[1][7] * xy +
            polynom->p[1][8] * xz + polynom->p[1][9] * yz;
        pe[2] =
            polynom->p[2][0] + polynom->p[2][1] * p[0] +
            polynom->p[2][2] * p[1] + polynom->p[2][3] * p[2] +
            polynom->p[2][4] * x2 + polynom->p[2][5] * y2 +
            polynom->p[2][6] * z2 + polynom->p[2][7] * xy +
            polynom->p[2][8] * xz + polynom->p[2][9] * yz;
    }
    return pe;
}

point
eval (point p, struct polynom * polynom)
{
    int coef, i, j, n;
    GLdouble result, *c;

    if (polynom->order == 2)
        return fastEval (p, polynom);

    point pe = newPoint ();

    for (coef = 0; coef < fset.dimension; coef++) {
        n = 0;
        result = 0;
        c = (GLdouble *) polynom->p[coef];
        for (i = 0; i <= polynom->order; i++) {
            for (j = 0; j <= polynom->order - i; j++) {
                if (fset.dimension == 2)
                    result += c[n++] * power (p[0], j) * power (p[1], i);
                else {
                    int k;
                    for (k = 0; k <= polynom->order - i - j; k++) {
                        result +=
                            c[n++] * power (p[0], k) * power (p[1],
                                                              j) *
                            power (p[2], i);
                    }
                }
            }
        }
        pe[coef] = result;
    }
    return pe;
}


void
displayPoint (point p)
{
    fprintf (stdout, "0x%08x : [%.10Lf,%.10Lf,%.10Lf]\n", (int) p, p[0], p[1],
             p[2]);
}

point
computeLyapunov (point p, point pe, struct attractor *at)
{
    point p2, dl, np;
    GLdouble dl2, df, rs;
    struct lyapu *lyapu = at->lyapunov;

    p2 = eval (pe, at->polynom);
    dl = _sub (p2, p);
    dl2 = _modulus (dl);

    if (dl2 == 0) {
        fprintf (stderr,
                 "Unable to compute Lyapunov exponent, trying to go on...\n");
        free (dl);
        free (p2);
        return pe;
    }

    df = dl2 / (LYAPU_DELTA * LYAPU_DELTA);
    rs = 1 / sqrt (df);

    lyapu->lsum += log (df);
    lyapu->n++;
    lyapu->ly = lyapu->lsum / lyapu->n / log (2);

    np = _sub (p, _scalar_mul (dl, rs));

    free (dl);
    free (p2);

    return np;
}

int
checkConvergence (struct attractor *at)
{
    point p, pe, pnew = NULL;
    int i, result = 0;

    p = newPoint ();
    pe = newPoint ();
    for (i = 0; i < fset.dimension; i++)
        p[i] = pe[i] = 0.1;
    pe[0] += LYAPU_DELTA;
    at->lyapunov->lsum = at->lyapunov->ly = at->lyapunov->n = 0;

    for (i = 0; i < at->convergenceIterations; i++) {
        pnew = eval (p, at->polynom);

        if (_abs (pnew) > AT_INFINITY) {        /* Diverging - not an SA */
            break;
        }
        point ptmp = _sub (pnew, p);
        if (_abs (ptmp) < 1 / AT_INFINITY) {    /* Fixed point - not an SA */
            free (ptmp);
            break;
        }
        free (ptmp);
        ptmp = computeLyapunov (pnew, pe, at);
        free (pe);
        pe = ptmp;
        if (at->lyapunov->ly < 0.005 && i >= NUM_CONVERGENCE_POINTS) {  /* Limit cycle - not an SA */
            break;
        }
        free (p);
        p = pnew;
    }
    if (i == at->convergenceIterations)
        result = 1;
    free (pnew);
    free (pe);
    return result;
}

inline int
factorial (n)
{
    int r = 1, i;

    for (i = 1; i <= n; i++) {
        r *= i;
    }

    return r;
}

inline int
getPolynomLength (int dim, int order)
{
    return factorial (order + dim) / factorial (order) / factorial (dim);
}

void
freePolynom (struct polynom *p)
{
    int i;

    for (i = 0; i < fset.dimension; i++) {
        free (p->p[i]);
    }
    free (p->p);
    free (p);
}

void
displayPolynom (struct polynom *p)
{
    int i, j;

    for (i = 0; i < fset.dimension; i++) {
        fprintf (stdout, "[ ");
        for (j = 0; j < p->length; j++) {
            fprintf (stdout, "%+.2f ", (p->p[i])[j]);
        }
        fprintf (stdout, "]\n");
    }
}

void
getRandom (struct attractor *at)
{
    int i, j, v;
    struct polynom *p = at->polynom;

    for (i = 0; i < fset.dimension; i++) {
        for (j = 0; j < p->length; j++) {
            v = rand () % lc;
            (p->p[i])[j] = (v - lc / 2) * 0.08;
            at->code[3 + i * p->length + j] = codelist[v];
        }
    }
}

void
explore (struct attractor *at)
{
    while (1) {
        getRandom (at);
        if (checkConvergence (at)) {
            break;
        }
    }
}

void
iterateMap (struct attractor *at)
{
    point p, pnew, pmin, pmax, ptmp;
    int i, j;

    if ((at->array = malloc (at->numPoints * (sizeof *(at->array)))) == NULL) {
        fprintf (stderr,
                 "Unable to allocate memory for point array. Exiting\n");
        exit (EXIT_FAILURE);
    }

    p = newPoint ();
    pmin = newPoint ();
    pmax = newPoint ();
    ptmp = p;
    for (i = 0; i < fset.dimension; i++) {
        p[i] = 0.1;
        pmin[i] = AT_INFINITY;
        pmax[i] = -AT_INFINITY;
    }

    for (i = 0; i < at->numPoints; i++) {
        pnew = eval (p, at->polynom);
        p = pnew;
        if (i >= NUM_CONVERGENCE_POINTS) {
            at->array[i - NUM_CONVERGENCE_POINTS] = pnew;
            for (j = 0; j < fset.dimension; j++) {
                pmin[j] = min (p[j], pmin[j]);
                pmax[j] = max (p[j], pmax[j]);
            }
        }
    }
    free (ptmp);
    at->bound[0] = pmin;
    at->bound[1] = pmax;
    at->numPoints -= NUM_CONVERGENCE_POINTS;
}

void
applyCode (struct polynom *p, char *code)
{
    int i, j, n, k, dim;

    dim = code[0] - '0';
    for (i = 0; i < dim; i++) {
        for (j = 0; j < p->length; j++) {
            n = 3 + i * p->length + j;
            for (k = 0; k < lc; k++) {
                if (code[n] == codelist[k])
                    break;
            }
            if (k == lc)
                fprintf (stderr, "Serious error while applying code\n");
            p->p[i][j] = (k - lc / 2) * 0.08;
        }
    }
}

int
checkCode (char *code)
{
    int dim, order, l, length, i, j;

    l = strlen (code);
    if (l < 3)
        return -1;
    if (code[2] != '_')
        return -1;

    dim = code[0] - '0';        /* I know, Unicode will likely not like this */
    order = code[1] - '0';

    if (dim < 2 || dim > 3)
        return -1;

    length = getPolynomLength (dim, order);
    if (l != length * dim + 3)
        return -1;

    for (i = 3; i < l; i++) {
        for (j = 0; j < lc; j++) {
            if (code[i] == codelist[j])
                break;
        }
        if (j == lc)
            return -1;
    }

    return 0;
}

void
freeAttractor (struct attractor *at)
{
    int i;

    free (at->lyapunov);
    for (i = 0; i < at->numPoints; i++) {
        free (at->array[i]);
    }
    free (at->array);
    for (i = 0; i < 2; i++) {
        free (at->bound[i]);
    }

    freePolynom (at->polynom);
    free (at->code);
    free (at);
}

GLdouble
getRadius (struct attractor *at)
{
    point p = _sub (at->bound[1], at->bound[0]);
    GLdouble r = 0.5 * sqrt (_modulus (p));
    free (p);
    return r;
}

void
centerAttractor (struct attractor *at)
{
    int i, j;

    point m = _middle (at->bound[0], at->bound[1]);
    for (i = 0; i < at->numPoints; i++) {
        for (j = 0; j < fset.dimension; j++) {
            at->array[i][j] -= m[j];
        }
    }
    for (i = 0; i < 2; i++) {
        for (j = 0; j < fset.dimension; j++) {
            at->bound[i][j] -= m[j];
        }
    }
    free (m);
}

struct attractor *
newAttractor (char *code)
{
    int i, codeValid = 1;

    if ((at = malloc (sizeof *at)) == NULL) {
        fprintf (stderr,
                 "Unable to allocate memory for attractor. Exiting\n");
        exit (EXIT_FAILURE);
    }

    if ((at->lyapunov = malloc (sizeof *(at->lyapunov))) == NULL) {
        fprintf (stderr,
                 "Unable to allocate memory for lyapunov structure. Exiting\n");
        exit (EXIT_FAILURE);
    }

    if ((at->polynom = malloc (sizeof *(at->polynom))) == NULL) {
        fprintf (stderr, "Unable to allocate memory for polynom. Exiting\n");
        exit (EXIT_FAILURE);
    }

    if ((code == NULL) || (checkCode (code)))
        codeValid = 0;

    if (codeValid) {
        at->dimension = code[0] - '0';
        fset.dimension = at->dimension;
    }
    else
        at->dimension = fset.dimension;


    if ((at->polynom->p =
         malloc (at->dimension * sizeof *(at->polynom->p))) == NULL) {
        fprintf (stderr, "Unable to allocate memory for polynom. Exiting\n");
        exit (EXIT_FAILURE);
    }

    if (codeValid) {
        at->polynom->order = code[1] - '0';
        fset.order = at->polynom->order;
    }
    else
        at->polynom->order = fset.order;

    at->polynom->length =
        getPolynomLength (at->dimension, at->polynom->order);
    for (i = 0; i < at->dimension; i++) {
        if ((at->polynom->p[i] =
             malloc (at->polynom->length * (sizeof *(at->polynom->p[i])))) ==
            NULL) {
            fprintf (stderr,
                     "Unable to allocate memory for polynom. Exiting\n");
            exit (EXIT_FAILURE);
        }
    }

    if (codeValid) {
        at->code = code;
    }
    else {
        if ((at->code =
             malloc ((at->polynom->length * fset.dimension +
                      4) * (sizeof *at->code))) == NULL) {
            fprintf (stderr, "Unable to allocate memory for code\n");
        }
        else {
            at->code[(at->polynom->length * fset.dimension + 3)] = '\0';
            at->code[0] = '0' + fset.dimension;
            at->code[1] = '0' + fset.order;
            at->code[2] = '_';
        }
    }

    at->convergenceIterations = fset.convergenceIterations;
    at->numPoints = fset.numPoints;

    return at;
}

void
computeAttractor (struct attractor *at, char *code)
{
    struct timeval t1, t2;

    if (code == NULL) {
        explore (at);
    }
    else {
        applyCode (at->polynom, code);
        checkConvergence (at);
    }
    displayPolynom (at->polynom);
    fprintf (stdout, "Lyapunov exponent: %.6f\n", at->lyapunov->ly);
    gettimeofday (&t1, NULL);
    iterateMap (at);
    gettimeofday (&t2, NULL);
    diffTime ("Map iteration", &t1, &t2);
    at->r = getRadius (at);
    centerAttractor (at);
    fprintf (stdout, "Code: %s\n", at->code);
}

void
usage (char *prog_name, FILE * stream)
{
    fprintf (stream, "Usage: %s\n", prog_name);
    fprintf (stream, "\t--code [string]\n");
    fprintf (stream, "\t--conviter [int] (%d)\n", DEFAULT_ITER);
    fprintf (stream, "\t--dimension [2|3] (%d)\n", DEFAULT_DIM);
    fprintf (stream, "\t--fullscreen [int] (false)\n");
    fprintf (stream, "\t--geometry [int]x[int] (%dx%d)\n", DEFAULT_X,
             DEFAULT_Y);
    fprintf (stream, "\t--help\n");
    fprintf (stream, "\t--npoints [int] (%d)\n", DEFAULT_POINTS);
    fprintf (stream, "\t--order [int] (%d)\n", DEFAULT_ORDER);
    fprintf (stream, "\t--version\n");
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
            {"code", required_argument, 0, 'C'},
            {"conviter", required_argument, 0, 'c'},
            {"dimension", required_argument, 0, 'd'},
            {"fullscreen", no_argument, &dset.fullscreen, 1},
            {"geometry", required_argument, 0, 'g'},
            {"help", no_argument, 0, 'h'},
            {"npoints", required_argument, 0, 'n'},
            {"order", required_argument, 0, 'o'},
            {"version", no_argument, 0, 'v'},
            {0, 0, 0, 0}
        };

        /* getopt_long stores the option index here. */
        int option_index = 0;
        c = getopt_long (argc, argv, "C:c:d:fg:hn:o:v", long_options,
                         &option_index);

        /* Detect the end of the options. */
        if (c == -1)
            break;
        switch (c) {
        case 0:
            break;
        case 'C':
            if ((fset.code = strdup (optarg)) == NULL) {        /* POSIX, not ANSI... who cares */
                fprintf (stderr, "Unable to allocate memory to code\n");
            }
            break;
        case 'c':
            fset.convergenceIterations = strtol (optarg, NULL, 0);
            break;
        case 'd':
            fset.dimension = strtol (optarg, NULL, 0);
            if (fset.dimension < 2 || fset.dimension > 3) {
                fprintf (stderr, "Specified dimension out of bound\n");
                usage (argv[0], stderr);
                exit (EXIT_FAILURE);
            }
            break;
        case 'g':
            {
                long n[2];
                if (numbers_from_string (n, optarg, 'x', 2) == -1) {
                    fprintf (stderr, "Bad geometry string\n");
                    exit (EXIT_FAILURE);
                }
                dset.w = n[0];
                dset.h = n[1];
                break;
            }

        case 'n':
            fset.numPoints = strtol (optarg, NULL, 0);
            break;

        case 'o':
            fset.order = strtol (optarg, NULL, 0);
            break;

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
    fset.code = NULL;
}

void
positionLight ()
{
    GLfloat ambient[] = { 0.1f, 0.1f, 0.1f };
    GLfloat diffuse1[] = { 0.5f, 0.0f, 0.0f, 1.0f };
    GLfloat diffuse2[] = { 0.0f, 0.5f, 0.0f, 1.0f };
    GLfloat diffuse3[] = { 0.0f, 0.0f, 0.5f, 1.0f };
    GLfloat specular1[] = { 1.0f, 0.5f, 0.5f, 1.0f };
    GLfloat specular2[] = { 0.5f, 1.0f, 0.5f, 1.0f };
    GLfloat specular3[] = { 0.5f, 0.5f, 1.0f, 1.0f };
    GLfloat position1[] = { 0.0f, 0.0f, -10.0f, 1.0f };
    GLfloat position2[] = { -10.0f, 0.0f, 10.0f, 1.0f };
    GLfloat position3[] = { 10.0f, 0.0f, 10.0f, 1.0f };

    glLightfv (GL_LIGHT7, GL_AMBIENT, ambient);
    glEnable (GL_LIGHT7);
    glLightfv (GL_LIGHT0, GL_DIFFUSE, diffuse1);
    glLightfv (GL_LIGHT0, GL_POSITION, position1);
    glEnable (GL_LIGHT0);
    glLightfv (GL_LIGHT1, GL_DIFFUSE, diffuse2);
    glLightfv (GL_LIGHT1, GL_POSITION, position2);
    glEnable (GL_LIGHT1);
    glLightfv (GL_LIGHT2, GL_DIFFUSE, diffuse3);
    glLightfv (GL_LIGHT2, GL_POSITION, position3);
    glEnable (GL_LIGHT2);
    glLightfv (GL_LIGHT3, GL_DIFFUSE, specular1);
    glLightfv (GL_LIGHT3, GL_POSITION, position1);
    glEnable (GL_LIGHT3);
    glLightfv (GL_LIGHT4, GL_DIFFUSE, specular2);
    glLightfv (GL_LIGHT4, GL_POSITION, position2);
    glEnable (GL_LIGHT4);
    glLightfv (GL_LIGHT5, GL_DIFFUSE, specular3);
    glLightfv (GL_LIGHT5, GL_POSITION, position3);
    glEnable (GL_LIGHT5);
}

void
initDisplay ()
{
    glClearColor (0.0f, 0.0f, 0.0f, 1.0f);
    glColor4f (1.0f, 1.0f, 1.0f, 0.0f);
    glViewport (0, 0, dset.w, dset.h);

    glMatrixMode (GL_PROJECTION);
    glLoadIdentity ();

    /* Add 2% to move the clipping planes a bit further */
    glOrtho (-at->r, at->r, -at->r, at->r, -at->r, at->r);

    glMatrixMode (GL_MODELVIEW);
    glLoadIdentity ();

    if (fset.dimension == 2) {
        glEnable (GL_BLEND);
        glBlendFunc (GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA);
    }

    glEnable (GL_POINT_SMOOTH);
    glEnable (GL_LIGHTING);
    glDisable (GL_COLOR_MATERIAL);
    glPointSize (1.0f);
}

void
display ()
{
    int i;

    glClear (GL_COLOR_BUFFER_BIT);
    glMatrixMode (GL_MODELVIEW);
    glLoadIdentity ();
    positionLight ();
    if (fset.dimension == 2) {
        glRotatef (angle, 1.0, 1.0, 1.0);
    }
    else {
        glRotatef (angle, 1.0, 1.0, 1.0);
    }
    glBegin (GL_POINTS);
    for (i = 0; i < at->numPoints; i++) {
        if (fset.dimension == 2)
            glVertex2dv (at->array[i]);
        else {
            glVertex3dv (at->array[i]);
            /* Normal equal to the vector -> vertex redirects light in the same direction */
            glNormal3dv (at->array[i]);
        }
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
        glOrtho (-at->r, at->r, -at->r / ar, at->r / ar, -at->r, at->r);
    }
    else {
        glOrtho (-at->r * ar, at->r * ar, -at->r, at->r, -at->r, at->r);
    }
    glMatrixMode (GL_MODELVIEW);
    glLoadIdentity ();
}

void
key (unsigned char mychar, int x, int y)
{
    // exit the program when the Esc key is pressed
    if (mychar == 27) {
        exit (EXIT_SUCCESS);
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
    at = newAttractor (fset.code);
    computeAttractor (at, fset.code);
    animate (argc, argv);
    freeAttractor (at);
    return EXIT_SUCCESS;
}

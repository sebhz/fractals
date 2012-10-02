#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <sys/time.h>
#include <GL/glut.h>
#include "global.h"

extern struct fractal_settings fset;

void
diffTime (const char *caption, struct timeval *t1, struct timeval *t2)
{
    float td =
        (float) (t2->tv_sec - t1->tv_sec) * 1000 + ((float) t2->tv_usec -
                                                    (float) t1->tv_usec) /
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

GLdouble
euclidianDistance (point a, point b)
{
    int i;
    GLdouble d = 0.0;

    for (i = 0; i < fset.dimension; i++) {
        d += (a[i] - b[i]) * (a[i] - b[i]);
    }
    return d;
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

static point
fastEval (point p, struct polynom *polynom)
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
    int i;

    fprintf (stdout, "0x%08x : [ ", (int) p);
    for (i = 0; i < fset.dimension; i++) {
        fprintf (stdout, "%.6f ", (double) p[i]);
    }
    fprintf (stdout, "]\n");
}

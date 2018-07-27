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
 *
 */
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
GLdouble
power (GLdouble base, unsigned int exp)
{
    int i;
    GLdouble result = 1.0;

    for (i = 0; i < exp; i++)
        result *= base;
    return result;
}

point
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

point
_scalar_mul (point p, GLdouble m)
{
    int i;

    for (i = 0; i < fset.dimension; i++)
        p[i] *= m;

    return p;
}

GLdouble
_modulus (point p)
{
    GLdouble m = 0;
    int i;

    for (i = 0; i < fset.dimension; i++)
        m += p[i] * p[i];

    return m;
}

GLdouble
_abs (point p)
{
    GLdouble a = 0;
    int i;

    for (i = 0; i < fset.dimension; i++)
        a += fabsl (p[i]);

    return a;
}

point
_sub (point a, point b)
{
    point c = newPoint ();
    int i;

    for (i = 0; i < fset.dimension; i++)
        c[i] = a[i] - b[i];

    return c;
}

point
_middle (point a, point b)
{
    point c = newPoint ();
    int i;

    for (i = 0; i < fset.dimension; i++)
        c[i] = (a[i] + b[i]) / 2;

    return c;
}

point
fastEval (point p, struct polynom *polynom)
{                               /* For polynoms of order 2 */
    int i;
    point pe = newPoint ();
    GLfloat x2 = p[0] * p[0];
    GLfloat y2 = p[1] * p[1];
    GLfloat xy = p[0] * p[1];

    if (fset.dimension == 2) {
        for (i = 0; i < 2; i++)
            pe[i] =
                polynom->p[i][0] + polynom->p[i][1] * p[0] +
                polynom->p[i][2] * p[1] + polynom->p[i][3] * x2 +
                polynom->p[i][4] * y2 + polynom->p[i][5] * xy;
    }
    else {
        GLfloat z2 = p[2] * p[2];
        GLfloat xz = p[0] * p[2];
        GLfloat yz = p[1] * p[2];
        for (i = 0; i < 3; i++)
            pe[i] =
                polynom->p[i][0] + polynom->p[i][1] * p[0] +
                polynom->p[i][2] * p[1] + polynom->p[i][3] * p[2] +
                polynom->p[i][4] * x2 + polynom->p[i][5] * y2 +
                polynom->p[i][6] * z2 + polynom->p[i][7] * xy +
                polynom->p[i][8] * xz + polynom->p[i][9] * yz;
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

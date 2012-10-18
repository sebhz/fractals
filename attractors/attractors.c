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
 * Attractor generation algorithm taken from J. Sprott book "Strange Attractors" (http://sprott.physics.wisc.edu/sa.htm)
 */
#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <string.h>
#include <time.h>
#include <sys/time.h>
#include <GL/glut.h>

#include "global.h"
#include "util.h"

#define min(x, y) (x)<(y)?(x):(y)
#define max(x, y) (x)>(y)?(x):(y)

const char codelist[] = { 48, 49, 50, 51, 52, 53, 54, 55, 56, 57, 65, 66, 67,
    68, 69, 70, 71, 72, 73, 74, 75, 76, 77, 78, 79, 80, 81, 82, 83, 84,
    85, 86, 87,
    88, 89, 90, 97, 98, 99, 100, 101, 102, 103, 104, 105, 106, 107, 108,
    109, 110,
    111, 112, 113, 114, 115, 116, 117, 118, 119, 120, 121, 122
};

const int lc = (sizeof codelist) / (sizeof codelist[0]);

extern struct fractal_settings fset;

point
computeLyapunov (point p, point pe, struct attractor *a)
{
    point p2, dl, np;
    GLdouble dl2, df, rs;
    struct lyapu *lyapu = a->lyapunov;

    p2 = eval (pe, a->polynom);
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
isAttractorConverging (struct attractor *at)
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
	    free(p);
            break;
        }
        point ptmp = _sub (pnew, p);
        if (_abs (ptmp) < 1 / AT_INFINITY) {    /* Fixed point - not an SA */
	    free(p);
            free (ptmp);
            break;
        }
        free (ptmp);
        ptmp = computeLyapunov (pnew, pe, at);
        free (pe);
        pe = ptmp;
        if (at->lyapunov->ly < 0.005 && i >= NUM_CONVERGENCE_POINTS) {  /* Limit cycle - not an SA */
	    free(p);
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
getPolynomLength (int dim, int order)
{
    int i, a = 1;
    /* (order + dim)! / order! / dim ! */
    for (i = order + 1; i <= order + dim; i++)
        a *= i;
    if (dim == 2)
        return a / 2;
    else
        return a / 6;
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
getRandom (struct attractor *a)
{
    int i, j, v;
    struct polynom *p = a->polynom;

    for (i = 0; i < fset.dimension; i++) {
        for (j = 0; j < p->length; j++) {
            v = rand () % lc;
            (p->p[i])[j] = (v - lc / 2) * 0.08;
            a->code[3 + i * p->length + j] = codelist[v];
        }
    }
}

#define DIM_RADIUS1 0.001
#define DIM_RADIUS2 0.00001
GLdouble
computeDimension (struct attractor *at)
{
    /* An estimate of the correlation dimension: accumulate the values of the distances between
       point p and one of its predecessors, ignoring the points right before p */
    GLdouble n1 = 0.0, n2 = 0.0, d2;
    GLdouble d2max = 4 * at->r * at->r; /* Square of the attractor radius */
    int twod = 1 << at->dimension;
    int i, j;

    if (at->numPoints <= DIM_DEPTH) {
        return -1;
    }

    for (i = DIM_DEPTH; i < at->numPoints - NUM_CONVERGENCE_POINTS; i++) {
        j = i - DIM_IGNORE - (rand () % (DIM_DEPTH - DIM_IGNORE));
        d2 = euclidianDistance (at->array[i], at->array[j]);
        if (d2 < DIM_RADIUS1 * twod * d2max)
            n2++;
        if (d2 > DIM_RADIUS2 * twod * d2max)
            continue;
        n1++;
    }

    at->correlationDimension = log10 (n2 / n1);
    return at->correlationDimension;
}

void
explore (struct attractor *a)
{
    while (1) {
        getRandom (a);
        if (isAttractorConverging (a)) {
            break;
        }
    }
}

void
iterateMap (struct attractor *a)
{
    point p, pnew, pmin, pmax, ptmp, ptofree[NUM_CONVERGENCE_POINTS];
    int i, j;


    p = newPoint ();
    pmin = newPoint ();
    pmax = newPoint ();
    ptmp = p;
    for (i = 0; i < fset.dimension; i++) {
        p[i] = 0.1;
        pmin[i] = AT_INFINITY;
        pmax[i] = -AT_INFINITY;
    }

    for (i = 0; i < NUM_CONVERGENCE_POINTS; i++) {
	ptofree[i] = eval (p, a->polynom);
	p = ptofree[i];
    }
    for (i = 0; i < NUM_CONVERGENCE_POINTS-1; i++) {
	free(ptofree[i]);
    }
    free (ptmp);
    ptmp = p;

    for (i = 0; i < a->numPoints-NUM_CONVERGENCE_POINTS; i++) {
        pnew = eval (p, a->polynom);
        a->array[i] = pnew;
        p = pnew;
        for (j = 0; j < fset.dimension; j++) {
            pmin[j] = min (p[j], pmin[j]);
            pmax[j] = max (p[j], pmax[j]);
        }
    }
    free(ptmp);
    a->bound[0] = pmin;
    a->bound[1] = pmax;
}

double
getPolynomSum (struct polynom *p)
{
    int i, j;
    double sum = 0.0;

    for (i = 0; i < fset.dimension; i++) {
        for (j = 0; j < p->length; j++) {
            sum += p->p[i][j];
        }
    }
    return sum;
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

    if (code == NULL)
        return -1;

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
    for (i = 0; i < (at->numPoints-NUM_CONVERGENCE_POINTS); i++) {
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
getRadius (struct attractor *a)
{
    return 0.5 * sqrt (euclidianDistance (a->bound[1], a->bound[0]));
}

void
centerAttractor (struct attractor *a)
{
    int i, j;

    point m = _middle (a->bound[0], a->bound[1]);
    for (i = 0; i < a->numPoints - NUM_CONVERGENCE_POINTS; i++) {
        for (j = 0; j < fset.dimension; j++) {
            a->array[i][j] -= m[j];
        }
    }
    for (i = 0; i < 2; i++) {
        for (j = 0; j < fset.dimension; j++) {
            a->bound[i][j] -= m[j];
        }
    }
    free (m);
}

/* Allocate memory for a polynomial attractor */
struct attractor *
newAttractor (int order, int dimension, int convergenceIterations,
              int numPoints)
{
    int i;
    struct attractor *a;


    if ((a = malloc (sizeof *a)) == NULL) {
        fprintf (stderr,
                 "Unable to allocate memory for attractor. Exiting\n");
        exit (EXIT_FAILURE);
    }

    if ((a->lyapunov = malloc (sizeof *(a->lyapunov))) == NULL) {
        fprintf (stderr,
                 "Unable to allocate memory for lyapunov structure. Exiting\n");
        exit (EXIT_FAILURE);
    }

    if ((a->polynom = malloc (sizeof *(a->polynom))) == NULL) {
        fprintf (stderr, "Unable to allocate memory for polynom. Exiting\n");
        exit (EXIT_FAILURE);
    }

    a->dimension = dimension;

    if ((a->polynom->p =
         malloc (a->dimension * sizeof *(a->polynom->p))) == NULL) {
        fprintf (stderr, "Unable to allocate memory for polynom. Exiting\n");
        exit (EXIT_FAILURE);
    }

    a->polynom->sum = 0;
    a->polynom->order = order;
    a->polynom->length = getPolynomLength (dimension, order);
    for (i = 0; i < dimension; i++) {
        if ((a->polynom->p[i] =
             malloc (a->polynom->length * (sizeof *(a->polynom->p[i])))) ==
            NULL) {
            fprintf (stderr,
                     "Unable to allocate memory for polynom. Exiting\n");
            exit (EXIT_FAILURE);
        }
    }

    if ((a->code =
         malloc ((a->polynom->length * dimension +
                  4) * (sizeof *a->code))) == NULL) {
        fprintf (stderr, "Unable to allocate memory for code\n");
        exit (EXIT_FAILURE);
    }
    else {
        a->code[(a->polynom->length * dimension + 3)] = '\0';
        a->code[0] = '0' + dimension;
        a->code[1] = '0' + order;
        a->code[2] = '_';
    }
    a->convergenceIterations = convergenceIterations;
    a->numPoints = numPoints;

    if ((a->array = malloc ((a->numPoints - NUM_CONVERGENCE_POINTS) * (sizeof *(a->array)))) == NULL) {
        fprintf (stderr,
                 "Unable to allocate memory for point array. Exiting\n");
        exit (EXIT_FAILURE);
    }
    return a;
}

/* Compute an attractor previously allocated by newAttractor */
void
computeAttractor (struct attractor *a, char *code)
{
    struct timeval t1, t2;

    if (code == NULL || checkCode (code)) {
        explore (a);
    }
    else {
        strncpy (a->code, code, a->polynom->length * a->dimension + 3);
        applyCode (a->polynom, code);
        if (!isAttractorConverging (a))
            fprintf (stderr, "Bad code - attractor not converging\n");
    }

    a->polynom->sum = getPolynomSum (a->polynom);

    displayPolynom (a->polynom);
    fprintf (stdout, "Lyapunov exponent: %.6f\n", a->lyapunov->ly);
    gettimeofday (&t1, NULL);
    iterateMap (a);
    gettimeofday (&t2, NULL);
    diffTime ("Map iteration", &t1, &t2);
    a->r = getRadius (a);
    centerAttractor (a);
    computeDimension (a);
    fprintf (stdout, "Correlation dimension: %.6f\n",
             a->correlationDimension);
    fprintf (stdout, "Code: %s\n", a->code);
}

#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <time.h>
#include "attractors.h"

#define NUM_CONVERGENCE_POINTS 128
#define AT_INFINITY 1000000

/* Probably best algo as we are dealing with low exponents here (typically < 5)
     so no need to bother with exponentation by squaring */
inline long double
power (long double base, unsigned int exp)
{
    int i;
    long double result = 1.0;

    for (i = 0; i < exp; i++)
        result *= base;
    return result;
}

inline point
newPoint (void)
{
    point p;

    if ((p = malloc (MDIM * (sizeof *p))) == NULL) {
        fprintf (stderr, "Unable to allocate memory for point.\n");
        fprintf (stderr,
                 "I'm trying to go on, but expect a crash pretty soon :-)\n");
    }
    return p;
}

inline point
_scalar_mul (point p, long double m)
{
    int i;

    for (i = 0; i < MDIM; i++)
        p[i] *= m;

    return p;
}

inline long double
_modulus (point p)
{
    long double m = 0;
    int i;

    for (i = 0; i < MDIM; i++)
        m += p[i] * p[i];

    return m;
}

inline long double
_abs (point p)
{
    long double a = 0;
    int i;

    for (i = 0; i < MDIM; i++)
        a += fabsl (p[i]);

    return a;
}

inline point
_sub (point a, point b)
{
    point c = newPoint ();
    int i;

    for (i = 0; i < MDIM; i++)
        c[i] = a[i] - b[i];

    return c;
}

inline point
_middle (point a, point b)
{
    point c = newPoint ();
    int i;

    for (i = 0; i < MDIM; i++)
        c[i] = (a[i] + b[i]) / 2;

    return c;
}

point
eval (point p, struct polynom * polynom)
{
    int coef, i, j, n;
    long double result, *c;
    point pe = newPoint ();

    for (coef = 0; coef < MDIM; coef++) {
        n = 0;
        result = 0;
        c = (long double *) polynom->p[coef];
        for (i = 0; i <= polynom->order; i++) {
            for (j = 0; j <= polynom->order - i; j++) {
#if (MDIM == 2)
                result += c[n++] * power (p[0], j) * power (p[1], i);
#else
                int k;
                for (k = 0; k <= polynom->order - i - j; k++) {
                    result +=
                        c[n++] * power (p[0], k) * power (p[1],
                                                          j) * power (p[2],
                                                                      i);
                }
#endif
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
    long double dl2, df, rs;
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

    df = 1000000000000 * dl2;
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
    for (i = 0; i < MDIM; i++)
        p[i] = pe[i] = 0.1;
    pe[0] += 0.000001;
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
    free (p);                   // FIXME:  p=pnew -> multiple  free here... Will this ever compile on Linux ?
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

    for (i = 0; i < MDIM; i++) {
        free (p->p[i]);
    }
    free (p);
}

void
displayPolynom (struct polynom *p)
{
    int i, j;

    for (i = 0; i < MDIM; i++) {
        fprintf (stdout, "[ ");
        for (j = 0; j < p->length; j++) {
            fprintf (stdout, "%+.2Lf ", (p->p[i])[j]);
        }
        fprintf (stdout, "]\n");
    }
}

struct polynom *
getRandom (int order)
{
    struct polynom *p;
    int i, j;

    if ((p = malloc (sizeof *p)) == NULL) {
        fprintf (stderr, "Unable to allocate memory for polynom. Exiting\n");
        exit (EXIT_FAILURE);
    }

    p->order = order;
    p->length = getPolynomLength (MDIM, order);
    for (i = 0; i < MDIM; i++) {
        if ((p->p[i] = malloc (p->length * (sizeof *(p->p[i])))) == NULL) {
            fprintf (stderr,
                     "Unable to allocate memory for polynom. Exiting\n");
            exit (EXIT_FAILURE);
        }
        for (j = 0; j < p->length; j++) {
            (p->p[i])[j] = (double) ((rand () % 61) - 30) * 0.08;
        }
    }
    return p;
}

void
explore (struct attractor *at, int order)
{
    while (1) {
        at->polynom = getRandom (order);
        if (checkConvergence (at)) {
            break;
        }
        freePolynom (at->polynom);
    }
}

#define min(x, y) (x) < (y)? (x) : (y)
#define max(x, y) (x) > (y)? (x) : (y)

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
    for (i = 0; i < MDIM; i++) {
        p[i] = 0.1;
        pmin[i] = AT_INFINITY;
        pmax[i] = -AT_INFINITY;
    }

    for (i = 0; i < at->numPoints; i++) {
        pnew = eval (p, at->polynom);
        p = pnew;
        if (i >= NUM_CONVERGENCE_POINTS) {
            at->array[i - NUM_CONVERGENCE_POINTS] = pnew;
            for (j = 0; j < MDIM; j++) {
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
    free (at);
}

void
centerAttractor (struct attractor *at)
{
    int i, j;

    point m = _middle (at->bound[0], at->bound[1]);
    for (i = 0; i < at->numPoints; i++) {
        for (j = 0; j < MDIM; j++) {
            at->array[i][j] -= m[j];
        }
    }
    for (i = 0; i < 2; i++) {
        for (j = 0; j < MDIM; j++) {
            at->bound[i][j] -= m[j];
        }
    }
    free (m);
}

struct attractor *
newAttractor (void)
{
    struct attractor *at;

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

    at->convergenceIterations = 8192;
    at->numPoints = 250000;
    explore (at, 2);
    displayPolynom (at->polynom);
    fprintf (stdout, "Lyapunov exponent: %.6Lf\n", at->lyapunov->ly);
    iterateMap (at);
    centerAttractor (at);
    return at;
}

#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <time.h>

#define MDIM 3

struct lyapu {
	long double lsum;
	int n;
	long double ly;
}; 

struct polynom {
	long double *p[MDIM];
	int length;
	int order;
};

typedef long double *point;

inline long double power(long double x, unsigned int exp) {
    int i;
	long double result = 1.0;

    for (i = 0; i < exp; i++)
        result *= x;
    return result;
 }

inline point newPoint(void) {
	point p;

	if ((p = malloc(MDIM*(sizeof *p))) == NULL) {
		fprintf(stderr, "Unable to allocate memory for point.\n");
		fprintf(stderr, "I'm trying to go on, but expect a crash pretty soon :-)\n");
	}
	return p;
}

inline point _scalar_mul(point p, long double m) {

	int i;

	for (i=0; i < MDIM; i++)
		p[i]*=m;
	
	return p;
}

inline long double _modulus(point p) {
	long double m = 0;
	int i;

	for (i=0; i < MDIM; i++)
		m += p[i]*p[i];

	return m;
}

inline long double _abs(point p) {
	long double a = 0;
	int i;

	for (i=0; i < MDIM; i++)
		a += fabsl(p[i]);

	return a;
}

inline point _sub(point a, point b) {
	point c = newPoint();
	int i;

	for (i=0; i < MDIM; i++)
		c[i] = a[i] - b[i];

	return c;
}

point eval(point p, struct polynom *polynom) {
	int coef, i, j, k, n;
	long double result, *c;
	point pe = newPoint();

	for (coef = 0; coef < MDIM; coef++) {
		n = 0;
		result = 0;
		c = polynom->p[coef];
		for (i=0; i<=polynom->order; i++) {
			for (j=0; j<=polynom->order-i; j++) {
				for (k=0; k<= polynom->order-i-j; k++) {
					result += c[n++]*power(p[0],k)*power(p[1],j)*power(p[2],i);
				}
			}
		}
		pe[coef] = result;
	}
	return pe;
}

void displayPoint(point p) {
	fprintf(stdout, "0x%08x : (%.10Lf,%.10Lf,%.10Lf)\n", (int)p, p[0], p[1], p[2]);
}

point computeLyapunov(point p, point pe, struct lyapu lyapu, struct polynom *polynom) {
	point p2, dl, np;
	long double dl2, df, rs;

	p2 = eval(pe, polynom);
	dl = _sub(p2, p);
	dl2 = _modulus(dl);

	if (dl2 == 0) {
		fprintf(stderr, "Unable to compute Lyapunov exponent, trying to go on...\n");
		free(dl);
		free(p2);
		return pe;
	}

	df = 1000000000000*dl2;
    rs = 1/sqrt(df);
 
	lyapu.lsum += log(df);
	lyapu.n++;
	lyapu.ly = lyapu.lsum/lyapu.n/log(2);

	np = _sub(p, _scalar_mul(dl, rs));

	free(dl);
	free(p2);

	return np;
}

int checkConvergence(struct polynom *polynom, int maxiter) {
	struct lyapu lyapu = {0.0, 0, 0.0};
	point p, pe, pnew;
	int i, result = 0;

	p = newPoint(); pe = newPoint();
	for (i=0; i<MDIM; i++) p[i] = pe[i] = 0.1;
	pe[0] += 0.000001;

  	for (i=0; i < maxiter; i++) {
		pnew = eval(p, polynom);

		if (_abs(pnew) > 1000000) { /* Diverging - not an SA */
			break;
		}
		point ptmp = _sub(pnew, p);
		if (_abs(ptmp) < 0.00000001) { /* Fixed point - not an SA */
			free(ptmp);
			break;
		}
		free(ptmp);
		ptmp = computeLyapunov(pnew, pe, lyapu, polynom);
		free(pe);
		pe = ptmp;
		if (lyapu.ly < 0.005 && i > 128) { /* Limit cycle - not an SA */
			break;
		}
		free(p);
		p = pnew;
	}
	if (i == maxiter) result = 1;
	free(pnew);
	free(pe);
	free(p);
	return result;
}

inline int factorial(n) {
	int r = 1, i;

	for (i=1; i<=n; i++) {
		r *= i;
	}

	return r;
}

inline int getPolynomLength(int dim, int order) {
	return factorial(order+dim)/factorial(order)/factorial(dim);
}

void freePolynom(struct polynom *p) {
	int i;

	for (i=0; i<MDIM; i++) {
		free(p->p[i]);
	}
	free(p);
}

void displayPolynom(struct polynom *p) {
	int i, j;

	fprintf(stdout, "length: %d\n", p->length);
	for (i=0; i < MDIM; i++) {
		fprintf(stdout, "[ ");
		for (j=0; j< p->length; j++) {
			fprintf(stdout, "%.2Lf ", (p->p[i])[j]);
		}
		fprintf(stdout, "]\n");
	}
}

struct polynom *getRandom(int order) {
	struct polynom *p;
	int i, j;
	
	if ((p = malloc(sizeof *p)) == NULL) {
		fprintf(stderr, "Unable to allocate memory for polynom. Exiting\n");
		exit(EXIT_FAILURE);
	}

	p->order  = order;
	p->length = getPolynomLength(MDIM, order);
	for (i=0; i < MDIM; i++) {
		if ((p->p[i] = malloc(p->length*(sizeof *(p->p[i])))) == NULL) {
			fprintf(stderr, "Unable to allocate memory for polynom. Exiting\n");
		}
		for (j=0; j<p->length; j++) {
			(p->p[i])[j] = (long double)((rand()%61)-30)*0.08;
		}
	}
	return p;
}
	
struct polynom *explore(int order, int maxiter) {
	struct polynom *p;
	int n = 0;
	while (1) {
		p = getRandom(order);
		if (checkConvergence(p, maxiter)) {
			break;
		}
		freePolynom(p);
	}
	return p;
}		

int main (int argc, char **argv) {
	struct polynom *p;

	srand(time(NULL));
	p = explore(2, 16384);

	return EXIT_SUCCESS;
}

typedef long double *point;

struct lyapu
{
    long double lsum;
    int n;
    long double ly;
};

struct polynom
{
    long double *p[MDIM];
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
    point bound[2];
};

void freeAttractor(struct attractor *at);
struct attractor *newAttractor(void);
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
    double sum;
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
    GLdouble correlationDimension;
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
    int displayInfo;
    int speed;                  /* Rotation speed in degree per sec */
    float fps;
    GLfloat angle;
    unsigned long int old_w;    /* To keep original window size in mem when going full screen */
    unsigned long int old_h;
    unsigned long int old_x;
    unsigned long int old_y;
    float increment;
    int currentTime;
    double divergence;
};

#define DEFAULT_W 800
#define DEFAULT_H 600
#define DEFAULT_X 128
#define DEFAULT_Y 128
#define DEFAULT_SPEED 30
#define DEFAULT_INCREMENT 0.0005
#define DEFAULT_POINTS 65536
#define DEFAULT_ITER 8192
#define DEFAULT_ORDER 2
#define DEFAULT_DIM 3
#define DIM_DEPTH 512           // Use the DIM_DEPTH predecessors of each point to compute the dimension
#define DIM_IGNORE 32           // but ignore DIM_IGNORE predecessors (presumably too correlated)
#define NUM_CONVERGENCE_POINTS 128
#define AT_INFINITY 1000000
#define LYAPU_DELTA 0.000001
#define MAX_ITER 1000
#define MAX_DIVERGENCE 1.5

#include <stdio.h>
#include <stdlib.h>
#include <sys/time.h>
#include <time.h>
#include <GL/glut.h>

#include "global.h"
#include "util.h"
#include "attractors.h"
#include "display.h"
#include "args.h"

struct fractal_settings fset = {
    .numPoints = DEFAULT_POINTS,
    .convergenceIterations = DEFAULT_ITER,
    .order = DEFAULT_ORDER,
    .dimension = DEFAULT_DIM,
    .code = NULL
};

struct display_settings dset = {
    .speed = DEFAULT_SPEED,
    .fullscreen = 0,
    .displayInfo = 0,
    .angle = 0.0,
    .fps = 0.0,
    .old_x = DEFAULT_X,
    .old_y = DEFAULT_Y,
    .old_h = DEFAULT_H,
    .old_w = DEFAULT_W,
    .currentTime = 0,
    .increment = DEFAULT_INCREMENT,
    .divergence = 0
};

struct attractor *at[2];
int frontBuffer = 0;

int
main (int argc, char **argv)
{
#ifdef __MINGW__
    freopen ("CON", "w", stdout);
    freopen ("CON", "w", stderr);
#endif

    srand (time (NULL));
    parseOptions (argc, argv);
    if (fset.code != NULL && !checkCode (fset.code)) {
        fset.dimension = fset.code[0] - '0';
        fset.order = fset.code[1] - '0';
    }
    at[frontBuffer] =
        newAttractor (fset.order, fset.dimension, fset.convergenceIterations,
                      fset.numPoints);
    at[1 - frontBuffer] =
        newAttractor (fset.order, fset.dimension, fset.convergenceIterations,
                      fset.numPoints);

    computeAttractor (at[frontBuffer], fset.code);

    animate (argc, argv);
    freeAttractor (at[frontBuffer]);
    freeAttractor (at[1 - frontBuffer]);
    return EXIT_SUCCESS;
}

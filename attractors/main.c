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

struct attractor *at[2];
int frontBuffer = 0;

int
main (int argc, char **argv)
{
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

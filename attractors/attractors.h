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
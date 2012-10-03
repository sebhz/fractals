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
struct attractor *newAttractor (int order, int dimension,
                                int convergenceIterations, int numPoints);

void computeAttractor (struct attractor *a, char *code);

void freeAttractor (struct attractor *at);

int checkCode (char *code);

int isAttractorConverging (struct attractor *at);

void iterateMap (struct attractor *a);

GLdouble getRadius (struct attractor *a);

void centerAttractor (struct attractor *a);

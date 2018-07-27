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
void diffTime (const char *caption, struct timeval *t1, struct timeval *t2);

GLdouble power (GLdouble base, unsigned int exp);

point newPoint (void);

point eval (point p, struct polynom *polynom);

GLdouble euclidianDistance (point a, point b);

point _scalar_mul (point p, GLdouble m);

GLdouble _abs (point p);

GLdouble _modulus (point p);

point _sub (point a, point b);;

point _middle (point a, point b);

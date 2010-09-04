/* 
 * This program is free software; you can redistribute it and/or modify 
 * it under the terms of the GNU General Public License as published by 
 * the Free Software Foundation; either version 3 of the License, or 
 * (at your option) any later version.
 * 
 * This program is distributed in the hope that it will be useful, but 
 * WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY 
 * or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License 
 * for more details.
 * 
 * You should have received a copy of the GNU General Public License along 
 * with this program; if not, write to the Free Software Foundation, Inc., 
 * 59 Temple Place, Suite 330, Boston, MA 02111-1307 USA
 */
#ifndef __PREC__
#define __PREC__

#ifdef HAS_MPFR
#include <mpfr.h>
#else
#define mpfr_t long double
#define mpfr_rnd_t  int
#define mpfr_prec_t int
#define mpfr_div(a, b, c, d) ( (a) = (b)/(c) )
#define mpfr_neg(a, b, c) ( (a) = -(b) )
#define mpfr_init2(a, b)
#define mpfr_clear(a)
#define MPFR_RNDZ 0
#endif

#endif 

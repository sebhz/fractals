#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include "SDL/SDL.h"

/*
  Found this at http://www.cs.rit.edu/~ncs/color/t_convert.html

  Convert HSV to RGB 
   h -> hue in degree (0 to 360)
   s -> saturation (0 to 1)
   v -> value/brightness (0 to 1)

   returns r, g, b (0 to 1)
*/
int  HSVtoRGB(float h, float s, float v )
{
	int i;
	float f, p, q, t, r, g , b;

	if( s == 0 ) {
		// achromatic (grey)
		r = g = b = v;
		goto end;
	}

	h /= 60;			// sector 0 to 5
	i = floor( h );
	f = h - i;			// factorial part of h
	p = v * ( 1 - s );
	q = v * ( 1 - s * f );
	t = v * ( 1 - s * ( 1 - f ) );

	switch( i ) {
		case 0:
			r = v;
			g = t;
			b = p;
			break;
		case 1:
			r = q;
			g = v;
			b = p;
			break;
		case 2:
			r = p;
			g = v;
			b = t;
			break;
		case 3:
			r = p;
			g = q;
			b = v;
			break;
		case 4:
			r = t;
			g = p;
			b = v;
			break;
		default:		// case 5:
			r = v;
			g = p;
			b = q;
			break;
	}

end:
	return ((int)(r*255) << 24) + ((int)(g*255) << 16) + (int)(b*255);
}

Uint32 *create_colormap(SDL_Surface *screen, Uint32 *colormap, int nmax) {
	int i, v;

	if (colormap != NULL) free(colormap);
	if ( (colormap = (Uint32 *)malloc((nmax+1)*sizeof(Uint32))) == NULL ) {
		fprintf(stderr, "Unable to allocate memory for colormap\n");
		exit(EXIT_FAILURE);
	}

	for (i=0; i<nmax; i++) {
		v = (int)(767*(double)i/(nmax-1));
		if (v > 511) 
			colormap[i] = SDL_MapRGB(screen->format, 0xFF, 0xFF, v%256);
		else if (v>255) 
			colormap[i] = SDL_MapRGB(screen->format, 0, v%256, 0xFF);
		else 
			colormap[i] = SDL_MapRGB(screen->format, 0,   0,  v%256);
	}
	colormap[nmax] = SDL_MapRGB(screen->format, 0, 0, 0);

	return colormap;
}


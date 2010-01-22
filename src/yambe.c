#include <stdio.h>
#include <stdlib.h>
#include <time.h>
#include "SDL/SDL.h"
#include "SDL/SDL_image.h"
#include "SDL/SDL_gfxPrimitives.h"

typedef struct {
	double x;
	double y;
} point_t;

static int nx = 640, ny = 400;
static int nmax = 100;
const char *WINDOW_TITLE = "Mandelbrot";
static int *colormap;

void
apply_surface (int x, int y, SDL_Surface * source, SDL_Surface * destination)
{
    SDL_Rect offset;
    offset.x = x;
    offset.y = y;
    SDL_BlitSurface (source, NULL, destination, &offset);
}


void mandelbrot(point_t *center, double width, int *res)
{
	double a, b, x, y, x1, xmin, ymax, step;
	int i, j, n;
	
	xmin = center->x-width/2;
	ymax = center->y+width/2*ny/nx;
	step = width/nx;
	
	for (j=0; j<ny; j++) {
		b = ymax-j*step;
		for (i=0; i < nx; i++) {
			a = i*step+xmin;
			x=0; y=0; n=0;
			do {
				x1 = x*x-y*y+a;
				y  = 2*x*y+b;
				x  = x1;
				n++;
			} while (((x*x+y*y) < 4) && (n <= nmax));
			res[j*nx + i] = n;
		}
	}
}

SDL_Surface *init_SDL(void)
{
	SDL_Surface *s;

	SDL_Init(SDL_INIT_VIDEO);
    s = SDL_SetVideoMode (nx, ny, 0,
                          SDL_HWSURFACE | SDL_DOUBLEBUF |
                          SDL_RESIZABLE);
    SDL_WM_SetCaption (WINDOW_TITLE, 0);

	return s;
}

void DrawPixel(SDL_Surface *screen, int x, int y, Uint8 R, Uint8 G, Uint8 B)
{
  Uint32 color = SDL_MapRGB(screen->format, R, G, B);
  switch (screen->format->BytesPerPixel)
  {
    case 1: // 8-bpp
      {
        Uint8 *bufp;
        bufp = (Uint8 *)screen->pixels + y*screen->pitch + x;
        *bufp = color;
      }
      break;
    case 2: // 15-bpp or 16-bpp
      {
        Uint16 *bufp;
        bufp = (Uint16 *)screen->pixels + y*screen->pitch/2 + x;
        *bufp = color;
      }
      break;
    case 3: // 24-bpp mode, usually not used
      {
        Uint8 *bufp;
        bufp = (Uint8 *)screen->pixels + y*screen->pitch + x * 3;
        if(SDL_BYTEORDER == SDL_LIL_ENDIAN)
        {
          bufp[0] = color;
          bufp[1] = color >> 8;
          bufp[2] = color >> 16;
        } else {
          bufp[2] = color;
          bufp[1] = color >> 8;
          bufp[0] = color >> 16;
        }
      }
      break;
    case 4: // 32-bpp
      {
        Uint32 *bufp;
        bufp = (Uint32 *)screen->pixels + y*screen->pitch/4 + x;
        *bufp = color;
      }
      break;
  }
} 

void display_screen(SDL_Surface *s, int *res)
{
	int x, y, n;

	for (x=0; x< nx; x++)
		for (y=0; y<ny; y++) {
			n = res[y*nx+x];
			DrawPixel(s, x, y, colormap[n] >> 16, (colormap[n] >> 8)& 0x0000FF, (colormap[n] >> 16)& 0x0000FF);
	}
	SDL_Flip(s);
	SDL_Delay(2000);
}

int main(int argc, char **argv)
{
	int *res, i;
	point_t p;
	SDL_Surface *screen;
	
    srand (time (NULL));
	if ((res = (int *)malloc(nx*ny*sizeof(int))) == NULL ) {
		fprintf(stderr, "Unable to allocate memory for screen buffer\n");
		exit(EXIT_FAILURE);
	}
	
	if ((colormap = (int *)malloc((nmax+1)*sizeof(int))) == NULL ) {
		fprintf(stderr, "Unable to allocate memory for colormap\n");
		exit(EXIT_FAILURE);
	}
	for (i=0; i<nmax; i++) {
		colormap[i] = rand()%(256*256*256); 
	}
	colormap[nmax] = 0;

	screen = init_SDL();
	p.x = -0.5; p.y = 0;
	mandelbrot(&p, 3.5, res);
	display_screen(screen, res);
	SDL_Quit();
	return EXIT_SUCCESS;
}	

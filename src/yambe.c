#include <stdio.h>
#include <stdlib.h>
#include <time.h>
#include <getopt.h>
#include "SDL/SDL.h"
#include "SDL/SDL_gfxPrimitives.h"

#define VERSION_STRING "1.0"

typedef struct {
	double x;
	double y;
} point_t;

typedef enum {
	MANDELBROT = 0,
	JULIA
} algo_t;

typedef enum {
	MU = 0,
	INV_MU = 1,
	MAX_PAR = 2
} parametrization_t;

typedef struct {
	int nx; /* X resolution of window */
	int ny; /* Y resolution of window */
	int nmax; /* Number of iterations to perform before auuming divergence */
	point_t julia_c;
	algo_t algo;
	parametrization_t para;
	int current_alloc;
} settings_t;

static settings_t settings;
static SDL_Rect zoom;

const char *WINDOW_TITLE = "Mandelbrot explorer";
static Uint32 *colormap = NULL;

void usage(char *prog_name, FILE *stream) {
	fprintf(stream, "%s (version %s):\n", prog_name, VERSION_STRING);
	fprintf(stream, "\t--version      | -v: show program version\n");
	fprintf(stream, "\t--help         | -h: show this help\n");
	fprintf(stream, "\t--n_iterations | -n: number of iterations to perform before assuming divergence\n");
	fprintf(stream, "\t--geometry=<geo>  | -g: sets the window geometry.\n");
	fprintf(stream, "\t--parametrization=<para>  | -p: sets initial parametrization. Valid values are mu and mu_inv.\n\n");
}

void default_settings(void) 
{
	settings.nmax = 128;
	settings.nx = 640; 
	settings.ny = 480; 
	settings.algo = MANDELBROT;
	settings.julia_c.x = 0;
	settings.julia_c.y = 0;
	settings.para = MU;
	settings.current_alloc = 640*480;
}

int set_geometry(char *s) {
	int l, i, spos = -1;

	l = strlen(s);
	if (l == 0) {
		fprintf(stderr, "Missing geometry definition\n");
		return -1;
	}

	for (i=0; i < l; i++) {
		if ( ((s[i] < '0') || (s[i] > '9')) && (s[i] != 'x') ) {
			fprintf(stderr, "Wrong character found in geometry definition at position %d: %c\n", i, s[i]);
			return -1;
		}
		if (s[i] == 'x') {
			if (spos != -1) {
				fprintf(stderr, "Bad geometry definition string (contains at least two 'x')\n");
				return -1;
			}
			if (i == 0) {
				fprintf(stderr, "Bad geometry definition string (missing x dimension)\n");
				return -1;
			}
			s[i] = '\0';
			spos = i;
		}
	}
	if (spos == -1) {
		fprintf(stderr, "Bad geometry definition\n");
		return -1;
	}

	settings.nx = atoi(s);
	settings.ny = atoi(s+spos+1);
	return 0;

}

void parse_options (int argc, char **argv)
{
  int c;

  while (1)
    {
      static struct option long_options[] =
        {
          /* These options set a flag. */
          {"version",      no_argument, 0, 'v'},
          {"help",         no_argument, 0, 'h'},
          {"n_iterations", required_argument, 0, 'n'},
          {"geometry",     required_argument, 0, 'g'},
          {"parametrization", required_argument, 0, 'p'},
          {0, 0, 0, 0}
        };
      /* getopt_long stores the option index here. */
      int option_index = 0;

      c = getopt_long (argc, argv, "vhn:g:p:",
                       long_options, &option_index);

      /* Detect the end of the options. */
      if (c == -1)
        break;

      switch (c)
        {
        case 'h':
			usage(argv[0], stdout);
			exit(EXIT_SUCCESS);

        case 'v':
			fprintf(stdout, "%s\n", VERSION_STRING);
			exit(EXIT_SUCCESS);

        case 'n':
			settings.nmax = atoi(optarg);
			if ((settings.nmax < 1) || (settings.nmax > 2*65536)) settings.nmax = 1024;
			break;

		case 'g':
			if (set_geometry(optarg)) exit(EXIT_FAILURE);
			break;

   		case 'p':
			if (strcmp(optarg, "mu") == 0) {
				settings.para = MU;
				break;
			}
			if (strcmp(optarg, "mu_inv") == 0) {
				settings.para = INV_MU;
				break;
			}
			fprintf(stderr, "Bad parametrization parameter\n");
			usage(argv[0], stderr);
			exit(EXIT_FAILURE);

		case '?':
          /* getopt_long already printed an error message. */
          break;

        default:
          abort ();
        }
    }

  /* Print any remaining command line arguments (not options). */
  if (optind < argc)
    {
       while (optind < argc)
			fprintf(stderr, "%s is not recognized as a valid option or argument\n", argv[optind++]);
		usage(argv[0], stderr);
	}
}

inline void parametrize (double *x, double *y) {
	double a = *x, b = *y, m;

	switch(settings.para) {
		case INV_MU:
			m = a*a + b*b;
			*x = a/m; *y = -b/m;
			break;
		default:
			break;
	}
}
		
void mandelbrot(point_t *center, double width, int *res)
{
	double a, b, x, y, x1, xmin, ymax, step;
	int i, j, n;
	
	xmin = center->x-width/2;
	ymax = center->y+width/2*settings.ny/settings.nx;
	step = width/settings.nx;
	
	for (j=0; j<settings.ny; j++) {
		b = ymax-j*step;
		for (i=0; i < settings.nx; i++) {
			double c = b;
			a = i*step+xmin;
			parametrize(&a, &c);
			x=0; y=0; n=0;
			do {
				x1 = x*x-y*y+a;
				y  = 2*x*y+c;
				x  = x1;
				n++;
			} while (((x*x+y*y) < 4) && (n < settings.nmax));
			res[j*settings.nx + i] = n;
		}
	}
}

void julia(point_t *center, double width, int *res, point_t *c)
{
	double a, b, x, y, x1, xmin, ymax, step;
	int i, j, n;
	point_t c1; c1.x = c->x; c1.y = c->y;
	
	xmin = center->x-width/2;
	ymax = center->y+width/2*settings.ny/settings.nx;
	step = width/settings.nx;
	
	parametrize(&(c1.x), &(c1.y));
	for (j=0; j<settings.ny; j++) {
		b = ymax-j*step;
		for (i=0; i < settings.nx; i++) {
			a = i*step+xmin;
			x=a; y=b; n=0;
			do {
				x1 = x*x-y*y+c1.x;
				y  = 2*x*y+c1.y;
				x  = x1;
				n++;
			} while (((x*x+y*y) < 4) && (n < settings.nmax));
			res[j*settings.nx + i] = n;
		}
	}
}

SDL_Surface *init_SDL(void)
{
	SDL_Surface *s;

	SDL_Init(SDL_INIT_VIDEO);
    s = SDL_SetVideoMode (settings.nx, settings.ny, 0,
                          SDL_HWSURFACE | SDL_DOUBLEBUF |
                          SDL_RESIZABLE);
    SDL_WM_SetCaption (WINDOW_TITLE, 0);

	return s;
}

void display_screen(SDL_Surface *screen, int *res)
{
	int i, imax = settings.nx*settings.ny;

  switch (screen->format->BytesPerPixel)
  {
    case 1: // 8-bpp
      {
        Uint8 *bufp;
		for (i=0; i < imax; i++) {
        	bufp = (Uint8 *)screen->pixels + i;
        	*bufp = colormap[res[i]];
      	}
		}
      	break;
    case 2: // 15-bpp or 16-bpp
      {
        Uint16 *bufp;
 		for (i=0; i < imax; i++) {
        	bufp = (Uint16 *)screen->pixels + i;
        	*bufp = colormap[res[i]];
      	}
      }
      break;
    case 3: // 24-bpp mode, usually not used
      {
 
        Uint8 *bufp;
		for (i=0; i < imax; i++) {
        	bufp = (Uint8 *)screen->pixels + i*3;
        if(SDL_BYTEORDER == SDL_LIL_ENDIAN)
        {
          bufp[0] = colormap[res[i]];
          bufp[1] = colormap[res[i]] >> 8;
          bufp[2] = colormap[res[i]] >> 16;
        } else {
          bufp[2] = colormap[res[i]];
          bufp[1] = colormap[res[i]] >> 8;
          bufp[0] = colormap[res[i]] >> 16;
        }
      }
		}
      break;
    case 4: // 32-bpp
      {
        Uint32 *bufp;
  		for (i=0; i < imax; i++) {
        	bufp = (Uint32 *)screen->pixels + i;
        	*bufp = colormap[res[i]];
      	}
      }
      break;
  }
} 

void create_colormap(SDL_Surface *screen) {
	int i, v;

	if (colormap != NULL) free(colormap);
	if ((colormap = (Uint32 *)malloc((settings.nmax+1)*sizeof(Uint32))) == NULL ) {
		fprintf(stderr, "Unable to allocate memory for colormap\n");
		exit(EXIT_FAILURE);
	}
	for (i=0; i<settings.nmax; i++) {
		v = (int)(2048*(double)i/settings.nmax);
		if (v > 1024) 
			colormap[i] = SDL_MapRGB(screen->format, 0xFF, 0xFF, v%255);
		else if (v>512) 
			colormap[i] = SDL_MapRGB(screen->format, 0xFF, v%255, 0);
		else 
			colormap[i] = SDL_MapRGB(screen->format, v%255,   0,  0);

	}
	colormap[settings.nmax] = SDL_MapRGB(screen->format, 0, 0, 0);
}

void compute(point_t *p, double width, int *res) {
	switch (settings.algo) {
		case MANDELBROT:
			mandelbrot(p, width, res);
			break;

		case JULIA:
			julia(p, width, res, &settings.julia_c);
			break;

		default:
			break;
	}
}

void screen_to_real(double width, point_t *center, point_t *p) {
	double r;
			
	r = width/settings.nx;
	p->x = center->x - r*settings.nx/2 + p->x*r;
	p->y = center->y + r*settings.ny/2 - p->y*r;
}

int main(int argc, char **argv)
{
	int *res, prog_running = 1, zooming = 0;
	point_t p;
	double width, r;
	SDL_Surface *screen;
    SDL_Event event;
	
    srand (time (NULL));
	default_settings();
	parse_options(argc, argv);
	
	if ((res = (int *)malloc(settings.nx*settings.ny*2*sizeof(int))) == NULL ) {
		fprintf(stderr, "Unable to allocate memory for screen buffer\n");
		exit(EXIT_FAILURE);
	}
	settings.current_alloc = settings.nx*settings.ny*2;
	screen = init_SDL();
	create_colormap(screen);
	width = 3;
	
	switch(settings.para) {
		case MU: p.x = -0.75; p.y = 0; width = 3; break;
		case INV_MU: p.x = 1/.75; p.y = 0; width = 6; break;
		default: break;
	}
	compute(&p, width, res);
	while (prog_running) {
		display_screen(screen, res);
		if (zooming) 
			rectangleColor(screen, zoom.x, zoom.y, zoom.w, zoom.h, 0xFFFFFFFF);

		SDL_Flip(screen);
		if (SDL_PollEvent (&event)) {
			switch (event.type) {
            	case SDL_VIDEORESIZE:
         			settings.nx = event.resize.w;
					settings.ny = event.resize.h;
					if (settings.nx*settings.ny >  settings.current_alloc) {
						while (settings.nx*settings.ny >  settings.current_alloc) settings.current_alloc*=2;
						if ((res = (int *)realloc(res, settings.current_alloc*sizeof(int))) == NULL ) {
							fprintf(stderr, "Unable to allocate memory for screen buffer\n");
							exit(EXIT_FAILURE);
						}
					}
					screen =
                        SDL_SetVideoMode (event.resize.w,
                                          event.resize.h, 0,
                                          SDL_HWSURFACE |
                                          SDL_DOUBLEBUF | SDL_RESIZABLE);
                    if (screen == NULL) {
                        return -1;
                    }
					compute(&p, width, res);
                    break;

                case SDL_KEYDOWN:
                    switch (event.key.keysym.sym) {
	                    case SDLK_ESCAPE:
							if (zooming) 
								zooming = 0;
							else
								prog_running = 0;
                            break;
					 
						case SDLK_EQUALS:
							settings.nmax*=2;	
							create_colormap(screen);
							compute(&p, width, res);
							break;	

                       	case SDLK_MINUS:
							settings.nmax/=2;	
							if (settings.nmax < 1) settings.nmax = 1;
							create_colormap(screen);
							compute(&p, width, res);
							break;	

                       	case SDLK_j:
							if (settings.algo == MANDELBROT) {
								int x, y;
								SDL_GetMouseState(&x, &y);
								settings.julia_c.x = x; settings.julia_c.y = y;
								screen_to_real(width, &p, &settings.julia_c);
								p.x = 0; p.y = 0; width = 3.5; 
								settings.algo = JULIA;
								compute(&p, width, res);
							}	
							break;	
				
				     	case SDLK_p:
							settings.para = (settings.para+1)%MAX_PAR;
                       	case SDLK_r:
							settings.algo = MANDELBROT;
							switch(settings.para) {
								case MU: p.x = -0.75; p.y = 0; width = 3; break;
								case INV_MU: p.x = 1/.75; p.y = 0; width = 6; break;
								default: break;
							}
							compute(&p, width, res);
							break;	
                            
						default:
                            break;
					}
					break;

                 case SDL_MOUSEMOTION:
					if (zooming) {
                    	zoom.w = event.motion.x;
                    	zoom.h = event.motion.y;
					}
                    break;

                case SDL_MOUSEBUTTONDOWN:
					if (zooming) {
						zooming = 0;
						r = width/settings.nx;
						p.x = p.x - r*settings.nx/2 + (zoom.x+zoom.w)/2*r;
						p.y = p.y + r*settings.ny/2 - (zoom.y+zoom.h)/2*r;
					
						width = r*abs(zoom.w-zoom.x);
						compute(&p, width, res);
					}
					else {
						zooming = 1;
                    	zoom.x = event.button.x;
                     	zoom.w = event.button.x;
                    	zoom.y = event.button.y;
 	                  	zoom.h = event.button.y;
					}
					break;
 
                case SDL_QUIT:
					prog_running = 0;
                    break;

				default:
					break;
 
			}
		}
	}
	SDL_Quit();
	return EXIT_SUCCESS;
}	


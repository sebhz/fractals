#include <stdio.h>
#include <stdlib.h>
#include <time.h>
#include <getopt.h>
#include "SDL/SDL.h"
#include "SDL/SDL_gfxPrimitives.h"

#define VERSION_STRING "1.0"

Uint32 *create_colormap(SDL_Surface *screen, Uint32 *colormap, int nmax);

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
	int nmax;               /* Number of iterations to perform before assuming divergence */
	point_t julia_c;        /* Point on which to compute Julia set */
	algo_t algo;            /* Mandelbrot or Julia */
	parametrization_t para; /* Normal or inverted */
	int *t;                 /* Table containing the fractal data */ 
	int current_alloc;      /* Current allocated memory for t */
} fractal_settings_t;

typedef struct {
	int w;            /* width of current window (in pixels) */
	int h;            /* height of current window (in pixels) */
	int screen_w;     /* Width of the screen (in pixels) */
	int screen_h;     /* Height of thr screen (in pixels) */
	int fullscreen;   /* Are we drawing fullscreen or not */
	Uint32 *colormap; /* The colormap */
} display_settings_t;

static fractal_settings_t fset;
static display_settings_t dset;

const char *WINDOW_TITLE = "Mandelbrot explorer";

void usage(char *prog_name, FILE *stream) {
	fprintf(stream, "%s (version %s):\n", prog_name, VERSION_STRING);
	fprintf(stream, "\t--version      | -v            : show program version\n");
	fprintf(stream, "\t--help         | -h            : show this help\n");
	fprintf(stream, "\t--n_iterations | -n            : number of iterations to perform before assuming divergence\n");
	fprintf(stream, "\t--geometry=<geo> | -g          : sets the window geometry.\n");
	fprintf(stream, "\t--parametrization=<para> | -p  : sets initial parametrization. Valid values are mu and mu_inv.\n\n");
	fprintf(stream, "\t--fullscreen                   : runs in fullscreen.\n\n");
}

void default_settings(void) 
{
	fset.nmax = 128;
	dset.w = 640; 
	dset.h = 480; 
	fset.algo = MANDELBROT;
	fset.julia_c.x = 0;
	fset.julia_c.y = 0;
	fset.para = MU;
	fset.current_alloc = dset.w*dset.h*2;
	dset.screen_w = 640; 
	dset.screen_h = 480; 
	dset.fullscreen = 0; 
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

	dset.w = atoi(s);
	dset.h = atoi(s+spos+1);
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
          {"fullscreen",   no_argument, &dset.fullscreen, 1},
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
		case 0:
			break;

        case 'h':
			usage(argv[0], stdout);
			exit(EXIT_SUCCESS);

        case 'v':
			fprintf(stdout, "%s\n", VERSION_STRING);
			exit(EXIT_SUCCESS);

        case 'n':
			fset.nmax = atoi(optarg);
			if ((fset.nmax < 1) || (fset.nmax > 2*65536)) fset.nmax = 1024;
			break;

		case 'g':
			if (set_geometry(optarg)) exit(EXIT_FAILURE);
			break;

   		case 'p':
			if (strcmp(optarg, "mu") == 0) {
				fset.para = MU;
				break;
			}
			if (strcmp(optarg, "mu_inv") == 0) {
				fset.para = INV_MU;
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

	switch(fset.para) {
		case INV_MU:
			m = a*a + b*b;
			*x = a/m; *y = -b/m;
			break;
		default:
			break;
	}
}
		
void mandelbrot(point_t *center, double width)
{
	double a, b, x, y, x1, xmin, ymax, step;
	int i, j, n;
	
	xmin = center->x-width/2;
	ymax = center->y+width/2*dset.h/dset.w;
	step = width/dset.w;
	
	for (j=0; j<dset.h; j++) {
		b = ymax-j*step;
		for (i=0; i < dset.w; i++) {
			double c = b;
			a = i*step+xmin;
			parametrize(&a, &c);
			x=0; y=0; n=0;
			do {
				x1 = x*x-y*y+a;
				y  = 2*x*y+c;
				x  = x1;
				n++;
			} while (((x*x+y*y) < 4) && (n < fset.nmax));
			fset.t[j*dset.w + i] = n;
		}
	}
}

void julia(point_t *center, double width, point_t *c)
{
	double a, b, x, y, x1, xmin, ymax, step;
	int i, j, n;
	point_t c1; c1.x = c->x; c1.y = c->y;
	
	xmin = center->x-width/2;
	ymax = center->y+width/2*dset.h/dset.w;
	step = width/dset.w;
	
	parametrize(&(c1.x), &(c1.y));
	for (j=0; j<dset.h; j++) {
		b = ymax-j*step;
		for (i=0; i < dset.w; i++) {
			a = i*step+xmin;
			x=a; y=b; n=0;
			do {
				x1 = x*x-y*y+c1.x;
				y  = 2*x*y+c1.y;
				x  = x1;
				n++;
			} while (((x*x+y*y) < 4) && (n < fset.nmax));
			fset.t[j*dset.w + i] = n;
		}
	}
}

SDL_Surface *init_SDL(void)
{
	SDL_Surface *s;
	SDL_VideoInfo *vinfo;

	SDL_Init(SDL_INIT_VIDEO);

	vinfo = (SDL_VideoInfo *)SDL_GetVideoInfo();
	dset.screen_w = vinfo->current_w;
	dset.screen_h = vinfo->current_h;

	if (dset.fullscreen == 0) {
   		 s = SDL_SetVideoMode (dset.w, dset.h, 0,
        	                  SDL_HWSURFACE | SDL_DOUBLEBUF |
            	              SDL_RESIZABLE);
    }
	else {
		dset.w = dset.screen_w;
		dset.h = dset.screen_h;
		fset.current_alloc = dset.w*dset.h;
		s = SDL_SetVideoMode (dset.w, dset.h, 0,
        	                  SDL_HWSURFACE | SDL_DOUBLEBUF |
            	              SDL_FULLSCREEN);
	}
	SDL_WM_SetCaption (WINDOW_TITLE, 0);

	return s;
}

void display_screen(SDL_Surface *screen)
{
	int i, imax = dset.w*dset.h;

  switch (screen->format->BytesPerPixel)
  {
    case 1: // 8-bpp
      {
        Uint8 *bufp;
		for (i=0; i < imax; i++) {
        	bufp = (Uint8 *)screen->pixels + i;
        	*bufp = dset.colormap[fset.t[i]];
      	}
		}
      	break;
    case 2: // 15-bpp or 16-bpp
      {
        Uint16 *bufp;
 		for (i=0; i < imax; i++) {
        	bufp = (Uint16 *)screen->pixels + i;
        	*bufp = dset.colormap[fset.t[i]];
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
          bufp[0] = dset.colormap[fset.t[i]];
          bufp[1] = dset.colormap[fset.t[i]] >> 8;
          bufp[2] = dset.colormap[fset.t[i]] >> 16;
        } else {
          bufp[2] = dset.colormap[fset.t[i]];
          bufp[1] = dset.colormap[fset.t[i]] >> 8;
          bufp[0] = dset.colormap[fset.t[i]] >> 16;
        }
      }
		}
      break;
    case 4: // 32-bpp
      {
        Uint32 *bufp;
  		for (i=0; i < imax; i++) {
        	bufp = (Uint32 *)screen->pixels + i;
        	*bufp = dset.colormap[fset.t[i]];
      	}
      }
      break;
  }
} 

void compute(point_t *p, double width) {
	switch (fset.algo) {
		case MANDELBROT:
			mandelbrot(p, width);
			break;

		case JULIA:
			julia(p, width, &fset.julia_c);
			break;

		default:
			break;
	}
}

void screen_to_real(double width, point_t *center, point_t *p) {
	double r;
			
	r = width/dset.w;
	p->x = center->x - r*dset.w/2 + p->x*r;
	p->y = center->y + r*dset.h/2 - p->y*r;
}

void reset_video_mode(SDL_Surface *screen, int w, int h, Uint32 flag) { 
	dset.w = w;
	dset.h = h;
	if (dset.w*dset.h >  fset.current_alloc) {
		while (dset.w*dset.h > fset.current_alloc) fset.current_alloc*=2;
		if ((fset.t = (int *)realloc(fset.t, fset.current_alloc*sizeof(int))) == NULL ) {
			fprintf(stderr, "Unable to allocate memory for screen buffer\n");
			exit(EXIT_FAILURE);
		}
	}
	screen =
    SDL_SetVideoMode (dset.w,
           	              dset.h, 0,
						  flag);
   	if (screen == NULL) {
   		fprintf(stderr, "Unable to change video mode. Exiting...\n");
		exit(EXIT_FAILURE);
    }
}

int main(int argc, char **argv)
{
	int prog_running = 1, zooming = 0, cw=640, ch=480;
	point_t p;
	double width, r;
	SDL_Surface *screen;
    SDL_Event event;
	SDL_Rect zoom;

    srand (time (NULL));
	default_settings();
	parse_options(argc, argv);
	
	screen = init_SDL();
	dset.colormap = create_colormap(screen, dset.colormap, fset.nmax);
	width = 3;

	if ((fset.t = (int *)malloc(fset.current_alloc*sizeof(int))) == NULL ) {
		fprintf(stderr, "Unable to allocate memory for screen buffer\n");
		exit(EXIT_FAILURE);
	}

	switch(fset.para) {
		case MU: p.x = -0.75; p.y = 0; width = 3.5; break;
		case INV_MU: p.x = 1/.75; p.y = 0; width = 6; break;
		default: break;
	}
	compute(&p, width);
	while (prog_running) {
		display_screen(screen);
		if (zooming) 
			rectangleColor(screen, zoom.x, zoom.y, zoom.w, zoom.h, 0xFFFFFFFF);

		SDL_Flip(screen);
		if (SDL_PollEvent (&event)) {
			switch (event.type) {
            	case SDL_VIDEORESIZE:
					reset_video_mode(screen, event.resize.w, event.resize.h, SDL_HWSURFACE | SDL_DOUBLEBUF | SDL_RESIZABLE);
					compute(&p, width);
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
							fset.nmax*=2;	
							dset.colormap = create_colormap(screen, dset.colormap, fset.nmax);
							compute(&p, width);
							break;	

                       	case SDLK_MINUS:
							fset.nmax/=2;	
							if (fset.nmax < 1) fset.nmax = 1;
							dset.colormap = create_colormap(screen, dset.colormap, fset.nmax);
							compute(&p, width);
							break;	

                       	case SDLK_j:
							if (fset.algo == MANDELBROT) {
								int x, y;
								SDL_GetMouseState(&x, &y);
								fset.julia_c.x = x; fset.julia_c.y = y;
								screen_to_real(width, &p, &fset.julia_c);
								p.x = 0; p.y = 0; width = 3.5; 
								fset.algo = JULIA;
								compute(&p, width);
							}	
							break;	

                       	case SDLK_c:
							{
								int x, y;
								point_t tmp;
								SDL_GetMouseState(&x, &y);
								tmp.x = x; tmp.y = y;
								screen_to_real(width, &p, &tmp);
								p.x = tmp.x; p.y = tmp.y;
								compute(&p, width);
							}	
							break;	

						case SDLK_o:
							width*=2;
							compute(&p, width);
							break;

					    case SDLK_RETURN:
							if (dset.fullscreen == 0) { 
								cw = dset.w; ch = dset.h;
								reset_video_mode(screen, dset.screen_w, dset.screen_h, SDL_HWSURFACE | SDL_DOUBLEBUF | SDL_FULLSCREEN);
								dset.fullscreen = 1;
							}
							else {
								reset_video_mode(screen, cw, ch, SDL_HWSURFACE | SDL_DOUBLEBUF | SDL_RESIZABLE);
								dset.fullscreen = 0;
							}
							compute(&p, width);
                    		break;

				     	case SDLK_p:
							fset.para = (fset.para+1)%MAX_PAR;

                       	case SDLK_r:
							fset.algo = MANDELBROT;
							switch(fset.para) {
								case MU: p.x = -0.75; p.y = 0; width = 3.5; break;
								case INV_MU: p.x = 1/.75; p.y = 0; width = 6; break;
								default: break;
							}
							compute(&p, width);
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
						r = width/dset.w;
						p.x = p.x - r*dset.w/2 + (zoom.x+zoom.w)/2*r;
						p.y = p.y + r*dset.h/2 - (zoom.y+zoom.h)/2*r;
					
						width = r*abs(zoom.w-zoom.x);
						compute(&p, width);
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


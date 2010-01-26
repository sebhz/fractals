#include <stdio.h>
#include <stdlib.h>
#include <time.h>
#include <getopt.h>
#include "SDL/SDL.h"
#include "SDL/SDL_image.h"
#include "SDL/SDL_gfxPrimitives.h"

#define VERSION_STRING "1.0"

typedef struct {
	double x;
	double y;
} point_t;

typedef struct {
	int nx; /* X resolution of window */
	int ny; /* Y resolution of window */
	int nmax; /* Number of iterations to perform before auuming divergence */
} settings_t;

static settings_t settings;

const char *WINDOW_TITLE = "Mandelbrot";
static Uint32 *colormap;

void usage(char *prog_name, FILE *stream) {
	fprintf(stream, "%s (version %s):\n", prog_name, VERSION_STRING);
	fprintf(stream, "\t--version      | -v: show program version\n");
	fprintf(stream, "\t--help         | -h: show this help\n");
	fprintf(stream, "\t--n_iterations | -n: number of iterations to perform before assuming divergence\n");
	fprintf(stream, "\t--geometry=<geo>  | -g: sets the window geometry.\n\n");
}

void default_settings(void) 
{
	settings.nmax = 1024;
	settings.nx = 640; 
	settings.ny = 480; 
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
          {0, 0, 0, 0}
        };
      /* getopt_long stores the option index here. */
      int option_index = 0;

      c = getopt_long (argc, argv, "vhn:g:",
                       long_options, &option_index);

      /* Detect the end of the options. */
      if (c == -1)
        break;

      switch (c)
        {
        case 'h':
			usage(argv[0], stdout);
			exit(EXIT_SUCCESS);
			break;

        case 'v':
			fprintf(stdout, "%s\n", VERSION_STRING);
			exit(EXIT_SUCCESS);
			break;

        case 'n':
			settings.nmax = atoi(optarg);
			break;

		case 'g':
			if (set_geometry(optarg)) exit(EXIT_FAILURE);
			break;

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
			a = i*step+xmin;
			x=0; y=0; n=0;
			do {
				x1 = x*x-y*y+a;
				y  = 2*x*y+b;
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

void DrawPixel(SDL_Surface *screen, int x, int y, Uint32 color)
{

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

	for (x=0; x< settings.nx; x++)
		for (y=0; y<settings.ny; y++) {
			n = res[y*settings.nx+x];
			DrawPixel(s, x, y, colormap[n]);
	}
	SDL_Flip(s);
}

void create_colormap(SDL_Surface *screen) {

	int i;
	if ((colormap = (Uint32 *)malloc((settings.nmax+1)*sizeof(Uint32))) == NULL ) {
		fprintf(stderr, "Unable to allocate memory for colormap\n");
		exit(EXIT_FAILURE);
	}
	for (i=0; i<settings.nmax; i++) {
		colormap[i] = SDL_MapRGB(screen->format, rand()%256, rand()%256, rand()%256);
	}
	colormap[settings.nmax] = SDL_MapRGB(screen->format, 0, 0, 0);
}

int main(int argc, char **argv)
{
	int *res, prog_running = 1;
	point_t p;
	SDL_Surface *screen;
    SDL_Event event;
	
    srand (time (NULL));
	default_settings();
	parse_options(argc, argv);
	
	if ((res = (int *)malloc(settings.nx*settings.ny*sizeof(int))) == NULL ) {
		fprintf(stderr, "Unable to allocate memory for screen buffer\n");
		exit(EXIT_FAILURE);
	}

	screen = init_SDL();
	create_colormap(screen);
	p.x = -0.5; p.y = 0;
	mandelbrot(&p, 3.5, res);
	while (prog_running) {
		display_screen(screen, res);
		if (SDL_PollEvent (&event)) {
             switch (event.type) {
                case SDL_VIDEORESIZE:
         			settings.nx = event.resize.w;
					settings.ny = event.resize.h;
		if ((res = (int *)realloc(res, settings.nx*settings.ny*sizeof(int))) == NULL ) {
		fprintf(stderr, "Unable to allocate memory for screen buffer\n");
		exit(EXIT_FAILURE);
	}

		       screen =
                        SDL_SetVideoMode (event.resize.w,
                                          event.resize.h, 0,
                                          SDL_HWSURFACE |
                                          SDL_DOUBLEBUF | SDL_RESIZABLE);
                    if (screen == NULL) {
                        return -1;
                    }
					mandelbrot(&p, 3.5, res);
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

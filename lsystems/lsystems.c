#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <getopt.h>
#include <math.h>
#include "SDL.h"
#include "SDL/SDL_gfxPrimitives.h"

#define ALLOC_SIZE 8
#define VERSION_STRING "1.0"
#define WINDOW_TITLE "Lindenmayer systems"

#define max(a,b) ((a) > (b) ? (a) : (b))

typedef struct
{
    double x;
    double y;
} point_t;

typedef struct
{
    point_t p1;
    point_t p2;
} rect_t;

typedef struct
{
    point_t p;
    double angle;
} stack_element_t;

typedef struct
{
    int size;
    stack_element_t *element;
    int cmax_size;              /* For reallocation policy */
} stack_t;

typedef struct
{
    int size;
    char *rulestring;
} rule_t;

typedef struct
{
    char *title;
    double angle;
    double init_angle;
    char *axiom;
    rule_t *ruleset[256];
} lsystem_t;

typedef struct lsystem_list_s
{
    lsystem_t *l;
    struct lsystem_list_s *n;
    struct lsystem_list_s *p;
} lsystem_list_t;

typedef struct
{
    char *filename;
    int w;
    int h;
    int screen_w;
    int screen_h;
    int fullscreen;
    int border_width;
    lsystem_list_t *lsystems;
} settings_t;

static settings_t settings;

stack_t *
create_stack (void)
{
    stack_t *s;

    if ((s = malloc (sizeof *s)) == NULL) {
        fprintf (stderr, "Unable to allocate memory for stack.\n");
        exit (EXIT_FAILURE);
    }
    s->size = 0;
    if ((s->element = malloc (ALLOC_SIZE * (sizeof *s->element))) == NULL) {
        fprintf (stderr, "Unable to allocate memory for stack.\n");
        exit (EXIT_FAILURE);
    }
    s->cmax_size = ALLOC_SIZE - 1;
    return s;
}

void
free_stack (stack_t * stack)
{
    free (stack->element);
    free (stack);
}

void
push (stack_t * s, stack_element_t * e)
{
    if (s->size == s->cmax_size) {
        s->cmax_size += ALLOC_SIZE;
        if ((s->element = realloc (s->element,
                                   (s->cmax_size +
                                    1) * (sizeof *s->element))) == NULL) {
            fprintf (stderr,
                     "%s:%d: Unable to reallocate %d elements for stack\n",
                     __FILE__, __LINE__, s->cmax_size + 1);
            exit (EXIT_FAILURE);
        }
    }
    s->element[s->size].angle = e->angle;
    s->element[s->size].p.x = e->p.x;
    s->element[s->size].p.y = e->p.y;
    s->size++;
}

void
pop (stack_t * s, stack_element_t * e)
{
    stack_element_t *le;
    if (s->size == 0) {
        fprintf (stderr, "Trying to pop from an empty stack\n");
        return;
    }
    le = &(s->element[--s->size]);
    e->angle = le->angle;
    e->p.x = le->p.x;
    e->p.y = le->p.y;
}

inline void
max_point (point_t * p0, point_t * p1)
{
    if (p0->x > p1->x) {
        p1->x = p0->x;
    }
    if (p0->y > p1->y) {
        p1->y = p0->y;
    }
}

inline void
min_point (point_t * p0, point_t * p1)
{
    if (p0->x < p1->x) {
        p1->x = p0->x;
    }
    if (p0->y < p1->y) {
        p1->y = p0->y;
    }
}

inline void
copy_point (point_t * dest, point_t * src)
{
    dest->x = src->x;
    dest->y = src->y;
}

void
lsystem_act (char c, point_t * maxp, point_t * minp, point_t * p,
             point_t * p0, double *angle, stack_t * stack, int *u, double aa,
             int draw, double alpha, SDL_Surface * screen)
{
    stack_element_t se = { {
                            0.0, 0.0}, 0.0
    };

    switch (c) {
    case 'F':
    case 'A':
    case 'B':
        p->x += alpha * cos (*angle);
        p->y -= alpha * sin (*angle);
        if (draw == 0) {
            max_point (p, maxp);
            min_point (p, minp);
        }
        else {
            lineRGBA (screen, (Sint16) p0->x, (Sint16) p0->y, (Sint16) p->x,
                      (Sint16) p->y, 0x22, 0x8B, 0x22, SDL_ALPHA_OPAQUE);
            copy_point (p0, p);
        }
        break;
    case 'f':
    case 'G':
        p->x += alpha * cos (*angle);
        p->y -= alpha * sin (*angle);
        if (draw == 0) {
            max_point (p, maxp);
            min_point (p, minp);
        }
        else {
            copy_point (p0, p);
        }
        break;
    case '+':
        if (*u) {
            *angle += aa;
        }
        else {
            *angle -= aa;
        }
        break;
    case '-':
        if (*u) {
            *angle -= aa;
        }
        else {
            *angle += aa;
        }
        break;
    case '|':
        *angle += M_PI;
        break;
    case '_':
        *u = 1 - *u;
        break;
    case '[':
        se.angle = *angle;
        copy_point (&(se.p), p);
        push (stack, &se);
        break;
    case ']':
        pop (stack, &se);
        *angle = se.angle;
        copy_point (p, &(se.p));
        if (draw) {
            copy_point (p0, p);
        }
        break;
    default:
        break;
    }
}

void
get_bounding_box (char *ls, lsystem_t * ll, point_t * pm, point_t * o)
{
    int l = strlen (ls), i, u = 1;
    double angle = ll->init_angle / 180.0 * M_PI, aa =
        ll->angle / 180.0 * M_PI;
    point_t p, maxp, minp;
    stack_t *stack;

    stack = create_stack ();
    for (i = 0; i < l; i++) {
        lsystem_act (ls[i], &maxp, &minp, &p, NULL, &angle, stack, &u, aa, 0,
                     1.0, NULL);
    }
    free_stack (stack);
    pm->x = maxp.x - minp.x;
    pm->y = maxp.y - minp.y;
    o->x = -minp.x;
    o->y = -minp.y;
}

void
display_lsystem (SDL_Surface * screen, char *ls, lsystem_t * ll,
                 point_t * pm, point_t * o)
{
    int l = strlen (ls), i, u = 1;
    double angle = ll->init_angle / 180.0 * M_PI, aa =
        ll->angle / 180.0 * M_PI;
    double ar, AR, W, H, w, h, alpha, c;
    point_t p, p0;
    stack_t *stack;

    stack = create_stack ();

    /* First compute a few factors to fit the drawing in the screen */
    W = (double) (screen->w - settings.border_width * 2);
    H = (double) (screen->h - settings.border_width * 2);
    w = pm->x;
    h = pm->y;
    ar = w / h;
    AR = W / H;

    if (ar > AR) {
        alpha = W / w;
        c = h * alpha;
        p0.x = settings.border_width + o->x * alpha;
        p0.y = settings.border_width + (H - c) / 2 + o->y * alpha;
    }
    else {
        alpha = H / h;
        c = w * alpha;
        p0.x = settings.border_width + (W - c) / 2 + o->x * alpha;
        p0.y = settings.border_width + o->y * alpha;
    }
    copy_point (&p, &p0);

    SDL_FillRect (screen, NULL,
                  SDL_MapRGB (screen->format, 0xFE, 0xEB, 0xCD));
    for (i = 0; i < l; i++) {
        lsystem_act (ls[i], NULL, NULL, &p, &p0, &angle, stack, &u, aa, 1,
                     alpha, screen);
    }
    free_stack (stack);
}

lsystem_t *
create_lsystem (void)
{
    lsystem_t *l;
    int i;

    if ((l = malloc (sizeof *l)) == NULL) {
        fprintf (stderr, "Unable to allocate memory for lsystem\n");
        exit (EXIT_FAILURE);
    }
    l->title = NULL;
    l->angle = 0.0;
    l->init_angle = 0.0;
    l->axiom = NULL;
    for (i = 0; i < 256; i++) {
        l->ruleset[i] = NULL;
    }
    return l;
}

void
delete_lsystem (lsystem_t * l)
{
    int i;

    if (l->title != NULL)
        free (l->title);
    if (l->axiom != NULL)
        free (l->axiom);
    for (i = 0; i < 256; i++)
        if (l->ruleset[i] != NULL)
            free (l->ruleset[i]);
    free (l);
}

int
lsystem_is_valid (lsystem_t * l)
{
    int i;

    if (l->axiom == NULL)
        return 0;
    for (i = 0; i < 256; i++)
        if (l->ruleset[i] != NULL)
            return 1;
    return 0;
}

char *
lsystem_compute (char *cur_string, rule_t ** ruleset, int chunk, int *n)
{
    int cl, sl = 0, i, a = chunk, t, c = 0;
    char *s;

    if ((s = malloc (chunk * (sizeof *s))) == NULL) {
        fprintf (stderr,
                 "%s:%d: Unable to allocate memory for new string (%d bytes requested)\n",
                 __FILE__, __LINE__, chunk);
        exit (EXIT_FAILURE);
    }
    cl = *n;
    for (i = 0; i < cl; i++) {
        c = (int) cur_string[i];
        if (ruleset[c] == NULL) {
            t = 1;
        }
        else {
            t = ruleset[c]->size;
        }
        sl += t;
        if (sl > a) {
            while (sl > a) {
                a += chunk;
            }
            if ((s = realloc (s, a * (sizeof *s))) == NULL) {
                fprintf (stderr,
                         "%s:%d: Unable to reallocate memory for new string (%d bytes requested)\n",
                         __FILE__, __LINE__, a);
                exit (EXIT_FAILURE);
            }
        }
        if (ruleset[c] == NULL) {
            s[sl - 1] = (char) c;
        }
        else if (ruleset[c]->size != 0) {
            memcpy (s + sl - t, ruleset[c]->rulestring, t);
        }
    }
    free (cur_string);
    if (sl > a) {
        fprintf (stderr, "%s:%d: memory allocation error. Exiting\n",
                 __FILE__, __LINE__);
        exit (EXIT_FAILURE);
    }
    if ((sl + 1) != a) {        /* Either sl = a -> allocate one more element. Or sl < a -> reallocate the right numbers of elements */
        if ((s = realloc (s, (sl + 1) * (sizeof *s))) == NULL) {
            fprintf (stderr,
                     "%s:%d: Unable to reallocate memory for final string (%d bytes requested)\n",
                     __FILE__, __LINE__, sl + 1);
            exit (EXIT_FAILURE);
        }
    }
    s[sl] = '\0';
    *n = sl;
    return s;
}

char *
lsystem_iterate (lsystem_t * l, int n)
{
    int chunk = 1024, i, l0, l1;
    float r;
    char *cur_string;
    if ((cur_string =
         malloc ((strlen (l->axiom) + 1) * (sizeof *cur_string))) == NULL) {
        fprintf (stderr, "Unable to allocate memory for initial string\n");
        exit (EXIT_FAILURE);
    }
    cur_string = strcpy (cur_string, l->axiom);
    l0 = strlen (cur_string);
    l1 = l0;
    for (i = 0; i < n; i++) {
        cur_string = lsystem_compute (cur_string, l->ruleset, chunk, &l1);

        /* Assume that the growth rate is constant (geometric progression) and
           recompute the chunk size to try and limit the number of reallocs to about 8 */
        r = ((float) l1) / l0;
        chunk = (l1 * r) / 8;
        l0 = l1;
    }
    return cur_string;
}

lsystem_list_t *
add_lsystem (lsystem_list_t * list, lsystem_t * l)
{
    lsystem_list_t *tmp;

    if (l == NULL)
        return list;
    if ((tmp = malloc (sizeof *tmp)) == NULL) {
        fprintf (stderr,
                 "Unable to allocate memory for lsystem list element\n");
        exit (EXIT_FAILURE);
    }
    if (list != NULL) {
        list->p = tmp;
    }
    tmp->n = list;
    tmp->l = l;
    return tmp;
}

void
usage (char *prog_name, FILE * stream)
{
    fprintf (stream, "%s (version %s):\n", prog_name, VERSION_STRING);
    fprintf (stream, "\t--version      | -v: show program version\n");
    fprintf (stream, "\t--help         | -h: show this help\n");
    fprintf (stream,
             "\t--file=<set_file> | -f: file in which the lsystem rules and axiom are stored\n");
    fprintf (stream,
             "\t--geometry=<geo>  | -g: sets the window geometry.\n\n");
}

void
default_settings (void)
{
    settings.filename = NULL;
    settings.screen_w = 640;
    settings.screen_h = 480;
    settings.w = 640;
    settings.h = 480;
    settings.fullscreen = 0;
    settings.lsystems = NULL;
    settings.border_width = 20;
} int

numbers_from_string (long double *num, char *s, char separator, int n)
{
    int i;
    char *ss = s, *p;

    for (i = 0; i < n; i++) {
        num[i] = strtold (ss, &p);
        if ((num[i] == 0) && (p == ss)) {
            return -1;
        }
        if (i == n - 1) {
            break;
        }
        if (*p++ != separator) {
            return -1;
        }
        ss = p;
    }
    return 0;
}

void
parse_options (int argc, char **argv)
{
    int c, l;
    while (1) {
        static struct option long_options[] = {
            /* These options set a flag. */
            {"version", no_argument, 0, 'v'},
            {"help", no_argument, 0, 'h'},
            {"file", required_argument, 0, 'f'},
            {"geometry", required_argument, 0, 'g'},
            {"fullscreen", no_argument, 0, 'F'},
            {0, 0, 0, 0}
        };

        /* getopt_long stores the option index here. */
        int option_index = 0;
        c = getopt_long (argc, argv, "f:Fgh:v", long_options, &option_index);

        /* Detect the end of the options. */
        if (c == -1)
            break;
        switch (c) {
        case 'h':
            usage (argv[0], stdout);
            exit (EXIT_SUCCESS);
            break;
        case 'v':
            fprintf (stdout, "%s\n", VERSION_STRING);
            exit (EXIT_SUCCESS);
            break;
        case 'f':
            l = strlen (optarg);
            if ((settings.filename =
                 malloc ((l + 1) * (sizeof *(settings.filename)))) == NULL) {
                fprintf (stderr, "Unable to allocate memory for filename\n");
                exit (EXIT_FAILURE);
            }
            settings.filename = strcpy (settings.filename, optarg);
            break;
        case 'F':
            settings.fullscreen = 1;
            break;
        case 'g':{
                long double n[2];
                if (numbers_from_string (n, optarg, 'x', 2) == -1) {
                    fprintf (stderr, "Bad geometry string\n");
                    exit (EXIT_FAILURE);
                }
                settings.w = (int) n[0];
                settings.h = (int) n[1];
                break;
            }
        case '?':

            /* getopt_long already printed an error message. */
            break;
        default:
            abort ();
        }
    }
    if (settings.filename == NULL) {
        l = strlen ("rules.txt");
        if ((settings.filename =
             malloc ((l + 1) * (sizeof *(settings.filename)))) == NULL) {
            fprintf (stderr, "Unable to allocate memory for filename\n");
            exit (EXIT_FAILURE);
        }
        settings.filename = strcpy (settings.filename, "rules.txt");
    }

    /* Print any remaining command line arguments (not options). */
    if (optind < argc) {
        while (optind < argc)
            fprintf (stderr,
                     "%s is not recognized as a valid option or argument\n",
                     argv[optind++]);
        usage (argv[0], stderr);
    }
}

void
remove_white_characters (char *s, int l)
{
    int i, j;
    for (i = 0, j = 0; i < l; i++) {
        if ((s[i] == ' ') || (s[i] == '\t'))
            continue;
        s[j++] = s[i];
    }
}

int
parse_line (char *line, int num)
{
    static lsystem_t *current_lsystem = NULL;
    int i, j, l;
    static rule_t **current_ruleset = NULL;
    l = strlen (line);

    /* Remove heading white spaces */
    i = 0;
    while (((line[i] == ' ') || (line[i] == '\t')) && (i < l))
        i++;
    if (i == l)
        return 0;               /* Blank line */
    for (j = i; j < l + 1; j++)
        line[j - i] = line[j];

    /* Remove trailing white spaces */
    i = l - i - 1;
    while (((line[i] == ' ') || (line[i] == '\t')) && (i > 0))
        i--;
    line[i + 1] = '\0';
    l = i + 1;

    if (line[0] == '#')
        return 0;               /* Ignore comments */

    /* First check if this is a new lsystem def */
    if ((strcmp (line, "~lsystem") == 0) || (strcmp (line, "~end") == 0)) {
        if (current_lsystem != NULL) {
            if (lsystem_is_valid (current_lsystem)) {
                settings.lsystems =
                    add_lsystem (settings.lsystems, current_lsystem);
            }
            else {
                delete_lsystem (current_lsystem);
            }
        }
        current_lsystem = create_lsystem ();
        current_ruleset = current_lsystem->ruleset;
        return 0;
    }

    /* Next look for axiom, angle or title definition */
    if ((line[0] == '~') && (line[6] == ':')) {
        if (current_lsystem != NULL) {
            line[6] = '\0';
            if (strcmp (line, "~axiom") == 0) {
                remove_white_characters (line + 7, l - 7);
                if (current_lsystem->axiom != NULL) {
                    fprintf (stderr,
                             "Looks like two axioms are defined for current lsystem. Previous one is %s. Current one is %s (defined at line %d)\n",
                             current_lsystem->axiom, line + 7, num);
                }
                if ((current_lsystem->axiom =
                     malloc ((l - 6) * sizeof (char))) == NULL) {
                    fprintf (stderr, "Unable to allocate memory for axiom\n");
                    exit (EXIT_FAILURE);
                }
                current_lsystem->axiom =
                    strcpy (current_lsystem->axiom, line + 7);
            }

            else if (strcmp (line, "~title") == 0) {
                if (current_lsystem->title != NULL) {
                    fprintf (stderr,
                             "Looks like two titles are defined for current lsystem. Previous one is %s.Current one is %s (defines at line %d)\n",
                             current_lsystem->title, line + 7, num);
                }
                if ((current_lsystem->title =
                     malloc ((l - 6) * sizeof (char))) == NULL) {
                    fprintf (stderr, "Unable to allocate memory for axiom\n");
                    exit (EXIT_FAILURE);
                }
                current_lsystem->title =
                    strcpy (current_lsystem->title, line + 7);
            }

            else if (strcmp (line, "~angle") == 0) {
                if (current_lsystem->angle != 0) {
                    fprintf (stderr,
                             "Found an angle def at line %d. An earlier angle was already defined and will be overriden\n",
                             num);
                }
                current_lsystem->angle = atof (line + 7);
            }

            else if (strcmp (line, "~iangl") == 0) {
                if (current_lsystem->init_angle != 0) {
                    fprintf (stderr,
                             "Found an initial angle def at line %d. An earlier angle was already defined and will be overriden\n",
                             num);
                }
                current_lsystem->init_angle = atof (line + 7);
            }

            else {
                fprintf (stderr, "Error line %d - unknown command %s\n",
                         num, line);
            }
        }

        else {
            fprintf (stderr,
                     "Looks like a command at line %d - but out of an lsystem definition - ignoring\n",
                     num);
        }
        return 0;
    }

    /* In all other cases - try and parse a rule */
    /* First check the charset used */
    for (i = 0; i < l; i++) {
        if ((line[i] < '$') || (line[i] >= '~'))
            return -1;
    }
    if (line[1] != ':')
        return -1;
    i = (int) line[0];
    if (current_ruleset[i] != NULL) {
        fprintf (stderr, "Found duplicate rule for the %c predicate\n",
                 line[0]);
        fprintf (stderr, "Original rule: %s\n",
                 current_ruleset[i]->rulestring);
        fprintf (stderr, "New rule: %s\n", line + 2);
        fprintf (stderr, "New rule will be ignored\n");
    }

    else {
        if ((current_ruleset[i] =
             malloc ((sizeof *current_ruleset[i]))) == NULL) {
            fprintf (stderr, "Unable to allocate memory for rule\n");
            exit (EXIT_FAILURE);
        }
        if (l == 2) {
            current_ruleset[i]->rulestring = NULL;
        }

        else {
            if ((current_ruleset[i]->rulestring =
                 malloc ((l - 1) * sizeof (char))) == NULL) {
                fprintf (stderr,
                         "Unable to allocate memory for rule string\n");
                exit (EXIT_FAILURE);
            }
            current_ruleset[i]->rulestring =
                memcpy (current_ruleset[i]->rulestring, line + 2, l - 2);
        } current_ruleset[i]->size = l - 2;
    }
    return 0;
}

int
parse_file (char *fname)
{
    FILE *f;
    long size, i, l = 1;
    char *f_content, *ptr;

    if ((f = fopen (fname, "r")) == NULL) {
        fprintf (stderr, "Unable to open %s\n", fname);
        exit (EXIT_FAILURE);
    }
    fseek (f, 0, SEEK_END);
    size = ftell (f);
    fseek (f, 0, SEEK_SET);
    if ((f_content = malloc (size * (sizeof *f_content) + 1)) == NULL) {
        fprintf (stderr, "Unable to allocate memory for %s file content.\n",
                 fname);
        exit (EXIT_FAILURE);
    }
    if ((fread (f_content, sizeof (char), size, f)) != size) {
        fprintf (stderr, "Unable to read the data from file %s.\n", fname);
        exit (EXIT_FAILURE);
    }
    fclose (f);
    f_content[size] = '\0';
    ptr = f_content;
    for (i = 0; i < size; i++) {
        if (f_content[i] == '\n') {
            f_content[i] = '\0';
            parse_line (ptr, l++);
            ptr = f_content + i + 1;
        }
    }
    free (f_content);
    return 0;
}

void
print_lsystem (lsystem_t * l)
{
    int i, j;
    fprintf (stderr, "\nlsystem: %s (%f, %s)\n", l->title, l->angle,
             l->axiom);
    for (i = 0; i < 256; i++) {
        if (l->ruleset[i] != NULL) {
            fprintf (stderr, "%c -> ", i);
            for (j = 0; j < l->ruleset[i]->size; j++) {
                fprintf (stderr, "%c", l->ruleset[i]->rulestring[j]);
            }
            fprintf (stderr, "\n");
        }
    }
}

void
print_list (void)
{
    lsystem_list_t *l = settings.lsystems;
    while (l != NULL) {
        print_lsystem (l->l);
        l = l->n;
    }
}

SDL_Surface *
init_SDL (void)
{
    SDL_Surface *s;
    SDL_VideoInfo *vinfo;

    SDL_Init (SDL_INIT_VIDEO);
    vinfo = (SDL_VideoInfo *) SDL_GetVideoInfo ();
    settings.screen_w = vinfo->current_w;
    settings.screen_h = vinfo->current_h;
    if (settings.fullscreen == 0) {
        s = SDL_SetVideoMode (settings.w, settings.h, 0,
                              SDL_HWSURFACE | SDL_DOUBLEBUF | SDL_RESIZABLE);
    }
    else {
        settings.w = settings.screen_w;
        settings.h = settings.screen_h;
        s = SDL_SetVideoMode (settings.w, settings.h, 0,
                              SDL_HWSURFACE | SDL_DOUBLEBUF | SDL_FULLSCREEN);
    }
    SDL_WM_SetCaption (WINDOW_TITLE, 0);
    return s;
}

SDL_Surface *
create_surface (Uint32 width, Uint32 height, int bpp, int flags)
{
    /* Create a 32-bit surface with the bytes of each pixel in R,G,B,A order,
       as expected by OpenGL for textures */
    SDL_Surface *surface;
    Uint32 rmask, gmask, bmask, amask;

    /* SDL interprets each pixel as a 32-bit number, so our masks must depend
       on the endianness (byte order) of the machine */
#if SDL_BYTEORDER == SDL_BIG_ENDIAN
    rmask = 0xff000000;
    gmask = 0x00ff0000;
    bmask = 0x0000ff00;
    amask = 0x000000ff;
#else /*  */
    rmask = 0x000000ff;
    gmask = 0x0000ff00;
    bmask = 0x00ff0000;
    amask = 0xff000000;
#endif /*  */
    surface =
        SDL_CreateRGBSurface (flags, width, height, bpp, rmask, gmask, bmask,
                              amask);
    if (surface == NULL) {
        fprintf (stderr, "CreateRGBSurface failed: %s\n", SDL_GetError ());
        exit (EXIT_FAILURE);
    }
    return surface;
}

int
main (int argc, char **argv)
{
    char *c;
    int prog_running = 1, cw = settings.w, ch = settings.h;
    SDL_Surface *screen, *canvas;
    SDL_Rect r;
    SDL_Event event;
    point_t origin, box_up;
    lsystem_list_t *lsystem_l;
    lsystem_t *l;
    int iter = 3;

#ifdef __MINGW__
    freopen ("CON", "w", stdout);
    freopen ("CON", "w", stderr);

#endif /*  */
    default_settings ();
    parse_options (argc, argv);
    parse_file (settings.filename);
    lsystem_l = settings.lsystems;
    l = lsystem_l->l;
    c = lsystem_iterate (l, iter);
    get_bounding_box (c, l, &box_up, &origin);
    screen = init_SDL ();
    canvas =
        create_surface (screen->w, screen->h, screen->format->BitsPerPixel,
                        screen->
                        flags & (SDL_SWSURFACE | SDL_HWSURFACE |
                                 SDL_SRCCOLORKEY | SDL_SRCALPHA));
    r.x = 0;
    r.y = 0;
    r.w = screen->w;
    r.h = screen->h;
    display_lsystem (canvas, c, l, &box_up, &origin);
    while (prog_running) {
        SDL_BlitSurface (canvas, &r, screen, &r);
        SDL_Flip (screen);
        SDL_WM_SetCaption (l->title, 0);
        if (SDL_PollEvent (&event)) {
            switch (event.type) {
            case SDL_QUIT:
                prog_running = 0;
                break;
            case SDL_VIDEORESIZE:
                screen =
                    SDL_SetVideoMode (event.resize.w, event.resize.h, 0,
                                      SDL_HWSURFACE | SDL_DOUBLEBUF |
                                      SDL_RESIZABLE);
                if (screen == NULL) {
                    fprintf (stderr,
                             "Unable to change video mode. Exiting...\n");
                    exit (EXIT_FAILURE);
                }
                SDL_FreeSurface (canvas);
                canvas =
                    create_surface (screen->w, screen->h,
                                    screen->format->BitsPerPixel,
                                    screen->flags);
                r.w = screen->w;
                r.h = screen->h;
                display_lsystem (canvas, c, l, &box_up, &origin);
                break;
            case SDL_KEYDOWN:
                switch (event.key.keysym.sym) {
                case SDLK_ESCAPE:
                case SDLK_q:
                    prog_running = 0;
                    break;
                case SDLK_RETURN:
                    if (settings.fullscreen == 0) {
                        cw = settings.w;
                        ch = settings.h;
                        screen =
                            SDL_SetVideoMode (settings.screen_w,
                                              settings.screen_h, 0,
                                              SDL_HWSURFACE | SDL_DOUBLEBUF
                                              | SDL_FULLSCREEN);
                        settings.fullscreen = 1;
                    }
                    else {
                        screen =
                            SDL_SetVideoMode (cw, ch, 0,
                                              SDL_HWSURFACE | SDL_DOUBLEBUF
                                              | SDL_RESIZABLE);
                        settings.fullscreen = 0;
                    }
                    if (screen == NULL) {
                        fprintf (stderr,
                                 "Unable to change video mode. Exiting...\n");
                        exit (EXIT_FAILURE);
                    }
                    SDL_FreeSurface (canvas);
                    canvas =
                        create_surface (screen->w, screen->h,
                                        screen->format->BitsPerPixel,
                                        screen->flags);
                    r.w = screen->w;
                    r.h = screen->h;
                    display_lsystem (canvas, c, l, &box_up, &origin);
                    break;
                case SDLK_UP:
                    free (c);
                    c = lsystem_iterate (l, ++iter);
                    get_bounding_box (c, l, &box_up, &origin);
                    display_lsystem (canvas, c, l, &box_up, &origin);
                    break;
                case SDLK_DOWN:
                    if (iter == 0) {
                        break;
                    }
                    free (c);
                    c = lsystem_iterate (l, --iter);
                    get_bounding_box (c, l, &box_up, &origin);
                    display_lsystem (canvas, c, l, &box_up, &origin);
                    break;
                case SDLK_LEFT:
                    if (lsystem_l->p == NULL) {
                        break;
                    }
                    lsystem_l = lsystem_l->p;
                    if (lsystem_l->l == NULL) {
                        fprintf (stderr, "Error, found null lsystem\n");
                        break;
                    }
                    l = lsystem_l->l;
                    print_lsystem (l);
                    iter = 3;
                    free (c);
                    c = lsystem_iterate (l, iter);
                    get_bounding_box (c, l, &box_up, &origin);
                    display_lsystem (canvas, c, l, &box_up, &origin);
                    break;
                case SDLK_RIGHT:
                    if (lsystem_l->n == NULL) {
                        break;
                    }
                    lsystem_l = lsystem_l->n;
                    if (lsystem_l->l == NULL) {
                        fprintf (stderr, "Error, found null lsystem\n");
                        break;
                    }
                    l = lsystem_l->l;
                    print_lsystem (l);
                    iter = 3;
                    free (c);
                    c = lsystem_iterate (l, iter);
                    get_bounding_box (c, l, &box_up, &origin);
                    display_lsystem (canvas, c, l, &box_up, &origin);
                    break;
                default:
                    break;
                }
            default:
                break;
            }
        }
    }
    SDL_Quit ();
    exit (EXIT_SUCCESS);
}

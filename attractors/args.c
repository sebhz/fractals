#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>
#include <getopt.h>
#include <GL/glut.h>

#include "global.h"

#define VERSION_STRING "Polynomial strange attractors - version 1.0"

extern struct fractal_settings fset;
extern struct display_settings dset;

static void
usage (char *prog_name, FILE * stream)
{
    fprintf (stream, "Usage: %s\n", prog_name);
    fprintf (stream, "\t--code or -C [string]\n");
    fprintf (stream, "\t--conviter or -c [int] (%d)\n", DEFAULT_ITER);
    fprintf (stream, "\t--dimension or -d [2|3] (%d)\n", DEFAULT_DIM);
    fprintf (stream, "\t--fullscreen or -f [int] (false)\n");
    fprintf (stream, "\t--geometry  or -g [int]x[int] (%dx%d)\n", DEFAULT_W,
             DEFAULT_H);
    fprintf (stream, "\t--help or -h\n");
    fprintf (stream, "\t--info or -i\n");
    fprintf (stream, "\t--increment or -I [float] (%0+.4f)\n",
             DEFAULT_INCREMENT);
    fprintf (stream, "\t--npoints or -n [int] (%d)\n", DEFAULT_POINTS);
    fprintf (stream, "\t--order or -o [int] (%d)\n", DEFAULT_ORDER);
    fprintf (stream, "\t--speed or -s [int] (%d)\n", DEFAULT_SPEED);
    fprintf (stream, "\t--version or -v\n");
}

static int
numbers_from_string (long *num, char *s, char separator, int n)
{
    int i;
    char *ss = s, *p = NULL;

    for (i = 0; i < n; i++) {
        num[i] = strtol (ss, &p, 0);
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
parseOptions (int argc, char **argv)
{
    int c;

    while (1) {
        static struct option long_options[] = {
            {"code", required_argument, 0, 'C'},
            {"conviter", required_argument, 0, 'c'},
            {"dimension", required_argument, 0, 'd'},
            {"fullscreen", no_argument, 0, 'f'},
            {"geometry", required_argument, 0, 'g'},
            {"help", no_argument, 0, 'h'},
            {"info", no_argument, 0, 'i'},
            {"increment", required_argument, 0, 'I'},
            {"npoints", required_argument, 0, 'n'},
            {"order", required_argument, 0, 'o'},
            {"speed", required_argument, 0, 's'},
            {"version", no_argument, 0, 'v'},
            {0, 0, 0, 0}
        };

        /* getopt_long stores the option index here. */
        int option_index = 0;
        c = getopt_long (argc, argv, "C:c:d:fg:hiI:n:o:s:v", long_options,
                         &option_index);

        /* Detect the end of the options. */
        if (c == -1)
            break;
        switch (c) {
        case 0:
            break;

        case 'C':
            if ((fset.code = strdup (optarg)) == NULL) {        /* POSIX, not ANSI... who cares */
                fprintf (stderr, "Unable to allocate memory to code\n");
            }
            break;

        case 'c':
            fset.convergenceIterations = strtol (optarg, NULL, 0);
            break;

        case 'd':
            fset.dimension = strtol (optarg, NULL, 0);
            if (fset.dimension < 2 || fset.dimension > 3) {
                fprintf (stderr, "Specified dimension out of bound\n");
                usage (argv[0], stderr);
                exit (EXIT_FAILURE);
            }
            break;

        case 'f':
            dset.fullscreen = 1;
            break;

        case 'g':
            {
                long n[2];
                if (numbers_from_string (n, optarg, 'x', 2) == -1) {
                    fprintf (stderr, "Bad geometry string\n");
                    exit (EXIT_FAILURE);
                }
                dset.old_w = n[0];
                dset.old_h = n[1];
                break;
            }

        case 'h':
            usage (argv[0], stdout);
            exit (EXIT_SUCCESS);

        case 'i':
            dset.displayInfo = 1;
            break;

        case 'I':
            dset.increment = strtof (optarg, NULL);
            if (fabs (dset.increment > 1)) {
                fprintf (stderr,
                         "Increment probably way too high. Defaulting back to %f\n",
                         DEFAULT_INCREMENT);
                dset.increment = DEFAULT_INCREMENT;
            }
            break;

        case 'n':
            fset.numPoints = strtol (optarg, NULL, 0);
            break;

        case 'o':
            fset.order = strtol (optarg, NULL, 0);
            break;

        case 's':
            {
                int sp = strtol (optarg, NULL, 0);
                if (sp < 0) {
                    fprintf (stderr,
                             "Invalid speed. Defaulting to %d degrees/s\n",
                             DEFAULT_SPEED);
                }
                else {
                    dset.speed = sp;
                }
                break;
            }
        case 'v':
            fprintf (stdout, "%s\n", VERSION_STRING);
            exit (EXIT_SUCCESS);
            break;

        case '?':
            /* getopt_long already printed an error message. */
            break;

        default:
            abort ();
        }
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

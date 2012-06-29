#include <stdio.h>
#include <math.h>
#include <time.h>

#ifdef __MINGW__
#include <windows.h>
#endif
#include <GL/glut.h>
#include "attractors.h"

static struct attractor *at;
static float angle = 3.0;
static double r = 0;

void
myinit ()
{
    int i;

    glClearColor (0.0f, 0.0f, 0.0f, 1.0f);
    glColor4f (1.0f, 1.0f, 1.0f, 0.02f);
    glViewport (0, 0, 800, 600);

    glMatrixMode (GL_PROJECTION);
    glLoadIdentity ();

    /* The square of the diagonal length */
    for (i = 0; i < MDIM; i++) {
        r += (at->bound[1][i] - at->bound[0][i]) * (at->bound[1][i] -
                                                    at->bound[0][i]);
    }
    /* Add 2% to move the clipping planes a bit further */
    r = 0.51 * sqrt (r);
    glOrtho (-r, r, -r, r, -r, r);

    glMatrixMode (GL_MODELVIEW);
    glLoadIdentity ();

#if (MDIM == 2)
    glEnable (GL_BLEND);
    glBlendFunc (GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA);
#endif

    glEnable (GL_POINT_SMOOTH);
    glPointSize (1.0f);
}

void
display ()
{
    int i;

    glClear (GL_COLOR_BUFFER_BIT);
    glMatrixMode (GL_MODELVIEW);
    glLoadIdentity ();
    glRotatef (angle, 1.0, 1.0, 1.0);

    glBegin (GL_POINTS);
    for (i = 0; i < at->numPoints; i++) {
#if (MDIM == 2)
        glVertex2f (at->array[i][0], at->array[i][1]);
#else
        glVertex3f (at->array[i][0], at->array[i][1], at->array[i][2]);
#endif
    }
    glEnd ();

    glutSwapBuffers ();
    angle += 1.0;
}

/* Keep aspect ratio */
void
reshape (int w, int h)
{
    GLdouble ar;

    glViewport (0, 0, w, h);
    ar = (GLdouble) w / (GLdouble) h;

    glMatrixMode (GL_PROJECTION);
    glLoadIdentity ();

    if (ar < 1.0) {
        glOrtho (-r, r, -r / ar, r / ar, -r, r);
    }
    else {
        glOrtho (-r * ar, r * ar, -r, r, -r, r);
    }
    glMatrixMode (GL_MODELVIEW);
    glLoadIdentity ();
}

void
key (unsigned char mychar, int x, int y)
{
    // exit the program when the Esc key is pressed
    if (mychar == 27) {
        exit (0);
    }

}

int
main (int argc, char **argv)
{

#ifdef __MINGW__
    freopen ("CON", "w", stdout);
    freopen ("CON", "w", stderr);
#endif

    srand (time (NULL));
    at = newAttractor ();

    glutInit (&argc, argv);
    glutInitDisplayMode (GLUT_RGBA | GLUT_DOUBLE | GLUT_ALPHA | GLUT_DEPTH);

    glutInitWindowSize (800, 600);
    glutCreateWindow ("Strange Attractors");

    /* Even if there are no events, redraw our gl scene. */
    glutIdleFunc (display);
    glutDisplayFunc (display);
    glutKeyboardFunc (key);
    glutReshapeFunc (reshape);

    myinit ();
    glutMainLoop ();

    freeAttractor (at);

    return 0;
}

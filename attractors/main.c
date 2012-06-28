/**
 * 
 * Copied from Nathan Selikoff code
 * http://nathanselikoff.com/resources/tutorial-strange-attractors-in-c-and-opengl
 * 
 */
#include <stdio.h>
#include <math.h>
#include <time.h>

#ifdef __MINGW__
#include <windows.h>
#endif
#include <GL/glut.h>
#include "attractors.h"

struct attractor *at;
static float angle = 3.0;

void
myinit ()
{

    // set the background color
    glClearColor (0.0f, 0.0f, 0.0f, 1.0f);

    // set the foreground (pen) color
    glColor4f (1.0f, 1.0f, 1.0f, 0.02f);

    // set up the viewport
    glViewport (0, 0, 800, 600);

    // set up the projection matrix (the camera)
    glMatrixMode (GL_PROJECTION);
    glLoadIdentity ();
#if (MDIM == 2)
    float woff = abs (at->bound[1][0] - at->bound[0][0]) * 0.05;
    float hoff = abs (at->bound[1][1] - at->bound[0][1]) * 0.05;
    gluOrtho2D (at->bound[0][0] - woff, at->bound[1][0] + woff,
                at->bound[0][1] - hoff, at->bound[1][1] + hoff);
#else
    glOrtho (at->bound[0][0], at->bound[1][0],
             at->bound[0][1], at->bound[1][1],
             at->bound[0][2], at->bound[1][2]);
#endif
    // set up the modelview matrix (the objects)
    glMatrixMode (GL_MODELVIEW);
    glLoadIdentity ();

    // enable blending
    //glEnable (GL_BLEND);
    //glBlendFunc (GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA);

    // enable point smoothing
    glEnable (GL_POINT_SMOOTH);
    glPointSize (1.0f);
}

void
mydisplay ()
{
    int i;

    // clear the screen
    glClear (GL_COLOR_BUFFER_BIT);
    glMatrixMode (GL_MODELVIEW);
    glLoadIdentity ();
    glRotatef (angle, 0.0, 1.0, 0.0);
    // draw some points
    glBegin (GL_POINTS);

    for (i = 0; i < at->maxiter; i++) {
        // draw the new point
#if (MDIM == 2)
        glVertex2f (at->array[i][0], at->array[i][1]);
#else
        glVertex3f (at->array[i][0], at->array[i][1], at->array[i][2]);
#endif
    }
    glEnd ();

    // swap the buffers
    glutSwapBuffers ();
    angle += 3.0;
}

void
mykey (unsigned char mychar, int x, int y)
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
    // initialize GLUT
    glutInit (&argc, argv);

    // set up our display mode for color with alpha and double buffering
    glutInitDisplayMode(GLUT_RGBA | GLUT_DOUBLE | GLUT_ALPHA | GLUT_DEPTH);  

    // create a 400px x 400px window
    glutInitWindowSize (800, 600);
    glutCreateWindow ("Strange Attractors in C and OpenGL");

    // register our callback functions
  /* Even if there are no events, redraw our gl scene. */
    glutIdleFunc(mydisplay);
    glutDisplayFunc (mydisplay);
    glutKeyboardFunc (mykey);

    // call our initialization function
    myinit ();

    // start the program
    glutMainLoop ();

    freeAttractor (at);

    return 0;
}

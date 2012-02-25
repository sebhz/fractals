/**
 * This file accompanies the tutorial "Strange Attractors in C++ and OpenGL"
 * available at http://nathanselikoff.com/tutorial-strange-attractors-in-c-and-opengl
 * 
 * This application renders a Pickover strange attractor, "The King's Dream", the
 * parameters of which are found on page 27 of "Chaos in Wonderland" by Clifford Pickover
 * 
 * This file is released under Creative Commons Attribution Noncommercial Share-Alike 3.0 License
 * http://creativecommons.org/licenses/by-nc-sa/3.0/
 * You may modify this code, but you may not republish it without crediting me. Thank you.
 * 
 * Created by Nathan Selikoff on 4/13/11
 * http://nathanselikoff.com
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

void
myinit ()
{

    // set the background color
    glClearColor (0.0f, 0.0f, 0.0f, 1.0f);

    // set the foreground (pen) color
    glColor4f (1.0f, 1.0f, 1.0f, 0.02f);

    // set up the viewport
    glViewport (0, 0, 1280, 1024);

    // set up the projection matrix (the camera)
    glMatrixMode (GL_PROJECTION);
    glLoadIdentity ();
    gluOrtho2D (-2.0f, 2.0f, -2.0f, 2.0f);

    // set up the modelview matrix (the objects)
    glMatrixMode (GL_MODELVIEW);
    glLoadIdentity ();

    // enable blending
    glEnable (GL_BLEND);
    glBlendFunc (GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA);

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

    // draw some points
    glBegin (GL_POINTS);


    // iterate through the equations many times, drawing one point for each iteration
    for (i = 0; i < at->maxiter; i++) {
        // draw the new point
        glVertex2f (at->array[i][0], at->array[i][1]);
    }

    glEnd ();

    // swap the buffers
    glutSwapBuffers ();
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
    glutInitDisplayMode (GLUT_RGBA | GLUT_DOUBLE);

    // create a 400px x 400px window
    glutInitWindowSize (1280, 1024);
    glutCreateWindow ("Strange Attractors in C++ and OpenGL Tutorial");

    // register our callback functions
    glutDisplayFunc (mydisplay);
    glutKeyboardFunc (mykey);

    // call our initialization function
    myinit ();

    // start the program
    glutMainLoop ();

    freeAttractor (at);

    return 0;
}

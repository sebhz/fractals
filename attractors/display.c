/*
 * This program is free software; you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation; either version 3 of the License, or
 * (at your option) any later version
 *
 * This program is distributed in the hope that it will be useful, but
 * WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY
 * or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License
 * for more details
 *
 * You should have received a copy of the GNU General Public License along
 * with this program; if not, write to the Free Software Foundation, Inc.,
 * 59 Temple Place, Suite 330, Boston, MA 02111-1307 USA
 *
 * fps display code heavily inspired from http://mycodelog.com/2010/04/16/fps/
 */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdarg.h>
#include <math.h>
#include <time.h>
#include <sys/time.h>
#include <pthread.h>
#ifdef __MINGW__
#include <windows.h>
#endif
#include <GL/glut.h>

#include "global.h"
#include "util.h"
#include "attractors.h"

#define COLOR_ALPHA 0.2f

const char *WINDOW_TITLE = "Strange Attractors";

struct display_settings dset = {
    .speed = DEFAULT_SPEED,
    .fullscreen = 0,
    .displayInfo = 0,
    .angle = 0.0,
    .fps = 0.0,
    .old_x = DEFAULT_X,
    .old_y = DEFAULT_Y,
    .old_h = DEFAULT_H,
    .old_w = DEFAULT_W,
    .currentTime = 0,
    .increment = DEFAULT_INCREMENT,
    .divergence = 0
};

extern struct fractal_settings fset;
extern struct attractor *at[2];
extern int frontBuffer;

static volatile int threadRunning = 0;
static pthread_t ph;
static pthread_mutex_t mt = PTHREAD_MUTEX_INITIALIZER;

GLvoid *const font_style = GLUT_BITMAP_9_BY_15;

void
printw (float x, float y, int v, char *format, ...)
{
    va_list args, args2;
    int len;
    int i;
    char *text;

    va_start (args, format);
    va_copy (args2, args);
    len = vsnprintf (NULL, 0, format, args) + 1;
    if (len == -1)
        goto cleanup;
    if ((text = malloc (len * (sizeof *text))) == NULL)
        goto cleanup;
    vsnprintf (text, len, format, args2);
    if (len == -1) {
        free (text);
        goto cleanup;
    }

    glRasterPos2f (x, v - y);
    for (i = 0; i < len - 1; i++)
        glutBitmapCharacter (font_style, text[i]);

    free (text);
  cleanup:
    va_end (args2);
    va_end (args);
}

void
drawInfo ()
{
    int i, j, y = 30;
    char *s;
    int viewport[4];

    glColor4f (1.0f, 1.0f, 0.0f, 1.0f);
    glDisable (GL_LIGHTING);

    glGetIntegerv (GL_VIEWPORT, viewport);
    glMatrixMode (GL_PROJECTION);
    glPushMatrix ();
    glLoadIdentity ();
    glOrtho (viewport[0], viewport[2], viewport[1], viewport[3], -1, 1);
    glMatrixMode (GL_MODELVIEW);
    glLoadIdentity ();

    printw (20, y, viewport[3], "fps : %4.2f", dset.fps);
    if (dset.speed != 0) {
        y += 20;
        printw (20, y, viewport[3], "Speed: %d degrees/s", dset.speed);
        y += 20;
        printw (20, y, viewport[3], "Angle: %d",
                (int) floor (dset.angle) % 360);
    }
    y += 20;
    printw (20, y, viewport[3], "Lyapunov exponent: %f",
            at[frontBuffer]->lyapunov->ly);

    if ((s = malloc (3 + (at[frontBuffer]->polynom->length) * 8 + 1)) != NULL) {
        s[0] = '[';
        s[1] = ' ';
        s[3 + (at[frontBuffer]->polynom->length) * 8] = '\0';
        for (i = 0; i < fset.dimension; i++) {
            for (j = 0; j < at[frontBuffer]->polynom->length; j++)
                sprintf (s + 2 + j * 8, "%+0.4f ",
                         at[frontBuffer]->polynom->p[i][j]);
            s[3 + (at[frontBuffer]->polynom->length) * 8 - 1] = ']';
            y += 20;
            printw (20, y, viewport[3], "%s", s);
        }
        free (s);
    }
    y += 20;
    printw (20, y, viewport[3], "Divergence :%f", dset.divergence);

    glMatrixMode (GL_PROJECTION);
    glPopMatrix ();
    glMatrixMode (GL_MODELVIEW);
    glPopMatrix ();

}

void
positionLight ()
{
    GLfloat ambient[] = { 0.1f, 0.1f, 0.1f };
    GLfloat diffuse1[] = { 0.5f, 0.0f, 0.0f, 1.0f };
    GLfloat diffuse2[] = { 0.0f, 0.5f, 0.0f, 1.0f };
    GLfloat diffuse3[] = { 0.0f, 0.0f, 0.5f, 1.0f };
    GLfloat specular1[] = { 1.0f, 0.5f, 0.5f, 1.0f };
    GLfloat specular2[] = { 0.5f, 1.0f, 0.5f, 1.0f };
    GLfloat specular3[] = { 0.5f, 0.5f, 1.0f, 1.0f };
    GLfloat position1[] = { 0.0f, 0.0f, -10.0f, 1.0f };
    GLfloat position2[] = { -10.0f, 0.0f, 10.0f, 1.0f };
    GLfloat position3[] = { 10.0f, 0.0f, 10.0f, 1.0f };

    glLightfv (GL_LIGHT7, GL_AMBIENT, ambient);
    glEnable (GL_LIGHT7);
    glLightfv (GL_LIGHT0, GL_DIFFUSE, diffuse1);
    glLightfv (GL_LIGHT0, GL_POSITION, position1);
    glEnable (GL_LIGHT0);
    glLightfv (GL_LIGHT1, GL_DIFFUSE, diffuse2);
    glLightfv (GL_LIGHT1, GL_POSITION, position2);
    glEnable (GL_LIGHT1);
    glLightfv (GL_LIGHT2, GL_DIFFUSE, diffuse3);
    glLightfv (GL_LIGHT2, GL_POSITION, position3);
    glEnable (GL_LIGHT2);
    glLightfv (GL_LIGHT3, GL_DIFFUSE, specular1);
    glLightfv (GL_LIGHT3, GL_POSITION, position1);
    glEnable (GL_LIGHT3);
    glLightfv (GL_LIGHT4, GL_DIFFUSE, specular2);
    glLightfv (GL_LIGHT4, GL_POSITION, position2);
    glEnable (GL_LIGHT4);
    glLightfv (GL_LIGHT5, GL_DIFFUSE, specular3);
    glLightfv (GL_LIGHT5, GL_POSITION, position3);
    glEnable (GL_LIGHT5);
}

void
initDisplay ()
{
    glClearColor (0.0f, 0.0f, 0.0f, 1.0f);
    glColor4f (1.0f, 1.0f, 1.0f, COLOR_ALPHA);
    glViewport (0, 0, dset.old_w, dset.old_h);

    glMatrixMode (GL_PROJECTION);
    glLoadIdentity ();

    /* Add 2% to move the clipping planes a bit further */
    glOrtho (-at[frontBuffer]->r, at[frontBuffer]->r, -at[frontBuffer]->r,
             at[frontBuffer]->r, -at[frontBuffer]->r, at[frontBuffer]->r);

    glMatrixMode (GL_MODELVIEW);
    glLoadIdentity ();

    if (fset.dimension == 2) {
        glEnable (GL_BLEND);
        glBlendFunc (GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA);
    }
    else {
        glEnable (GL_LIGHTING);
        glDisable (GL_COLOR_MATERIAL);
    }

    glEnable (GL_POINT_SMOOTH);
    glPointSize (1.0f);
}

void
animateAttractor (void)
{
    static int pt = 0;

    int ti = dset.currentTime - pt;
    if (pt != 0)
        dset.angle += dset.speed * ti / 1000.0;
    pt = dset.currentTime;
}

void
drawAttractor (void)
{
    int i;

    glClear (GL_COLOR_BUFFER_BIT);
    glMatrixMode (GL_MODELVIEW);
    glLoadIdentity ();
    if (fset.dimension == 2) {
        glColor4f (1.0f, 1.0f, 1.0f, COLOR_ALPHA);
        glRotatef (dset.angle, 0.0, 0.0, 1.0);
    }
    else {
        glColor4f (1.0f, 1.0f, 1.0f, 1.0f);
        glEnable (GL_LIGHTING);
        positionLight ();
        glRotatef (dset.angle, 1.0, 1.0, 1.0);
    }
    glBegin (GL_POINTS);
    for (i = 0; i < at[frontBuffer]->numPoints; i++) {
        if (fset.dimension == 2)
            glVertex2dv (at[frontBuffer]->array[i]);
        else {
            glVertex3dv (at[frontBuffer]->array[i]);
            /* Normal equal to the vector -> vertex redirects light in the same direction */
            glNormal3dv (at[frontBuffer]->array[i]);
        }
    }
    glEnd ();
}

void
display ()
{
    drawAttractor ();
    if (dset.displayInfo) {
        drawInfo ();
    }
    glutSwapBuffers ();
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
        glOrtho (-at[frontBuffer]->r, at[frontBuffer]->r,
                 -at[frontBuffer]->r / ar, at[frontBuffer]->r / ar,
                 -at[frontBuffer]->r, at[frontBuffer]->r);
    }
    else {
        glOrtho (-at[frontBuffer]->r * ar, at[frontBuffer]->r * ar,
                 -at[frontBuffer]->r, at[frontBuffer]->r, -at[frontBuffer]->r,
                 at[frontBuffer]->r);
    }
    glMatrixMode (GL_MODELVIEW);
    glLoadIdentity ();
}

void
toggleFullscreen (void)
{
    if (dset.fullscreen) {
        glutReshapeWindow (dset.old_w, dset.old_h);
        glutPositionWindow (dset.old_x, dset.old_y);
    }
    else {
        dset.old_x = glutGet ((GLenum) GLUT_WINDOW_X);
        dset.old_y = glutGet ((GLenum) GLUT_WINDOW_Y);
        dset.old_w = glutGet ((GLenum) GLUT_WINDOW_WIDTH);
        dset.old_h = glutGet ((GLenum) GLUT_WINDOW_HEIGHT);
        glutFullScreen ();
    }

    dset.fullscreen = dset.fullscreen == 0 ? 1 : 0;
}

void
key (unsigned char mychar, int x, int y)
{
    switch (mychar) {
    case 'f':
        toggleFullscreen ();
        break;
    case 'i':
        dset.displayInfo = dset.displayInfo ? 0 : 1;
        break;
    case 27:
    case 'q':
        exit (EXIT_SUCCESS);
    default:
        break;
    }
}

void
computeFPS (void)
{
    static int frameCount = 0;
    static int previousTime = 0;

    frameCount++;
    int timeInterval = dset.currentTime - previousTime;
    if (frameCount == 1) {
        previousTime = dset.currentTime;
        return;
    }
    if (timeInterval > 1000) {
        dset.fps = (frameCount - 1) / (timeInterval / 1000.0f);
        previousTime = dset.currentTime;
        frameCount = 0;
    }
}

void
copyPolynom (struct attractor *a, struct polynom *p2)
{
    int i, j;

    for (i = 0; i < fset.dimension; i++) {
        for (j = 0; j < p2->length; j++) {
            a->polynom->p[i][j] = p2->p[i][j];
        }
    }
    a->polynom->sum = p2->sum;
}

void
setClosePolynom (struct attractor *a, struct polynom *p2, int dir)
{
    int place = rand () % (fset.dimension * p2->length);
    int coord = place / p2->length;
    int expon = place % p2->length;

    a->polynom->p[coord][expon] += dir * dset.increment;
    a->polynom->sum += dir * dset.increment;
}

static void *
backgroundCompute (void *v)
{
    struct attractor *a;
    int i, dir, iter;
    double baseSum = AT_INFINITY;

    dir = -1;
    iter = 0;
    /* Under windows, random is working strangely with threads */
#ifdef __MINGW__
    srand (time (NULL));
#endif

    while (1) {
        a = at[1 - frontBuffer];
        do {
            copyPolynom (a, at[frontBuffer]->polynom);
            strncpy (a->code, at[frontBuffer]->code,
                     a->polynom->length * a->dimension + 3);
            setClosePolynom (a, at[frontBuffer]->polynom, dir);
            iter++;
            dset.divergence = fabs (baseSum - a->polynom->sum);
            if (baseSum == AT_INFINITY || iter > MAX_ITER
                || dset.divergence > MAX_DIVERGENCE) {
                baseSum = a->polynom->sum;
                dir = -dir;
                iter = 0;
            }
        }
        while (!isAttractorConverging (a));

        // OK is now using a polynom close to its sibling. And it is converging - time to do the full calculation
        if (a->array != NULL) {
            for (i = 0; i < a->numPoints; i++) {
                if (a->array[i] != NULL)
                    free (a->array[i]);
            }
        }
        iterateMap (a);
        a->r = getRadius (a);
        centerAttractor (a);

        pthread_mutex_lock (&mt);
        threadRunning = 0;
        pthread_mutex_unlock (&mt);
        while (threadRunning == 0);
    }
    /* To please the compiler */
    return NULL;
}

void
idle (void)
{
    dset.currentTime = glutGet (GLUT_ELAPSED_TIME);

    /* Thread is waiting -> calculation done in the backbuffer */
    if (threadRunning == 0) {
        pthread_mutex_lock (&mt);
        frontBuffer = 1 - frontBuffer;  /* Swap the buffers */
        threadRunning = 1;      /* Relaunch thread to compute next attractor in the series */
        pthread_mutex_unlock (&mt);
    }
    animateAttractor ();
    computeFPS ();
    glutPostRedisplay ();
}

void
animate (int argc, char **argv)
{
    glutInit (&argc, argv);
    glutInitDisplayMode (GLUT_RGBA | GLUT_DOUBLE | GLUT_ALPHA | GLUT_DEPTH);

    glutInitWindowSize (dset.old_w, dset.old_h);
    glutCreateWindow (WINDOW_TITLE);
    dset.old_x = glutGet ((GLenum) GLUT_INIT_WINDOW_X) + 6;
    dset.old_y = glutGet ((GLenum) GLUT_INIT_WINDOW_Y) + 36;

    /* Even if there are no events, redraw our gl scene. */
    glutIdleFunc (idle);
    glutDisplayFunc (display);
    glutKeyboardFunc (key);
    glutReshapeFunc (reshape);

    if (dset.fullscreen)
        glutFullScreen ();

    initDisplay ();
    threadRunning = 1;
    pthread_create (&ph, NULL, backgroundCompute, NULL);
    glutMainLoop ();
}

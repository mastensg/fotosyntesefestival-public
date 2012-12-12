#include <err.h>
#include <stdlib.h>

#include <X11/Xlib.h>
#include <GL/glx.h>

#include "draw.h"
#include "net.h"

int main(int argc, char *argv[]) {
    Display *dpy;
    Window root;
    XVisualInfo *vi;
    Colormap cmap;
    XSetWindowAttributes swa;
    Window win;
    GLXContext context;
    XWindowAttributes wa;

    GLint visual_attribs[] = {GLX_RGBA, GLX_DEPTH_SIZE, 24, GLX_DOUBLEBUFFER, None};

    if(NULL == (dpy = XOpenDisplay(NULL)))
        err(EXIT_FAILURE, "XOpenDisplay");

    root = DefaultRootWindow(dpy);

    if(NULL == (vi = glXChooseVisual(dpy, 0, visual_attribs)))
        errx(EXIT_FAILURE, "glXChooseVisual");

    cmap = XCreateColormap(dpy, root, vi->visual, AllocNone);

    swa.colormap = cmap;
    swa.event_mask = ExposureMask | KeyPressMask;

    win = XCreateWindow(dpy, root, 0, 0, 1280, 768, 0, vi->depth, InputOutput, vi->visual, CWColormap | CWEventMask, &swa);

    XMapWindow(dpy, win);

    XStoreName(dpy, win, "Fotosyntesefestival");

    context = glXCreateContext(dpy, vi, NULL, GL_TRUE);

    glXMakeCurrent(dpy, win, context);

    XGetWindowAttributes(dpy, win, &wa);

    draw_init(wa.width, wa.height);
    net_init();

    for(;;)
    {
        draw();
        glXSwapBuffers(dpy, win);

        char *s = NULL;

        do
        {
            s = net_recv();
            if(s)
                draw_command(s);
        }
        while(s);
    }

    return EXIT_SUCCESS;
}

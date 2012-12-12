#include <err.h>
#include <inttypes.h>
#include <stdio.h>
#include <signal.h>
#include <stdlib.h>

#include <bcm_host.h>
#include <EGL/egl.h>
#include <GLES2/gl2.h>

#include "draw.h"
#include "net.h"

EGLDisplay display;
EGLSurface surface;
EGLContext context;

static const char *
egl_strerror(EGLint error)
{
    switch(error)
    {
    case EGL_SUCCESS:
        return "EGL_SUCCESS, The last function succeeded without error.";
        break;
    case EGL_NOT_INITIALIZED:
        return "EGL_NOT_INITIALIZED, EGL is not initialized, or could not be initialized, for the specified EGL display connection.";
        break;
    case EGL_BAD_ACCESS:
        return "EGL_BAD_ACCESS, EGL cannot access a requested resource (for example a context is bound in another thread).";
        break;
    case EGL_BAD_ALLOC:
        return "EGL_BAD_ALLOC, EGL failed to allocate resources for the requested operation.";
        break;
    case EGL_BAD_ATTRIBUTE:
        return "EGL_BAD_ATTRIBUTE, An unrecognized attribute or attribute value was passed in the attribute list.";
        break;
    case EGL_BAD_CONTEXT:
        return "EGL_BAD_CONTEXT, An EGLContext argument does not name a valid EGL rendering context.";
        break;
    case EGL_BAD_CONFIG:
        return "EGL_BAD_CONFIG, An EGLConfig argument does not name a valid EGL frame buffer configuration.";
        break;
    case EGL_BAD_CURRENT_SURFACE:
        return "EGL_BAD_CURRENT_SURFACE, The current surface of the calling thread is a window, pixel buffer or pixmap that is no longer valid.";
        break;
    case EGL_BAD_DISPLAY:
        return "EGL_BAD_DISPLAY, An EGLDisplay argument does not name a valid EGL display connection.";
        break;
    case EGL_BAD_SURFACE:
        return "EGL_BAD_SURFACE, An EGLSurface argument does not name a valid surface (window, pixel buffer or pixmap) configured for GL rendering.";
        break;
    case EGL_BAD_MATCH:
        return "EGL_BAD_MATCH, Arguments are inconsistent (for example, a valid context requires buffers not supplied by a valid surface).";
        break;
    case EGL_BAD_PARAMETER:
        return "EGL_BAD_PARAMETER, One or more argument values are invalid.";
        break;
    case EGL_BAD_NATIVE_PIXMAP:
        return "EGL_BAD_NATIVE_PIXMAP, A NativePixmapType argument does not refer to a valid native pixmap.";
        break;
    case EGL_BAD_NATIVE_WINDOW:
        return "EGL_BAD_NATIVE_WINDOW, A NativeWindowType argument does not refer to a valid native window.";
        break;
    case EGL_CONTEXT_LOST:
        return "EGL_CONTEXT_LOST, A power management event has occurred. The application must destroy all contexts and reinitialise OpenGL ES state and objects to continue rendering.";
        break;
    default:
        return "Unknown EGL error.";
    }
}

static NativeWindowType
vc_init(uint32_t *width, uint32_t *height)
{
    VC_RECT_T dst_rect, src_rect;
    DISPMANX_DISPLAY_HANDLE_T dispman_display;
    DISPMANX_UPDATE_HANDLE_T dispman_update;
    DISPMANX_ELEMENT_HANDLE_T dispman_element;

    static EGL_DISPMANX_WINDOW_T native_window;

    bcm_host_init();

    if(!(*width || *height))
        if(-1 == graphics_get_display_size(0, width, height))
            err(EXIT_FAILURE, "graphics_get_display_size");

    dst_rect.x = 0;
    dst_rect.y = 0;
    dst_rect.width = *width;
    dst_rect.height = *height;

    src_rect.x = 0;
    src_rect.y = 0;
    src_rect.width = *width << 16;
    src_rect.height = *height << 16;

    dispman_display = vc_dispmanx_display_open(0);
    dispman_update = vc_dispmanx_update_start(0);
    dispman_element = vc_dispmanx_element_add(dispman_update, dispman_display, 0, &dst_rect, 0, &src_rect, DISPMANX_PROTECTION_NONE, 0, 0, 0);

    native_window.element = dispman_element;
    native_window.width = *width;
    native_window.height = *height;

    vc_dispmanx_update_submit_sync(dispman_update);

    return &native_window;
}

static void
egl_init(NativeWindowType native_window)
{
    static const EGLint config_attrib_list[] = {
        EGL_RED_SIZE, 8,
        EGL_GREEN_SIZE, 8,
        EGL_BLUE_SIZE, 8,
        EGL_ALPHA_SIZE, 8,
        EGL_NONE
    };
    static const EGLint context_attrib_list[] = {
        EGL_CONTEXT_CLIENT_VERSION, 2,
        EGL_NONE
    };
    EGLConfig config;
    EGLint num_config;

    if(EGL_DEFAULT_DISPLAY == (display = eglGetDisplay(EGL_DEFAULT_DISPLAY)))
        errx(EXIT_FAILURE, "eglGetDisplay: EGL_NO_DISPLAY, can't obtain display");

    if(EGL_FALSE == eglInitialize(display, NULL, NULL))
        errx(EXIT_FAILURE, "eglInitialize: %s", egl_strerror(eglGetError()));

    if(EGL_FALSE == eglChooseConfig(display, config_attrib_list, &config, 1, &num_config))
        errx(EXIT_FAILURE, "eglChooseConfig: %s", egl_strerror(eglGetError()));

    if(EGL_FALSE == eglBindAPI(EGL_OPENGL_ES_API))
        errx(EXIT_FAILURE, "eglBindAPI: %s", egl_strerror(eglGetError()));

    if(EGL_NO_CONTEXT == (context = eglCreateContext(display, config, EGL_NO_CONTEXT, context_attrib_list)))
        errx(EXIT_FAILURE, "eglCreateContext: %s", egl_strerror(eglGetError()));

    if(EGL_NO_SURFACE == (surface = eglCreateWindowSurface(display, config, native_window, NULL)))
        errx(EXIT_FAILURE, "eglCreateWindowSurface: %s", egl_strerror(eglGetError()));

    if(EGL_FALSE == eglMakeCurrent(display, surface, surface, context))
        errx(EXIT_FAILURE, "eglMakeCurrent: %s", egl_strerror(eglGetError()));
}

static void
cleanup()
{
   eglMakeCurrent(display, EGL_NO_SURFACE, EGL_NO_SURFACE, EGL_NO_CONTEXT);
   eglDestroySurface(display, surface);
   eglDestroyContext(display, context);
   eglTerminate(display);
}

static void
sigint_handler(int signal)
{
    exit(EXIT_SUCCESS);
}

int main(int argc, char *argv[]) {
    NativeWindowType window;
    unsigned w = 0, h = 0;

    atexit(cleanup);
    signal(SIGINT, sigint_handler);

    window = vc_init(&w, &h);
    egl_init(window);

    draw_init(w, h);
    net_init();

    for(;;)
    {
        draw();
        eglSwapBuffers(display, surface);

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

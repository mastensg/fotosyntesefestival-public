bin_PROGRAMS = videomode

AM_CFLAGS = -Wall -Wextra -Werror -pedantic -std=c99 -O0 -g

videomode_SOURCES = draw.c draw.h net.c net.h tga.c tga.h

if VC
videomode_SOURCES += vc_main.c
videomode_LDADD = -L/opt/vc/lib -lGLESv2 -lEGL -lbcm_host -lm
videomode_CFLAGS = -I/opt/vc/include -I/opt/vc/include/interface/vcos/pthreads
endif

if GLX
videomode_SOURCES += x11_main.c
videomode_LDADD = -lGL -lGLEW -lX11 -lm
endif

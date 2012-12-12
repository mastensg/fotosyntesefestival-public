AC_INIT(videomode, 0.1.0)
AM_INIT_AUTOMAKE([-Wall -Werror foreign])

AC_PROG_CC
AC_PROG_INSTALL
AC_PROG_MAKE_SET

GLX=0
VC=0

#AC_CHECK_HEADER([stdio.h], [VC=1])
AC_CHECK_HEADER([stdio.h], AC_DEFINE(HAVE_STDIO_H, 1, [standard input and output]))
#AC_CHECK_HEADER([math.h], [AC_DEFINE([HAVE_MATH_H])])

old_CPPFLAGS="$CPPFLAGS"
CPPFLAGS="-I/opt/vc/include -I/opt/vc/include/interface/vcos/pthreads"
AC_CHECK_HEADER([bcm_host.h], VC=1, GLX=1)
CPPFLAGS="$old_CPPFLAGS"

test x$GLX = x1 && AC_DEFINE(USE_GLEW, 1, [Use GLEW])

AM_CONDITIONAL(GLX, [test x$GLX = x1])
AM_CONDITIONAL(VC, [test x$VC = x1])

AC_CONFIG_HEADER(config.h)
AC_OUTPUT(Makefile)

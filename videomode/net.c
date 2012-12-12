#include <arpa/inet.h>
#include <netinet/in.h>
#include <err.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/ioctl.h>
#include <sys/socket.h>
#include <sys/types.h>
#include <unistd.h>

#include "net.h"

#define BUFLEN 512

int fd;

char *
net_recv()
{
    static char buf[BUFLEN];
    struct sockaddr_in si_other;
    socklen_t slen = sizeof(si_other);
    ssize_t numbytes;

    if(-1 == ioctl(fd, FIONREAD, &numbytes))
        err(EXIT_FAILURE, "ioctl");

    if(!numbytes)
        return NULL;

    if(-1 == (numbytes = recvfrom(fd, buf, BUFLEN, 0, (struct sockaddr *)&si_other, &slen)))
        err(EXIT_FAILURE, "recvfrom");

    //buf[numbytes >= BUFLEN ? BUFLEN - 1 : numbytes] = '\0';
    buf[numbytes ? numbytes - 1 : 0] = '\0';

    //printf("%s %d: (%3d) %s\n", inet_ntoa(si_other.sin_addr), ntohs(si_other.sin_port), numbytes, buf);

    return buf;
}

void
net_init()
{
    struct sockaddr_in si_me;

    if(-1 == (fd = socket(AF_INET, SOCK_DGRAM, IPPROTO_UDP)))
        err(EXIT_FAILURE, "socket");

    memset(&si_me, 0, sizeof(si_me));

    si_me.sin_family = AF_INET;
    si_me.sin_port = htons(PORT);
    si_me.sin_addr.s_addr = htonl(INADDR_ANY);

    if(-1 == bind(fd, (struct sockaddr *)&si_me, sizeof(si_me)))
        err(EXIT_FAILURE, "bind");
}

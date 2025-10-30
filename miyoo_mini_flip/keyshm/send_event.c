#define _GNU_SOURCE
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <string.h>
#include <fcntl.h>
#include <unistd.h>
#include <linux/input.h>
#include <sys/time.h>
#include <errno.h>

/* usage */
static void usage(const char *prog) {
    fprintf(stderr,
            "Usage: %s [device] code:value [code:value ...]\n"
            "  device optional, defaults to /dev/input/event0\n"
            "  code:value pairs send events. type defaults to EV_KEY (1)\n"
            "  Examples:\n"
            "    %s 57:1 97:1       # press SELECT + X\n"
            "    %s 57:0 97:0       # release SELECT + X\n"
            "    %s /dev/input/event2 57:1 97:1\n",
            prog, prog, prog, prog);
}

int main(int argc, char *argv[]) {
    if (argc < 2) {
        usage(argv[0]);
        return 1;
    }

    const char *dev;
    int arg_start;

    /* detect if first arg is device */
    if (strncmp(argv[1], "/dev/input/", 11) == 0) {
        dev = argv[1];
        arg_start = 2;
    } else {
        dev = "/dev/input/event0";
        arg_start = 1;
    }

    if (argc <= arg_start) {
        usage(argv[0]);
        return 1;
    }

    int fd = open(dev, O_WRONLY | O_NONBLOCK);
    if (fd < 0) {
        perror(dev);
        return 1;
    }

    struct input_event ev;
    memset(&ev, 0, sizeof(ev));

    for (int i = arg_start; i < argc; i++) {
        char *arg = argv[i];
        char *colon = strchr(arg, ':');
        if (!colon) {
            fprintf(stderr, "Invalid code:value pair: %s\n", arg);
            close(fd);
            return 1;
        }
        *colon = '\0';
        char *endptr;
        errno = 0;
        long code = strtol(arg, &endptr, 0);
        if (errno || *endptr != '\0') {
            fprintf(stderr, "Invalid code: %s\n", arg);
            close(fd);
            return 1;
        }
        long value = strtol(colon + 1, &endptr, 0);
        if (errno || *endptr != '\0') {
            fprintf(stderr, "Invalid value: %s\n", colon + 1);
            close(fd);
            return 1;
        }

        /* set timestamp */
        if (gettimeofday(&ev.time, NULL) != 0) {
            perror("gettimeofday");
            close(fd);
            return 1;
        }

        ev.type = EV_KEY;       // default type
        ev.code = (unsigned short)code;
        ev.value = (int)value;

        ssize_t written = write(fd, &ev, sizeof(ev));
        if (written != (ssize_t)sizeof(ev)) {
            if (written < 0) perror("write event");
            else fprintf(stderr, "Short write: %zd of %zu\n", written, sizeof(ev));
            close(fd);
            return 1;
        }
    }

    /* flush all events with a single SYN_REPORT */
    if (gettimeofday(&ev.time, NULL) != 0) {
        perror("gettimeofday");
        close(fd);
        return 1;
    }
    ev.type = EV_SYN;
    ev.code = SYN_REPORT;
    ev.value = 0;

    if (write(fd, &ev, sizeof(ev)) != (ssize_t)sizeof(ev)) {
        perror("write syn");
        close(fd);
        return 1;
    }

    close(fd);
    return 0;
}

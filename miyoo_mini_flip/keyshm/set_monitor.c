#define _GNU_SOURCE
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <dlfcn.h>
#include <string.h>
#include <fcntl.h>
#include <unistd.h>
#include <linux/input.h>
#include <sys/time.h>

// opaque SHM struct
typedef struct { uint8_t data[512]; } KeyShmInfo;

// function pointer types
typedef void (*InitKeyShm_t)(KeyShmInfo *);
typedef void (*SetKeyShm_t)(KeyShmInfo *, int, int);

int send_fake_key() {
    int fd = open("/dev/input/event0", O_WRONLY);
    if(fd < 0) {
        perror("open /dev/input/event0");
        return 1;
    }

    struct input_event ev;
    memset(&ev, 0, sizeof(ev));
    gettimeofday(&ev.time, NULL);

    // Key press
    ev.type = EV_KEY;
    ev.code = KEY_ENTER;  // harmless key
    ev.value = 1;
    write(fd, &ev, sizeof(ev));

    // Key release
    ev.value = 0;
    write(fd, &ev, sizeof(ev));

    // SYN_REPORT
    ev.type = EV_SYN;
    ev.code = SYN_REPORT;
    ev.value = 0;
    write(fd, &ev, sizeof(ev));

    close(fd);
    return 0;
}

int main(int argc, char *argv[]) {
    if(argc < 3) {
        fprintf(stderr, "Usage: %s <key> <value>\n", argv[0]);
        return 1;
    }

    int key = atoi(argv[1]);
    int value = atoi(argv[2]);

    void *lib = dlopen("/customer/lib/libshmvar.so", RTLD_LAZY);
    if(!lib) {
        fprintf(stderr, "Failed to load libshmvar.so: %s\n", dlerror());
        return 1;
    }

    InitKeyShm_t InitKeyShm = (InitKeyShm_t)dlsym(lib, "InitKeyShm");
    SetKeyShm_t SetKeyShm = (SetKeyShm_t)dlsym(lib, "SetKeyShm");
    if(!InitKeyShm || !SetKeyShm) {
        fprintf(stderr, "Failed to find symbols\n");
        return 1;
    }

    KeyShmInfo shminfo;
    InitKeyShm(&shminfo);
    SetKeyShm(&shminfo, key, value);

    dlclose(lib);

    // Send fake keypress to force UI refresh
    send_fake_key();

    return 0;
}

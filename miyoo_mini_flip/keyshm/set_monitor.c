#define _GNU_SOURCE
#include <stdio.h>
#include <stdlib.h>
#include <dlfcn.h>
#include <stdint.h>

typedef struct { uint8_t data[512]; } KeyShmInfo; // opaque buffer

typedef void (*InitKeyShm_t)(KeyShmInfo *);
typedef void (*SetKeyShm_t)(KeyShmInfo *, int, int);

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
    return 0;
}

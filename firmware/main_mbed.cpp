extern "C" {
    #include "targetlib.h"
}

#if PLAT_KINETIS

int main(void) {
    daq_setup();
    for (;;) {
        daq_loop();
    }
}

#endif


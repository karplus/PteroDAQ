extern "C" {
    #include "targetlib.h"
}

int main(void) {
    daq_setup();
    for (;;) {
        daq_loop();
    }
}


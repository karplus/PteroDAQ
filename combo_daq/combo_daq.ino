extern "C" {
    #include "targetlib.h"
}

void setup(void) {
    daq_setup();
}

void loop(void) {
    daq_loop();
}

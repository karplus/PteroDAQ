#include "targetlib.h"
#include "adc.h"

#ifdef PLAT_ATMEGA

uint8_t* get_model(void) {
    static uint8_t resp[MODEL_INFO_LEN];
    uint16_t bandgap;

    #if defined(__AVR_ATmega328P__) || defined(__AVR_ATmega168__)
        #if NUM_ANALOG_INPUTS == 8
            resp[0] = 1;
        #else
            resp[0] = 0;
        #endif
    #elif defined(__AVR_ATmega32U4__)
        resp[0] = 3;
    #elif defined(__AVR_ATmega2560__) || defined(__AVR_ATmega1280__)
        resp[0] = 2;
    #endif
    resp[1] = 0;
    resp[2] = (F_CPU/1000) & 0xFF;
    resp[3] = ((F_CPU/1000) >> 8) & 0xFF;
    adc_aref(1); // power supply as reference
    #if defined(__AVR_ATmega328P__) || defined(__AVR_ATmega168__)
        adc_read(14); // settle
        bandgap = adc_read(14); // read bandgap
    #else
        adc_read(30); // settle
        bandgap = adc_read(30); // read bandgap
    #endif
    adc_aref(0); // external aref to avoid shorts
    resp[4] = bandgap & 0xFF;
    resp[5] = (bandgap >> 8) & 0xFF;
    return resp;
}

#elif defined(PLAT_KINETIS)

uint8_t* get_model(void) {
    static uint8_t resp[MODEL_INFO_LEN];
    uint16_t bandgap;

    resp[0] = 5;
    resp[1] = 0;
    adc_aref(1); // power supply as reference
    bandgap = adc_read(0x1B); // read bandgap
    resp[2] = bandgap & 0xFF;
    resp[3] = (bandgap >> 8) & 0xFF;
    return resp;
}

#endif

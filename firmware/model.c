#include "targetlib.h"
#include "adc.h"

#if PLAT_ATMEGA
#include <util/delay.h>

// returns a pointer to a static response byte array
// that has been loaded with
//  16-bit words (LSB-first)
//  [0,1]   board model
//     1    Uno equivalent
//     2    Fio equivalent
//     3    Mega equivalent
//     4    Leonardo equivalent
//     5    KL25Z
//  [2,3]   Bandgap raw ADC reading
//  [4,5]   CPU frequency in kHz (Arduino only)
uint8_t* get_model(void) {
    static uint8_t resp[MODEL_INFO_LEN];
    uint16_t bandgap;

    #if defined(__AVR_ATmega328P__) || defined(__AVR_ATmega168__)
        #if NUM_ANALOG_INPUTS == 8
            resp[0] = 2;
        #else
            resp[0] = 1;
        #endif
    #elif defined(__AVR_ATmega32U4__)
        resp[0] = 4;
    #elif defined(__AVR_ATmega2560__) || defined(__AVR_ATmega1280__)
        resp[0] = 3;
    #endif
    resp[1] = 0;
    adc_aref(DEFAULT_AREF); // power supply as reference
    #if defined(__AVR_ATmega328P__) || defined(__AVR_ATmega168__)
        #define BANDGAP_PORT (14)
    #else
    #define BANDGAP_PORT (30)
    #endif
    // read and ignore bandgap to start it settling
    bandgap = adc_read(BANDGAP_PORT); 
    bandgap = adc_read(BANDGAP_PORT); 
    bandgap = adc_read(BANDGAP_PORT); 
    // average 64 readings
    uint8_t i;
    bandgap=0;
    for (i=0; i<64; i++)
    {    bandgap += (adc_read(BANDGAP_PORT) >> 6);
    }
    
    adc_aref(0); // external aref to avoid shorts
    resp[2] = bandgap & 0xFF;
    resp[3] = (bandgap >> 8) & 0xFF;
    resp[4] = (F_CPU/1000) & 0xFF;
    resp[5] = ((F_CPU/1000) >> 8) & 0xFF;
    return resp;
}

#elif PLAT_KINETIS
#define BANDGAP_PORT (0x1B)
uint8_t* get_model(void) {
    static uint8_t resp[MODEL_INFO_LEN];
    uint16_t bandgap;
    uint32_t sum_bandgap;

    resp[0] = MODEL_BOARDNUM;
    resp[1] = 0;
    adc_aref(DEFAULT_AREF); // power supply as reference
    adc_avg(0x7);  // do 32x hardware averaging
    bandgap = adc_read(BANDGAP_PORT); // read bandgap and discard
    // average 64 readings
    uint8_t i;
    sum_bandgap=32;  // set to 1/2 number to average, to get rounding
    for (i=0; i<64; i++)
    {    sum_bandgap += adc_read(BANDGAP_PORT);
    }
    bandgap = sum_bandgap >> 6;
    resp[2] = bandgap & 0xFF;
    resp[3] = (bandgap >> 8) & 0xFF;
    return resp;
}

#endif

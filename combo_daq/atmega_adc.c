#include "adc.h"

#if PLAT_ATMEGA

void adc_init(void) {
    ADCSRB = 0;
    
    // disable digital input buffers
    #if defined(__AVR_ATmega328P__) || defined(__AVR_ATmega168__)
        DIDR0 = 0x3F;
    #elif defined(__AVR_ATmega32U4__)
        DIDR0 = 0xF3;
        DIDR1 = 0x3F;
    #elif defined(__AVR_ATmega2560__) || defined(__AVR_ATmega1280__)
        DIDR0 = 0xFF;
        DIDR1 = 0xFF;
    #endif
    
    // adjust clock prescale to keep below 200 kHz
    #if F_CPU > 12800
        ADCSRA = 7; // prescale by 128
    #elif F_CPU > 6400
        ADCSRA = 6; // prescale by 64
    #elif F_CPU > 3200
        ADCSRA = 5; // prescale by 32
    #elif F_CPU > 1600
        ADCSRA = 4; // prescale by 16
    #elif F_CPU > 800
        ADCSRA = 3; // prescale by 8
    #elif F_CPU > 400
        ADCSRA = 2; // prescale by 4
    #elif F_CPU >= 100
        ADCSRA = 1; // prescale by 2
    #else
        #warning "F_CPU too low for ADC operation"
    #endif
    
    // set external aref to avoid shorts
    adc_aref(0);
}

void adc_aref(uint8_t choice) {
    // set aref choice, left-align, and bandgap channel
    #if defined(__AVR_ATmega328P__) || defined(__AVR_ATmega168__)
        ADMUX = (choice << REFS0) | _BV(ADLAR) | 0xE;
    #else
        ADMUX = (choice << REFS0) | _BV(ADLAR) | 0x1E;
        ADCSRB = 0;
    #endif
    
    // conversion to let aref settle
    ADCSRA |= _BV(ADEN)|_BV(ADSC); // enable, start conversion
    loop_until_bit_is_clear(ADCSRA, ADSC);
}

void adc_avg(uint8_t choice) {
    ;
}

uint16_t adc_read(uint8_t mux) {
    uint8_t low;
    
    #if defined(__AVR_ATmega328P__) || defined(__AVR_ATmega168__)
        ADMUX &= ~0xF;
        ADMUX |= mux;
    #else
        ADMUX &= ~0x1F;
        ADMUX |= (mux & 0x1F);
        ADCSRB = ((mux & 0x20) >> 5) << MUX5;
    #endif
    
    ADCSRA |= _BV(ADEN)|_BV(ADSC); // enable, start conversion
    loop_until_bit_is_clear(ADCSRA, ADSC);
    
    low = ADCL;
    return (ADCH << 8) | low;
}

#endif


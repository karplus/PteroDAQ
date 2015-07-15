#include "pio.h"

#if PLAT_ATMEGA

void pio_init(void) {
    ; // no init needed
}

#if defined(__AVR_ATmega328P__) || defined(__AVR_ATmega168__)
    volatile uint8_t* pinregs[] = {NULL, &PINB, &PINC, &PIND};
#elif defined(__AVR_ATmega32U4__)
    volatile uint8_t* pinregs[] = {NULL, &PINB, &PINC, &PIND, &PINE, &PINF};
#elif defined(__AVR_ATmega2560__) || defined(__AVR_ATmega1280__)
    volatile uint8_t* pinregs[] = {&PINA, &PINB, &PINC, &PIND, &PINE, &PINF, &PING, &PINH, NULL, &PINJ, &PINK, &PINL};
#endif

uint8_t pio_read(uint8_t pin) {
    return (*(pinregs[pin >> 4]) & (1 << (pin & 0xF))) ? 1 : 0;
}

void pio_trigger(uint8_t pin, uint8_t sense) {
    EIFR = 0xFF; // clear flags
    switch (pin) {
        #if defined(__AVR_ATmega328P__) || defined(__AVR_ATmega168__)
        case 0: // PD2, aka INT0
            EICRA = sense;
            EIMSK = _BV(INT0);
            break;
        case 1: // PD3, aka INT1
            EICRA = sense << 2;
            EIMSK = _BV(INT1);
            break;
        #else
        case 0: // PD0, aka INT0
            EICRA = sense;
            EIMSK = _BV(INT0);
            break;
        case 1: // PD1, aka INT1
            EICRA = sense << 2;
            EIMSK = _BV(INT1);
            break;
        case 2: // PD2, aka INT2
            EICRA = sense << 4;
            EIMSK = _BV(INT2);
            break;
        case 3: // PD3, aka INT3
            EICRA = sense << 6;
            EIMSK = _BV(INT3);
            break;
        case 6: // PE6, aka INT6
            EICRB = sense << 4;
            EIMSK = _BV(INT6);
            break;
        #if defined(__AVR_ATmega2560__) || defined(__AVR_ATmega1280__)
        case 4: // PE4, aka INT4
            EICRB = sense;
            EIMSK = _BV(INT4);
            break;
        case 5: // PE5, aka INT5
            EICRB = sense << 2;
            EIMSK = _BV(INT5);
            break;
        case 7: // PE7, aka INT7
            EICRB = sense << 6;
            EIMSK = _BV(INT7);
            break;
        #endif
        #endif
    }
}

void pio_cancel(uint8_t pin) {
    EIMSK = 0; // disable
}

ISR(INT0_vect) {
    trigger_handler();
}

ISR(INT1_vect, ISR_ALIASOF(INT0_vect));

#if defined(__AVR_ATmega32U4__) || defined(__AVR_ATmega2560__) || defined(__AVR_ATmega1280__)

ISR(INT2_vect, ISR_ALIASOF(INT0_vect));
ISR(INT3_vect, ISR_ALIASOF(INT0_vect));
ISR(INT6_vect, ISR_ALIASOF(INT0_vect));

#if defined(__AVR_ATmega2560__) || defined(__AVR_ATmega1280__)

ISR(INT4_vect, ISR_ALIASOF(INT0_vect));
ISR(INT5_vect, ISR_ALIASOF(INT0_vect));
ISR(INT7_vect, ISR_ALIASOF(INT0_vect));

#endif
#endif

#endif

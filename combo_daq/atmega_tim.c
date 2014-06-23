#include "tim.h"

#if PLAT_ATMEGA

static volatile uint32_t longticks;
static uint16_t wrap_to;

void tim_watch(void) {
    longticks = 0; // clear software counter
    TCCR1A = 0; // no pwm output, normal mode
    TCNT1 = 0; // clear counter
    TIFR1 = _BV(TOV1); // clear interrupt flag
    TIMSK1 = _BV(TOIE1); // enable interrupt
    TCCR1B = _BV(CS11); // prescale of 8, normal mode, go
}

uint64_t tim_time(void) {
    // complicated to avoid race conditions with timer overflows
    // in most cases, equiv to return (longticks << 16) | TCNT1
    // checks for overflows to ensure consistency between
    // values of longticks and TCNT1
    uint8_t pre_flag, post_flag;
    uint16_t tval;
    uint8_t save_sreg = SREG;
    cli();
    pre_flag = TIFR1;
    tval = TCNT1;
    post_flag = TIFR1;
    if (bit_is_set(pre_flag, TOV1) || (bit_is_set(post_flag, TOV1) && tval < 0x8000)) {
        longticks += 1;
        TIFR1 |= _BV(TOV1);
    }
    uint64_t res = ((uint64_t) longticks << 16) | tval;
    SREG = save_sreg;
    return res;
}

void tim_trigger(uint8_t prescale, uint32_t reload) {
    wrap_to = (reload & 0xFFFF);
    longticks = 0;
    TCCR1A = 0; // no pwm output, wgm setting
    TCNT1 = 0; // clear counter
    OCR1A = (reload >> 16); // set overflow value
    TIFR1 = _BV(OCF1A); // clear interrupt flag
    TIMSK1 = _BV(OCIE1A); // enable interrupt
    TCCR1B = _BV(WGM12) | prescale; // ctc mode, go
}

void tim_cancel(void) {
    // TODO
}

ISR(TIMER1_OVF_vect) {
    longticks += 1;
}

ISR(TIMER1_COMPA_vect) {
    longticks++;
    if (longticks >= wrap_to) {
        longticks = 0;
        trigger_handler();
    }
}

#endif


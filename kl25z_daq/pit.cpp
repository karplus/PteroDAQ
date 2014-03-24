#include "pit.h"

void pit_init(void) {
    SIM->SCGC6 |= SIM_SCGC6_PIT_MASK; // clock gate enable
    PIT->MCR = 0; // enable pit
    PIT->CHANNEL[1].LDVAL = 0xFFFFFFFF; // maximum load values
    PIT->CHANNEL[0].LDVAL = 0xFFFFFFFF;
    PIT->CHANNEL[1].TCTRL = PIT_TCTRL_CHN_MASK|PIT_TCTRL_TEN_MASK; // chain and enable timer 1
    PIT->CHANNEL[0].TCTRL = PIT_TCTRL_TEN_MASK; // enable timer 0
}

uint64_t pit_time(void) {
    uint32_t high_count = ~PIT->LTMR64H; // timer 1 value (high 32 bits)
    uint32_t low_count = ~PIT->LTMR64L; // timer 0 value (low 32 bits, synced with previous read)
    return (((uint64_t) high_count) << 28) | (low_count >> 4); // combine to 60 bits
    // lowest four bits are dropped to acheive microsecond resolution
    // (with 16 MHz bus clock)
}

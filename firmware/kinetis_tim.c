#include "tim.h"

#if PLAT_KINETIS

void tim_trigger(uint8_t prescale, uint32_t reload) {
    SCB->ICSR = SCB_ICSR_PENDSTCLR_Msk; // clear systick pending
    SysTick->LOAD = reload; // set period to reload + 1
    SysTick->VAL = 0; // clear current value
    SysTick->CTRL = (prescale << SysTick_CTRL_CLKSOURCE_Pos) | // select prescale of core clock
        SysTick_CTRL_TICKINT_Msk | // enable systick interrupt
        SysTick_CTRL_ENABLE_Msk; // enable timer
}

void tim_cancel(void) {
    SysTick->CTRL = 0; // stop timer
}

bool tim_pending(void) {
    // return 1 if there is an interrupt pending since the last time 
    // SysTick->CTRL was read.
    
    // Calling tim_pending at the beginning of a SysTick handler
    // and again at the end lets you know whether another interrupt should have
    // happened while the handler was running.
    return (SysTick->CTRL & SysTick_CTRL_COUNTFLAG_Msk) !=0;
}

void tim_watch(void) {
    SIM->SCGC6 |= SIM_SCGC6_PIT_MASK; // clock gate enable
    PIT->MCR = 0; // enable pit
    PIT->CHANNEL[1].LDVAL = 0xFFFFFFFF; // maximum load values
    PIT->CHANNEL[0].LDVAL = 0xFFFFFFFF;
    PIT->CHANNEL[1].TCTRL = PIT_TCTRL_CHN_MASK|PIT_TCTRL_TEN_MASK; // chain and enable timer 1
    PIT->CHANNEL[0].TCTRL = PIT_TCTRL_TEN_MASK; // enable timer 0
}

uint64_t tim_time(void) {
    uint32_t high_count = ~PIT->LTMR64H; // timer 1 value (high 32 bits)
    uint32_t low_count = ~PIT->LTMR64L; // timer 0 value (low 32 bits, synced with previous read)
    return (((uint64_t) high_count) << 32) | (low_count); // combine to 64 bits
}

void SysTick_Handler(void) {
    uint8_t pending = tim_pending(); // read SysTick>CTRL, to clear COUNTFLAG
    trigger_handler();
}

#endif

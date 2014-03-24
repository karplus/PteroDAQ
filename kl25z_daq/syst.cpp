#include "syst.h"

void syst_trigger(uint8_t prescale, uint32_t reload) {
    SCB->ICSR = SCB_ICSR_PENDSTCLR_Msk; // clear systick pending
    SysTick->LOAD = reload; // set period to reload + 1
    SysTick->VAL = 0; // clear current value
    SysTick->CTRL = (prescale << SysTick_CTRL_CLKSOURCE_Pos) | // select prescale of core clock
        SysTick_CTRL_TICKINT_Msk | // enable systick interrupt
        SysTick_CTRL_ENABLE_Msk; // enable timer
}

void syst_stop(void) {
    SysTick->CTRL = 0; // stop timer
}
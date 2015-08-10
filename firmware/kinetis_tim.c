#include "tim.h"

#if PLAT_KL25Z

// On KL25Z, the timing interrupts are based on the SysTick counter,
//	which is prescaled from the CPU clock

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

void SysTick_Handler(void) {
    uint8_t pending = tim_pending(); // read SysTick>CTRL, to clear COUNTFLAG
    trigger_handler();
}


// PITs 0 and 1 are used for timestamps.

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

#elif PLAT_TEENSY31

// On the Teensy3.1, the SysTick is always the CPU clock, so we use
//	one periodic interrupt timer (PIT) to get a 32-bit timer.
// The Teensy3.1 has 4 PIT timers available, so PIT2 will be used here.

// Future upgrade: go to 64-bit timer (PITs 2 and 3) to get longer
//	interval than 44s.

void tim_trigger(uint8_t prescale, uint32_t reload) {
    SIM_SCGC6 |= SIM_SCGC6_PIT; // clock gate enable
    PIT_MCR = 0; // enable pit
    
    PIT_LDVAL2 = reload;
    PIT_TFLG2 = PIT_TFLG_TIF;	// clear pending interrupt
    
    //enable interrupt and timer
    NVIC_ENABLE_IRQ(IRQ_PIT_CH2);
    PIT_TCTRL2 = PIT_TCTRL_TIE|PIT_TCTRL_TEN;
    
}

void tim_cancel(void) {
    PIT_TCTRL2 = 0;
    NVIC_DISABLE_IRQ(IRQ_PIT_CH2);
}

bool tim_pending(void) {
    // return 1 if there is an interrupt pending since the last time 
    return PIT_TFLG2;
}

void pit2_isr(void) {
    PIT_TFLG2 = PIT_TFLG_TIF;	// clear pending interrupt
    trigger_handler();
}


// PITs 0 and 1 are used for timestamps.

void tim_watch(void) {
    SIM_SCGC6 |= SIM_SCGC6_PIT; // clock gate enable
    PIT_MCR = 0; // enable pit
    PIT_LDVAL1 = 0xFFFFFFFF; // maximum load values
    PIT_LDVAL0 = 0xFFFFFFFF;
    PIT_TCTRL1 = PIT_TCTRL_CHN|PIT_TCTRL_TEN; // chain and enable timer 1
    PIT_TCTRL0 = PIT_TCTRL_TEN; // enable timer 0
}

uint64_t tim_time(void) {
    uint32_t low_count = PIT_CVAL0;
    uint32_t high_count = PIT_CVAL1;
    uint32_t low_count2 = PIT_CVAL0;
    if (low_count2 > low_count)
    {    // oops, wrapped around
    	high_count = PIT_CVAL1;
    }
    return (((uint64_t) ~high_count) << 32) | (~low_count2); // combine to 64 bits
}
#endif


#include "tim.h"

#if PLAT_KINETIS
  // These should be defined in Teensyduino's kinetis.h
  // but were missing in some releases.
   #ifndef SCB_ICSR_PENDSTSET
	#define SCB_ICSR_PENDSTSET		((uint32_t) (1<<26))
   #endif
   #ifndef SCB_ICSR_PENDSTCLR
	#define SCB_ICSR_PENDSTCLR		((uint32_t) (1<<25))
   #endif
#endif


#if PLAT_KL25Z

// On KL25Z, the timing interrupts are based on the SysTick counter,
//	which is prescaled from the CPU clock

void tim_start(void){
    SIM->SCGC6 |= SIM_SCGC6_PIT_MASK; // clock gate enable
}

void tim_trigger(uint8_t prescale, uint32_t reload) {
    PIT->MCR = 0; // enable pit
    tim_cancel();
    
    PIT->CHANNEL[0].LDVAL = prescale;
    PIT->CHANNEL[1].LDVAL = reload;
    PIT->CHANNEL[1].TFLG = PIT_TFLG_TIF_MASK;
    
    NVIC_EnableIRQ(PIT_IRQn);
    PIT->CHANNEL[1].TCTRL = PIT_TCTRL_TIE_MASK|PIT_TCTRL_CHN_MASK|PIT_TCTRL_TEN_MASK; // chain and enable timer 1
    PIT->CHANNEL[0].TCTRL = PIT_TCTRL_TEN_MASK; // enable timer 0

}

void tim_cancel(void) {
    NVIC_DisableIRQ(PIT_IRQn);
    PIT->CHANNEL[1].TCTRL = 0;
    PIT->CHANNEL[0].TCTRL = 0;
}

bool tim_pending(void) {
    // return 1 if there is an interrupt pending 
    return PIT->CHANNEL[1].TFLG;
}

void PIT_IRQHandler(void) {
    PIT->CHANNEL[1].TFLG = PIT_TFLG_TIF_MASK;	// clear pending interrupt
    trigger_handler();
}


// PITs 0 and 1 are used for timestamps.

void timestamp_start(void) {
    SIM->SCGC6 |= SIM_SCGC6_PIT_MASK; // clock gate enable
    PIT->MCR = 0; // enable pit
    PIT->CHANNEL[1].LDVAL = 0xFFFFFFFF; // maximum load values
    PIT->CHANNEL[0].LDVAL = 0xFFFFFFFF;
    PIT->CHANNEL[1].TCTRL = PIT_TCTRL_CHN_MASK|PIT_TCTRL_TEN_MASK; // chain and enable timer 1
    PIT->CHANNEL[0].TCTRL = PIT_TCTRL_TEN_MASK; // enable timer 0
}

uint64_t timestamp_get(void) {
    uint32_t high_count = ~PIT->LTMR64H; // timer 1 value (high 32 bits)
    uint32_t low_count = ~PIT->LTMR64L; // timer 0 value (low 32 bits, synced with previous read)
    return (((uint64_t) high_count) << 32) | (low_count); // combine to 64 bits
}

///////////////////////////////
#elif PLAT_TEENSY31 || PLAT_TEENSYLC

// On the Teensy3.1, the SysTick is always the CPU clock, 
// but we have 4 PITs, so we use
//    Two PIT timers (PIT0 and PIT1) to get either a 64-bit timestamp,
//	or a 32-bit timer with an 8-bit prescale for longer time intervals.

// PIT timers are run off the BUS CLOCK (no prescaler)
// 	so prescale is used for PIT0 and PIT1 chained to PIT0


// Teensy LC has only 1 two-channel PIT, but we can use them with the same code,
//	with the slight modification that the IRQ_PIT_CH1 is just IRQ_PIT
//	and pit1_isr is just pit_isr
#if PLAT_TEENSYLC
#define IRQ_PIT_CH1	IRQ_PIT
#define pit1_isr	pit_isr
#endif

void tim_start(void){
    SIM_SCGC6 |= SIM_SCGC6_PIT; // clock gate enable
}

void tim_trigger(uint8_t prescale, uint32_t reload) {
    PIT_MCR = 0; // enable pit
    tim_cancel();
    
    PIT_LDVAL0 = prescale;
    PIT_LDVAL1 = reload;
    PIT_TFLG1 = PIT_TFLG_TIF;	// clear pending interrupt
    
    //enable interrupt and timer
    NVIC_ENABLE_IRQ(IRQ_PIT_CH1);
    PIT_TCTRL1 = PIT_TCTRL_TIE|PIT_TCTRL_CHN|PIT_TCTRL_TEN; // chain and enable timer 1
    PIT_TCTRL0 = PIT_TCTRL_TEN; // enable timer 0
}

void tim_cancel(void) {
    PIT_TCTRL0 = 0;
    PIT_TCTRL1 = 0;
    NVIC_DISABLE_IRQ(IRQ_PIT_CH1);
}

bool tim_pending(void) {
    // return  if there is an interrupt pending since the last time 
    return PIT_TFLG1;
}

void pit1_isr(void) {
    PIT_TFLG1 = PIT_TFLG_TIF;	// clear pending interrupt
    trigger_handler();
}


// PITs 0 and 1 are used for timestamps.

void timestamp_start(void) {
    SIM_SCGC6 |= SIM_SCGC6_PIT; // clock gate enable
    PIT_MCR = 0; // enable pit
    PIT_LDVAL1 = 0xFFFFFFFF; // maximum load values
    PIT_LDVAL0 = 0xFFFFFFFF;
    PIT_TCTRL1 = PIT_TCTRL_CHN|PIT_TCTRL_TEN; // chain and enable timer 1
    PIT_TCTRL0 = PIT_TCTRL_TEN; // enable timer 0
}

uint64_t timestamp_get(void) {
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


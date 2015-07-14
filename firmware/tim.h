#include "targetlib.h"

// TIM_WATCH_RATE is the rate at which tim_time advances (in Hz)
#ifdef PLAT_ATMEGA
#define TIM_WATCH_RATE	(F_CPU/8)
#elif defined(PLAT_KINETIS)
#define TIM_WATCH_RATE (F_CPU)
#endif

void tim_watch(void);	//set up timer for 64-bit time 
uint64_t tim_time(void); // read timer set up by tim_watch

void tim_trigger(uint8_t prescale, uint32_t reload);	// set up timer for interrupts
void tim_cancel(void);		// turn off timer interrupts
bool tim_pending(void);		// is there a timer interrupt pending?

// Note: the tim_watch and tim_trigger timers may be mutually exclusive,
//	as the same hardware timer may be used for either option.

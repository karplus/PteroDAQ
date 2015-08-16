#include "targetlib.h"

// TIMESTAMP_START_RATE is the rate at which timestamp_get advances (in Hz)
#if PLAT_ATMEGA
#define TIMESTAMP_START_RATE (F_CPU/8)
#elif PLAT_KINETIS
#define TIMESTAMP_START_RATE (F_CPU)
#endif

void timestamp_start(void); // set up timer for 64-bit time 
uint64_t timestamp_get(void); // read timer set up by timestamp_start

void tim_start(void);	// pre-initialize timers for triggering
void tim_trigger(uint8_t prescale, uint32_t reload); // set up timer for interrupts
void tim_cancel(void); // turn off timer interrupts
bool tim_pending(void); // is there a timer interrupt pending?

// Note: the timestamp_start and tim_trigger timers may be mutually exclusive,
//  as the same hardware timer may be used for either option.

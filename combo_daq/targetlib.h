#ifdef __AVR_MEGA__

#include <avr/io.h>
#include <avr/interrupt.h>
#include <stdbool.h>
#include <stddef.h>

#define PLAT_ATMEGA 1

#else

#include "cmsis.h"
#include <stdbool.h>
#include <stddef.h>

#ifdef MKL25Z4_H_

#define PLAT_KINETIS 1

#endif
#endif

void daq_setup(void);
void daq_loop(void);
void trigger_handler(void);



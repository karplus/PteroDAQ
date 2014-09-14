#include <stdbool.h>
#include <stddef.h>

#ifdef __AVR_MEGA__

#include <avr/io.h>
#include <avr/interrupt.h>

#define PLAT_ATMEGA 1

#define MODEL_INFO_LEN (6)

#else

#include "cmsis.h"

#ifdef MKL25Z4_H_

#define PLAT_KINETIS 1

#define MODEL_INFO_LEN (4)

#endif
#endif

void daq_setup(void);
void daq_loop(void);
void trigger_handler(void);
uint8_t* get_model(void);

#include <stdbool.h>
#include <stddef.h>

#ifdef __AVR_MEGA__

// ARDUINO
#include <avr/io.h>
#include <avr/interrupt.h>

#define ENABLE_INTERRUPT() sei()
#define DISABLE_INTERRUPT() cli()

#define PLAT_ATMEGA 1

#define MODEL_INFO_LEN (6)

#else

// ARM platforms
#include "cmsis.h"
#define F_CPU (48000000)

#define ENABLE_INTERRUPT() __enable_irq()
#define DISABLE_INTERRUPT() __disable_irq()

#ifdef MKL25Z4_H_

// KL25Z
#define PLAT_KINETIS 1

#define MODEL_INFO_LEN (4)

#endif
#endif

void daq_setup(void);
void daq_loop(void);
void trigger_handler(void);
uint8_t* get_model(void);

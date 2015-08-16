#ifndef TARGETLIB_H
#define TARGETLIB_H

#ifndef true
#include <stdbool.h>
#endif

#include <stddef.h>




/////////////////////////////////////////
#ifdef __AVR_MEGA__

// ARDUINO
#include <avr/io.h>
#include <avr/interrupt.h>

#define ENABLE_INTERRUPT() sei()
#define DISABLE_INTERRUPT() cli()

#define PLAT_ATMEGA 1
#define MODEL_INFO_LEN (6)
#define DEFAULT_AREF (1)
#define QUEUE_SIZE (1024)

// A couple of routines copied from Arduino.h
#ifdef __cplusplus
extern "C"{
#endif
void pinMode(uint8_t, uint8_t);
void digitalWrite(uint8_t, uint8_t);
#ifdef __cplusplus
} // extern "C"
#endif



/////////////////////////////////////////
#elif defined(TARGET_KL25Z)

// KL25Z
#include "cmsis.h"

#define ENABLE_INTERRUPT() __enable_irq()
#define DISABLE_INTERRUPT() __disable_irq()

#define PLAT_KINETIS 1
#define PLAT_KL25Z 1
#define MODEL_INFO_LEN (4)
#define MODEL_BOARDNUM (5)
#define DEFAULT_AREF (1)
#define QUEUE_SIZE (8192)
#define F_CPU (48000000)

/////////////////////////////////////////
#elif defined(__MK20DX256__)

// Teensy 3.1
#include "core_pins.h"
#include "kinetis.h"

#define ENABLE_INTERRUPT() __enable_irq()
#define DISABLE_INTERRUPT() __disable_irq()

#define PLAT_KINETIS 1
#define PLAT_TEENSY31 1
#define MODEL_INFO_LEN (4)
#define MODEL_BOARDNUM (6)
#define DEFAULT_AREF (0)
#define QUEUE_SIZE (32768)

/////////////////////////////////////////
#elif defined(__MKL26Z64__)

// Teensy LC
#include "core_pins.h"
#include "kinetis.h"

#define ENABLE_INTERRUPT() __enable_irq()
#define DISABLE_INTERRUPT() __disable_irq()

#define PLAT_KINETIS 1
#define PLAT_TEENSYLC 1
#define MODEL_INFO_LEN (4)
#define MODEL_BOARDNUM (7)
#define DEFAULT_AREF (1)
#define QUEUE_SIZE (4096)


#endif

void daq_setup(void);
void daq_loop(void);
void trigger_handler(void);
uint8_t* get_model(void);

#endif

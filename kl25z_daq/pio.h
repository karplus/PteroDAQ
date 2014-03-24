#include "mbed.h"

void pio_init(void);
uint8_t pio_read(uint8_t pin);
void pio_begin(uint8_t pin, uint8_t sense);
void pio_stop(void);
#include "targetlib.h"

void pio_init(void);
uint8_t pio_read(uint8_t pin);
void pio_trigger(uint8_t pin, uint8_t sense);
void pio_cancel(void);


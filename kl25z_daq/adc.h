#include "mbed.h"

bool adc_calib(void);
void adc_init(void);
uint16_t adc_read(uint8_t mux);
void adc_aref(uint8_t choice);

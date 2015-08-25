#ifndef FREQUENCY_H
#define FREQUENCY_H

#include "targetlib.h"


void freq_init(void);	// set up counters or DMA channels for counting

void freq_define(uint8_t freq_channel, uint8_t mux);	// attach a pin to a particular channel

uint32_t freq_read(uint8_t freq_channel);

void freq_start(uint8_t num_channels);	// start the first num_channels DMA channels
void freq_stop(uint8_t num_channels);	// stop the first num_channels DMA channels


#endif

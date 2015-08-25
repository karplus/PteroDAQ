#include "frequency.h"

#if PLAT_ATMEGA

// The ATMega platforms do not have any spare counters that can be
//	used for doing frequency measurements.
// Eventually we can set up interrupt routines that increment counters
//	in memory.

// set up counters or DMA channels for counting
void freq_init(void)
{
}

// attach a pin to a particular channel
void freq_define(uint8_t freq_channel, uint8_t mux)
{
}

uint32_t freq_read(uint8_t freq_channel)
{    return(0);
}

// start the first num_channels DMA channels
void freq_start(uint8_t num_channels)
{
}

// stop the first num_channels DMA channels
void freq_stop(uint8_t num_channels)
{
}


#endif

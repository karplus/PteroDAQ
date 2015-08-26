#include "frequency.h"

#if PLAT_KL25Z

#define DMA_NUM_CHANNELS (4)
#define DMAMUX_SOURCE_PORTA (49)

// set up counters or DMA channels for counting
void freq_init(void)
{   SIM->SCGC6 |= SIM_SCGC6_DMAMUX_MASK;	// turn on clocking for DMAMUX
    SIM->SCGC7 |= SIM_SCGC7_DMA_MASK;	// turn on clocking for DMA

    freq_stop(DMA_NUM_CHANNELS);
}

static uint8_t dummy_for_DMA;	// dummy location to provide legal DMA addresses

#define DMA_REGISTER_STRIDE (&DMA[1]-&DMA[0])
#define PORT_REGISTER_STRIDE_BYTES (PORTB_BASE-PORTA_BASE)
#define PORT_PTR(p) ( (PORT_Type*) (PORTA_BASE + PORT_REGISTER_STRIDE_BYTES*(p)))


// attach a pin to a particular channel
void freq_define(uint8_t freq_channel, uint8_t mux)
{
    if (freq_channel >= 3)
    {    return;	// only 3 channels usable, 1 each for ports A, C, D
    }
    
    uint8_t port= mux>>5;
    
    //  configure, but don't enable DMAMUX
    DMAMUX0->CHCFG[freq_channel] = (DMAMUX_SOURCE_PORTA + port); 
    __asm__ volatile( "nop" );

    // The 4 registers are DMA_SAR, DMA_DAR, DMA_DSR_BCR, DMA_DCR in order.
    
    DMA0->DMA[freq_channel].SAR = (uint32_t) &dummy_for_DMA;	// set DMA_SAR
    DMA0->DMA[freq_channel].DAR = (uint32_t) &dummy_for_DMA;	// set DMA_DAR
    DMA0->DMA[freq_channel].DSR_BCR = DMA_DSR_BCR_DONE_MASK;	// clear DONE flag 
    DMA0->DMA[freq_channel].DSR_BCR = DMA_DSR_BCR_DONE_MASK;	// write twice as suggested in KLQRUG.pdf
    DMA0->DMA[freq_channel].DCR  = 
    	  DMA_DCR_ERQ_MASK 			// enable peripheral request
	|  DMA_DCR_CS_MASK 			// cycle steal
	| DMA_DCR_SSIZE(1) 		// 1byte source (SINC=0 so no increment)
	| DMA_DCR_DSIZE(1) 		// 1byte dest   (DINC=0 so no increment)
	| DMA_DCR_D_REQ_MASK;		// disable request when counter full    
    
    PORT_PTR(port)->PCR[mux&0x1f]= 
    	  PORT_PCR_IRQC(1)	// DMA on rising
	| PORT_PCR_MUX(1) ;	// GPIO
}

uint32_t freq_read(uint8_t freq_channel)
{    
    if (freq_channel >= DMA_NUM_CHANNELS)
    {    return(1<<30);
    }
    
    // get pointer to appropriate DMA_DSR_BCR register
    DMAMUX0->CHCFG[freq_channel] &= ~(DMAMUX_CHCFG_ENBL_MASK);	// turn off at DMAMUX
    __asm__ volatile( "nop" );
    
    uint32_t count = 0xfffff - (DMA0->DMA[freq_channel].DSR_BCR & 0xfffff);
    DMA0->DMA[freq_channel].DSR_BCR = DMA_DSR_BCR_DONE_MASK;	// clear DONE flag
    DMA0->DMA[freq_channel].DSR_BCR = 0xfffff;	// set BCR 
    DMAMUX0->CHCFG[freq_channel] |= DMAMUX_CHCFG_ENBL_MASK;	// turn on at DMAMUX    

    return (count);
}

// start the first num_channels DMA channels
void freq_start(uint8_t num_channels)
{
    uint8_t i;
    freq_init();
    
    for (i=0; i< num_channels; i++)
    {	DMAMUX0->CHCFG[i] &= ~(DMAMUX_CHCFG_ENBL_MASK);	// turn off at DMAMUX
        __asm__ volatile( "nop" );	
        DMA0->DMA[i].DSR_BCR = DMA_DSR_BCR_DONE_MASK;	// clear DONE flag
        DMA0->DMA[i].DSR_BCR = 0xfffff;	// set BCR 
        DMAMUX0->CHCFG[i] |= DMAMUX_CHCFG_ENBL_MASK;	// turn on at DMAMUX    
    }
}

// stop the first num_channels DMA channels
void freq_stop(uint8_t num_channels)
{
    uint8_t i;
    for (i=0; i< num_channels; i++)
    {	DMAMUX0->CHCFG[i] &= ~(DMAMUX_CHCFG_ENBL_MASK);	// turn off at DMAMUX
        __asm__ volatile( "nop" );	
        DMA0->DMA[i].DSR_BCR = DMA_DSR_BCR_DONE_MASK;	// clear DONE flag
        DMA0->DMA[i].DSR_BCR = DMA_DSR_BCR_DONE_MASK;	// write twice as suggested in KLQRUG.pdf
    }
}




///////////////////////////////
#elif PLAT_TEENSY31 

// NOT WRITTEN YET

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

///////////////////////////////
#elif PLAT_TEENSYLC

// set up counters or DMA channels for counting
void freq_init(void)
{   SIM_SCGC6 |= SIM_SCGC6_DMAMUX;	// turn on clocking for DMAMUX
    SIM_SCGC7 |= SIM_SCGC7_DMA;		// turn on clocking for DMA

    freq_stop(DMA_NUM_CHANNELS);
}


static uint8_t dummy_for_DMA;	// dummy location to provide legal DMA addresses

#define DMA_REGISTER_STRIDE (&DMA_SAR1-&DMA_SAR0)
#define PORT_REGISTER_STRIDE (&PORTB_PCR0-&PORTA_PCR0)


// attach a pin to a particular channel
void freq_define(uint8_t freq_channel, uint8_t mux)
{
    if (freq_channel >= 3)
    {    return;	// only 3 channels usable, 1 each for ports A, C, D
    }
    
    uint8_t port= mux>>5;
    
    //  configure, but don't enable DMAMUX
    (&DMAMUX0_CHCFG0)[freq_channel] = (DMAMUX_SOURCE_PORTA + port); 
     __asm__ volatile( "nop" );	
    
    // The 4 registers are DMA_SAR, DMA_DAR, DMA_DSR_BCR, DMA_DCR in order.
    volatile uint32_t*  DMA_reg = (volatile uint32_t*)(&DMA_SAR0) + DMA_REGISTER_STRIDE*freq_channel;
    
    *(DMA_reg++) = (uint32_t) &dummy_for_DMA;	// set DMA_SAR
    *(DMA_reg++) = (uint32_t) &dummy_for_DMA;	// set DMA_DAR
    *DMA_reg = DMA_DSR_BCR_DONE;	// clear DONE flag 
    *DMA_reg = DMA_DSR_BCR_DONE;	// write twice as suggested in KLQRUG.pdf
    DMA_reg++;
    *DMA_reg  = 
    	  DMA_DCR_ERQ 			// enable peripheral request
	|  DMA_DCR_CS 			// cycle steal
	| DMA_DCR_SSIZE(1) 		// 1byte source (SINC=0 so no increment)
	| DMA_DCR_DSIZE(1) 		// 1byte dest   (DINC=0 so no increment)
	| DMA_DCR_D_REQ;		// disable request when counter full    
    
    (&PORTA_PCR0) [(port*PORT_REGISTER_STRIDE) + (mux&0x1f)] = 
    	  PORT_PCR_IRQC(1)	// DMA on rising
	| PORT_PCR_MUX(1) ;	// GPIO
}

uint32_t freq_read(uint8_t freq_channel)
{    
    if (freq_channel >= DMA_NUM_CHANNELS)
    {    return(1<<30);
    }
    
    // get pointer to appropriate DMA_DSR_BCR register
    volatile uint32_t*  DMA_reg = (&DMA_DSR_BCR0) + DMA_REGISTER_STRIDE*freq_channel;
    (&DMAMUX0_CHCFG0)[freq_channel] &= ~(DMAMUX_ENABLE);	// turn off at DMAMUX
    __asm__ volatile( "nop" );
    
    uint32_t count = 0xfffff - ((*DMA_reg) & 0xfffff);
    DMA_reg[0] = DMA_DSR_BCR_DONE;	// clear DONE flag
    DMA_reg[0] = 0xfffff;	// set BCR 
    (&DMAMUX0_CHCFG0)[freq_channel] |= DMAMUX_ENABLE;	// turn on at DMAMUX

    return (count);
}

// start the first num_channels DMA channels
void freq_start(uint8_t num_channels)
{
    volatile uint32_t*  DMA_reg = (&DMA_DSR_BCR0);
    uint8_t i;
    freq_init();
    
    for (i=0; i< num_channels; i++)
    {	(&DMAMUX0_CHCFG0)[i] &= ~(DMAMUX_ENABLE);	// turn off at DMAMUX
        __asm__ volatile( "nop" );	
	DMA_reg[0] = DMA_DSR_BCR_DONE;
        DMA_reg[0] = 0xfffff;
	(&DMAMUX0_CHCFG0)[i] |= DMAMUX_ENABLE;	// turn on at DMAMUX
	DMA_reg += DMA_REGISTER_STRIDE;
    }

}

// stop the first num_channels DMA channels
void freq_stop(uint8_t num_channels)
{
    volatile uint32_t*  DMA_reg = (&DMA_DSR_BCR0);
    uint8_t i;
    for (i=0; i< num_channels; i++)
    {	(&DMAMUX0_CHCFG0)[i] &= ~(DMAMUX_ENABLE);	// turn off at DMAMUX
        __asm__ volatile( "nop" );	
        DMA_reg[0] = DMA_DSR_BCR_DONE;
        DMA_reg[0] = DMA_DSR_BCR_DONE;	// write twice as suggested in KLQRUG.pdf
	DMA_reg += DMA_REGISTER_STRIDE;
    }
}

#endif


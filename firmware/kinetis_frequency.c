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

// ToDo:
//	With only a 15-bit counter per DMA channel, we probably need to add a software
//	interrupt on each major cycle to increment a memory location
//	as well.
// Fri Aug 28 18:10:17 PDT 2015 Kevin Karplus
//	Attempts were made using dma_major_counter[], but the program always
//	froze when the count exceeded the 32767 limit.
//	Attempted changes have been commented out again.
//	

#define NUM_EXTERNAL_DMA (5)
// only 5 channels usable, 1 each for ports A, B, C, D, E

#define PORT_REGISTER_STRIDE (&PORTB_PCR0-&PORTA_PCR0)

#define TCD_32_STRIDE	(&DMA_TCD1_SADDR - &DMA_TCD0_SADDR) // stride for 32-bit registers

#define DMA_TCDn_SADDR(n)	((&DMA_TCD0_SADDR)[n*TCD_32_STRIDE])
#define DMA_TCDn_DADDR(n)	((&DMA_TCD0_DADDR)[n*TCD_32_STRIDE])
#define DMA_TCDn_NBYTES_MLNO(n)	((&DMA_TCD0_NBYTES_MLNO)[n*TCD_32_STRIDE])
#define DMA_TCDn_SLAST(n)	((&DMA_TCD0_SLAST)[n*TCD_32_STRIDE])
#define DMA_TCDn_DLASTSGA(n)	((&DMA_TCD0_DLASTSGA)[n*TCD_32_STRIDE])

#define TCD_16_STRIDE	(&DMA_TCD1_SOFF - &DMA_TCD0_SOFF) // stride for 16-bit registers

#define DMA_TCDn_SOFF(n)	((&DMA_TCD0_SOFF)[n*TCD_16_STRIDE])
#define DMA_TCDn_DOFF(n)	((&DMA_TCD0_DOFF)[n*TCD_16_STRIDE])
#define DMA_TCDn_ATTR(n)	((&DMA_TCD0_ATTR)[n*TCD_16_STRIDE])
#define DMA_TCDn_CITER_ELINKNO(n)	((&DMA_TCD0_CITER_ELINKNO)[n*TCD_16_STRIDE])
#define DMA_TCDn_CSR(n)		((&DMA_TCD0_CSR)[n*TCD_16_STRIDE])
#define DMA_TCDn_BITER_ELINKNO(n)	((&DMA_TCD0_BITER_ELINKNO)[n*TCD_16_STRIDE])

#define DEBUG_LED	(13)	// pin number for on-board LED, used for debugging only

static uint8_t dummy_for_DMA;	// dummy location to provide legal DMA addresses

volatile uint32_t dma_major_counter[NUM_EXTERNAL_DMA];	// counter of bytes transferred in completed major loops

// set up counters or DMA channels for counting
void freq_init(void)
{   SIM_SCGC6 |= SIM_SCGC6_DMAMUX;	// turn on clocking for DMAMUX
    SIM_SCGC7 |= SIM_SCGC7_DMA;		// turn on clocking for DMA

    freq_stop(NUM_EXTERNAL_DMA);
}


// attach a pin to a particular channel
void freq_define(uint8_t freq_channel, uint8_t mux)
{
    if (freq_channel >= NUM_EXTERNAL_DMA)
    {    return;	
    }
    
    uint8_t port= mux>>5;
    
    //  configure, but don't enable DMAMUX
    (&DMAMUX0_CHCFG0)[freq_channel] = (DMAMUX_SOURCE_PORTA + port); 
     __asm__ volatile( "nop" );	
    
    // Need to set up TCD (Transfer Control Description) registers 
    // for source and destination addresses.  
    //		TCDn_{SADDR, DADDR, CITER}
    // I want the minor loop count to be 1.
    // The major iteration count is what is used as the pulse counter.
    //	If the major iteration counter is too small, I may need to use
    //		an interrupt

    // Transfer from dummy_for_DMA to dummy_for_DMA with no increment
    DMA_TCDn_SADDR(freq_channel) = &dummy_for_DMA;
    DMA_TCDn_DADDR(freq_channel) = &dummy_for_DMA;
    DMA_TCDn_SLAST(freq_channel) = 0;		// no increment when major iteration done
    DMA_TCDn_DLASTSGA(freq_channel) = 0;    
    DMA_TCDn_SOFF(freq_channel) = 0;		// no increment per transfer
    DMA_TCDn_DOFF(freq_channel) = 0;


    DMA_TCDn_CITER_ELINKNO(freq_channel) = DMA_TCD_CITER_MASK;	// only a 15-bit counter!
    DMA_TCDn_BITER_ELINKNO(freq_channel) = DMA_TCD_CITER_MASK;	// only a 15-bit counter!
//    DMA_TCDn_CSR(freq_channel)=  DMA_TCD_CSR_INTMAJOR | DMA_TCD_CSR_DREQ;		// interrupt on major iteration done
    DMA_TCDn_CSR(freq_channel)=  DMA_TCD_CSR_DREQ;
    
    dma_major_counter[freq_channel] = 0;			// reset major loop counter
    
    DMA_TCDn_ATTR(freq_channel) = 0;	// 8-bit transfers no modulo
    DMA_TCDn_NBYTES_MLNO(freq_channel) = 1;	// do a single transfer (0 would be 4GB)


    DMA_CR = 0;				// none of the special modes
    DMA_SERQ = freq_channel;		// enable DMA peripheral request
    DMA_CDNE = freq_channel;		// Clear DONE bit
    DMA_CERR = freq_channel;		// Clear error
    DMA_CEEI = freq_channel;		// disable error interrupt
//    DMA_SEEI = freq_channel;		// enable error interrupt (debugging only)
    
    (&PORTA_PCR0) [(port*PORT_REGISTER_STRIDE) + (mux&0x1f)] = 
    	  PORT_PCR_IRQC(1)	// DMA on rising
	| PORT_PCR_MUX(1) ;	// GPIO
}

uint32_t freq_read(uint8_t freq_channel)
{    
    if (freq_channel >= NUM_EXTERNAL_DMA)
    {    return(1<<30);
    }
    
    (&DMAMUX0_CHCFG0)[freq_channel] &= ~(DMAMUX_ENABLE);	// turn off at DMAMUX
    __asm__ volatile( "nop" );
    
    uint32_t count = DMA_TCD_CITER_MASK 
		    -(DMA_TCDn_CITER_ELINKNO(freq_channel) & 0x7fff) 
		    + dma_major_counter[freq_channel];
    
    DMA_CDNE = freq_channel;		// Clear DONE bit
    DMA_SERQ = freq_channel;		// (re)enable DMA peripheral request

//    if (DMA_ES)
//    {    digitalWrite(DEBUG_LED,0);	// turn off LED if any errors
//    }
    
    DMA_CERR = freq_channel;		// Clear error
    DMA_CEEI = freq_channel;		// disable error interrupt
//    DMA_SEEI = freq_channel;		// enable error interrupt (debugging only)
    
    DMA_TCDn_CITER_ELINKNO(freq_channel) = DMA_TCD_CITER_MASK;	// Reset
//    DMA_TCDn_BITER_ELINKNO(freq_channel) = DMA_TCD_CITER_MASK;	// Reset
    dma_major_counter[freq_channel] = 0;			// reset major loop counter
    
    (&DMAMUX0_CHCFG0)[freq_channel] |= DMAMUX_ENABLE;	// turn on at DMAMUX

//    if (count>DMA_TCD_CITER_MASK)
//    {    digitalWrite(DEBUG_LED,0);	// turn off LED
//    }
    
    return (count);
}


// start the first num_channels DMA channels
void freq_start(uint8_t num_channels)
{
    uint8_t freq_channel;
    freq_init();
    
    for (freq_channel=0; freq_channel< num_channels; freq_channel++)
    {    
	(&DMAMUX0_CHCFG0)[freq_channel] &= ~(DMAMUX_ENABLE);	// turn off at DMAMUX
	__asm__ volatile( "nop" );

	DMA_CDNE = freq_channel;		// Clear DONE bit
	DMA_TCDn_CITER_ELINKNO(freq_channel) = DMA_TCD_CITER_MASK;	// only a 15-bit counter!
        dma_major_counter[freq_channel] = 0;			// reset major loop counter
        DMA_SERQ = freq_channel;		// (re)enable DMA peripheral request

        NVIC_ENABLE_IRQ(IRQ_DMA_CH0+freq_channel);
//        NVIC_ENABLE_IRQ(IRQ_DMA_ERROR);	// debugging only
	
	(&DMAMUX0_CHCFG0)[freq_channel] |= DMAMUX_ENABLE;	// turn on at DMAMUX
    }
    
//    pinMode(DEBUG_LED,1);
//    digitalWrite(DEBUG_LED,1);	// turn on LED
}

// stop the first num_channels DMA channels
void freq_stop(uint8_t num_channels)
{
    uint8_t freq_channel;
    for (freq_channel=0; freq_channel< num_channels; freq_channel++)
    {	(&DMAMUX0_CHCFG0)[freq_channel] &= ~(DMAMUX_ENABLE);	// turn off at DMAMUX
        __asm__ volatile( "nop" );	
	
	DMA_CDNE = freq_channel;		// Clear DONE bit
        NVIC_DISABLE_IRQ(IRQ_DMA_CH0+freq_channel);
    }
//    digitalWrite(DEBUG_LED,0);	// turn off LED

}


// Interrupt routine for DMA errors
extern void dma_error_isr(void)
{
//    digitalWrite(DEBUG_LED,0);	// turn off LED
    
    DMA_CERR = DMA_CERR_CAEI;		// clear all error indicators
}


// Interrupt routines for first 5 DMA channels. Need to clear the DONE
// bit and increment the major counter by number of bytes in minor loop.

void dma_ch0_isr(void)
{
    (&DMAMUX0_CHCFG0)[0] &= ~(DMAMUX_ENABLE);	// turn off at DMAMUX
    __asm__ volatile( "nop" );

//    if (DMA_ES)
//    {    digitalWrite(DEBUG_LED,0);	// turn off LED if any errors
//    }
    
    DMA_CDNE = 0;		// Clear DONE bit
    DMA_CERR = 0;		// Clear error
    DMA_CEEI = 0;		// disable error interrupt
//    DMA_SEEI = 0;		// enable error interrupt
    DMA_TCDn_CITER_ELINKNO(0) = DMA_TCD_CITER_MASK;	// only a 15-bit counter!

    DMA_SERQ = 0;		// (re)enable DMA peripheral request

    (&DMAMUX0_CHCFG0)[0] |= DMAMUX_ENABLE;	// turn on at DMAMUX

    dma_major_counter[0] += DMA_TCD_CITER_MASK;	// increment  bytes sent
    
//    if (DMA_ES)
//    {    digitalWrite(DEBUG_LED,0);	// turn off LED if any errors
//    }
}
void dma_ch1_isr(void)
{
    (&DMAMUX0_CHCFG0)[1] &= ~(DMAMUX_ENABLE);	// turn off at DMAMUX
    __asm__ volatile( "nop" );
    
    DMA_CDNE = 1;		// Clear DONE bit
    (&DMAMUX0_CHCFG0)[1] |= DMAMUX_ENABLE;	// turn on at DMAMUX

    dma_major_counter[1] += DMA_TCD_CITER_MASK;	// increment  bytes sent
}
void dma_ch2_isr(void)
{
    (&DMAMUX0_CHCFG0)[2] &= ~(DMAMUX_ENABLE);	// turn off at DMAMUX
    __asm__ volatile( "nop" );
    
    DMA_CDNE = 2;		// Clear DONE bit
    (&DMAMUX0_CHCFG0)[2] |= DMAMUX_ENABLE;	// turn on at DMAMUX

    dma_major_counter[2] += DMA_TCD_CITER_MASK;	// increment  bytes sent
}
void dma_ch3_isr(void)
{
    __asm__ volatile( "nop" );
    (&DMAMUX0_CHCFG0)[3] &= ~(DMAMUX_ENABLE);	// turn off at DMAMUX
    __asm__ volatile( "nop" );
    
    DMA_CDNE = 3;		// Clear DONE bit
    (&DMAMUX0_CHCFG0)[3] |= DMAMUX_ENABLE;	// turn on at DMAMUX

    dma_major_counter[3] += DMA_TCD_CITER_MASK;	// increment  bytes sent
}
void dma_ch4_isr(void)
{
    (&DMAMUX0_CHCFG0)[4] &= ~(DMAMUX_ENABLE);	// turn off at DMAMUX
    __asm__ volatile( "nop" );
    
    DMA_CDNE = 4;		// Clear DONE bit
    (&DMAMUX0_CHCFG0)[4] |= DMAMUX_ENABLE;	// turn on at DMAMUX

    dma_major_counter[4] += DMA_TCD_CITER_MASK;	// increment  bytes sent
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


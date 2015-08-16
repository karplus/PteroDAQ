#include "pio.h"

#if PLAT_KL25Z

void pio_init(void) {
    // gate
    SIM->SCGC5 |= SIM_SCGC5_PORTA_MASK | SIM_SCGC5_PORTB_MASK | SIM_SCGC5_PORTC_MASK | SIM_SCGC5_PORTD_MASK | SIM_SCGC5_PORTE_MASK;
    // set as gpio
    // all pins not analog or used for other functions
    PORTA->GPCLR = (0xF036UL << 16) | PORT_PCR_MUX(1);
    PORTA->GPCHR = (0x0003UL << 16) | PORT_PCR_MUX(1);
    PORTB->GPCLR = (0x0F00UL << 16) | PORT_PCR_MUX(1);
    PORTB->GPCHR = (0x0000UL << 16) | PORT_PCR_MUX(1);
    PORTC->GPCLR = (0x3FF8UL << 16) | PORT_PCR_MUX(1);
    PORTC->GPCHR = (0x0003UL << 16) | PORT_PCR_MUX(1);
    PORTD->GPCLR = (0x009DUL << 16) | PORT_PCR_MUX(1);
    PORTE->GPCLR = (0x003FUL << 16) | PORT_PCR_MUX(1);
    PORTE->GPCHR = (0x8000UL << 16) | PORT_PCR_MUX(1);
}

FGPIO_Type* gpio_ports[] = FGPIO_BASES;
PORT_Type* ctrl_ports[] = PORT_BASES;

uint8_t pio_read(uint8_t pin) {
    return ((gpio_ports[pin >> 5]->PDIR) >> (pin & 0x1F)) & 1;
}

void pio_trigger(uint8_t pin, uint8_t sense) {
    volatile uint32_t* pcr = &(ctrl_ports[pin >> 5]->PCR[pin & 0x1F]);
    *pcr &= ~PORT_PCR_IRQC_MASK;
    NVIC_EnableIRQ(PORTA_IRQn);
    NVIC_EnableIRQ(PORTD_IRQn);
    *pcr |= PORT_PCR_ISF_MASK | PORT_PCR_IRQC(sense | 8);
}

void pio_cancel(uint8_t pin) {
    ctrl_ports[pin >> 5]->PCR[pin & 0x1F] &= ~PORT_PCR_IRQC_MASK;
    NVIC_DisableIRQ(PORTA_IRQn);
    NVIC_DisableIRQ(PORTD_IRQn);
}

void PORTA_IRQHandler(void) {
    PORTA->ISFR = (uint32_t) (-1); // clear all port A interrupt flags
    trigger_handler();
}

void PORTD_IRQHandler(void) {
    PORTD->ISFR = (uint32_t) (-1); // clear all port D interrupt flags
    trigger_handler();
}

//////////////////////////////////////////////////////////////
#elif PLAT_TEENSY31

void pio_init(void) {
    // gate
    SIM_SCGC5 |= SIM_SCGC5_PORTA | SIM_SCGC5_PORTB | SIM_SCGC5_PORTC | SIM_SCGC5_PORTD | SIM_SCGC5_PORTE;
    // set as gpio just D0 through D13 
    // PTA12 PTA13 PTB16 PTB17 PTC3 PTC4 PTC5 PTC6 PTC7 PTD0 PTD2 PTD3 PTD4 PTD7
    // future extension: enable all pins not used for analog or something else
    PORTA_GPCLR = (0x3000UL << 16) | PORT_PCR_MUX(1);
    PORTA_GPCHR = (0x0000UL << 16) | PORT_PCR_MUX(1);
    PORTB_GPCLR = (0x0000UL << 16) | PORT_PCR_MUX(1);
    PORTB_GPCHR = (0x0003UL << 16) | PORT_PCR_MUX(1);
    PORTC_GPCLR = (0x00F8UL << 16) | PORT_PCR_MUX(1);
    PORTC_GPCHR = (0x0000UL << 16) | PORT_PCR_MUX(1);
    PORTD_GPCLR = (0x009DUL << 16) | PORT_PCR_MUX(1);
    PORTD_GPCHR = (0x0000UL << 16) | PORT_PCR_MUX(1);
    PORTE_GPCLR = (0x0000UL << 16) | PORT_PCR_MUX(1);
    PORTE_GPCHR = (0x0000UL << 16) | PORT_PCR_MUX(1);
}

#define port(pin)  ((pin)>>5)

#define gpio_pdir(pin)	(*(volatile uint32_t *)(&GPIOA_PDIR +   (port(pin)*(&GPIOB_PDIR-&GPIOA_PDIR))))
#define port_pcr(pin)	(* \
	(  (volatile uint32_t *)(&PORTA_PCR0 +(port(pin)*(&PORTB_PCR0-&PORTA_PCR0))) \
	    + (pin &0x1F)) )
	
uint8_t pio_read(uint8_t pin) {
    return   (gpio_pdir(pin) >> (pin & 0x1F)) & 1;
}

void pio_trigger(uint8_t pin, uint8_t sense) {
    volatile uint32_t* pcr = &port_pcr(pin);
    *pcr &= ~PORT_PCR_IRQC_MASK;
    NVIC_ENABLE_IRQ(IRQ_PORTA + port(pin));
    *pcr |= PORT_PCR_ISF | PORT_PCR_IRQC(sense | 8);
}

void pio_cancel(uint8_t pin) {
    port_pcr(pin)  &= ~PORT_PCR_IRQC_MASK;
    NVIC_DISABLE_IRQ(IRQ_PORTA + port(pin));
}

void porta_isr(void) {
    PORTA_ISFR = (uint32_t) (-1); // clear all port A interrupt flags
    trigger_handler();
}
void portb_isr(void) {
    PORTB_ISFR = (uint32_t) (-1); // clear all port B interrupt flags
    trigger_handler();
}
void portc_isr(void) {
    PORTC_ISFR = (uint32_t) (-1); // clear all port C interrupt flags
    trigger_handler();
}
void portd_isr(void) {
    PORTD_ISFR = (uint32_t) (-1); // clear all port D interrupt flags
    trigger_handler();
}

//////////////////////////////////////////////////////////////
#elif PLAT_TEENSYLC

void pio_init(void) {
    // gate
    SIM_SCGC5 |= SIM_SCGC5_PORTA | SIM_SCGC5_PORTB | SIM_SCGC5_PORTC | SIM_SCGC5_PORTD | SIM_SCGC5_PORTE;
    // set as gpio just D0 through D13 
    // PTA1 PTA2 PTB16 PTB17 PTC3 PTC4 PTC5 PTC6 PTC7 PTD0 PTD2 PTD3 PTD4 PTD7

    // future extension: enable all pins not used for analog or something else
    PORTA_GPCLR = (0x0006UL << 16) | PORT_PCR_MUX(1);
    PORTA_GPCHR = (0x0000UL << 16) | PORT_PCR_MUX(1);
    PORTB_GPCLR = (0x0000UL << 16) | PORT_PCR_MUX(1);
    PORTB_GPCHR = (0x0003UL << 16) | PORT_PCR_MUX(1);
    PORTC_GPCLR = (0x00F8UL << 16) | PORT_PCR_MUX(1);
    PORTC_GPCHR = (0x0000UL << 16) | PORT_PCR_MUX(1);
    PORTD_GPCLR = (0x009DUL << 16) | PORT_PCR_MUX(1);
    PORTD_GPCHR = (0x0000UL << 16) | PORT_PCR_MUX(1);
    PORTE_GPCLR = (0x0000UL << 16) | PORT_PCR_MUX(1);
    PORTE_GPCHR = (0x0000UL << 16) | PORT_PCR_MUX(1);
}

#define port(pin)  ((pin)>>5)

#define gpio_pdir(pin)	(*(volatile uint32_t *)(&GPIOA_PDIR +   (port(pin)*(&GPIOB_PDIR-&GPIOA_PDIR))))
#define port_pcr(pin)	(* \
	(  (volatile uint32_t *)(&PORTA_PCR0 +(port(pin)*(&PORTB_PCR0-&PORTA_PCR0))) \
	    + (pin &0x1F)) )
	
uint8_t pio_read(uint8_t pin) {
    return   (gpio_pdir(pin) >> (pin & 0x1F)) & 1;
}

void pio_trigger(uint8_t pin, uint8_t sense) {
    volatile uint32_t* pcr = &port_pcr(pin);
    *pcr &= ~PORT_PCR_IRQC_MASK;
    if (port(pin)) {
	NVIC_ENABLE_IRQ(IRQ_PORTCD);
    } else {
	NVIC_ENABLE_IRQ(IRQ_PORTA );
    }
    *pcr |= PORT_PCR_ISF | PORT_PCR_IRQC(sense | 8);
}

void pio_cancel(uint8_t pin) {
    port_pcr(pin)  &= ~PORT_PCR_IRQC_MASK;
    if (port(pin)) {
	NVIC_DISABLE_IRQ(IRQ_PORTCD);
    } else {
	NVIC_DISABLE_IRQ(IRQ_PORTA );
    }
}

void porta_isr(void) {
    PORTA_ISFR = (uint32_t) (-1); // clear all port A interrupt flags
    trigger_handler();
}
void portcd_isr(void) {
    PORTC_ISFR = (uint32_t) (-1); // clear all port C interrupt flags
    PORTD_ISFR = (uint32_t) (-1); // clear all port D interrupt flags
    trigger_handler();
}


#endif

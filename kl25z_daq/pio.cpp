#include "pio.h"

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

void pio_begin(uint8_t pin, uint8_t sense) {
    volatile uint32_t* pcr = &(ctrl_ports[pin >> 5]->PCR[pin & 0x1F]);
    *pcr &= ~PORT_PCR_IRQC_MASK;
    NVIC_EnableIRQ(PORTA_IRQn);
    NVIC_EnableIRQ(PORTD_IRQn);
    *pcr |= PORT_PCR_ISF_MASK | PORT_PCR_IRQC(sense | 8);
}

void pio_stop(void) {
    NVIC_DisableIRQ(PORTA_IRQn);
    NVIC_DisableIRQ(PORTD_IRQn);
}

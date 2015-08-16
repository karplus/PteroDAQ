#include "targetlib.h"
#include "led.h"
#include "tim.h"

#if (PLAT_ATMEGA || PLAT_TEENSY31 || PLAT_TEENSYLC)

#define LED_pin (13)

void LED_start(void){
    // LED signal when board is reset
    uint64_t time;
    uint64_t flash_time;

    pinMode(LED_pin, 1); // output
    timestamp_start();
    
    // 1 second of accelerating flashes
    for (flash_time = TIMESTAMP_START_RATE/4; flash_time > 0; flash_time = flash_time>>1) {
        digitalWrite(LED_pin, 1);
        time = timestamp_get();
        while (timestamp_get() < time+flash_time);
        digitalWrite(LED_pin, 0);
        time = timestamp_get();
        while (timestamp_get() < time+flash_time);
    }
}

void LED_handshake(void){
    // LED signal on handshake
    uint64_t time;
    uint8_t i;
    
    pinMode(LED_pin, 1); // output
    timestamp_start();

    // flash 4 times
    for (i=0; i<4; i++){
        digitalWrite(LED_pin, 1);
        time = timestamp_get();
        while (timestamp_get() < time+TIMESTAMP_START_RATE/16);
        digitalWrite(LED_pin, 0);
        time = timestamp_get();
        while (timestamp_get() < time+TIMESTAMP_START_RATE/16);
    }
}

#elif PLAT_KL25Z

// red   led on PTB18 is TPM2_CH0
// green led on PTB19 is TPM2_CH1
// blue  led on PTD1  is TPM0_CH1

#define PWM_MOD (100) // 16-bit modulus value for TPM counts for PWM

#define GREEN_DUR  TPM2->CONTROLS[1].CnV
#define RED_DUR    TPM2->CONTROLS[0].CnV
#define BLUE_DUR   TPM0->CONTROLS[1].CnV

void tpm_init(void) {
    // set clock source for TMP0 and TPM2
    SIM->SOPT2 = (SIM->SOPT2 & ~SIM_SOPT2_TPMSRC_MASK) | SIM_SOPT2_TPMSRC(1);
        // set TPM clock source to MCGFLLCLK clock or MCGPLLCLK/2
    SIM->SCGC6 |= SIM_SCGC6_TPM0_MASK | SIM_SCGC6_TPM2_MASK;
        // enable TPM0 and TPM2

    // prescale=64, yields 750 kHz tick, 7500 Hz PWM
    // (prescale is 1<< precale_code)

    TPM0->MOD = PWM_MOD-1;  // reset TPM0 modulus, rate = F_CPU/prescale/MOD
    TPM2->MOD = PWM_MOD-1;  // reset TPM2 modulus, rate = F_CPU/prescale/MOD
 
    // Green LED
    PORTB->PCR[19] = PORT_PCR_MUX(3);  
    FPTB->PDDR |= 1<<19;
    GREEN_DUR = PWM_MOD/6;  // 1/6 duty cycle
    TPM2->CONTROLS[1].CnSC = TPM_CnSC_MSB_MASK | TPM_CnSC_ELSA_MASK;  // edge-aligned, active low PWM

    // Red LED
    PORTB->PCR[18] = PORT_PCR_MUX(3);  
    FPTB->PDDR |= 1<<18;
    RED_DUR = PWM_MOD/6;  // 1/6 duty cycle
    TPM2->CONTROLS[0].CnSC = TPM_CnSC_MSB_MASK | TPM_CnSC_ELSA_MASK;  // edge-aligned, active low PWM

    // Blue LED
    PORTD->PCR[1] = PORT_PCR_MUX(4);  
    FPTD->PDDR |= 1<<1;
    BLUE_DUR = PWM_MOD/6;  // 1/6 duty cycle
    TPM0->CONTROLS[1].CnSC = TPM_CnSC_MSB_MASK | TPM_CnSC_ELSA_MASK;  // edge-aligned, active low PWM

    // start timers
    TPM0->SC = TPM_SC_CMOD(1)|TPM_SC_PS(6); 
    TPM2->SC = TPM_SC_CMOD(1)|TPM_SC_PS(6);
}


void LED_start(void){
    // LED signal when board is reset
    uint64_t time;
    uint16_t i;
    tpm_init();
    timestamp_start();  // start a 64-bit timer
    
    
    RED_DUR = 0;
    GREEN_DUR=0;
    BLUE_DUR=PWM_MOD;
    
    // 0.5-second color change (blue to light blue)
    for (i = 0; i <= PWM_MOD/2; i+= PWM_MOD/50) {
        RED_DUR = i;
        GREEN_DUR = i;
        time = timestamp_get();
        while (timestamp_get() < time+ (uint64_t)(TIMESTAMP_START_RATE/50)); // 20 ms
    }
    // dim yellow
    RED_DUR= PWM_MOD/4;
    GREEN_DUR=PWM_MOD/4;
    BLUE_DUR = 0;
}

void LED_handshake(void){
    // LED signal on handshake
    uint64_t time;
    // magenta
    GREEN_DUR=0;
    BLUE_DUR = (7*PWM_MOD)/10;
    RED_DUR = (7*PWM_MOD)/10;
    timestamp_start();
    time = timestamp_get();
    while (timestamp_get() < time+(uint64_t)(TIMESTAMP_START_RATE/2)); // 500 ms
    // dim yellow
    RED_DUR= PWM_MOD/4;
    GREEN_DUR=PWM_MOD/4;
    BLUE_DUR = 0;
    
}

#endif

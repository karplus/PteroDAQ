#include "adc.h"

#if PLAT_KINETIS

static bool adc_calib(void) {
    uint16_t acc;
    PMC->REGSC |= PMC_REGSC_BGBE_MASK;
    ADC0->CFG1 = 
        ADC_CFG1_ADICLK(1) | // half bus clock
        ADC_CFG1_MODE(3) | // sixteen-bit
        ADC_CFG1_ADLSMP_MASK | // long sample
        ADC_CFG1_ADIV(2); // clock divide four
    ADC0->SC2 = ADC_SC2_REFSEL(1); // vdda reference
    ADC0->SC3 = ADC_SC3_AVGS(3) | // average thirty-two samples
        ADC_SC3_AVGE_MASK | // enable averaging
        ADC_SC3_CAL_MASK; // begin callbration
    while (ADC0->SC3 & ADC_SC3_CAL_MASK);  // wait for calibration to finish
    if (ADC0->SC3 & ADC_SC3_CALF_MASK) {
        // calibration failed
        return false;
    }
    // combine calibration results as specified in manual
    acc = ADC0->CLP0+ADC0->CLP1+ADC0->CLP2+ADC0->CLP3+ADC0->CLP4+ADC0->CLPS;
    acc >>= 1;
    acc |= 1 << 15;
    ADC0->PG = acc;
    acc = ADC0->CLM0+ADC0->CLM1+ADC0->CLM2+ADC0->CLM3+ADC0->CLM4+ADC0->CLMS;
    acc >>= 1;
    acc |= 1 << 15;
    ADC0->MG = acc;
    return true;
}

void adc_init(void) {
    SIM->SCGC6 |= SIM_SCGC6_ADC0_MASK; // clock gate enable
    adc_calib();
    // bus clock is 24MHz
    // set conversion rate at bus clock/4 with short sample times
    // That sets ADCK to 6MHz
    ADC0->CFG1 = 
        ADC_CFG1_MODE(3) | // sixteen-bit
        ADC_CFG1_ADIV(2); // clock divide four
    ADC0->CFG2 = 0;
    ADC0->SC3 &= ~ADC_SC3_AVGE_MASK; // no hardware averaging
    // Conversion time is (num_avg*(25) + 5)*4 + 5 bus clocks for single-ended
    //      (num_avg*(34) + 5)*4 + 5 bus clocks for differential
    //
    // for example, 32x single-ended: 3225 cycles or 134.4 us
}

void adc_aref(uint8_t choice) {
    ADC0->SC2 = ADC_SC2_REFSEL(choice); // 0 for external, 1 for vdda
}

void adc_avg(uint8_t choice) {
    ADC0->SC3 = choice; // 0 for 1x, 4 for 4x, 5 for 8x, 6 for 16x, 7 for 32x averaging
}

uint16_t adc_read(uint8_t mux) {
/* ADC mux values for chosen analog inputs (bit 6 = MUXSEL, bit 5 = DIFF, bits 4-0 = ADCH)
    00 E20
    03 E22
    04 E21
    07 E23
    08 B0
    09 B1
    0B C2
    0C B2
    0D B3
    0E C0
    0F C1
    17 E30
    1A Temperature
    1B Bandgap  (remember to enable PMC_REGSC[BGBE])
    1D High Reference
    1E Low Reference
    20 E20-E21 (differential)
    23 E22-E23 (differential)
    3A Temperature (differential)
    3B Bandgap (differential)  (remember to enable PMC_REGSC[BGBE])
    3D Reference (differential)
    44 E29
    45 D1
    46 D5
    47 D6
*/
    if (mux & 0x40) {
        ADC0->CFG2 |= ADC_CFG2_MUXSEL_MASK; // b channels
    } else {
        ADC0->CFG2 &= ~ADC_CFG2_MUXSEL_MASK; // a channels
    }
    ADC0->SC1[0] = mux & 0x3F;    // specify channel and start conversion
    while (!(ADC0->SC1[0] & ADC_SC1_COCO_MASK));   // wait for conversion complete
    return ADC0->R[0];   // return 16-bit value
}

#endif


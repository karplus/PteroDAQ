#include "adc.h"

#if PLAT_KL25Z

    // bus clock is F_CPU/2 
    // ADC clock need to be 2MHz-12MHz, divided down from bus clock
#if F_CPU < 4000000
     #warning "F_CPU too low for ADC  operation"
#elif F_CPU <= 24000000
    // bus clock
    #define ADC_clock_setting   (ADC_CFG1_ADICLK(0) | ADC_CFG1_ADIV(0))
#elif F_CPU <= 48000000    
   // bus clock/2
    #define ADC_clock_setting   (ADC_CFG1_ADICLK(0) | ADC_CFG1_ADIV(1))
#elif F_CPU <= 96000000    
   // bus clock/4
    #define ADC_clock_setting   (ADC_CFG1_ADICLK(0) | ADC_CFG1_ADIV(2))
#elif F_CPU <= 192000000    
   // bus clock/8
    #define ADC_clock_setting   (ADC_CFG1_ADICLK(0) | ADC_CFG1_ADIV(3))
#elif F_CPU <= 384000000    
   // (bus clock/2)/8
    #define ADC_clock_setting   (ADC_CFG1_ADICLK(1) | ADC_CFG1_ADIV(3))
#else     
     #warning "F_CPU too high for ADC  operation"
#endif

static bool adc_calib(void) {
    uint16_t acc;
    PMC->REGSC |= PMC_REGSC_BGBE_MASK;
    ADC0->CFG1 = 
        ADC_CFG1_MODE(3) | // sixteen-bit
        ADC_CFG1_ADLSMP_MASK | // long sample
	ADC_clock_setting;

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
    ADC0->CFG1 = 
        ADC_CFG1_MODE(3) | // sixteen-bit
        ADC_CFG1_ADLSMP_MASK | // long sample
        ADC_clock_setting;
    ADC0->CFG2 = 0;
    ADC0->SC3 &= ~ADC_SC3_AVGE_MASK; // no hardware averaging
    
    // Assumin 48MHz CPU, so 24MHz bus
    // Conversion time is (num_avg*(25) + 5)*2 + 5 bus clocks for single-ended
    //      (num_avg*(34) + 5)*2 + 5 bus clocks for differential
    //
    // for example, 32x single-ended: 1665 cycles or 67.3 us
}

void adc_aref(uint8_t choice) {
    ADC0->SC2 = ADC_SC2_REFSEL(choice); // 0 for external, 1 for vdda
}

void adc_avg(uint8_t choice) {
    ADC0->SC3 = choice; // 0 for 1x, 4 for 4x, 5 for 8x, 6 for 16x, 7 for 32x averaging
}

uint16_t adc_read(uint8_t mux) {
    // ADC mux values for chosen analog inputs 
    //		(bit 6 = MUXSEL, bit 5 = DIFF, bits 4-0 = ADCH)
    //  See ../daq/boards.py for where codes are actually mapped.
    if (mux & 0x40) {
        ADC0->CFG2 |= ADC_CFG2_MUXSEL_MASK; // b channels
    } else {
        ADC0->CFG2 &= ~ADC_CFG2_MUXSEL_MASK; // a channels
    }
    ADC0->SC1[0] = mux & 0x3F;    // specify channel and start conversion
    while (!(ADC0->SC1[0] & ADC_SC1_COCO_MASK));   // wait for conversion complete
    return ADC0->R[0];   // return 16-bit value
}

#elif PLAT_TEENSY31

    // bus clock is F_CPU/2 
    // ADC clock need to be 2MHz-12MHz, divided down from bus clock
#if F_CPU < 4000000
     #warning "F_CPU too low for ADC  operation"
#elif F_CPU <= 24000000
    // bus clock
    #define ADC_clock_setting   (ADC_CFG1_ADICLK(0) | ADC_CFG1_ADIV(0))
#elif F_CPU <= 48000000    
   // bus clock/2
    #define ADC_clock_setting   (ADC_CFG1_ADICLK(0) | ADC_CFG1_ADIV(1))
#elif F_CPU <= 96000000    
   // bus clock/4
    #define ADC_clock_setting   (ADC_CFG1_ADICLK(0) | ADC_CFG1_ADIV(2))
#elif F_CPU <= 192000000    
   // bus clock/8
    #define ADC_clock_setting   (ADC_CFG1_ADICLK(0) | ADC_CFG1_ADIV(3))
#elif F_CPU <= 384000000    
   // (bus clock/2)/8
    #define ADC_clock_setting   (ADC_CFG1_ADICLK(1) | ADC_CFG1_ADIV(3))
#else     
     #warning "F_CPU too high for ADC  operation"
#endif

static bool adc_calib(void) {
    uint16_t acc;
    ADC0_CFG1 = 
        ADC_CFG1_MODE(3) | // sixteen-bit
        ADC_CFG1_ADLSMP | // long sample
	ADC_clock_setting;
    
    ADC0_SC2 = ADC_SC2_REFSEL(0); // Exernal (vdda) reference
    ADC0_SC3 = ADC_SC3_AVGS(3) | // average thirty-two samples
        ADC_SC3_AVGE | // enable averaging
        ADC_SC3_CAL; // begin calibration

    ADC1_CFG1 = 
        ADC_CFG1_MODE(3) | // sixteen-bit
        ADC_CFG1_ADLSMP | // long sample
	ADC_clock_setting;
    ADC1_SC2 = ADC_SC2_REFSEL(0); // Exernal (vdda) reference
    ADC1_SC3 = ADC_SC3_AVGS(3) | // average thirty-two samples
        ADC_SC3_AVGE | // enable averaging
        ADC_SC3_CAL; // begin calibration

    while ((ADC0_SC3 & ADC_SC3_CAL)  || (ADC1_SC3 & ADC_SC3_CAL))  {}  // wait for calibration to finish
    if ((ADC0_SC3 & ADC_SC3_CALF) || (ADC1_SC3 & ADC_SC3_CALF)) {
        // calibration failed
        return false;
    }
    
    // combine calibration results as specified in manual
    acc = ADC0_CLP0+ADC0_CLP1+ADC0_CLP2+ADC0_CLP3+ADC0_CLP4+ADC0_CLPS;
    acc >>= 1;
    acc |= 1 << 15;
    ADC0_PG = acc;
    acc = ADC0_CLM0+ADC0_CLM1+ADC0_CLM2+ADC0_CLM3+ADC0_CLM4+ADC0_CLMS;
    acc >>= 1;
    acc |= 1 << 15;
    ADC0_MG = acc;

    // combine calibration results as specified in manual
    acc = ADC1_CLP0+ADC1_CLP1+ADC1_CLP2+ADC1_CLP3+ADC1_CLP4+ADC1_CLPS;
    acc >>= 1;
    acc |= 1 << 15;
    ADC1_PG = acc;
    acc = ADC1_CLM0+ADC1_CLM1+ADC1_CLM2+ADC1_CLM3+ADC1_CLM4+ADC1_CLMS;
    acc >>= 1;
    acc |= 1 << 15;
    ADC1_MG = acc;
    return true;
}

void adc_init(void) {
    PMC_REGSC |= PMC_REGSC_BGBE;
    SIM_SCGC4 |= SIM_SCGC4_VREF;	// clock gate enable for Vref
    VREF_TRM = VREF_TRM_CHOPEN | VREF_TRM_TRIM(0x20) ;	// enable chop oscillator and set trim in the middle
    VREF_SC = VREF_SC_VREFEN | VREF_SC_REGEN | VREF_SC_ICOMPEN | VREF_SC_MODE_LV(1);
    while ( ! (VREF_SC & VREF_SC_VREFST)) {}
    
    SIM_SCGC6 |= SIM_SCGC6_ADC0; // clock gate enable for ADC0
    SIM_SCGC3 |= SIM_SCGC3_ADC1; // clock gate enable for ADC1
    adc_calib();
    // bus clock is 36MHz (48MHz if overclocked)
    // set conversion rate at bus clock/8 with long sample times
    // That sets ADCK to 4.5MHz (6MHz if overclocked)
    ADC0_CFG1 = 
        ADC_CFG1_MODE(3) | // sixteen-bit
        ADC_CFG1_ADLSMP | // long sample
	ADC_clock_setting;
    ADC0_CFG2 = 0;
    ADC0_SC3 &= ~ADC_SC3_AVGE; // no hardware averaging

    ADC1_CFG1 = 
        ADC_CFG1_MODE(3) | // sixteen-bit
        ADC_CFG1_ADLSMP | // long sample
	ADC_clock_setting;
    ADC1_CFG2 = 0;
    ADC1_SC3 &= ~ADC_SC3_AVGE; // no hardware averaging

    // Assuming 72MHz CPU, so 36MHz bus and bus/4
    // Conversion time is (num_avg*(25) + 5)*4 + 5 bus clocks for single-ended
    //      (num_avg*(34) + 5)*4 + 5 bus clocks for differential
    //
    // for example, 32x single-ended: 3225 cycles or 89.6us/conversion 
}

void adc_aref(uint8_t choice) {
    ADC0_SC2 = ADC_SC2_REFSEL(choice); // 0 for external(Vdda), 1 for 1.2V
    ADC1_SC2 = ADC_SC2_REFSEL(choice); // 0 for external(Vdda), 1 for 1.2V
}

void adc_avg(uint8_t choice) {
    ADC0_SC3 = choice; // 0 for 1x, 4 for 4x, 5 for 8x, 6 for 16x, 7 for 32x averaging
    ADC1_SC3 = choice; // 0 for 1x, 4 for 4x, 5 for 8x, 6 for 16x, 7 for 32x averaging
}

uint16_t adc_read(uint8_t mux) {
// ADC mux values for chosen analog inputs 
//	bit 7 ADC1=1, ADC0=0, 
//	bit 6 = MUXSEL (0=a channels, 1=b channels), 
//	bit 5 = DIFF, 
//	bits 4-0 = ADCH)
// (see ../daq/boards.py for where codes are actually mapped)

    if (mux & 0x80) {
	if (mux & 0x40) {
	    ADC1_CFG2 |= ADC_CFG2_MUXSEL; // b channels
	} else {
	    ADC1_CFG2 &= ~ADC_CFG2_MUXSEL; // a channels
	}
	ADC1_SC1A = mux & 0x3F;    // specify channel and start conversion
	while (!(ADC1_SC1A & ADC_SC1_COCO));   // wait for conversion complete
	return ADC1_RA;   // return 16-bit value
    } else {
	if (mux & 0x40) {
	    ADC0_CFG2 |= ADC_CFG2_MUXSEL; // b channels
	} else {
	    ADC0_CFG2 &= ~ADC_CFG2_MUXSEL; // a channels
	}
	ADC0_SC1A = mux & 0x3F;    // specify channel and start conversion
	while (!(ADC0_SC1A & ADC_SC1_COCO));   // wait for conversion complete
	return ADC0_RA;   // return 16-bit value
    }
}

/////////////////////////////////////////
#elif PLAT_TEENSYLC

    // bus clock is F_CPU/2 
    // ADC clock need to be 2MHz-12MHz, divided down from bus clock
#define ADC_clock_setting ADC_CFG1_ADIV(1) // clock divide two
#if F_CPU < 4000000
     #warning "F_CPU too low for ADC  operation"
#elif F_CPU <= 24000000
     #define ADC_clock_setting ADC_CFG1_ADIV(0) // clock divide one
#elif F_CPU <= 48000000    
    #define ADC_clock_setting ADC_CFG1_ADIV(1) // clock divide two
#elif F_CPU <= 96000000    
    #define ADC_clock_setting ADC_CFG1_ADIV(2) // clock divide four
#elif F_CPU <= 192000000    
    #define ADC_clock_setting ADC_CFG1_ADIV(3) // clock divide four
#else     
     #warning "F_CPU too high for ADC  operation"
#endif

static bool adc_calib(void) {
    uint16_t acc;
    ADC0_CFG1 = 
        ADC_CFG1_MODE(3) | // sixteen-bit
        ADC_CFG1_ADLSMP | // long sample
	ADC_clock_setting;
    ADC0_SC2 = ADC_SC2_REFSEL(1); // vdd) reference
    ADC0_SC3 = ADC_SC3_AVGS(3) | // average thirty-two samples
        ADC_SC3_AVGE | // enable averaging
        ADC_SC3_CAL; // begin calibration

    while (ADC0_SC3 & ADC_SC3_CAL)  {}  // wait for calibration to finish
    if (ADC0_SC3 & ADC_SC3_CALF) {
        // calibration failed
        return false;
    }
    
    // combine calibration results as specified in manual
    acc = ADC0_CLP0+ADC0_CLP1+ADC0_CLP2+ADC0_CLP3+ADC0_CLP4+ADC0_CLPS;
    acc >>= 1;
    acc |= 1 << 15;
    ADC0_PG = acc;
    acc = ADC0_CLM0+ADC0_CLM1+ADC0_CLM2+ADC0_CLM3+ADC0_CLM4+ADC0_CLMS;
    acc >>= 1;
    acc |= 1 << 15;
    ADC0_MG = acc;

    return true;
}

void adc_init(void) {
    PMC_REGSC |= PMC_REGSC_BGBE;
    SIM_SCGC6 |= SIM_SCGC6_ADC0; // clock gate enable for ADC0
    adc_calib();
    ADC0_CFG1 = 
        ADC_CFG1_MODE(3) | // sixteen-bit
     	ADC_CFG1_ADLSMP | // long sample
		ADC_clock_setting;
    ADC0_CFG2 = 0;
    ADC0_SC3 &= ~ADC_SC3_AVGE; // no hardware averaging

    // Assuming 48MHz clock, so 24MHz bus clock, divide by 2
    // Conversion time is (num_avg*(25) + 5)*2 + 5 bus clocks for single-ended
    //      (num_avg*(34) + 5)*2 + 5 bus clocks for differential
    //
    // for example, 32x single-ended: 1615 cycles or 67.3us/conversion
}

void adc_aref(uint8_t choice) {
    ADC0_SC2 = ADC_SC2_REFSEL(choice); // 0 for external, 1 for Vdda
}

void adc_avg(uint8_t choice) {
    ADC0_SC3 = choice; // 0 for 1x, 4 for 4x, 5 for 8x, 6 for 16x, 7 for 32x averaging
}

uint16_t adc_read(uint8_t mux) {
// ADC mux values for chosen analog inputs 
//	bit 6 = MUXSEL (0=a channels, 1=b channels), 
//	bit 5 = DIFF, 
//	bits 4-0 = ADCH)
// (see ../daq/boards.py for where codes are actually mapped)

    if (mux & 0x40) {
	ADC0_CFG2 |= ADC_CFG2_MUXSEL; // b channels
    } else {
	ADC0_CFG2 &= ~ADC_CFG2_MUXSEL; // a channels
    }
    ADC0_SC1A = mux & 0x3F;    // specify channel and start conversion
    while (!(ADC0_SC1A & ADC_SC1_COCO));   // wait for conversion complete
    return ADC0_RA;   // return 16-bit value
}
#endif


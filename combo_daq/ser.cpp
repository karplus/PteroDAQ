extern "C" {
    #include "ser.h"
}

#if PLAT_ATMEGA

extern "C" {

void ser_init(void) {
    Serial.begin(500000);
    while (!Serial); // wait for connection (32u4 only)
}

bool serc_readable(void) {
    return Serial.available() != 0;
}

void ser_putc(uint8_t c) {
    Serial.write(c);
}

uint8_t ser_getc(void) {
    while (!Serial.available()) ;
    return Serial.read();
}

}

#elif PLAT_KINETIS

#include "USBSerial.h"

static USBSerial _comm;

extern "C" {

void ser_init(void) {
    ;
}

bool ser_readable(void) {
    return _comm.readable();
}

void ser_putc(uint8_t c) {
    _comm.putc(c);
}

uint8_t ser_getc(void) {
    return _comm.getc();
}

}

#endif



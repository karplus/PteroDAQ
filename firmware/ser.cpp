extern "C" {
#include "ser.h"
}

#if PLAT_ATMEGA
#include "HardwareSerial.h"
#elif PLAT_TEENSY31
#include "usb_serial.h"
#endif

#if (PLAT_ATMEGA || PLAT_TEENSY31)

extern "C" {
#define MAX_PACKET_SIZE (64)
uint8_t ser_buffer[MAX_PACKET_SIZE];
uint8_t ser_buffer_used=0;

void ser_init(void) {
    Serial.begin(1000000); // 1Mbaud (fastest reliable Arduino UART speed)
    while (!Serial); // wait for connection (32u4 only)
    ser_buffer_used=0;
}

bool ser_readable(void) {
    return Serial.available() != 0;
}

void ser_putc(uint8_t c) {
   ser_buffer[ser_buffer_used++] = c;
   if (ser_buffer_used >=MAX_PACKET_SIZE-1){
       ser_flushout();
   }
}

uint8_t ser_getc(void) {
    while (!Serial.available()) ;
    return Serial.read();
}

void ser_flushout(void) {
    Serial.write(ser_buffer, ser_buffer_used);
    ser_buffer_used=0;
}

}

#elif PLAT_KL25Z

#include "USBSerial.h"

// TO DO:
//   Consider using non-blocking USB send and doing busy-wait before starting new packet,
//      rather than using blocking USB send.  Currently the MBED USBSerial stack doesn't seem to
//      to use the double-buffering built into the KL25Z USB interface, though, which could make
//      it messier to use non-blocking output.

static USBSerial _comm(0x1d50, 0x60cb);

extern "C" {

uint8_t ser_buffer[MAX_PACKET_SIZE_EPBULK];
uint16_t ser_buffer_used=0;

void ser_init(void) {
    ser_buffer_used=0;
}

bool ser_readable(void) {
    return _comm.readable();
}

void ser_putc(uint8_t c) {
   ser_buffer[ser_buffer_used++] = c;
   if (ser_buffer_used >=MAX_PACKET_SIZE_EPBULK-1){
       ser_flushout();
   }
}

uint8_t ser_getc(void) {
    return _comm.getc();
}

void ser_flushout(void) {
    _comm.writeBlock(ser_buffer, ser_buffer_used);
    // Note: send waits for completion of sending buffer, so this could take a while.
    ser_buffer_used=0;
    return;
}
}

#endif



#include "mbed.h"
#include "USBSerial.h"

extern "C" {
#include "queue.h"
}

#include "pit.h"
#include "adc.h"
#include "syst.h"
#include "pio.h"

/* PROTOCOL
message format: '!' + command + length + data + checksum
command: 1 byte for message meaning
length: 1 byte for length of data only (required even if zero)
data: array of bytes, interpretation depends on command
checksum: 1 byte such that modulo 256 sum of entire msg (including '!', command, length, and checksum) is zero

commands:
C config
H handshake (reset)
V version
G go
S stop
I individual read
M model info

report format: '*' + length + data + checksum
length: 1 byte for length of data only
data: array of bytes
checksum: 1 byte such that modulo 256 sum of entire msg (including '*', length, and checksum) is zero
*/


#define MSG(x) (x), (sizeof(x)-1)
#define NOMSG (NULL), (0)

#define sendchar(x) (comm.putc(x))

USBSerial comm;

PwmOut led_red(PTB18);
PwmOut led_green(PTB19);
PwmOut led_blue(PTD1);

struct Config {
    uint8_t trigtype;
    uint8_t trigprescale;
    uint32_t trigreload;
    uint8_t trigintsense;
    uint8_t trigintpin;
    uint8_t arefchoice;
    uint8_t avgana;
    uint8_t channelcount;
    uint8_t channeltypes[64];
    uint8_t channelchoices[64];
} conf;

uint8_t buf[128];
uint8_t cmd = 'H';
uint8_t datalen;

int8_t readcmd(void);
void parseconfig(uint8_t len);
void sendresp(const uint8_t* msg, uint8_t len);
void outputdata(void);
void startrunning(void);
void stoprunning(void);
void recorddata(void);



int main(void) {
    uint64_t pt;
    uint8_t i;
    led_red.period_ms(1);
    //led_red.pulsewidth_ms(10);
    led_green.period_ms(1);
    //led_green.pulsewidth_ms(10);
    led_blue.period_ms(1);
    led_blue = 1;

    adc_init();
    pit_init();
    pio_init();
    __enable_irq();
    
    for (i = 50; i <= 100; i++) {
        led_red = i/100.;
        led_green = i/100.;
        pt = pit_time();
        while (pit_time() < pt+480000); // 20 ms
    }
    led_red = 1;
    led_green = 1;
    led_blue = 0.7;
    
    // send handshake message
    sendresp(MSG("DAQ"));
    
    for (;;) {
        if (comm.readable()) {
            int8_t len = readcmd();
            if (len == -1) {
                continue;
            }
            switch (cmd) {
                case 'V':
                    sendresp(MSG("mbeta1"));
                    break;
                case 'C':
                    parseconfig(len);
                    sendresp(NOMSG);
                    break;
                case 'G':
                    startrunning();
                    sendresp(NOMSG);
                    break;
                case 'S':
                    stoprunning();
                    sendresp(NOMSG);
                    break;
                case 'I':
                    recorddata();
                    sendresp(NOMSG);
                    break;
                case 'H':
                    stoprunning();
                    queue_clear();
                    sendresp(MSG("DAQ"));
                    led_red = 0.7;
                    pt = pit_time();
                    while (pit_time() < pt+12000000); // 500 ms
                    led_red = 1;
                    break;
                case 'M':
                    adc_aref(1);
                    uint16_t bandgap_read = adc_read(0x1B);
                    uint8_t mresp[4];
                    mresp[0] = 5;
                    mresp[1] = 0;
                    mresp[2] = bandgap_read & 0xFF;
                    mresp[3] = bandgap_read >> 8;
                    sendresp(mresp, 4);
                    break;
            }
        }
        outputdata();
    }
}

int8_t readcmd(void) {
    uint8_t start, len, chk, ind;
    start = comm.getc();
    if (start != '!') {
        return -1;
    }
    cmd = comm.getc();
    len = comm.getc();
    chk = start + cmd + len;
    if (len > 64) {
        return -1;
    }
    for (ind = 0; ind < len; ind++) {
        buf[ind] = comm.getc();
        chk += buf[ind];
    }
    chk += comm.getc();
    if (chk) {
        return -1;
    }
    return len;
}

void parseconfig(uint8_t len) {
    uint8_t ind = 0, chnum = 0, digcount = 0;
    datalen = 8;
    // trigger
    conf.trigtype = buf[ind++];
    if (conf.trigtype == 1) { // timed
        conf.trigprescale = buf[ind++];
        conf.trigreload = buf[ind++];
        conf.trigreload |= buf[ind++] << 8;
        conf.trigreload |= buf[ind++] << 16;
    } else if (conf.trigtype == 2) { // pinchange
        conf.trigintsense = buf[ind++];
        conf.trigintpin = buf[ind++];
    }
    // aref
    conf.arefchoice = buf[ind++];
    conf.avgana = buf[ind++];
    // channels
    while (ind < len) {
        conf.channeltypes[chnum] = buf[ind++];
        if (conf.channeltypes[chnum] == 1) { // analog
            datalen += 2;
        } else if (conf.channeltypes[chnum] == 2) { // digital
            digcount += 1;
        }
        conf.channelchoices[chnum++] = buf[ind++];
    }
    conf.channelcount = chnum;
    datalen += (digcount + 7)/8;
}

void sendresp(const uint8_t* msg, uint8_t len) {
    uint8_t chk, ind;
    chk = '!' + cmd + len;
    sendchar('!');
    sendchar(cmd);
    sendchar(len);
    for (ind = 0; ind < len; ind++) {
        sendchar(msg[ind]);
        chk += msg[ind];
    }
    sendchar(-chk);
}

void outputdata(void) {
    if (queue_avail()) {
        uint8_t len = datalen;//queue_pop();
        uint8_t chk = '*' + len;
        sendchar('*');
        sendchar(len);
        while (len--) {
            uint8_t dat = queue_pop();
            sendchar(dat);
            chk += dat;
        }
        sendchar(-chk);
    }
}

void startrunning(void) {
    adc_aref(conf.arefchoice);
    adc_avg(conf.avgana);
    if (conf.trigtype == 1) {
        syst_trigger(conf.trigprescale, conf.trigreload);
    } else if (conf.trigtype == 2) {
        pio_begin(conf.trigintpin, conf.trigintsense);
    }
}

void stoprunning(void) {
    syst_stop();
    pio_stop();
}

void recorddata(void) {
    uint8_t ind;
    if (queue_space() < datalen) {
        return;
    }
    // get timestamp
    queue_push64(pit_time());
    // for each channel
    for (ind = 0; ind < conf.channelcount; ind++) {
        // record, push to queue
        if (conf.channeltypes[ind] == 1) { // analog
            queue_push16(adc_read(conf.channelchoices[ind]));
        } else if (conf.channeltypes[ind] == 2) { // digital
            queue_push1(pio_read(conf.channelchoices[ind]));
        }
    }
    queue_aggregate_bits();
}

extern "C" {

void SysTick_Handler(void) {
    recorddata();
}

void PORTA_IRQHandler(void) {
    PORTA->ISFR = (uint32_t) (-1); // clear all port A interrupt flags
    recorddata();
}

void PORTD_IRQHandler(void) {
    PORTD->ISFR = (uint32_t) (-1); // clear all port D interrupt flags
    recorddata();
}

}
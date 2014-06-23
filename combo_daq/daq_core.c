#include "adc.h"
#include "pio.h"
#include "queue.h"
#include "ser.h"
#include "tim.h"

#define DAQ_VERSION "beta2"
#define HANDSHAKE_CODE "DAQ"

uint8_t datalen;

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


void daq_setup(void) {
    adc_init();
    pio_init();
    ser_init();
    // TODO other startup code
}

void trigger_handler(void) {
    uint8_t ind;
    if (queue_space() < datalen) {
        return;
    }
    // get timestamp
    queue_push64(tim_time()); // TODO: not always valid (atmega)
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

void parse_config(uint8_t buf[], uint8_t len) {
    uint8_t ind = 0, chnum = 0, digcount = 0;
    datalen = 8;
    // trigger
    conf.trigtype = buf[ind++];
    if (conf.trigtype == 1) { // timed
        conf.trigprescale = buf[ind++];
        conf.trigreload = buf[ind++];
        conf.trigreload |= buf[ind++] << 8;
        conf.trigreload |= buf[ind++] << 16;
        conf.trigreload |= buf[ind++] << 24;
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

void start_running(void) {
    adc_aref(conf.arefchoice);
    adc_avg(conf.avgana);
    if (conf.trigtype == 1) {
        tim_trigger(conf.trigprescale, conf.trigreload);
    } else if (conf.trigtype == 2) {
        pio_trigger(conf.trigintpin, conf.trigintsense);
    }
}

void stop_running(void) {
    tim_cancel();
    pio_cancel();
}

void handle_command(void) {
    uint8_t start, len, chk, ind, cmd;
    uint8_t buf[64];
    uint8_t* resp = NULL;
    uint8_t resplen = 0;
    
    start = ser_getc();
    if (start != '!') {
        return;
    }
    cmd = ser_getc();
    len = ser_getc();
    chk = start + cmd + len;
    if (len > 64) {
        return;
    }
    for (ind = 0; ind < len; ind++) {
        buf[ind] = ser_getc();
        chk += buf[ind];
    }
    chk += ser_getc();
    if (chk) {
        return;
    }
    
    switch (cmd) {
        case 'V':
            resp = DAQ_VERSION;
            resplen = sizeof(DAQ_VERSION) - 1;
            break;
        case 'C':
            parse_config(buf, len);
            break;
        case 'G':
            start_running();
            break;
        case 'S':
            stop_running();
            break;
        case 'I':
            trigger_handler();
            break;
        case 'H':
            stop_running();
            queue_clear();
            resp = HANDSHAKE_CODE;
            resplen = sizeof(HANDSHAKE_CODE) - 1;
            // TODO indicate connection with LED
            break;
        case 'M':
            // TODO model info
            break;
        default:
            return;
    }
    
    chk = '!' + cmd + resplen;
    ser_putc('!');
    ser_putc(cmd);
    ser_putc(resplen);
    for (ind = 0; ind < resplen; ind++) {
        ser_putc(resp[ind]);
        chk += resp[ind];
    }
    ser_putc(-chk);
}

void output_data(void) {
    if (queue_avail()) {
        uint8_t len = datalen;
        uint8_t chk = '*' + len;
        ser_putc('*');
        ser_putc(len);
        while (len--) {
            uint8_t dat = queue_pop();
            ser_putc(dat);
            chk += dat;
        }
        ser_putc(-chk);
    }
}

void daq_loop(void) {
    if (ser_readable()) {
        handle_command();
    }
    output_data();
}


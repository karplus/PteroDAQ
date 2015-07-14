#include "adc.h"
#include "pio.h"
#include "queue.h"
#include "ser.h"
#include "tim.h"
#include "LED.h"

#define DAQ_VERSION "beta2"
#define HANDSHAKE_CODE "DAQ"

//  PROTOCOL
// Every command communication consists of a command from the host
//	computer followed by a response from the microcontroller board.
// All commands except 'G' (for "go") result in a single response packet.
// 'G' results in a stream of response packets (one per triggering) until
// 'S' (for "stop") is sent.
//
//  command format: '!' + command + length + data + checksum
//    command: 1 byte for message meaning
//    length: 1 byte for length of data only (required even if zero)
//    data: array of bytes, interpretation depends on command
//    checksum: 1 byte such that modulo 256 sum of entire msg
//	(including '!', command, length, and checksum) is zero
//  
//  commands:
//  C config
//  H handshake (reset)
//  V version
//  G go
//  S stop
//  I individual read
//  M model info
//  
//  responses format: '*' + length + data + checksum
//  length: 1 byte for length of data only
//  data: array of bytes
//  checksum: 1 byte such that modulo 256 sum of entire msg (including '*', length, and checksum) is zero



uint8_t datalen;

struct Config {
    uint8_t trigtype; // 1 means timer, 2 means wait for pin change,  
    uint8_t flush_every;   // nonzero means flsuh after every data packet
    uint8_t trigprescale;  // code for prescale for timer clock
    uint32_t trigreload;   // counter value for resetting counter
    uint8_t trigintsense;  // Code for rise/fall/change (board-specific meanings)
    uint8_t trigintpin;	   // pin number for trigger
    uint8_t arefchoice;
    uint8_t avgana;
    uint8_t channelcount;
    uint8_t channeltypes[64];
    uint8_t channelchoices[64];
} conf;

#define TRIG_FLUSH_EVERY (0x10)  // bit in trigtype to require flush after every data packet

volatile uint16_t trigger_error_count;   
    // increment if there is a pending trigger at the end of trigger handler
    
// TO DO:

void daq_setup(void) {
    adc_init();
    pio_init();
    ser_init();
    LED_start();
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
        if (conf.flush_every){
            ser_flushout();
        }
    }
}

// report an error with code, and optionally, up to 254 extra bytes of data
void report_error(uint8_t code, uint8_t extra_len, uint8_t *extra_data){
	// report an error by sending an error packet
	uint8_t chk = '!' + 'E'+extra_len+1+code;
	ser_putc('!');
	ser_putc('E');
	ser_putc(extra_len+1);
	ser_putc(code);
	uint8_t index;
	for(index=0; index<extra_len; index++){
		ser_putc(extra_data[index]);
		chk += extra_data[index];
	}
	ser_putc(-chk);
	ser_flushout();  // always flush after error messages
	
}
	
static volatile uint32_t readcount = 0;
// record timestamp and channels for one trigger into queue
void trigger_handler(void) {
    uint8_t ind;
    readcount++;
    if (queue_space() < datalen) {
        return;
    }
    // get timestamp
    if (conf.trigtype == 1) {
        queue_push32(readcount-1);
    } else {
        queue_push64(tim_time());
    }
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
    if (tim_pending()){
    	trigger_error_count++;
    }
}

void parse_config(uint8_t buf[], uint8_t len) {
    uint8_t ind = 0, chnum = 0, digcount = 0;
    // trigger
    conf.trigtype = buf[ind++];
    conf.flush_every = conf.trigtype & TRIG_FLUSH_EVERY;
    conf.trigtype &= ~TRIG_FLUSH_EVERY;
    if (conf.trigtype == 1) { // timed
        conf.trigprescale = buf[ind++];
        conf.trigreload = buf[ind++];
        conf.trigreload |= buf[ind++] << 8;
        conf.trigreload |= (uint32_t) buf[ind++] << 16;
        conf.trigreload |= (uint32_t) buf[ind++] << 24;
        datalen = 4;
    } else if (conf.trigtype == 2) { // pinchange
        conf.trigintsense = buf[ind++];
        conf.trigintpin = buf[ind++];
        datalen = 8;
    } else {
    	report_error(0x2,1,&(conf.trigtype));  //trigger type not recognized
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
    trigger_error_count = 0;
    if (conf.trigtype == 1) {
	    readcount=0;	// restart the timer at 0,
			// since timer wasn't runing while the data 
			// not being recorded.
	    tim_trigger(conf.trigprescale, conf.trigreload);
    } else if (conf.trigtype == 2) {
        tim_watch();	// restart the timer at 0
        pio_trigger(conf.trigintpin, conf.trigintsense);
    } else {
    	report_error(0x2,1,&(conf.trigtype));  //trigger type not recognized
    }
}

void stop_running(void) {
    tim_cancel();
    pio_cancel();
    while (queue_avail()) {
    	// empty the queue
    	output_data();
    }
    ser_flushout();
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
	    LED_handshake();
            resp = HANDSHAKE_CODE;
            resplen = sizeof(HANDSHAKE_CODE) - 1;
            break;
        case 'M':
            resp = get_model();
            resplen = MODEL_INFO_LEN;
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
    ser_flushout();
}

void daq_loop(void) {
    if (ser_readable()) {
        handle_command();
    }
    if ((trigger_error_count & 0x3FF)==1){
    	// Every 1024 trigger errors (trigger handler too slow),
    	// report triggering error 
    	report_error(0x1, 0, NULL); 
    }
    output_data();
}


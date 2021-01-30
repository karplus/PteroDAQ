from __future__ import division, print_function, unicode_literals

import sys
import struct
from datetime import datetime
from collections import namedtuple
from math import sqrt
import codecs
try:
    from future_builtins import zip
except ImportError:     # either before Python2.6 or one of the Python 3.*
    try:
        from itertools import izip as zip
    except ImportError: # not an early Python, so must be Python 3.*
        pass

from comm import CommPort, tobytes, tostr
from boards import getboardinfo

firmware_version = b'v0.3' # code used in firmware to identify protocol version

#  PROTOCOL
# Every command communication consists of a command from the host
#       computer followed by a response from the microcontroller board.
# Most commands result in a single response packet.
# Exceptions:
# 'G' results in a stream of data packets (one per triggering) until
#       'S' (for "stop") is sent.
# 'S' may result in two stop responses (final one after queue has emptied)
#
#  command format: '!' + command + length + data + checksum
#    command: 1 byte for message meaning
#    length: 1 byte for length of data only (required even if zero)
#    data: array of bytes, interpretation depends on command
#    checksum: 1 byte such that modulo 256 sum of entire msg
#       (including '!', command, length, and checksum) is zero
#
#  For most commands, the response is a packet in the same format:
#       '!' + command + length + data + checksum
#  with the command byte in the response being the same as in
#  the command being responded to.
#
#  Data response format after 'G' or 'I' commands have a different format
#        '*' + len+ Timestamp + data + checksum
#       len is number of bytes in (timestamp+data)
#       Timestamp is 4-byte serial number (in timed trigger) or
#               8-byte time in F_CPU ticks (in interrupt trigger)
#       data: array of bytes
#       checksum: 1 byte such that modulo 256 sum of entire packet
#               (including '*', len, timestamp, data, and checksum) is zero
#
#	Note: the ordering of channels is set by the configuration command,
#	as the firmware pushes each channel on the queue as it gets to it,
#	except for digital channels that are pushed on the queue every time
#	8 channels have accumulated (plus any leftovers at the end).
#
#	Frequency channels are sent as 4 bytes each, low-order first), 
#		with count of number of rising edges observed since previous sample.
#       Analog channels are sent as 2 bytes each, low-order first).
#       Digital channels are sent packed 8-channels per byte
#       	with ith digital channel in (1<<(i-1))
#
#  The board can also report an Error with an E packet:
#       '!E' + len + message + chk
#  The error message must be at least 1 byte, starting with an error code.
#       Codes:
#       1       The interrupt handler had an interrupt pending
#               when the handler ended---too fast a sampling rate
#               or edge triggers too close together.
#  
#  Commands that have no data argument, so are !+command+0+checksum:
#      H handshake (reset)
#          response should always be ! H 0x03 D A Q 0xbe
#      V version
#          response should always be version of software (e.g., 'beta2'):
#          ! V 0x5 b e t a 2 0xb6
#      M model info
#          response should be the board model (one of the names recognized by
#      S stop
#          response should be ! S 0x00 0x8C
#      I individual read
#          forces single triggger event, generating single data packet
#      G go
#          starts interrupts (based on previously sent configuration)
#          and sends data packets until stopped by 'S' command.
#
#
# Commands that send information to the boards
#      C config sends the following data:
#         Trigger information:
#           1, clock_prescale(1 byte),clock_value (4 bytes)       for timed trigger
#           2, trigger_sense (1 byte board-specific code for rise/fall/change),trigger_pin (1 byte)
#           Add 0x10 to first byte to require a serial flush after each data packet (so 0x11 for timed, 0x12 for external trigger)
#         Analog reference code (1-byte, board specific)
#         Code for hardware averaging (1-byte, board-specific)
#         2-byte probe number for each channel
#               low-order byte encodes analog=1,digital=2,frequency=3
#               high-order byte encodes mux value for analog or pin for digital
#

# TO DO:
#       Consider changing response to "!S" so that stop responds with information
#          about how much of queue remains to be emptied?
#
#       Consider change to data packets when running timed triggers to use
#          same time format as edge-triggered packets.  Could be used to
#          get real time of interrupts on boards with enough timing counters.
#
#	Change Hardware averaging code to be a per-channel choice, rather than shared by all analog channels.
#
#       Consider changing trigger_error to allow list of errors        
#
#       Reduce the number of error messages to console when packets are damaged.




class Interpretation(namedtuple('Interpretation', 
                ['is_analog', 'is_signed', 'is_frequency', 'downsample', 'gain'])):
    """ information needed for interpreting a data stream
    is_analog: (Boolean) treat as an analog value, rather than digital input
    is_signed: (Boolean) treat as 2's-complement, rather than unsigned value
    is_frequency: (Boolean) treat as a frequency rather than analog or digital value
    downsample: (int) keep only every nth value if downsample==n
    gain: divide read value down by gain to compensate for hardware amplifier
    """

class ChannelDescriptor(namedtuple('ChannelDescriptor',
                ['name', 'probe', 'interpretation'])):
    """provides all the information needed about a channel
    to send configuration strings to a DAQ board and
    interpret the returned data stream.
    
    name: string used for annotating saved data 
    probe: analog mux value or digital pin number, already encoded
        for sending to boards
    interpretation: see Interpretation class above
    """
    def volts(self,raw_value, aref):
        return raw_value/65536.*aref/self.interpretation.gain

class TriggerTimed(object):
    def __init__(self, period):
        self.period = period    # period in seconds
class TriggerPinchange(object):
    def __init__(self, pin, sense):
        self.pin, self.sense = pin, sense

class DataAcquisition(object):
    def __init__(self):
        self._data = []
        self.num_saved = 0      # how long was self._data when self.save() was last run
        self._timeoffset = None         # timestamp of first data packet received (sets 0 time)
        self.trigger_error=None         # error message to display on gui for triggering errors
    
    def is_timed_trigger(self):
        return self.conf and isinstance(self.conf[0], TriggerTimed)
    
    def connect(self, port, call_when_done):
        """non-blocking attempt to connect to DAQ at port
        Failing connection will call call_when_done with a string error message.
        Successful connection will call call_when_done with None.
        """
#        print('DEBUG: enter daq.connect', file=sys.stderr)
        self._conncall = call_when_done
        self.comm = CommPort(port, self._parsedata, self._onconnect, self._onerror)
        self.comm.connect()
    def go(self):
        self.trigger_error=None
        self.data_length_before_go = len(self._data)
#        print("DEBUG: starting with", self.data_length_before_go, "packets",file=sys.stderr)
        self.comm.command(b'G')
    def oneread(self):
        self.trigger_error=None
        self.data_length_before_go = 0 # 'I' command doesn't reset pseudo-timer
        self.comm.command(b'I')
    def stop(self):
        self.comm.command(b'S')
        # redo the setup to remeasure supply voltage
        model = self.comm.command(b'M')
        self.board.setup(model[2:])
    def config(self, conf):
        confsend = bytearray()
        trigger, aref, avg, channels = conf
#        print('DEBUG: conf=', conf, file=sys.stderr)
        if  hasattr(self,'channels') and len(self.channels) != len(channels):
            self.clear()        # new config means old data is unusable
        self.channels = channels
        num_analog = sum(1 for ch in channels if ch.interpretation.is_analog)
        num_frequency = sum(1 for ch in channels if ch.interpretation.is_frequency)
        num_digital = len(channels)-num_analog-num_frequency
        if isinstance(trigger, TriggerTimed):
            data_packet_length = 7 + 2*num_analog + (num_digital+7)//8
            bytes_per_sec =  (1./trigger.period)*data_packet_length
            buffer_per_sec = bytes_per_sec/63
            force_flush = 0x10 if buffer_per_sec < 20 else 0
            trigger.period, (clkdiv, clkval) = self.board.timer_calc(trigger.period)
#            print("DEBUG: clkdiv=",clkdiv, "clkval=",clkval, file=sys.stderr)
            confsend.extend(struct.pack(b'<BBL', force_flush | 1, clkdiv, clkval))
        elif isinstance(trigger, TriggerPinchange):
            sense = next(x[1] for x in self.board.intsense if x[0] == trigger.sense)
            pin = next(x[1] for x in self.board.eint if x[0] == trigger.pin)
            force_flush =0x10   # always force flush---don't know when next pin interrupt will be
            confsend.extend(struct.pack(b'<BBB', force_flush | 2, sense, pin))
        arefnum = next(x[1] for x in self.board.aref if x[0] == aref)
        confsend.append(arefnum)
        if not avg:
            avg = self.board.default_avg
        confsend.append(next(x[1] for x in self.board.avg if x[0] == avg))
        for ch in channels:
            probe = ch.probe
            confsend.append(probe& 0xff)
            confsend.append(probe >> 8)
        self.conf = conf
#        print('DEBUG: confsend', confsend, file=sys.stderr)
        self.comm.command(b'C', bytes(confsend))
    
    def data(self):
        return self._data
    def clear(self):
        self._data = []
        self._timeoffset = None
        self.trigger_error=""
        self.num_saved=0
    def save(self, fn, notes, convvolts, new_conf):
        """save the stored date into file named fn
                adding notes to the metadata header.
           If convvolts is true, scale by board.power_voltage
              to report measurements in volts.
        """
        if hasattr(self,'conf') and self.conf:
            use_conf=self.conf
        else:
            # configuration never done, probably because no data recorded yet
            use_conf=new_conf
        
        eol = '\r\n' if sys.platform=='win32' else '\n'
        
        scale = self.board.power_voltage / 65536.
        with codecs.open(fn, 'w', 'utf-8') as f:
            f.write('# PteroDAQ recording{}'.format(eol))
            f.write('# saved at {0:%Y %b %d %H:%M:%S}{1}'.format(datetime.now(),eol))
            if len(self.board.names)>1:
                f.write('# board is one of {0}{1}'.format( ", ".join(self.board.names),eol))
            else:
                f.write('# board is {0}{1}'.format(self.board.names[0],eol))
            if isinstance(use_conf[0], TriggerTimed):
                f.write('# Recording every {0} sec ({1} Hz){2}'.format(use_conf[0].period, 1./use_conf[0].period,eol))
            elif isinstance(use_conf[0], TriggerPinchange):
                f.write('# Recording when {0} {1}{2}'.format(use_conf[0].pin, use_conf[0].sense,eol))
            f.write('# Analog reference is {0}{1}'.format(use_conf[1],eol))
            if use_conf[2] != 1:
                f.write('# Averaging {0} readings together{1}'.format(use_conf[2],eol))
            f.write('# Power supply is {0:.4f} volts'.format(self.board.power_voltage,eol))
            if convvolts:
                f.write('# Scale: 0 to {0:.4f} volts{1}'.format(self.board.power_voltage,eol))
            else:
                f.write('# Scale: 0 to 65535{0}'.format(eol))
            f.write('# Notes:{}'.format(eol))
            for ln in notes.split('\n'):
                f.write('#   {0}{1}'.format(ln,eol))
            x0 = len(self._data)
            f.write('# {0} samples{1}'.format(x0,eol))

            f.write('# Recording channels:{}'.format(eol))
            f.write('#   timestamp (in seconds){}'.format(eol))
            # Use passed-in configuration for names, rather than the ones saved
            # but use saved for probes and downsampling
            # Note that channels is the last field of the configuration tuple.
            for chan_num,(ch_name,ch_probe) in enumerate(zip(new_conf[-1],use_conf[-1])):
                downsample = ch_probe.interpretation.downsample
                if downsample>1:
                    f.write('#   {0} : {1} downsample by {2}\t'.format(ch_name.name, 
                        self.board.name_from_probe[ch_probe.probe],
                        downsample))
                else:
                    f.write('#   {0} : {1}\t'.format(ch_name.name, 
                        self.board.name_from_probe[ch_probe.probe]))
                if x0:
                    x1 = sum(d[chan_num+1]    for d in self._data)
                    x2 = sum(d[chan_num+1]**2 for d in self._data)
                    mean = x1/x0
                    m2 = max(x2/x0-mean**2, 0)
                    if convvolts:
                        ch=self.channels[chan_num]
                        f.write(" DC= {0:.7g} RMS= {1:.7g}{2}".format(
                                  ch.volts(mean,self.board.power_voltage), 
                                  ch.volts(sqrt(m2),self.board.power_voltage),
                                  eol
                                ))
                    else:
                        f.write(" DC= {0:.7g} RMS= {1:.7g}{2}".format(
                        	mean, sqrt(m2),eol))
                else:
                    f.write(eol)
            old_time=0
            time_offset=None
            for d in self._data:
                time=d[0]
                if time_offset==None:
                    time_offset=time
                if time<old_time:
                    time_offset=time
                    f.write(eol)   # blank line if back in time
                old_time=time
            
                f.write('{0:.7f}'.format(time-time_offset)) # timestamp
                for n, x in enumerate(d[1:]):
                    ch = self.channels[n]
                    f.write('\t')
                    if convvolts and ch.interpretation.is_analog:
                        f.write("{0:.6f}".format(ch.volts(x,self.board.power_voltage)))
                    elif ch.interpretation.is_frequency:
                    	f.write("{0:.6f}".format(x))
                    else:
                        f.write(str(int(x)))
                f.write(eol)
        self.num_saved = len(self._data)
    
    def _onconnect(self):
        """A callback routine for handshake and other initial communication
        after as serial connection has been made.
        
        Either initializes connection or displays an error using _conncall.
        """
#        print('DEBUG: enter daq._onconnect',file=sys.stderr)
        handshake_tries = 0
        while True:
            try:
                hs = self.comm.command(b'H')
            except RuntimeError:
                handshake_tries += 1
                if handshake_tries>=3:
                    self._conncall('Handshake timed out. Check if PteroDAQ firmware is installed.')
                    return
                continue
            break
        if hs != b'DAQ':
            self._conncall('Handshake failed. Check if PteroDAQ firmware is installed.')
            return
        version = self.comm.command(b'V')
        if version != firmware_version:
            self._conncall('Incorrect version: {0} present, {1} needed.'.format(tostr(version), tostr(firmware_version)))
            return
        model = self.comm.command(b'M')
        self.board = getboardinfo(model)
        self._conncall(None)
    
    def _onerror(self, err_bytes):
        """A callback routine for handling error packets (that started with !E).
        """
        if len(err_bytes)==0:
            raise RuntimeError("ERROR: empty error packet received.")
        if err_bytes[0]==1:
            # triggering too fast, interrupt handler can't keep up
            self.trigger_error="triggering too fast, next trigger before finished"
        elif err_bytes[0]==2:
            # Illegal trigger type requested of board
            raise RuntimeError("Error: illegal trigger type requested: {0}".format(err_bytes[1]))
    
    def _parsedata(self, rd):
        # print('DEBUG: dat', repr(rd), file=sys.stderr)
        if not hasattr(self,'conf'):
            # No configuration sent yet.  Old packet in queue
            print("Warning: ignoring data packet before configuration set",file=sys.stderr)
            return
        if self.is_timed_trigger():
            ts = struct.unpack_from(b'<L', rd)[0]
            ts *= self.conf[0].period
            pos = 4
        else:
            ts = struct.unpack_from(b'<Q', rd)[0]
            ts *= self.board.timestamp_res
            pos = 8
        digbuf = bytearray()
        results = [ts] + [None] * len(self.channels)
        digcount = 0
        for n, ch in enumerate(self.channels, 1):
            if ch.interpretation.is_analog:
                results[n] = struct.unpack_from(b'<h' if ch.interpretation.is_signed else b'<H', rd, pos)[0]
                pos += 2
            elif ch.interpretation.is_frequency:
                count = struct.unpack_from(b'<L', rd, pos)[0]
                if self.is_timed_trigger():
                    freq = count/self.conf[0].period
                    # estimate how many counts occurred in the dead time
                    dead_counts =  freq *self.board.frequency_dead_time 
                    if dead_counts > 1:
                        # compensate for counts in the dead time that would have been missed
                        freq += (dead_counts-1)/self.conf[0].period
                    results[n] = freq
                elif self._data:
                    results[n] = count/(ts - self._data[-1][0])
                else:
                    results[n] = 0   
                if len(self._data)==1:
                    # replace the bogus first reading by duplicating second
#                    print("DEBUG: replacing freq[0]", self._data[0][n], "with", results[n], file=sys.stderr)
                    self._data[0][n] = results[n]   
                pos += 4
            else:
                digcount += 1
                if not (digcount % 8):
                    digbuf.append(rd[pos])
                    pos += 1
        if digcount % 8:
            digbuf.append(rd[pos])
        bitcount = 0
        bufpos = 0
        for n, res in enumerate(results):
            if res is None:
                results[n] = bool((digbuf[bufpos] >> bitcount) & 1)
                bitcount += 1
                if bitcount == 8:
                    bitcount = 0
                    bufpos += 1
        for n in range(len(self.channels)):
            if len(self._data) % self.channels[n].interpretation.downsample:
                results[n+1] = self._data[-1][n+1]
        self._data.append(results)

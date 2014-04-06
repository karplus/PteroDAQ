import struct
from datetime import datetime
from comm import CommPort, tobytes, tostr
from boards import getboardinfo

class TriggerTimed(object):
    def __init__(self, period):
        self.period = period
class TriggerPinchange(object):
    def __init__(self, pin, sense):
        self.pin, self.sense = pin, sense
class AnalogChannel(object):
    def __init__(self, name, pin, signed=False):
        self.name, self.pin, self.signed = name, pin, signed
class DigitalChannel(object):
    def __init__(self, name, pin):
        self.name, self.pin = name, pin

class DataAcquisition(object):
    def __init__(self):
        self._data = []
        self._nextdata = 0
        self._timeoffset = None
    def connect(self, port, cb):
        self._conncall = cb
        self.comm = CommPort(port, self._parsedata, self._onconnect)
        self.comm.connect()
    def go(self):
        self.comm.command('G')
    def stop(self):
        self.comm.command('S')
    def config(self, conf):
        confsend = bytearray()
        trigger, aref, avg, channels = conf
        self.conf = conf
        self.channels = channels
        if isinstance(trigger, TriggerTimed):
            clkdiv, clkval = self.board.timer_calc(trigger.period)[1]
            confsend.extend(struct.pack('<BBL', 1, clkdiv, clkval)[:-1])
        elif isinstance(trigger, TriggerPinchange):
            sense = next(x[1] for x in self.board.intsense if x[0] == trigger.sense)
            pin = next(x[1] for x in self.board.eint if x[0] == trigger.pin)
            confsend.extend(struct.pack('<BBB', 2, sense, pin))
        arefnum = next(x[1] for x in self.board.aref if x[0] == aref)
        confsend.append(arefnum)
        confsend.append({1: 0, 4: 4, 8: 5, 16: 6, 32: 7}[avg])
        for ch in channels:
            if isinstance(ch, AnalogChannel):
                confsend.append(1)
                confsend.append(next(x[1] for x in self.board.analogs if x[0] == ch.pin))
            elif isinstance(ch, DigitalChannel):
                confsend.append(2)
                confsend.append(next(x[1] for x in self.board.digitals if x[0] == ch.pin))
        self.comm.command('C', tostr(confsend))
    def oneread(self):
        self.comm.command('I')
    def new_data(self):
        ld = len(self._data)
        res = self._data[self._nextdata:ld]
        self._nextdata = ld
        return res
    def clear(self):
        self._data = []
        self._nextdata = 0
        self._timeoffset = None
    def save(self, fn, notes, convvolts):
        if convvolts:
            scale = self.board.power_voltage / 65535
            fmt = '.6f'
        else:
            scale = 1
            fmt = 'd'
        with open(fn, 'w') as f:
            f.write('# PteroDAQ recording\n')
            f.write('# {:%H:%M:%S, %d %b %Y}\n'.format(datetime.now()))
            if isinstance(self.conf[0], TriggerTimed):
                f.write('# Recording every {} sec ({} Hz)\n'.format(self.conf[0].period, 1./self.conf[0].period))
            elif isinstance(self.conf[0], TriggerPinchange):
                f.write('# Recording when {} {}\n'.format(self.conf[0].pin, self.conf[0].sense))
            f.write('# Analog reference is {}\n'.format(self.conf[1]))
            if self.conf[2] > 1:
                f.write('# Averaging {} readings together\n'.format(self.conf[2]))
            if convvolts:
                f.write('# Scale: 0 to {:.4f} volts\n'.format(self.board.power_voltage))
            else:
                f.write('# Scale: 0 to 65536\n')
            f.write('# Recording channels:\n')
            for ch in self.channels:
                f.write('#   {} : {}\n'.format(ch.name, ch.pin))
            f.write('# Notes:\n')
            for ln in notes.split('\n'):
                f.write('#   {}\n'.format(ln))
            for d in self._data:
                f.write('\t'.join(format(x*scale*(2 if getattr(self.channels[n-1], 'signed') else 1), fmt) if n else str(x) for n, x in enumerate(d)))
                f.write('\n')
    def _onconnect(self):
        # todo: version check
        version = self.comm.command('V')
        model = self.comm.command('M')
        self.board = getboardinfo(tobytes(model))
        self._conncall()
    def _parsedata(self, rd):
        ts = struct.unpack_from('<Q', rd)[0]
        if self._timeoffset is None:
            self._timeoffset = ts
        ts -= self._timeoffset
        digbuf = bytearray()
        results = [ts] + [None] * len(self.channels)
        pos = 8
        digcount = 0
        for n, ch in enumerate(self.channels, 1):
            if isinstance(ch, AnalogChannel):
                results[n] = struct.unpack_from('<h' if ch.signed else '<H', rd, pos)[0]
                pos += 2
            elif isinstance(ch, DigitalChannel):
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
        self._data.append(results)

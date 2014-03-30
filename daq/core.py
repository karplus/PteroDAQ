import struct
from comm import CommPort
from boards import FreedomKL25

class TriggerTimed(object):
    def __init__(self, period):
        self.period = period
class TriggerPinchange(object):
    def __init__(self, pin, sense):
        self.pin, self.sense = pin, sense
class AnalogChannel(object):
    def __init__(self, mux):
        self.mux = mux
class DigitalChannel(object):
    def __init__(self, pin):
        self.pin = pin

class DataAcquisition(object):
    def __init__(self):
        self._data = []
        self._nextdata = 0
        self.board = FreedomKL25()
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
        trigger, aref, channels = conf
        self.conf = conf
        self.channels = channels
        if isinstance(trigger, TriggerTimed):
            clkdiv, clkval = self.board.timer_calc(trigger.period)[1]
            confsend.extend(struct.pack('<BBL', 1, clkdiv, clkval)[:-1])
        elif isinstance(trigger, TriggerPinchange):
            sense = next(x[1] for x in daq.board.intsense if x[0] == trigger.sense)
            pin = next(x[1] for x in daq.board.eint if x[0] == trigger.pin)
            confsend.extend(struct.pack('<BBB', 2, sense, pin))
        confsend.append(aref)
        for ch in channels:
            if isinstance(ch, AnalogChannel):
                confsend.append(1)
                confsend.append(ch.mux)
            elif isinstance(ch, DigitalChannel):
                confsend.append(2)
                confsend.append(ch.pin)
        self.comm.command('C', str(confsend, encoding='latin1'))
    def oneread(self):
        self.comm.command('I')
    def new_data(self):
        ld = len(self._data)
        res = self._data[self._nextdata:ld]
        self._nextdata = ld
        return res
    def _onconnect(self):
        # todo: version and model info
        self._conncall()
    def _parsedata(self, rd):
        ts = struct.unpack_from('<Q', rd)[0]
        digbuf = bytearray()
        results = [ts] + [None] * len(self.channels)
        pos = 8
        digcount = 0
        for n, ch in enumerate(self.channels, 1):
            if isinstance(ch, AnalogChannel):
                results[n] = struct.unpack_from('<H', rd, pos)[0]
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
                results[n] = bool((digbuf[buspos] >> bitcount) & 1)
                bitcount += 1
                if bitcount == 8:
                    bitcount = 0
                    bufpos += 1
        self._data.append(results)

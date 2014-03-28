from serial import Serial
from time import sleep
from threading import Thread, Event
from sys import versioninfo
from getports import ports

if versioninfo[0] == 3:
    # Python 3
    def tobytes(x):
        return x.encode('latin1')
    def asbyte(x):
        return bytes([x])
    def asint(x):
        return x[0]
    def bytesum(x):
        return sum(x)
    def tostr(x):
        return x.decode('latin1')
else:
    # Python 2
    raise Exception('py2 support pending')

class CommPort(object):
    BAUDRATE = 500000 # may NOT be 1200, must match other end
    
    def __init__(self, port, datacb, conncb):
        self.port = port
        self._respavail = Event()
        self._datacb, self._conncb = datacb, conncb
    
    def connect(self):
        """Initiate a connection with the serial port specified upon instantiation.
        Non-blocking: when connected, calls conncb with no args."""
        t1 = Thread(target=self._connect)
        t1.daemon = True
        self._readthread = t2 = Thread(target=self._readin)
        t2.daemon = True
        t1.start()
    
    def _connect(self):
        self._reset()
        self._do_readin = True
        self._readthread.start()
        if self.handshake():
            self._conncb()
    
    # reset a serial port and prepare it for use
    def _reset(self):
        p = self.port
        self._enum_found = None
        self._enum_active = True
        t = Thread(target=self._enum) # start checking for new ports appearing
        t.daemon = True
        t.start()
        s1 = Serial(p, baudrate=self.BAUDRATE, timeout=1)
        sleep(0.1)
        s1.write(b'E') # end leonardo bootloader
        sleep(1)
        if self._enum_found is None: # not the leonardo
            self.ser = s1
            return
        self._enum_active = False
        s1.close()
        p = self.port = self._enum_found
        s2 = Serial(p, baudrate=self.BAUDRATE, timeout=1)
        sleep(0.1)
        self.ser = s2
        return
    
    def handshake(self):
        return self.command('H', '') == 'DAQ'
    
    def command(self, c, d):
        mbase = b'!' + tobytes(c) + asbyte(len(d)) + tobytes(d)
        msg = mbase + asbyte(-bytesum(mbase) % 256)
        self.ser.write(msg)
        self._respavail.wait()
        self._respavail.clear()
        cm, d = self._cmresp
        if cm != tobytes(c):
            return None
        return tostr(d)
    
    def _readin(self):
        """Read and process data from the serial port.
        If it forms a command response, store in _cmresp and set _respavail.
        If it forms a data record, call _datacallback with it.
        """
        rd = self.ser.read
        print('readin begin')
        while self._do_readin:
            c = rd(1)
            if c == b'!':
                cm = rd(1)
                ln = rd(1)
                data = rd(asint(ln))
                chk = rd(1)
                print('resp', c, cm, ln, data, chk)
                if (asint(b'!') + asint(cm) + asint(ln) + bytesum(data) + asint(chk)) % 256 == 0:
                    self._cmresp = cm, data
                    self._respavail.set()
            elif c == b'*':
                ln = rd(1)
                data = rd(asint(ln))
                chk = rd(1)
                if (asint(b'*') + asint(ln) + bytesum(data) + asint(chk)) == 0:
                    self._datacallback(data)
    
    def _enum(self):
        """Keep track of the number of serial ports available.
        When a new one appears, puts the address in _enum_found.
        To stop, set _enum_active to false.
        """
        p1 = ports()
        while self._enum_active:
            p2 = ports()
            if len(p2) > len(p1):
                self._enum_found = (set(p2) - set(p1)).pop()[1]
            p1 = p2
            sleep(0.1)

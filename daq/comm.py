from __future__ import division, print_function

import sys
from sys import version_info
from time import sleep
from threading import Thread, Event

from getports import Serial,ports

if version_info[0] == 3:
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
    def toints(x):
        return [a for a in x]
else:
    # Python 2
    def tobytes(x):
        return x
    def asbyte(x):
        return chr(x)
    def asint(x):
        return ord(x[0])
    def bytesum(x):
        return sum(bytearray(x))
    def tostr(x):
        return x
    def toints(bs):
        return [ord(c) for c in bs]

class CommPort(object):
    BAUDRATE = 1000000 # may NOT be 1200, must match other end
                # 1Mbaud seems to be fastes reliable Arduino UART speed
                # BAUDRATE is irrelevant for true USB communication
                #       (used by Leonardo and KL25Z)
    
    def __init__(self, port, 
                data_call_on_packet, 
                call_when_connected, 
                call_on_error=lambda x:None):
        self.portname = port
        self._respavail = Event()       # set when a full command 
                        # response has been read.
                        
        self._data_call_on_packet = data_call_on_packet
        self._call_when_connected = call_when_connected
        self._call_on_error       = call_on_error
    
    def connect(self):
        """Initiate a connection with the serial port specified upon instantiation.
        Non-blocking: when connected, calls call_when_connected with no args."""
        t1 = Thread(target=self._connect)
        t1.daemon = True
        self._readthread = t2 = Thread(target=self._readin)
        t2.daemon = True
        t1.start()
    
    def _connect(self):
        """Open the port (resetting the DAQ board),
        then start a thread reading from it.
        Call the _call_when_connected callback function to indicate success.
        """
#        print('DEBUG: enter comm._connect',file=sys.stderr)
        self._reset()
        self._do_readin = True  # set False to kill _readthread
        self._readthread.start()
#        print('DEBUG:about to handshake', file=sys.stderr)
        self._call_when_connected()
    
    def _reset(self):
        """Opens a serial port, makes sure it isn't a Leonardo bootloader,
        by writing an "E" to it and waiting to see if a new port appears 
                (resetting self.portname, if there is a new port).
        Sets self.ser to the serial port.
        """
        p = self.portname
        
        # Check to see if there is a Leonardo, using 
        self._enum_found = None         # None or single NEW port found 
                                        # by enum thread
        self._enum_active = True        # Turn off to end enum thread.
        t = Thread(target=self._enum) # enum thread for new ports appearing
        t.daemon = True # let program stop even if enum thread still running
        t.start()       
#        print("DEBUG: about to open s1 Serial(",repr(p),",",self.BAUDRATE,")", file=sys.stderr)
        s1 = Serial(p, baudrate=self.BAUDRATE, timeout=1)       #open port
#        print("DEBUG: back from attempt to open s1 Serial", file=sys.stderr)
        sleep(0.1)
        s1.write(b'E') # end leonardo bootloader
        sleep(1)
        if self._enum_found is None: 
            # no new ports, so not the leonardo bootloader
            # reopen port to get clean reset
            self.ser = s1           
            sleep(0.6)  # 1.5 seconds may be enough, 1.6 seems ok for Uno
            return
        
        s1.close()              # close the existing port
        self._enum_active = False       # kill the enum thread
        
        # open Leonardo port now that bootloader has stopped
        p = self.portname = self._enum_found
        self.ser = Serial(p, baudrate=self.BAUDRATE, timeout=1)
        sleep(0.1)
        return
    
    def command(self, c, d=b''):
        """send command c (a single-character string)
        together with data d (a byte string)
        and return the data from the response (a byte string).
        """
        mbase = b'!' + c + asbyte(len(d)) + d
        msg = mbase + asbyte(-bytesum(mbase) % 256)
        while True:
#            print("DEBUG: sending message", msg[:2],
#                    " ".join(map(hex, toints(msg[2:]))), file=sys.stderr)
            self.ser.write(msg)
            self._respavail.wait(timeout=5)
            if not self._respavail.is_set():
                print('Warning: Command timeout for command {}'.format(c),file=sys.stderr)
                if c=='H':
                    print('Try killing port-select window, and rerunning after unplugging and replugging the board into the USB port',
                        file=sys.stderr)
                continue
            self._respavail.clear()
            cm, res = self._cmresp
            if cm == ord(c):
                return res
            print('Warning: Invalid command response: sent {} command, response is {} {}'.format(c,
                         chr(cm), res), file=sys.stderr)
    
    if version_info[0] == 3:
        # Python 3
        def _readin(self):
            """Read and process data from the serial port.
            If it forms a command response, store in _cmresp and set _respavail.
            _cmresp is tuple( integer command, bytes response)
            If it forms a data record, call _datacallback with it.
            """
            rd = self.ser.read
            int_star = b'*'[0]
            int_bang = b'!'[0]
            int_E = b'E'[0]
            # print('DEBUG: readin begin on self.ser=', self.ser, file=sys.stderr)
            while self._do_readin:
                first_two=b''
                while not first_two:
                    first_two = rd(2)
                c,cm = first_two
    #            print("DEBUG: c=", c,"clock=", clock(), file=sys.stderr)
                if c == int_bang:
                    ln = rd(1)[0]
                    data = rd(ln)
                    chk = rd(1)
                    if len(chk)>0  and (c+cm+ln + sum(data) + chk[0]) % 256 == 0:
                        if cm == int_E:
                            self._call_on_error(data)
                        else:
                            self._cmresp = cm, data
                            self._respavail.set()
                    else:
                        print('Warning: Checksum error on',cm,'packet',file=sys.stderr)
                elif c == int_star:
                    ln = cm
                    data = rd(ln)
                    chk = rd(1)
    #                print('DEBUG: data=', data, 'clock=', clock(), file=sys.stderr)
                    if len(chk)>0 and (c + ln + sum(data) + chk[0]) % 256 == 0:
                        self._data_call_on_packet(data)
                    else:
                        print('Warning: Checksum error on data packet.',file=sys.stderr)
                elif c:
                    print('Warning: packet frame missing: expecting "!" or "*", but got', 
                            hex(c), file=sys.stderr)
    else:    
        # Python 2
        def _readin(self):
            """Read and process data from the serial port.
            If it forms a command response, store in _cmresp and set _respavail.
            If it forms a data record, call _datacallback with it.
            """
            rd = self.ser.read
            int_star = ord(b'*')
            int_bang = ord(b'!')
            int_E = ord(b'E')
            # print('DEBUG: readin begin on self.ser=', self.ser, file=sys.stderr)
            while self._do_readin:
                first_two=b''
                while not first_two:
                    first_two = rd(2)
                c=ord(first_two[0])
                cm = ord(first_two[1])
    #            print("DEBUG: c=", c,"clock=", clock(), file=sys.stderr)
                if c == int_bang:
                    ln = ord(rd(1))
                    data = rd(ln)
                    chk = rd(1)
                    if len(chk)>0  and (c+cm+ln + sum(bytearray(data)) + ord(chk)) % 256 == 0:
                        if cm == int_E:
                            self._call_on_error(data)
                        else:
                            self._cmresp = cm, data
                            self._respavail.set()
                    else:
                        print('Warning: Checksum error on',cm,'packet',file=sys.stderr)
                elif c == int_star:
                    ln = cm
                    data = rd(ln)
                    chk = rd(1)
    #                print('DEBUG: data=', data, 'clock=', clock(), file=sys.stderr)
                    if len(chk)>0 and (c + ln + sum(bytearray(data)) + ord(chk)) % 256 == 0:
                        self._data_call_on_packet(data)
                    else:
                        print('Warning: Checksum error on data packet.',file=sys.stderr)
                elif c:
                    print('Warning: packet frame missing: expecting "!" or "*", but got', 
                            hex(c), file=sys.stderr)
    
    def _enum(self):
        """Keep track of the number of serial ports available.
        When a new one appears, puts the port name in _enum_found.
        To stop, set _enum_active to false.
        """
        p1 = ports()
        while self._enum_active:
            p2 = ports()
            if len(p2) > len(p1):
                self._enum_found = (set(p2) - set(p1)).pop()[1]
            p1 = p2
            sleep(0.1)

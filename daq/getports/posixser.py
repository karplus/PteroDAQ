import os
import termios
import sys
import fcntl
import struct
import select
import errno

plat_linux = sys.platform.startswith('linux')
plat_osx = sys.platform.startswith('darwin')

class Serial(object):
    """A Posix serial port.
    
    Provides basic read/write functionality.
    """
    def __init__(self, fn, **args):
        """Open and initialize the serial port at path fn.
        
        Sets up a non-blocking, raw, 8N1, 1 Mbaud port.
        """
        self._rdcnt = 0
        
        custombaud = False # on osx, B1000000 might not be defined
         # but we can set the baudrate another way
        
        # open the serial port
        # for reading and writing (RDWR)
        # not as a controlling terminal (NOCTTY)
        # with non-blocking IO (NONBLOCK)
        self.fd = os.open(fn, os.O_RDWR|os.O_NOCTTY|os.O_NONBLOCK)
        
        # ignore modem control lines (CLOCAL)
        # enable receiver (CREAD)
        # use 8-bit characters (CS8)
        cflag = termios.CLOCAL|termios.CREAD|termios.CS8
        
        # set special characters to 0
        #  without flags like ICANON they are ignored
        # also sets VMIN and VTIME to 0
        #  with O_NONBLOCK they are ignored
        cc = [0]*termios.NCCS
        
        # set baudrate to 1 Mbaud
        if hasattr(termios, 'B1000000'):
            speed = termios.B1000000
        elif plat_linux:
            speed = 0x1008 # probable value of B1000000
        elif plat_osx:
            speed = termios.B38400 # placeholder
            custombaud = True
        
        # update all port settings (TCSANOW = immediately)
        termios.tcsetattr(self.fd, termios.TCSANOW, [0,0,cflag,0,speed,speed,cc])
        
        if custombaud:
            # use osx-specific IOSSIOSPEED ioctl to set baudrate
            fcntl.ioctl(self.fd, 0x80045402, struct.pack('I', 1000000))
        
        # flush input
        termios.tcflush(self.fd, termios.TCIFLUSH)
    
    def read(self, n):
        """Reads n characters from the port
        
        If fewer are available, waits 1 sec before returning.
        
        Return values is bytes (py3) / str (py2).
        """
        # list of bytestrings to concatenate
        result = []
        
        remaining = n
        while remaining:
            try:
                # check if ready to read with 1 sec timeout
                rlist, wlist, xlist = select.select([self.fd], [], [], 1.0)
                if not rlist:
                    # not ready to read
                    break
                # read up to however many we still need
                buf = os.read(self.fd, remaining)
                remaining -= len(buf)
                result.append(buf)
            except OSError as e:
                # on EAGAIN, keep trying
                if e.errno != errno.EAGAIN:
                    raise

        
        return b''.join(result)
    
    def write(self, d):
        """Write the given bytestring to the port.
        
        Should be bytes (py3) / str (py2) object.
        
        Blocking write: waits until all data written.
        """
        remaining = len(d)
        while remaining:
            try:
                # write as many bytes as possible
                written = os.write(self.fd, d[-remaining:])
                # os.write returns how many were written
                remaining -= written
            except OSError as e:
                # on EAGAIN, keep trying
                if e.errno != errno.EAGAIN:
                    raise
    
    def close(self):
        """Close the serial port.
        """
        os.close(self.fd)
        self.fd = None
    
    def __del__(self):
        """When object deleted, attempt to close port.
        """
        try:
            self.close()
        except:
            pass # nothing can be done if this close fails


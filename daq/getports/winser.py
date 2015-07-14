import ctypes as c
from ctypes import wintypes as wt

def sig(func, res, args):
    func.restype = res
    func.argtypes = args

k32 = c.WinDLL('kernel32')

GENERIC_READ  = 0x80000000
GENERIC_WRITE = 0x40000000
OPEN_EXISTING = 3
FILE_ATTRIBUTE_NORMAL = 128
FILE_FLAG_OVERLAPPED = 0x40000000
EV_ERR = 128
ONESTOPBIT = 0
RTS_CONTROL_ENABLE = 1
DTR_CONTROL_ENABLE = 1
PURGE_TXABORT = 1
PURGE_RXABORT = 2
PURGE_TXCLEAR = 4
PURGE_RXCLEAR = 8

if c.sizeof(c.c_ulong) == c.sizeof(c.c_void_p):
    # 32-bit
    ULONG_PTR = c.c_ulong
else:
    ULONG_PTR = c.c_int64

class _overlapped_s(c.Structure):
    _fields_ = [
        ('_0', wt.DWORD),
        ('_1', wt.DWORD)]

class _overlapped_u(c.Union):
    _fields_ = [
        ('_0', _overlapped_s),
        ('_1', c.c_void_p)]

class OVERLAPPED(c.Structure):
    _fields_ = [
        ('_0', ULONG_PTR),
        ('_1', ULONG_PTR),
        ('_2', _overlapped_u),
        ('hEvent', wt.HANDLE)]

class COMMTIMEOUTS(c.Structure):
    _fields_ = [
        ('ReadIntervalTimeout', wt.DWORD),
        ('ReadTotalTimeoutMultiplier', wt.DWORD),
        ('ReadTotalTimeoutConstant', wt.DWORD),
        ('WriteTotalTimeoutMultiplier', wt.DWORD),
        ('WriteTotalTimeoutConstant', wt.DWORD)]

class DCB(c.Structure):
    _fields_ = [
        ('DCBlength', wt.DWORD),
        ('BaudRate', wt.DWORD),
        ('fBinary', wt.DWORD, 1),
        ('fParity', wt.DWORD, 1),
        ('fOutxCtsFlow', wt.DWORD, 1),
        ('fOutxDsrFlow', wt.DWORD, 1),
        ('fDtrControl', wt.DWORD, 2),
        ('fDsrSensitivity', wt.DWORD, 1),
        ('fTXContinueOnXoff', wt.DWORD, 1),
        ('fOutX', wt.DWORD, 1),
        ('fInX', wt.DWORD, 1),
        ('fErrorChar', wt.DWORD, 1),
        ('fNull', wt.DWORD, 1),
        ('fRtsControl', wt.DWORD, 2),
        ('fAbortOnError', wt.DWORD, 1),
        ('fDummy2', wt.DWORD, 17),
        ('wReserved', wt.WORD),
        ('XonLim', wt.WORD),
        ('XoffLim', wt.WORD),
        ('ByteSize', wt.BYTE),
        ('Parity', wt.BYTE),
        ('StopBits', wt.BYTE),
        ('XonChar', c.c_char),
        ('XoffChar', c.c_char),
        ('ErrorChar', c.c_char),
        ('EofChar', c.c_char),
        ('EvtChar', c.c_char),
        ('wReserved1', wt.WORD)]

class COMSTAT(c.Structure):
    _fields_ = [
        ('fCtsHold', wt.DWORD, 1),
        ('fDsrHold', wt.DWORD, 1),
        ('fRlsdHold', wt.DWORD, 1),
        ('fXoffHold', wt.DWORD, 1),
        ('fXoffSent', wt.DWORD, 1),
        ('fEof', wt.DWORD, 1),
        ('fTxim', wt.DWORD, 1),
        ('fReserved', wt.DWORD, 25),
        ('cbInQue', wt.DWORD),
        ('cbOutQue', wt.DWORD)]

# function signatures
sig(k32.CreateFileW, wt.HANDLE,
    [wt.LPCWSTR, wt.DWORD, wt.DWORD, c.c_void_p, wt.DWORD, wt.DWORD, wt.HANDLE])
sig(k32.CreateEventW, wt.HANDLE,
    [c.c_void_p, wt.BOOL, wt.BOOL, wt.LPCWSTR])
sig(k32.SetupComm, wt.BOOL,
    [wt.HANDLE, wt.DWORD, wt.DWORD])
sig(k32.GetCommTimeouts, wt.BOOL,
    [wt.HANDLE, c.POINTER(COMMTIMEOUTS)])
sig(k32.SetCommTimeouts, wt.BOOL,
    [wt.HANDLE, c.POINTER(COMMTIMEOUTS)])
sig(k32.SetCommMask, wt.BOOL,
    [wt.HANDLE, wt.DWORD])
sig(k32.GetCommState, wt.BOOL,
    [wt.HANDLE, c.POINTER(DCB)])
sig(k32.SetCommState, wt.BOOL,
    [wt.HANDLE, c.POINTER(DCB)])
sig(k32.PurgeComm, wt.BOOL,
    [wt.HANDLE, wt.DWORD])
sig(k32.CloseHandle, wt.BOOL,
    [wt.HANDLE])
sig(k32.ResetEvent, wt.BOOL,
    [wt.HANDLE])
sig(k32.ClearCommError, wt.BOOL,
    [wt.HANDLE, c.POINTER(wt.DWORD), c.POINTER(COMSTAT)])
sig(k32.ReadFile, wt.BOOL,
    [wt.HANDLE, c.c_void_p, wt.DWORD, c.POINTER(wt.DWORD), c.POINTER(OVERLAPPED)])
sig(k32.GetOverlappedResult, wt.BOOL,
    [wt.HANDLE, c.POINTER(OVERLAPPED), c.POINTER(wt.DWORD), wt.BOOL])
sig(k32.WriteFile, wt.BOOL,
    [wt.HANDLE, c.c_void_p, wt.DWORD, c.POINTER(wt.DWORD), c.POINTER(OVERLAPPED)])

class Serial(object):
    def __init__(self, fn, **args):
        self.fd = k32.CreateFileW(fn,
            GENERIC_READ|GENERIC_WRITE,
            0, # exclusive access
            None, # no security
            OPEN_EXISTING,
            FILE_ATTRIBUTE_NORMAL|FILE_FLAG_OVERLAPPED,
            0)
        self._ovr = OVERLAPPED()
        self._ovw = OVERLAPPED()
        self._ovr.hEvent = k32.CreateEventW(None, 1, 0, None)
        self._ovw.hEvent = k32.CreateEventW(None, 0, 0, None)
        k32.SetupComm(self.fd, 4096, 4096)
        self._initial_timeouts = COMMTIMEOUTS()
        k32.GetCommTimeouts(self.fd, c.byref(self._initial_timeouts))
        k32.SetCommTimeouts(self.fd, c.byref(COMMTIMEOUTS(0,0,1000,0,0)))
        k32.SetCommMask(self.fd, EV_ERR)
        s = DCB()
        k32.GetCommState(self.fd, c.byref(s))
        s.BaudRate = 1000000
        s.ByteSize = 8
        s.Parity = 0
        s.fParity = 0
        s.StopBits = ONESTOPBIT
        s.fBinary = 1
        s.fRtsControl = RTS_CONTROL_ENABLE # always high
        s.fDtrControl = DTR_CONTROL_ENABLE # always high
        s.fOutxCtsFlow = 0
        s.fOutxDsrFlow = 0
        s.fOutX = 0
        s.fInX = 0
        s.fNull = 0
        s.fErrorChar = 0
        s.fAbortOnError = 0
        s.XonChar = b'\x11'
        s.XoffChar = b'\x13'
        k32.SetCommState(self.fd, c.byref(s))
        k32.PurgeComm(self.fd, PURGE_TXCLEAR|PURGE_TXABORT|PURGE_RXCLEAR|PURGE_RXABORT)
    
    def read(self, n):
        k32.ResetEvent(self._ovr.hEvent)
        flags = wt.DWORD()
        rc = wt.DWORD()
        cs = COMSTAT()
        k32.ClearCommError(self.fd, c.byref(flags), c.byref(cs))
        buf = c.create_string_buffer(n)
        k32.ReadFile(self.fd, buf, n, c.byref(rc), c.byref(self._ovr))
        k32.GetOverlappedResult(self.fd, c.byref(self._ovr), c.byref(rc), True)
        return buf.raw[:rc.value]
    
    def write(self, d):
        n = wt.DWORD()
        k32.WriteFile(self.fd, d, len(d), c.byref(n), self._ovw)
        k32.GetOverlappedResult(self.fd, self._ovw, c.byref(n), True)
        return n.value # TODO retry until all sent?
    
    def close(self):
        k32.SetCommTimeouts(self.fd, c.byref(self._initial_timeouts))
        k32.CloseHandle(self.fd)
        k32.CloseHandle(self._ovr.hEvent)
        k32.CloseHandle(self._ovw.hEvent)
        self.fd = None
    
    def __del__(self):
        try:
            self.close()
        except:
            pass

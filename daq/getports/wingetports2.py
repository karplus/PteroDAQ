import ctypes as c
from ctypes import wintypes as wt

def sig(func, res, args):
    func.restype = res
    func.argtypes = args

sa = c.windll.setupapi
aa = c.windll.advapi32

#DIGCF_DEFAULT = 1
DIGCF_PRESENT = 2
#DIGCF_ALLCLASSES = 4
#DIGCF_DEVICEINTERFACE = 0x10
SPDRP_FRIENDLYNAME = 12
#SPDRP_CLASSGUID = 8
DICS_FLAG_GLOBAL = 1
DIREG_DEV = 1
KEY_QUERY_VALUE = 1
ERROR_SUCCESS = 0
ERROR_INSUFFICIENT_BUFFER = 122
ERROR_NO_MORE_ITEMS = 259

if c.sizeof(c.c_void_p) == c.sizeof(c.c_ulong):
    # 32-bit
    ULONG_PTR = c.c_uint32
else:
    # 64-bit
    ULONG_PTR = c.c_uint64

class GUID(c.Structure):
    _fields_ = [
        ('d0', wt.DWORD),
        ('d1', wt.WORD),
        ('d2', wt.WORD),
        ('d3', wt.BYTE * 8)]

class SP_DEVINFO_DATA(c.Structure):
    _fields_ = [
        ('cbSize', wt.DWORD),
        ('ClassGuid', GUID),
        ('DevInst', wt.DWORD),
        ('_0', ULONG_PTR)]

#GUID_DEVINTERFACE_COMPORT = GUID(0x86e0d1e0, 0x8089, 0x11d0, (wt.BYTE*8)(0x9c, 0xe4, 0x08, 0x00, 0x3e, 0x30, 0x1f, 0x73))
GUID_DEVINTERFACE_SERENUM_BUS_ENUMERATOR = GUID(0x4D36E978, 0xE325, 0x11CE, (wt.BYTE*8)(0xBF, 0xC1, 0x08, 0x00, 0x2B, 0xE1, 0x03, 0x18))

INVALID_HANDLE_VALUE = c.c_void_p(-1).value

sig(sa.SetupDiGetClassDevsA, wt.HANDLE,
    [c.POINTER(GUID), c.c_void_p, c.c_void_p, wt.DWORD])
sig(sa.SetupDiEnumDeviceInfo, wt.BOOL,
    [wt.HANDLE, wt.DWORD, c.POINTER(SP_DEVINFO_DATA)])
sig(sa.SetupDiGetDeviceRegistryPropertyA, wt.BOOL,
    [wt.HANDLE, c.POINTER(SP_DEVINFO_DATA), wt.DWORD, c.c_void_p, c.c_void_p, wt.DWORD, c.POINTER(wt.DWORD)])
sig(sa.SetupDiOpenDevRegKey, wt.HKEY,
    [wt.HANDLE, c.POINTER(SP_DEVINFO_DATA), wt.DWORD, wt.DWORD, wt.DWORD, wt.ULONG])
sig(aa.RegQueryValueExA, wt.LONG,
    [wt.HKEY, wt.LPCSTR, c.c_void_p, c.c_void_p, c.c_void_p, c.POINTER(wt.DWORD)])
sig(aa.RegCloseKey, wt.LONG,
    [wt.HKEY])
sig(sa.SetupDiDestroyDeviceInfoList, wt.BOOL,
    [wt.HANDLE])

def portiter():
    hdi = sa.SetupDiGetClassDevsA(c.byref(GUID_DEVINTERFACE_SERENUM_BUS_ENUMERATOR), b'USB', None, DIGCF_PRESENT)
    if hdi == INVALID_HANDLE_VALUE:
        raise c.WinError()
    dev = SP_DEVINFO_DATA()
    dev.cbSize = c.sizeof(dev)
    needed = wt.DWORD()
    n = 0
    while sa.SetupDiEnumDeviceInfo(hdi, n, c.byref(dev)):
        #if not sa.SetupDiGetDeviceRegistryPropertyA(hdi, c.byref(dev), SPDRP_CLASSGUID, None, None, 0, c.byref(needed)):
        #    if c.GetLastError() != ERROR_INSUFFICIENT_BUFFER:
        #        raise (c.WinError())
        #guid_buf = c.create_string_buffer(needed.value+1)
        #if not sa.SetupDiGetDeviceRegistryPropertyA(hdi, c.byref(dev), SPDRP_CLASSGUID, None, c.byref(guid_buf), needed.value, None):
        #    raise (c.WinError())
        #guid = guid_buf.raw[:needed.value]
        if not sa.SetupDiGetDeviceRegistryPropertyA(hdi, c.byref(dev), SPDRP_FRIENDLYNAME, None, None, 0, c.byref(needed)):
            if c.GetLastError() != ERROR_INSUFFICIENT_BUFFER:
                raise (c.WinError())
        name_buf = c.create_string_buffer(needed.value+1)
        if not sa.SetupDiGetDeviceRegistryPropertyA(hdi, c.byref(dev), SPDRP_FRIENDLYNAME, None, c.byref(name_buf), needed.value, None):
            raise (c.WinError())
        name = name_buf.raw[:needed.value].rstrip(b'\x00')
        #print('DEBUG: name =', repr(name), 'guid =', repr(guid))
        key = sa.SetupDiOpenDevRegKey(hdi, c.byref(dev), DICS_FLAG_GLOBAL, 0, DIREG_DEV, KEY_QUERY_VALUE)
        if key == INVALID_HANDLE_VALUE:
            raise (c.WinError())
        err = aa.RegQueryValueExA(key, b'PortName', None, None, None, c.byref(needed))
        if err != ERROR_SUCCESS:
            raise (c.WinError())
        com_buf = c.create_string_buffer(needed.value+1)
        err = aa.RegQueryValueExA(key, b'PortName', None, None, c.byref(com_buf), c.byref(needed))
        if err != ERROR_SUCCESS:
            raise (c.WinError())
        com = com_buf.raw[:needed.value].rstrip(b'\x00')
        err = aa.RegCloseKey(key)
        if err != ERROR_SUCCESS:
            raise (c.WinError())
        yield name, b'\\\\.\\'+com
        n += 1
    if c.GetLastError() != ERROR_NO_MORE_ITEMS:
        raise (c.WinError())
    if not sa.SetupDiDestroyDeviceInfoList(hdi):
        raise (c.WinError())

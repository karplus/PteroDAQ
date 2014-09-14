"""(Private) Serial port lister for Mac OS X.

Do not import on other operating systems.

Inspired by osxserialports by Pascal Oberndoerfer.
"""

import sys
import ctypes
from ctypes.util import find_library

# we could also do this with a glob of /dev, something like '/dev/tty.*', but that is somewhat more fragile
# and does not get usb device names

# load cdll libraries
corefound = ctypes.CDLL(find_library('CoreFoundation'))
iokit = ctypes.CDLL(find_library('IOKit'))

# defining argument and return types is necessary to stop ctypes treating everything as 32-bit integers
# however, we don't really care about the contents of the various structs, so c_void_p is good enough
corefound.__CFStringMakeConstantString.argtypes = [ctypes.c_char_p]
corefound.__CFStringMakeConstantString.restype = ctypes.c_void_p
iokit.IOServiceMatching.argtypes = [ctypes.c_char_p]
iokit.IOServiceMatching.restype = ctypes.c_void_p
iokit.IOServiceGetMatchingServices.argtypes  = [ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p]
iokit.IOIteratorNext.argtypes = [ctypes.c_void_p]
iokit.IOIteratorNext.restype = ctypes.c_void_p
iokit.IORegistryEntryCreateCFProperty.argtypes = [ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p, ctypes.c_int]
iokit.IORegistryEntryCreateCFProperty.restype = ctypes.c_void_p
iokit.IORegistryEntryCreateIterator.argtypes = [ctypes.c_void_p, ctypes.c_char_p, ctypes.c_int, ctypes.c_void_p]
iokit.IORegistryEntryGetName.argtypes = [ctypes.c_void_p, ctypes.c_char_p]
corefound.CFStringGetCString.argtypes = [ctypes.c_void_p, ctypes.c_char_p, ctypes.c_int, ctypes.c_int]
corefound.CFRelease.argtypes = [ctypes.c_void_p]
iokit.IOObjectRelease.argtypes = [ctypes.c_void_p]

# useful constants from IOKit and CoreFoundation, not easily accessible with ctypes
kIORegistryIterateRecursively = 1
kIOServicePlane = b'IOService'
kIOSerialBSDServiceValue = b'IOSerialBSDClient'
kIODialinDeviceKey = corefound.__CFStringMakeConstantString(b'IODialinDevice')
kCFStringEncodingASCII = 0x600
kCFDefaultAllocator = None # null pointers
kIOMasterPortDefault = None
kNilOptions = 0

MAXSTRLEN = 1024 # I doubt device names will be longer than this

def getstring(dev, key):
    cf = iokit.IORegistryEntryCreateCFProperty(dev, key, kCFDefaultAllocator, kNilOptions) # get from device object
    buf = ctypes.create_string_buffer(MAXSTRLEN) # c string (byte array)
    corefound.CFStringGetCString(cf, buf, MAXSTRLEN, kCFStringEncodingASCII) # convert from CFString to c string
    corefound.CFRelease(cf)
    return buf.value # the .value goes from ctypes byte arrays to python strings

def getname(dev):
    buf = ctypes.create_string_buffer(MAXSTRLEN) # c string (byte array)
    iokit.IORegistryEntryGetName(dev, buf)
    return buf.value

def portiter():
    itr = ctypes.c_void_p() # iterator of devices
    # populate the iterator with all usb devices
    iokit.IOServiceGetMatchingServices(kIOMasterPortDefault, iokit.IOServiceMatching(b'IOUSBDevice'), ctypes.byref(itr))
    while True:
        ds = iokit.IOIteratorNext(itr) # going through each item in the iterator
        if not ds: # a null pointer means we've exhausted the iterator
            break
        itr2 = ctypes.c_void_p() # iterator within device
        # populate the iterator with all children of device
        iokit.IORegistryEntryCreateIterator(ds, kIOServicePlane, kIORegistryIterateRecursively, ctypes.byref(itr2))
        while True:
            bs = iokit.IOIteratorNext(itr2) # going through each item in the iterator
            if not bs: # a null pointer means we've exhausted the iterator
                break
            bsname = getname(bs)
            if bsname == kIOSerialBSDServiceValue: # serial port children have this name
                yield (getname(ds), getstring(bs, kIODialinDeviceKey)) # device name and dialin address
                break
            iokit.IOObjectRelease(bs)
        iokit.IOObjectRelease(itr2)
        iokit.IOObjectRelease(ds)
    iokit.IOObjectRelease(itr)

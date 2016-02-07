"""(Private) Serial port lister for Mac OS X.

Do not import on other operating systems.

Inspired by osxserialports by Pascal Oberndoerfer.
Also by PySerial implementation of port finder, to get function on OS X 10.11.
"""

from __future__ import print_function,division

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
    """generator that yields pairs (name, /dev string)  for USB serial ports
    """
    # look for an IOSerialBSDClient which has an ancestor
    #     that is an AppleUSBEHCI or AppleUSB20HubPort
    # and get the name from the child of that
    itr = ctypes.c_void_p() # iterator of interfaces
    # populate the iterator with all SerialBSDClients
    iokit.IOServiceGetMatchingServices(kIOMasterPortDefault, iokit.IOServiceMatching(b'IOSerialBSDClient'), ctypes.byref(itr))
    while True:
        service = iokit.IOIteratorNext(itr) # going through each item in the iterator
        if not service: # a null pointer means we've exhausted the iterator
            break
#        print("DEBUG: starting from ", getname(service), file=sys.stderr)
        child = service
        while True:
#            print("DEBUG: looking for parent of ", getname(child), file=sys.stderr)
            parent = ctypes.c_void_p()
            response = iokit.IORegistryEntryGetParentEntry(
                child,
                b"IOService",
                ctypes.byref(parent))
            if response != 0:
                # Unable to find a parent for the child, we're done.
                break
            if getname(parent) in [b'AppleUSBEHCI', b'AppleUSB20HubPort']:
                # found  child and parent
                break
            child = parent
        if response!=0:
            continue

#        print("DEBUG: found child", getname(child), "parent", getname(parent), file=sys.stderr)	
#        print("DEBUG: getstring(service, kIODialinDeviceKey)=", getstring(service, kIODialinDeviceKey), file=sys.stderr)	

        yield (getname(child), getstring(service, kIODialinDeviceKey)) # device name and dialin address
#        iokit.IOObjectRelease(service)
#        iokit.IOObjectRelease(interface)
#    iokit.IOObjectRelease(itr)

# MAC OS X 10.6.8
# Parental chain for Teensy LC board:
# DEBUG: starting from  IOSerialBSDClient
# DEBUG: looking for parent of  IOSerialBSDClient
# DEBUG: looking for parent of  IOModemSerialStreamSync
# DEBUG: looking for parent of  AppleUSBCDCACMData
# DEBUG: looking for parent of  IOUSBInterface
# DEBUG: found interface IOSerialBSDClient parent PteroDAQ (Teensy)

# continues with
# DEBUG: looking for parent of  PteroDAQ (Teensy)
# DEBUG: looking for parent of  AppleUSBEHCI
# DEBUG: looking for parent of  EHC2
# DEBUG: looking for parent of  AppleACPIPCI
# DEBUG: looking for parent of  PCI0
# DEBUG: looking for parent of  AppleACPIPlatformExpert
# DEBUG: looking for parent of  MacBookPro5,3
# DEBUG: looking for parent of  Root

# Almost identical chain for KL25Z board:
# DEBUG: starting from  IOSerialBSDClient
# DEBUG: looking for parent of  IOSerialBSDClient
# DEBUG: looking for parent of  IOModemSerialStreamSync
# DEBUG: looking for parent of  AppleUSBCDCACMData
# DEBUG: looking for parent of  IOUSBInterface
# DEBUG: found interface IOSerialBSDClient parent PteroDAQ (FRDM-KL25Z)

# Parental chain for Arduino Duemilanove and Sparkfun Redboard:
# DEBUG: starting from  IOSerialBSDClient
# DEBUG: looking for parent of  IOSerialBSDClient
# DEBUG: looking for parent of  IORS232SerialStreamSync
# DEBUG: looking for parent of  FTDIUSBSerialDriver
# DEBUG: looking for parent of  FT232R USB UART
# DEBUG: looking for parent of  FT232R USB UART
# DEBUG: looking for parent of  AppleUSBEHCI
# DEBUG: looking for parent of  EHC2
# DEBUG: looking for parent of  AppleACPIPCI
# DEBUG: looking for parent of  PCI0
# DEBUG: looking for parent of  AppleACPIPlatformExpert
# DEBUG: looking for parent of  MacBookPro5,3
# DEBUG: looking for parent of  Root

# Note that above the IOSerialBSDClient the first common name between
# Kinetis-processor boards and the Arduino boards is AppleUSBEHCI,
# which is the parent of the device name we want to use.

# undesired Bluetooth devices:
# DEBUG: starting from  IOSerialBSDClient
# DEBUG: looking for parent of  IOSerialBSDClient
# DEBUG: looking for parent of  IOBluetoothSerialClientSerialStreamSync
# DEBUG: looking for parent of  IOBluetoothSerialClient
# DEBUG: looking for parent of  IOBluetoothSerialManager
# DEBUG: looking for parent of  IOResources
# DEBUG: looking for parent of  MacBookPro5,3
# DEBUG: looking for parent of  Root

################################################
# Mac OS X 10.11.3 has different USB hierarchy:
################################################

# undesired Bluetooth looks the same
# DEBUG: starting from  IOSerialBSDClient
# DEBUG: looking for parent of  IOSerialBSDClient
# DEBUG: looking for parent of  IOBluetoothSerialClientSerialStreamSync
# DEBUG: looking for parent of  IOBluetoothSerialClient
# DEBUG: looking for parent of  IOBluetoothSerialManager
# DEBUG: looking for parent of  IOResources
# DEBUG: looking for parent of  iMac12,2
# DEBUG: looking for parent of  Root

# Arduino FTDI interfaces look the same
# DEBUG: starting from  IOSerialBSDClient
# DEBUG: looking for parent of  IOSerialBSDClient
# DEBUG: looking for parent of  IORS232SerialStreamSync
# DEBUG: looking for parent of  FTDIUSBSerialDriver
# DEBUG: looking for parent of  FT232R USB UART
# DEBUG: looking for parent of  FT232R USB UART
# DEBUG: found child FT232R USB UART parent AppleUSBEHCI

# Teensy board has a very different stack!
# DEBUG: starting from  IOSerialBSDClient
# DEBUG: looking for parent of  IOSerialBSDClient
# DEBUG: looking for parent of  IOModemSerialStreamSync
# DEBUG: looking for parent of  AppleUSBACMData
# DEBUG: looking for parent of  IOUSBHostInterface
# DEBUG: looking for parent of  PteroDAQ (Teensy)
# DEBUG: looking for parent of  AppleUSB20HubPort
# DEBUG: looking for parent of  AppleUSB20Hub
# DEBUG: looking for parent of  USB 2.0 Hub
# DEBUG: looking for parent of  AppleUSB20HubPort
# DEBUG: looking for parent of  AppleUSB20InternalHub
# DEBUG: looking for parent of  IOUSBHostDevice
# DEBUG: looking for parent of  PRT1
# DEBUG: looking for parent of  EHC2
# DEBUG: looking for parent of  EHC2
# DEBUG: looking for parent of  AppleACPIPCI
# DEBUG: looking for parent of  PCI0
# DEBUG: looking for parent of  AppleACPIPlatformExpert
# DEBUG: looking for parent of  iMac12,2
# DEBUG: looking for parent of  Root


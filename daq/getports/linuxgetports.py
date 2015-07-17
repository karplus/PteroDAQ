"""(Private) Serial port lister for Linux."""

import ctypes
from ctypes.util import find_library
import codecs

ud = ctypes.CDLL(find_library('udev'))

ud.udev_new.restype = ctypes.c_void_p
ud.udev_enumerate_new.argtypes = [ctypes.c_void_p]
ud.udev_enumerate_new.restype = ctypes.c_void_p
ud.udev_enumerate_add_match_is_initialized.argtypes = [ctypes.c_void_p]
ud.udev_enumerate_add_match_subsystem.argtypes = [ctypes.c_void_p, ctypes.c_char_p]
ud.udev_enumerate_add_match_property.argtypes = [ctypes.c_void_p, ctypes.c_char_p, ctypes.c_char_p]
ud.udev_enumerate_scan_devices.argtypes = [ctypes.c_void_p]
ud.udev_enumerate_get_list_entry.argtypes = [ctypes.c_void_p]
ud.udev_enumerate_get_list_entry.restype = ctypes.c_void_p
ud.udev_list_entry_get_name.argtypes = [ctypes.c_void_p]
ud.udev_list_entry_get_name.restype = ctypes.c_char_p
ud.udev_device_new_from_syspath.argtypes = [ctypes.c_void_p, ctypes.c_void_p]
ud.udev_device_new_from_syspath.restype = ctypes.c_void_p
ud.udev_device_get_property_value.argtypes = [ctypes.c_void_p, ctypes.c_char_p]
ud.udev_device_get_property_value.restype = ctypes.c_char_p
ud.udev_device_get_devnode.argtypes = [ctypes.c_void_p]
ud.udev_device_get_devnode.restype = ctypes.c_char_p
ud.udev_device_unref.argtypes = [ctypes.c_void_p]
ud.udev_list_entry_get_next.argtypes = [ctypes.c_void_p]
ud.udev_list_entry_get_next.restype = ctypes.c_void_p
ud.udev_enumerate_unref.argtypes = [ctypes.c_void_p]
ud.udev_unref.argtypes = [ctypes.c_void_p]

def hexdec(be):
    return codecs.decode(be.replace(b'=',b'\\x3d').replace(b'\\x',b'='), 'quoted-printable')

def portiter():
    ctx = ud.udev_new()
    en = ud.udev_enumerate_new(ctx)
    ud.udev_enumerate_add_match_is_initialized(en)
    ud.udev_enumerate_add_match_subsystem(en, b'tty')
    ud.udev_enumerate_add_match_property(en, b'ID_MODEL', b'*')
    ud.udev_enumerate_scan_devices(en)
    itm = ud.udev_enumerate_get_list_entry(en)
    while itm is not None:
        name = ud.udev_list_entry_get_name(itm)
        dev = ud.udev_device_new_from_syspath(ctx, name)
        model = hexdec(ud.udev_device_get_property_value(dev, b'ID_MODEL_ENC'))
        node = ud.udev_device_get_devnode(dev)
        yield model, node
        ud.udev_device_unref(dev)
        itm = ud.udev_list_entry_get_next(itm)
    ud.udev_enumerate_unref(en)
    ud.udev_unref(ctx)


"""(Private) Serial port lister for POSIX systems other than Linux and Mac OS X.

Adapted from list_ports_posix in pySerial.
In addition to portiter, provides the constant VALID,
which is true if the platform is supported by this module.
"""

import sys
import glob

platlocs = [
    ('cygwin', b'ttyS*'),
    ('openbsd', b'cua*'),
    ('bsd', b'cuad*'),
    ('freebsd', b'cuad*'),
    ('netbsd', b'dty*'),
    ('irix', b'ttyf*'),
    ('hp', b'tty*p0'),
    ('sunos', b'tty*c'),
    ('aix', b'tty*'),
    ('linux', b'ttyS*'), # but use linuxgetports instead
    ('darwin', b'tty.*'), # but use macgetports instead
]
dev_prefix = b'/dev/'

VALID = False
for p, d in platlocs:
    if p == sys.platform:
        VALID = True
        dev_search = dev_prefix + d
        break

def portiter():
    return ((x[len(dev_prefix):], x) for x in glob.iglob(dev_search))

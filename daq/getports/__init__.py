"""Serial port lister.

The function `ports` returns a tuple of pairs.
The first element of each pair is the name of a serial device as a bytes object,
and the second element is the address of the device as a bytes object.
Names are more-or-less human readable, and addresses may be passed directly to pySerial's Serial class to create the port.

The function `portiter` is the same except for returning an iterable.
If only looping through once, it is likely more efficient.

The `Serial` class is either from pySerial,
or a partially-compatible minimalist implementation.
"""

import sys

__all__ = ['portiter', 'ports', 'Serial']

from . import posixgetports

p = sys.platform
if p == 'win32':
    from .wingetports2 import portiter
    from .winser import Serial
else:
    if p == 'darwin': # mac
        from .macgetports import portiter
    elif p.startswith('linux'):
        from .linuxgetports import portiter
    elif posixgetports.VALID:
        from .posixgetports import portiter
    else:
        raise OSError('Unsupported platform {}'.format(p))
    from .posixser import Serial

def ports():
    return tuple(portiter())

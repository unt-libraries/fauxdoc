"""Tools for generating fake data."""
import sys

if sys.version_info >= (3, 8):
    from importlib import metadata
else:
    import importlib_metadata as metadata
from . import dtrange
from . import emitter
from . import emitters
from . import group
from . import mathtools
from . import mixins
from . import profile
from . import typing


__version__ = metadata.version('fauxdoc')
__all__ = [
    'dtrange', 'emitter', 'emitters', 'group', 'mathtools', 'mixins',
    'profile', 'typing'
]

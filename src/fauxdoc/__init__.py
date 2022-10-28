"""Tools for generating fake data."""
try:
    from importlib import metadata
except (ImportError, ModuleNotFoundError):
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

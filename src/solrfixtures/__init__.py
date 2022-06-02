"""Generates randomized data for populating Solr test fixtures.

Sort of like model-bakery (aka model-mommy), for Solr.
"""
from . import dtrange
from . import emitter
from . import emitters
from . import group
from . import mathtools
from . import mixins
from . import profile
from . import typing


__version__ = '0.1.0'
__all__ = [
    'dtrange', 'emitter', 'emitters', 'group', 'mathtools', 'mixins',
    'profile', 'typing'
]

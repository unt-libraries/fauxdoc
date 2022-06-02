"""Contains emitters, the meat of the solrfixtures package.

Emitters are objects (based on emitter.Emitter) that you configure once
and then call repeatedly to generate output data. Each different type
of emitter is built to create a specific type of data or be configured
in a specific way.
"""
from . import choice
from .choice import chance, Choice, gaussian_choice, poisson_choice
from . import fixed
from .fixed import Iterative, Sequential, Static
from . import fromfields
from .fromfields import BasedOnFields, CopyFields
from . import text
from .text import make_alphabet, Text, Word
from . import wrappers
from .wrappers import Wrap, WrapMany


__all__ = [
    'choice', 'chance', 'Choice', 'gaussian_choice', 'poisson_choice',
    'fixed', 'Iterative', 'Sequential', 'Static', 'fromfields',
    'BasedOnFields', 'CopyFields', 'text', 'make_alphabet', 'Text',
    'Word', 'wrappers', 'Wrap', 'WrapMany'
]

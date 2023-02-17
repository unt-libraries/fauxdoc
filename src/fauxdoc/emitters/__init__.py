"""Contains emitters, the meat of the solrfixtures package.

Emitters are objects (based on emitter.Emitter) that you configure once
and then call repeatedly to generate output data. Each different type
of emitter is built to create a specific type of data or be configured
in a specific way.
"""
from typing import Any, List

from fauxdoc.warn import get_deprecated_attr

from . import choice
from .choice import chance, Choice, gaussian_choice, poisson_choice
from . import fixed
from .fixed import Iterative, Sequential, Static
from . import fromfields
from .fromfields import BasedOnFields, CopyFields
from . import text
from .text import make_alphabet, Text, Word
from . import wrappers
from .wrappers import WrapOne, WrapMany, DEPRECATED as WRAPPERS_DEPRECATED


# Below: Deprecated attributes don't get imported directly but are
# imported dynamically via __getattr__. Pylint doesn't recognize this
# and so complains about undefined variables in __all__, although star
# imports still work. This error is suppressed.
__all__ = [
    'choice', 'chance', 'Choice', 'gaussian_choice', 'poisson_choice',
    'fixed', 'Iterative', 'Sequential', 'Static', 'fromfields',
    'BasedOnFields', 'CopyFields', 'text', 'make_alphabet', 'Text',
    'Word', 'wrappers',
    'Wrap',  # pylint: disable=undefined-all-variable
    'WrapOne', 'WrapMany'
]


DEPRECATED = {}
DEPRECATED.update(WRAPPERS_DEPRECATED)


def __getattr__(name: str) -> Any:
    # Note: Because this appears in __init__.py, it ends up firing
    # twice when you do a "from" import:
    # "from fauxdoc.emitters import Wrap" raises two warnings instead
    # of one. This is because the underlying mechanism does a `hasattr`
    # call before accessing the attribute, which results in two calls.
    # I don't think there is a way around this, but it doesn't hurt
    # anything.
    return get_deprecated_attr(name, __name__, 'module', DEPRECATED)


def __dir__() -> List[str]:
    return sorted(list(globals()) + list(DEPRECATED.keys()))

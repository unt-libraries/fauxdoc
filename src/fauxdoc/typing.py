"""Contains constants/variables/etc. used for type hinting."""
import collections
import random
import sys
from typing import (
    Any, Callable, List, Optional, overload, Sequence, TYPE_CHECKING, TypeVar,
    Union
)

from fauxdoc.warn import get_deprecated_attr

if sys.version_info >= (3, 8):
    from typing import Protocol
else:
    from typing_extensions import Protocol

# For Python 3.7 and 3.8: standard library ABC classes (including
# collections) aren't subscriptable and don't accept e.g. UserList[T]
# at runtime, although they're required for type hints. This is the
# fix.
#
# On Python >= 3.9, or during type checking, the collections versions
# of these classes work.
if sys.version_info >= (3, 9) or TYPE_CHECKING:
    OrderedDict = collections.OrderedDict
    UserList = collections.UserList

# Otherwise, we need to hack it so these classes are subscriptable but
# are otherwise identical.
else:
    class _OrderedDict:
        def __getitem__(self, *args):
            return collections.OrderedDict

    class _UserList:
        def __getitem__(self, *args):
            return collections.UserList

    OrderedDict = _OrderedDict()
    UserList = _UserList()


# Type aliases defined here.

T = TypeVar('T')
F = TypeVar('F', bound=float)
CT = TypeVar('CT', covariant=True)
SourceT = TypeVar('SourceT', contravariant=True)
OutputT = TypeVar('OutputT', covariant=True)
FieldReturn = Optional[Union[T, List[T]]]


# Protocols defined here.

class EmitterLike(Protocol[T]):
    """Is like an emitter.Emitter object."""

    @property
    def num_unique_values(self) -> Optional[int]:
        ...

    @property
    def emits_unique_values(self) -> bool:
        ...

    @overload
    def __call__(self, number: None = None) -> T:
        ...

    @overload
    def __call__(self, number: int) -> List[T]:
        ...

    def __call__(self, number: Optional[int] = None) -> Union[T, List[T]]:
        ...

    def reset(self) -> None:
        ...


class ImplementsRNG(Protocol):
    """Is a type that implements RNG."""

    rng: random.Random

    def seed(self, rng_seed: Any) -> None:
        ...


class RandomEmitterLike(ImplementsRNG, EmitterLike[T], Protocol[T]):
    """Is like an emitter.RandomEmitter object."""


class FieldLike(Protocol[CT]):
    """Is like a profile.Field object."""

    multi_valued: bool
    name: str
    hide: bool

    def __call__(self) -> FieldReturn[CT]:
        ...

    def reset(self) -> None:
        ...

    @property
    def previous(self) -> FieldReturn[CT]:
        ...


# Handle deprecated module attributes.
# (Note that this is placed at the end of the module so we can use vars
# defined earlier in the module, in DEPRECATED.)

_deprecated_EmitterLike = Union[Callable[[int], Sequence[T]], EmitterLike[T]]

DEPRECATED = {
    'Number': ('float', float),
    'EmitterLikeCallable': ('EmitterLike', _deprecated_EmitterLike),
    'StrEmitterLike': ('EmitterLike[str]', EmitterLike[str]),
    'IntEmitterLike': ('EmitterLike[int]', EmitterLike[int]),
    'BoolEmitterLike': ('EmitterLike[bool]', EmitterLike[bool])
}


def __getattr__(name: str) -> Any:
    return get_deprecated_attr(name, __name__, 'module', DEPRECATED)


def __dir__() -> List[str]:
    return sorted(list(globals()) + list(DEPRECATED.keys()))

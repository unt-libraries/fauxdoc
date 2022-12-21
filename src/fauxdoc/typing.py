"""Contains constants/variables/etc. used for type hinting."""
import sys
from typing import (
    Any, Callable, Generic, List, Optional, Sequence, TypeVar, Union
)

if sys.version_info >= (3, 8):
    from typing import Protocol
else:
    from typing_extensions import Protocol


# Type aliases defined here.

Number = Union[int, float]
T = TypeVar('T')
CT = TypeVar('CT', covariant=True)
EmitterLikeCallable = Union[Callable[[int], Sequence[T]], 'EmitterLike']


# Protocols defined here.

class EmitterLike(Protocol[CT]):
    """Is like an emitter.Emitter object."""

    def __call__(self, number: Optional[int] = None) -> Union[CT, List[CT]]:
        ...

    def reset(self) -> None:
        ...


class BoolEmitterLike(EmitterLike[bool], Protocol):
    """An emitter.Emitter-like object that emits booleans."""

    def __call__(self,
                 number: Optional[int] = None) -> Union[bool, List[bool]]:
        ...


class IntEmitterLike(EmitterLike[int], Protocol):
    """An emitter.Emitter-like object that emits integers."""

    def __call__(self, number: Optional[int] = None) -> Union[int, List[int]]:
        ...


class StrEmitterLike(EmitterLike[str], Protocol):
    """An emitter.Emitter-like object that emits strings."""

    def __call__(self, number: Optional[int] = None) -> Union[str, List[str]]:
        ...


class RandomEmitterLike(EmitterLike[CT], Protocol):
    """Is like an emitter.RandomEmitter object."""

    def seed(self, rng_seed: Any) -> None:
        ...


class FieldLike(Protocol):
    """Is like a profile.Field object."""

    multi_valued: bool

    def __call__(self) -> Any:
        ...

    def reset(self) -> None:
        ...

    @property
    def previous(self) -> Any:
        ...

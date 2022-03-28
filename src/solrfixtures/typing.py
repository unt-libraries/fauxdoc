"""Contains constants/variables/etc. used for type hinting."""
from typing import Any, Optional, List, TypeVar, Union

try:
    from typing import Protocol
except ImportError:
    from typing_extensions import Protocol


# Type aliases defined here.

Number = Union[int, float]
T = TypeVar('T')


# Protocols defined here.

class EmitterLike(Protocol):
    """Is like a data.emitter.BaseEmitter object."""

    def __call__(self, number: Optional[int] = None) -> Union[T, List[T]]:
        ...

    def reset(self) -> None:
        ...


class IntEmitterLike(EmitterLike, Protocol):
    """A data.emitter.BaseEmitter-like object that emits integers."""

    def __call__(self, number: Optional[int] = None) -> Union[int, List[int]]:
        ...


class StrEmitterLike(EmitterLike, Protocol):
    """A data.emitter.BaseEmitter-like object that emits strings."""

    def __call__(self, number: Optional[int] = None) -> Union[str, List[str]]:
        ...


class RandomEmitterLike(EmitterLike, Protocol):
    """Is like a data.emitter.BaseRandomEmitter object."""

    def seed(self, rng_seed: Any) -> None:
        ...

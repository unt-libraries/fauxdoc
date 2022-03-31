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
    """Is like an emitter.Emitter object."""

    def __call__(self, number: Optional[int] = None) -> Union[T, List[T]]:
        ...

    def reset(self) -> None:
        ...


class BoolEmitterLike(EmitterLike, Protocol):
    """An emitter.Emitter-like object that emits booleans."""

    def __call__(self,
                 number: Optional[int] = None) -> Union[bool, List[bool]]:
        ...


class IntEmitterLike(EmitterLike, Protocol):
    """An emitter.Emitter-like object that emits integers."""

    def __call__(self, number: Optional[int] = None) -> Union[int, List[int]]:
        ...


class StrEmitterLike(EmitterLike, Protocol):
    """An emitter.Emitter-like object that emits strings."""

    def __call__(self, number: Optional[int] = None) -> Union[str, List[str]]:
        ...


class RandomEmitterLike(EmitterLike, Protocol):
    """Is like an emitter.RandomEmitter object."""

    def seed(self, rng_seed: Any) -> None:
        ...

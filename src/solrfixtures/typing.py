"""Contains constants/variables/etc. used for type hinting."""
from typing import Any, Optional, Sequence, TypeVar, Union

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

    def __call__(self, number: Optional[int] = None) -> Sequence[Any]:
        ...

    def reset(self) -> None:
        ...


class IntEmitterLike(EmitterLike, Protocol):
    """A data.emitter.BaseEmitter-like object that emits integers."""

    def __call__(self, number: Optional[int] = None) -> Sequence[int]:
        ...


class StrEmitterLike(EmitterLike, Protocol):
    """A data.emitter.BaseEmitter-like object that emits strings."""

    def __call__(self, number: Optional[int] = None) -> Sequence[str]:
        ...


class RandomEmitterLike(EmitterLike, Protocol):
    """Is like a data.emitter.BaseRandomEmitter object."""

    def seed_rngs(self, seed: Any) -> None:
        ...

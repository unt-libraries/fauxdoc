"""Contains constants/variables/etc. used for type hinting."""
from datetime import date, datetime, time, timedelta
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


class RandomEmitterLike(EmitterLike, Protocol):
    """Is like a data.emitter.BaseRandomEmitter object."""

    def seed_rngs(self, seed: Any) -> None:
        ...


class RandomIntEmitterLike(RandomEmitterLike, Protocol):
    """Is like a data.emitter.IntEmitter object."""

    def __call__(self, number: Optional[int] = None) -> Sequence[int]:
        ...


class RandomStrEmitterLike(RandomEmitterLike, Protocol):
    """Is like a data.emitter.StrEmitter object."""

    def __call__(self, number: Optional[int] = None) -> Sequence[str]:
        ...


class RandomDateEmitterLike(RandomEmitterLike, Protocol):
    """Is like a data.emitter.DateEmitter object."""

    def __call__(self, number: Optional[int] = None) -> Sequence[date]:
        ...


class RandomTimeEmitterLike(RandomEmitterLike, Protocol):
    """Is like a data.emitter.TimeEmitter object."""

    def __call__(self, number: Optional[int] = None) -> Sequence[time]:
        ...


class TzInfoLike(Protocol):
    """Can be tzinfo for a datetime.time or datetime.datetime object."""

    def utcoffset(dt: datetime) -> timedelta:
        ...

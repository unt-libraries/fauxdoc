"""Contains constants/variables/etc. used for type hinting."""
import datetime
from typing import Any, Union, TypeVar

try:
    from typing import Protocol
except ImportError:
    from typing_extensions import Protocol


# Type aliases defined here.

Number = Union[int, float]
T = TypeVar('T')


# Protocols defined here.

class RandomEmitterLike(Protocol):
    """Is like a data.emitter.BaseRandomEmitter object."""

    def __call__(self) -> Any:
        ...

    def seed_rngs(self, seed: Any) -> None:
        ...


class RandomStrEmitterLike(RandomEmitterLike, Protocol):
    """Is like a data.emitter.StrEmitter object."""

    def __call__(self) -> str:
        ...


class RandomDateEmitterLike(RandomEmitterLike, Protocol):
    """Is like a data.emitter.DateEmitter object."""

    def __call__(self) -> datetime.date:
        ...


class RandomTimeEmitterLike(RandomEmitterLike, Protocol):
    """Is like a data.emitter.TimeEmitter object."""

    def __call__(self) -> datetime.time:
        ...


class TzInfoLike(Protocol):
    """Can be tzinfo for a datetime.time or datetime.datetime object."""

    def utcoffset(dt: datetime.datetime) -> datetime.timedelta:
        ...

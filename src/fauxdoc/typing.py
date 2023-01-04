"""Contains constants/variables/etc. used for type hinting."""
import random
import sys
from typing import Any, List, Optional, TypeVar, Union

if sys.version_info >= (3, 8):
    from typing import Protocol
else:
    from typing_extensions import Protocol


# Type aliases defined here.

Number = Union[int, float]
T = TypeVar('T')
CT = TypeVar('CT', covariant=True)
SourceT = TypeVar('SourceT', contravariant=True)
OutputT = TypeVar('OutputT', covariant=True)


# Protocols defined here.

class EmitterLike(Protocol[CT]):
    """Is like an emitter.Emitter object."""

    def __call__(self, number: Optional[int] = None) -> Union[CT, List[CT]]:
        ...

    def reset(self) -> None:
        ...


BoolEmitterLike = EmitterLike[bool]
IntEmitterLike = EmitterLike[int]
StrEmitterLike = EmitterLike[str]


class ImplementsRNG(Protocol):
    """Is a type that implements RNG."""

    rng: random.Random

    def seed(self, rng_seed: Any) -> None:
        ...


class RandomEmitterLike(ImplementsRNG, EmitterLike[CT]):
    """Is like an emitter.RandomEmitter object."""




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

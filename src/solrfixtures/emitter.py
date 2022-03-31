"""Contains base Emitter classes, for emitting data values."""
from abc import ABC, abstractmethod
import random
from typing import Any, List, Optional, Sequence, Union, TypeVar

from .typing import T


class Emitter(ABC):
    """Abstract base class for defining emitter objects.

    Subclass this to implement an emitter object. At this level all you
    are required to override is the `emit` method, but you should also
    look at `reset`, `emits_unique_values`, and `num_unique_values`.
    Use `__init__` to configure whatever options your emitter may need.

    The `__call__` method wraps `emit` so you can emit data values
    simply by calling the object.
    """

    def reset(self) -> None:
        """Resets state on this object.

        Override this in your subclass if your emitter stores state
        changes that may need to be reset to their initial values. (The
        subclass is responsible for tracking state, of course.) This is
        a no-op by default.
        """

    @property
    def emits_unique_values(self) -> bool:
        """Returns a bool; True if an instance emits unique values.

        We mean "unique" in terms of the lifetime of the instance, not
        a given call to `emit`. This should return True if the instance
        is guaranteed never to return a duplicate until it is reset.
        """
        return False

    @property
    def num_unique_values(self) -> Union[None, int]:
        """Returns an int, the number of unique values emittable.

        This number should be relative to the next `emit` call. If your
        instance is one where `emits_unique_values` is True, then this
        should return the number of unique values that remain at any
        given time. Otherwise, this should give the total number of
        unique values that can be emitted. Return None if the number is
        so high as to be effectively infinite (such as with a random
        text emitter).
        """
        return None

    def raise_uniqueness_violation(self, number: int) -> None:
        """Raises a ValueError indicating not enough unique values.

        Args:
            number: An integer indicating how many new unique values
                were requested.
        """
        raise ValueError(
            f"Could not emit: {number} new unique value"
            f"{' was' if number == 1 else 's were'} requested, out of "
            f"{self.num_unique_values} possible selection"
            f"{'' if self.num_unique_values == 1 else 's'}."
        )

    def __call__(self, number: Optional[int] = None) -> Union[T, List[T]]:
        """Wraps the `emit` method so that this obj is callable.

        You can control whether you get a single value or a list of
        values via the `number` arg. E.g.:
            >>> some_emitter()
            'a val'
            >>> some_emitter(1)
            ['a val']
            >>> some_emitter(2)
            ['a val', 'another val']

        Args:
            number: (Optional.) How many data values to emit. Default
                is None, which causes us to return a single value
                instead of a list.

        Returns:
            One emitted value if `number` is None, or a list of
            emitted values if `number` is an int.
        """
        if number is None:
            return self.emit(1)[0]
        return self.emit(number)

    @abstractmethod
    def emit(self, number: int) -> List[T]:
        """Returns a list of data values.

        You must override this in your subclass. It should return a
        list of generated data values.

        Args:
            number: An int; how many values to return.
        """

class RandomEmitter(Emitter):
    """Abstract base class for defining emitters that need RNG.

    Subclass this to implement an emitter object that uses randomized
    values. In your subclass, instead of calling the `random` module
    directly, use the `rng` attribute. Override the `seed` method if
    you have an emitter composed of multiple BaseRandomEmitters and
    need to seed multiple RNGs at once.

    Attributes:
        rng: A random.Random object. Use this for generating random
            values in subclasses.
        rng_seed: (Optional.) Any valid seed value you'd provide to
            random.seed. This value is used to reset the RNG when
            `reset` is called; it can be set to something else either
            directly or by calling `seed` and providing a new value.
            Default is None.
    """

    def __init__(self, rng_seed: Any = None) -> None:
        """Inits a BaseRandomEmitter.

        Args:
            rng_seed: See `rng_seed` attribute.
        """
        self.rng_seed = rng_seed
        self.reset()

    def reset(self) -> None:
        """Reset the emitter's RNG instance."""
        self.rng = random.Random(self.rng_seed)

    def seed(self, rng_seed: Any) -> None:
        """Seeds all RNGs on this object with the given seed value.

        Args:
            seed: Any valid seed value you'd provide to random.seed.
        """
        self.rng_seed = rng_seed
        self.rng.seed(rng_seed)


class StaticEmitter(Emitter):
    """Class for defining emitters that emit a static value.

    Attributes:
        value: The static value that is emitted.
    """

    def __init__(self, value: T) -> None:
        """Inits a StaticEmitter instance with the given value."""
        self.value = value

    def emit(self, number: int) -> List[T]:
        """Returns a list with the static val repeated `number` times."""
        return [self.value] * number

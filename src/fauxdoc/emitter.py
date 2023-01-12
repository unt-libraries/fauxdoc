"""Contains base Emitter classes, for emitting data values."""
from abc import ABC, abstractmethod
from typing import Generic, List, Optional, overload, Union

from fauxdoc.typing import CT


class Emitter(Generic[CT], ABC):
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
    def num_unique_values(self) -> Optional[int]:
        """Returns an int, the number of unique values emittable.

        This number should be relative to the next `emit` call. If your
        instance is one where `emits_unique_values` is True, then this
        should return the number of unique values that remain at any
        given time. Otherwise, this should give the total number of
        unique values that can be emitted. Return None if the number is
        unknowable (such as with purely generated values).
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

    @overload
    def __call__(self, number: None = None) -> CT:
        ...

    @overload
    def __call__(self, number: int) -> List[CT]:
        ...

    def __call__(self, number: Optional[int] = None) -> Union[CT, List[CT]]:
        """Emits one data value or a list of multiple values.

        Use the 'number' kwarg to control whether you get a single
        value or a list. E.g.:
            >>> some_emitter()
            'a val'
            >>> some_emitter(1)
            ['a val']
            >>> some_emitter(2)
            ['a val', 'another val']

        Implementation note: Subclasses should override `emit` and
        `emit_many` to define how to generate one and multiple values,
        respectively.

        Args:
            number: (Optional.) How many data values to emit. Default
                is None, which returns a one value instead of a list.

        Returns:
            One emitted value if `number` is None, or a list of
            emitted values if `number` is an int.
        """
        if number is None:
            return self.emit()
        if number == 1:
            return [self.emit()]
        return self.emit_many(number)

    @abstractmethod
    def emit(self) -> CT:
        """Return one data value."""

    @abstractmethod
    def emit_many(self, number: int) -> List[CT]:
        """Return multiple data values, as a list."""

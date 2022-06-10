"""Contains functions and classes for implementing counter emitters."""
import itertools
from typing import Callable, Iterator, List, Sequence

from solrfixtures.emitter import Emitter
from solrfixtures.mixins import ItemsMixin
from solrfixtures.typing import T


class Static(ItemsMixin, Emitter):
    """Class for emitting static values.

    Attributes:
        value: The static value that is emitted.
    """

    def __init__(self, value: T) -> None:
        """Inits a Static instance with the given value.

        Args:
            value: See `value` attribute.
        """
        self.value = value
        super().__init__(items=[value])

    def emit(self) -> T:
        return self.value

    def emit_many(self, number: int) -> List[T]:
        return [self.value] * number


class Iterative(Emitter):
    """Class for emitting values from an iterator.

    Iterative emitters are infinite and will restart from the
    beginning when they run out of values -- like itertools.cycle,
    without storing values in memory. That's why this class wants an
    iterator *factory* and not just an iterator: iterators by
    definition cannot be reset or copied. The only way to implement an
    emitter with a resettable iterator (without resorting to caching
    emitted values) is to generate a new iterator each time we need to
    reset. To do that, we need a factory that returns a new iterator.

    In many cases you may just want to emit a static sequence. For that
    you should use the Sequential subclass. Otherwise, if you're using
    a generator or some other iterator, you can just wrap it in a
    lambda, e.g.:

        >>> em = Iterative(lambda: iter(range(5)))
        >>> em(8)
        [0, 1, 2, 3, 4, 0, 1, 2]
        >>> em(8)
        [3, 4, 0, 1, 2, 3, 4, 0]

    The above example shows the default scenario, where the iterator
    state is kept between calls. If you want it to reset for each call,
    you can set the `reset_after_call` attribute to True. E.g.:

        >>> em = Iterative(lambda: iter(range(5)),
        ...                reset_after_call=True)
        >>> em(8)
        [0, 1, 2, 3, 4, 0, 1, 2]
        >>> em(8)
        [0, 1, 2, 3, 4, 0, 1, 2]

    Note that your iterator_factory *must* return an iterable with at
    least one value. Passing something like `lambda: iter([])` raises
    an error, to prevent an infinite loop when you try to emit.

    Attributes:
        iterator_factory: A callable that takes no args and returns an
            iterator.
        iterator: The currently active iterator, generated from the
            iterator_factory.
        reset_after_call: If True, the emitter automatically resets
            after each call.
    """

    def __init__(self,
                 iterator_factory: Callable[[], Iterator],
                 reset_after_call: bool = False) -> None:
        """Inits a Iterative emitter.

        Args:
            iterator_factory: See `iterator_factory` attribute.
            reset_after_call: See `reset_after_call` attribute.
        """
        self.iterator_factory = iterator_factory
        self.reset_after_call = reset_after_call
        self.reset()

    @property
    def iterator_factory(self) -> None:
        return self._iterator_factory

    @iterator_factory.setter
    def iterator_factory(self, factory: Callable[[], Iterator]) -> None:
        """Sets the iterator_factory property."""
        try:
            next(factory())
        except StopIteration:
            raise ValueError(
                "The provided 'iterator_factory' appears to return an empty "
                "iterator. This will result in an infinite loop while trying "
                "to emit values."
            )
        self._iterator_factory = factory

    def _infinite_iterator(self):
        """Returns an infinitely regenerating iterator."""
        while True:
            for item in self.iterator_factory():
                yield item

    def reset(self) -> None:
        """Resets self.iterator to the initial state."""
        self.iterator = self._infinite_iterator()

    def emit(self) -> T:
        """Returns one emitted value."""
        ret_value = next(self.iterator)
        if self.reset_after_call:
            self.reset()
        return ret_value

    def emit_many(self, number: int) -> List[T]:
        """Returns a list of emitted values.

        Args:
            number: See superclass.
        """
        ret_value = list(itertools.islice(self.iterator, 0, number))
        if self.reset_after_call:
            self.reset()
        return ret_value


class Sequential(ItemsMixin, Iterative):
    """Class for creating an Iterative emitter for a sequence.

    Although you can achieve this using a plain Iterative emitter:
        Iterative(lambda: iter(sequence))

    ... this class also stores the sequence in self.items so that all
    available choices can be accessed as a finite set of values.

    Attributes:
        iterator_factory: See superclass (Iterative).
        iterator: See superclass (Iterative).
        items: The sequence of values this emitter emits.
        reset_after_call: See superclass (Iterative).
    """

    def __init__(self,
                 items: Sequence,
                 reset_after_call: bool = False) -> None:
        """Inits a Sequential emitter instance.

        Args:
            items: See `items` attribute.
            reset_after_call: See `reset_after_call` attribute.
        """
        super().__init__(lambda: iter(self.items),
                         reset_after_call=reset_after_call, items=items)

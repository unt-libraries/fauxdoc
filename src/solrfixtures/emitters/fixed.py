"""Contains functions and classes for implementing counter emitters."""
import itertools
from typing import Callable, Iterator, List, Sequence

from solrfixtures.emitter import Emitter
from solrfixtures.typing import T


class Static(Emitter):
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

    def emit(self) -> T:
        return self.value

    def emit_many(self, number: int) -> List[T]:
        return [self.value] * number


class Iterative(Emitter):
    """Class for emitting values from an iterator.

    Iterative emitters are infinite and will restart from the
    beginning when they run out of values.

    Note that this class wants an iterator *factory* and not just an
    iterator. Why? Iterators by definition cannot be reset, nor can
    they be copied. The only way to implement an emitter with a
    resettable iterator (without resorting to caching emitted values)
    is to generate a new iterator each time we need to reset. To do
    that, we need a factory that returns a new iterator. In most cases,
    you can just wrap your iterator in a lambda, like this.

        >>> em = Iterative(lambda: iter(range(5)))
        >>> em(6)
        [0, 1, 2, 3, 4, 0, 1]

    Or of course you can use a function that returns a generator.
    However, very often -- including in the above example -- you just
    want to emit a static sequence of some kind (like a range or list).
    For this, you should use the Sequential class, instead.

    Attributes:
        iterator_factory: A callable that takes no args and returns an
            iterator.
        iterator: The currently active iterator, generated from the
            iterator_factory.
    """

    def __init__(self, iterator_factory: Callable[[], Iterator]) -> None:
        """Inits a Iterative emitter.

        Args:
            iterator_factory: See `iterator_factory` attribute.
        """
        self.iterator_factory = iterator_factory
        self.reset()

    def reset(self) -> None:
        """Resets self.iterator to the initial state."""
        self.iterator = self.iterator_factory()

    def emit(self) -> T:
        """Returns one emitted value."""
        try:
            return next(self.iterator)
        except StopIteration:
            self.reset()
            return next(self.iterator, None)

    def emit_many(self, number: int) -> List[T]:
        """Returns a list of emitted values.

        Args:
            number: See superclass.
        """
        result = list(itertools.islice(self.iterator, 0, number))
        n_result = len(result)
        if not n_result:
            return [None] * number
        if n_result == number:
            return result
        self.reset()
        result.extend(self.emit_many(number - n_result))
        return result


class Sequential(Iterative):
    """Class for creating an Iterative emitter for a sequence.

    Although you can acheive this using a plain Iterative emitter:
        Iterative(lambda: iter(sequence))

    ... this class also stores the sequence in self.items so that all
    available choices can be accessed as a finite value.

    Attributes:
        iterator_factory: See superclass.
        iterator: See superclass.
        items: The sequence of values this emitter emits.
    """

    def __init__(self, items: Sequence) -> None:
        """Inits a Sequential emitter instance.

        Args:
            items: See `items` attribute.
        """
        self.items = items
        self.reset()

    def reset(self) -> None:
        """Resets this emitter based on current self.items."""
        self.iterator_factory = lambda: iter(self.items)
        super().reset()

"""Contains functions and classes for implementing counter emitters."""
import itertools
from typing import Callable, Iterable, Iterator, List, Optional, Union

from solrfixtures.emitter import Emitter
from solrfixtures.typing import Number, T


class Sequential(Emitter):
    """Class for emitting values in a sequence from an iterator.

    Sequential emitters are infinite and will restart from the
    beginning when they run out of values.

    Note that this class wants an iterator *factory* and not just an
    iterator. Why? Iterators by definition cannot be reset, nor can
    they be copied. The only way to implement a sequential emitter with
    a resettable iterator (without resorting to caching emitted values)
    is to generate a new iterator each time we need to reset. To do
    that, we need a factory. In most cases you should just be able to
    wrap your iterator in a lambda, e.g.:

        >>> em = Sequential(lambda: iter(range(5)))
        >>> em(6)
        [0, 1, 2, 3, 4, 0, 1]

    If you just want an emitter based on an iterable value, you can use
    the `sequential_from_iterator` factory, if that's easier. (It just
    does the above for you.)

    Attributes:
        iterator_factory: A callable that takes no args and returns an
            iterator.
        iterator: The currently active iterator, generated from the
            iterator_factory.
    """

    def __init__(self, iterator_factory: Callable[[], Iterator]) -> None:
        """Inits a Sequential emitter.

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


def sequential_from_iterable(iterable: Iterable) -> Sequential:
    """Creates a Sequential emitter from the given iterable.

    This is just a convenience factory for when you just want to create
    a Sequential emitter from an iterable.

    Args:
        iterable: The iterable from which to create the Sequential
            emitter.
    """
    return Sequential(lambda: iter(iterable))

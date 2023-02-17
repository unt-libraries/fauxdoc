"""Contains functions and classes for implementing static emitters."""
import itertools
from typing import Callable, Iterator, List, Sequence
import warnings

from fauxdoc.emitter import Emitter
from fauxdoc.mixins import ItemsMixin
from fauxdoc.typing import T


class Static(ItemsMixin[T], Emitter[T]):
    """Class for emitting static values.

    Attributes:
        items: (Read-only.) See superclass (ItemsMixin).
        value: The static value that is emitted.
        emits_unique_values: (Read-only.) See superclass (Emitter). A
            Static emitter emits infinite values, so this is always
            False.
        num_unique_values: (Read-only.) See superclass (Emitter). A
            Static emitter always emits only one value, so this is
            always 1.
    """

    def __init__(self, value: T) -> None:
        """Inits a Static instance with the given value.

        Args:
            value: See 'value' attribute.
        """
        self._value = value
        super().__init__(items=[value])

    @property
    def value(self) -> T:
        """See the 'value' attribute."""
        return self._value

    @value.setter
    def value(self, value: T) -> None:
        """Sets the 'value' attribute."""
        self._value = value
        self._items = [value]

    def emit(self) -> T:
        """Returns the static value."""
        return self._value

    def emit_many(self, number: int) -> List[T]:
        """Returns a list with `number` copies of the static value.

        Args:
            number: See superclass.
        """
        return [self._value] * number


class Iterative(Emitter[T]):
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
        iterator: (Read-only.) The currently active iterator, generated
            from the iterator_factory.
        reset_after_call: If True, the emitter automatically resets
            after each call.
        emits_unique_values: (Read-only.) See superclass. Iterative
            emitters emit infinite values, so this is always False.
        num_unique_values: (Read-only.) See superclass. The number of
            unique values is not universally knowable, since the
            iterator that `iterator_factory` creates may generate
            infinite values, so this is None.
    """

    def __init__(self,
                 iterator_factory: Callable[[], Iterator[T]],
                 reset_after_call: bool = False) -> None:
        """Inits a Iterative emitter.

        Args:
            iterator_factory: See `iterator_factory` attribute.
            reset_after_call: See `reset_after_call` attribute.
        """
        self.reset_after_call = reset_after_call
        self.iterator_factory = iterator_factory

    @staticmethod
    def check_iter_factory(factory: Callable[[], Iterator[T]]) -> None:
        """Checks a user-provided iterator factory for errors."""
        try:
            next(factory())
        except StopIteration:
            raise ValueError(
                'The provided iterator factory appears to return an empty '
                'iterator. This will result in an infinite loop while trying '
                'to emit values.'
            )

    @staticmethod
    def make_infinite_iter(factory: Callable[[], Iterator[T]]) -> Iterator[T]:
        """Creates an infinitely regenerating iterator.

        Args:
            factory: A callable that takes no args and returns an
                iterator.
        """
        while True:
            for item in factory():
                yield item

    @property
    def iterator_factory(self) -> Callable[[], Iterator[T]]:
        """See the 'iterator_factory' attribute."""
        return self._iterator_factory

    @iterator_factory.setter
    def iterator_factory(self, factory: Callable[[], Iterator[T]]) -> None:
        """Sets the 'iterator_factory' attribute."""
        self.check_iter_factory(factory)
        self._iterator_factory = factory
        self.reset()

    @property
    def iterator(self) -> Iterator[T]:
        """See the 'iterator' attribute."""
        return self._iterator

    def reset(self) -> None:
        """Resets self.iterator to the initial state."""
        self._iterator = self.make_infinite_iter(self.iterator_factory)

    def emit(self) -> T:
        """Returns one emitted value."""
        ret_value = next(self._iterator)
        if self.reset_after_call:
            self.reset()
        return ret_value

    def emit_many(self, number: int) -> List[T]:
        """Returns a list of emitted values.

        Args:
            number: See superclass.
        """
        ret_value = list(itertools.islice(self._iterator, 0, number))
        if self.reset_after_call:
            self.reset()
        return ret_value


# TODO: Revisit Sequential in the future and reimplement it so that (at
# minimum) 'iterator_factory' is not mutable. This does not make sense
# for the Sequential emitter, but it was part of the v1.0.0 API, so I
# won't change it until v2.0.0.
#
# Background: In v1.0.0 Sequential was implemented as a subclass of
# Iterative. As such, the 'iterator_factory' attribute was mutable,
# although I didn't recognize or deal with any of the implications.
# Now that I'm going back and refactoring to make sure these kinds of
# things are explicit, I'm realizing it doesn't make much sense. But,
# for now, I'm implementing a mutable 'iterator_factory' as best as I
# can, for v1.1.0. Also: Sequential should not be a subclass of
# Iterative, as this violates LSP.

class Sequential(ItemsMixin[T], Emitter[T]):
    """Class for creating an emitter that iterates over a sequence.

    Although you can achieve this using a plain Iterative emitter:
        Iterative(lambda: iter(sequence))

    ... this class also stores the sequence in self.items so that all
    available choices can be accessed as a finite set of values.

    Like Iterative, Sequential is infinite: it repeats when it runs out
    of items.

    Note that, although this class uses nearly the same interface as
    Iterative, it is not a subclass of Iterative, since it can only
    handle sequences, and not any iterator. (This would violate LSP.)

    Attributes:
        items: (Read-only.) See superclass (ItemsMixin).
        iterator_factory: A callable that takes no args and returns an
            iterator. The returned iterator MUST iterate over a
            sequence. Setting this changes the `items` attribute so
            that it contains all items output by the iterator.
        iterator: (Read-only.) The currently active iterator, generated
            from the iterator_factory.
        reset_after_call: If True, the emitter automatically resets
            after each call.
        emits_unique_values: (Read-only.) See superclass (Emitter).
            Sequential emitters emit infinite values, so this is always
            False.
        num_unique_values: (Read-only.) See superclass (ItemsMixin).
    """

    def __init__(self,
                 items: Sequence[T],
                 reset_after_call: bool = False) -> None:
        """Inits a Sequential emitter instance.

        Args:
            items: The sequence of items you with to emit. It cannot be
                empty. (See `items` attribute.)
            reset_after_call: See `reset_after_call` attribute.
        """
        if not items:
            raise ValueError(
                'The supplied `items` sequence cannot be empty. This will '
                'result in an infinite loop when emitting items.'
            )
        super().__init__(items=items)
        self.reset_after_call = reset_after_call
        self._iterator_factory = lambda: iter(self.items)
        self.reset()

    @staticmethod
    def check_seq_iter_factory(factory: Callable[[], Iterator[T]]) -> None:
        """Checks to see if an iter factory probably returns sequence."""
        len_hint = getattr(factory(), '__length_hint__', lambda: None)()
        if not isinstance(len_hint, int):
            raise ValueError(
                'The provided iterator factory appears not to return a '
                'sequence iterator. The returned iterator must iterate over a '
                'finite sequence.'
            )

    def reset(self) -> None:
        """Resets self.iterator to the initial state."""
        self._iterator = Iterative.make_infinite_iter(self.iterator_factory)

    @property
    def iterator(self) -> Iterator[T]:
        """See the 'iterator' attribute."""
        return self._iterator

    @property
    def iterator_factory(self) -> Callable[[], Iterator[T]]:
        """See the 'iterator_factory' attribute."""
        return self._iterator_factory

    @iterator_factory.setter
    def iterator_factory(self, factory: Callable[[], Iterator[T]]) -> None:
        """Sets the 'iterator_factory' attribute.

        Setting 'iterator_factory' for Sequential emitters is now
        deprecated, since it's not a very intuitive way to set the
        emitted sequence, and it's impossible to ensure that the set
        factory actually returns a sequence. From now on, if you need
        to emit a different sequence, you should create a new
        Sequential emitter instance. The 'iterator_factory' attribute
        will become read-only in v2.0.0.
        """
        warnings.warn(
            f'Setting {type(self).__name__}.iterator_factory is deprecated; '
            f'in the next major version release this will be changed to a '
            f'read-only attribute. If you need to emit a different sequence, '
            f'please create a new {type(self).__name__} instance instead.',
            DeprecationWarning
        )
        Iterative.check_iter_factory(factory)
        self.check_seq_iter_factory(factory)
        self._items = tuple([item for item in factory()])
        self._iterator_factory = factory
        self.reset()

    def emit(self) -> T:
        """Returns one emitted value."""
        ret_value = next(self._iterator)
        if self.reset_after_call:
            self.reset()
        return ret_value

    def emit_many(self, number: int) -> List[T]:
        """Returns a list of emitted values.

        Args:
            number: See superclass (Emitter).
        """
        ret_value = list(itertools.islice(self._iterator, 0, number))
        if self.reset_after_call:
            self.reset()
        return ret_value

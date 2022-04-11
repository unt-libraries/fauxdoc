"""Contains emitters that wrap other emitters."""
from typing import Any, Callable, List, Optional, Sequence, Union

from solrfixtures.emitter import Emitter
from solrfixtures.group import ObjectGroup
from solrfixtures.typing import EmitterLikeCallable, T


class Wrap(Emitter):
    """General Emitter class for wrapping another emitter.

    The intention is to allow creating emitters that convert the values
    from a source emitter. The source emitter should be emitter-like in
    that, when you call it, you tell it how many values you want, and
    it returns a sequence containing that many values. The wrapper
    should act on each individual value in that sequence and return the
    transformed value.

    E.g.:
        >>> em1 = AutoIncrementNumber()
        >>> em2 = Wrap(AutoIncrementNumber(), str)
        >>> em1(5); em2(5)
        [0, 1, 2, 3, 4]
        ['0', '1', '2', '3', '4']

    Note that there is some overhead in wrapping one emitter with
    another. Instead of the above example, you could subclass
    AutoIncrementNumber, extending it so that it converts ints to strs
    internally. This does result in a slightly more performant emitter.
    However, the timing difference isn't huge, and the wrapper approach
    is much more flexible: you can create general-purpose wrapper
    functions to do generic data conversions instead of hard-coding it
    in each and every class that might need it. But -- as always, you
    should use whatever approach works best for your use case.
    
    Attributes:
        source: The object to wrap. An emitter-like is expected, but it
            *could* be any callable that takes an int (number of values
            to emit) and returns a sequence of that length.
        wrapper: A callable to serve as the wrapper. The wrapper should
            take one input value from the source sequence and return a
            corresponding value.
    """

    def __init__(self,
                 source: EmitterLikeCallable,
                 wrapper: Callable[[T], Any]) -> None:
        """Inits a Wrap emitter with a source and a wrapper callable.

        Args:
            source: See 'source' attribute for details.
            wrapper: See 'wrapper' attribute.
        """
        self.source = source
        self.wrapper = wrapper

    def reset(self) -> None:
        """Resets 'source' state, if it can be reset."""
        try:
            self.source.reset()
        except AttributeError:
            pass

    def seed(self, rng_seed: Any) -> None:
        """Seed or reseed the 'source' with the given rng_seed value.

        This does nothing if the 'source' object is not RandomEmitter-
        like and has no `seed` method.

        Args:
            rng_seed: Any seed value that the random module accepts.
        """
        try:
            self.source.seed(rng_seed)
        except AttributeError:
            pass

    def emit(self) -> T:
        """Returns an emitted value, run through `self.wrapper`."""
        return self.wrapper(self.source())

    def emit_many(self, number: int) -> List[T]:
        """Returns a list of emitted, wrapped values.

        Args:
            number: See superclass.
        """
        return [self.wrapper(v) for v in self.source(number)]


class WrapMany(Emitter):
    """Emitter class for wrapping multiple emitters.

    This is like `Wrap`, except it wraps multiple emitters. The wrapper
    callable should accept N arguments, where N is len(sources); the
    output for each source emitter is passed to 'wrapper' in 'sources'
    order.

    E.g.:
        >>> e = Wrap([StaticEmitter('Susan'), StaticEmitter('Hello!')],
        ...          lambda em_a, em_b: f'{em_a} says, "{em_b}"')
        >>> e(2)
        ['Susan says, "Hello!"', 'Susan says, "Hello!"']

    See the docstring for `Wrap`.

    Attributes:
        sources: An ObjectGroup of the objects to wrap. Emitter-like
            objects are expected, but they could be any callables that
            take an int (number of values to emit) and return a
            sequence of that length.
        wrapper: A callable to serve as the wrapper. The arg list
            should comprise one value from each source emitter output
            sequence.
    """

    def __init__(self,
                 sources: Sequence[EmitterLikeCallable],
                 wrapper: Callable) -> None:
        """Inits WrapMany with sources and a wrapper callable.

        Args:
            sources: A sequence of the objects to wrap. See 'sources'
                attribute for details. (You do not have to provide an
                ObjectGroup -- your sequence is converted.)
            wrapper: See 'wrapper' attribute.
        """
        self.sources = sources
        self.wrapper = wrapper

    @property
    def sources(self) -> ObjectGroup:
        """Returns the 'sources' attribute."""
        return self._sources

    @sources.setter
    def sources(self, sources: Sequence[EmitterLikeCallable]) -> None:
        """Sets the 'sources' attribute."""
        self._sources = ObjectGroup(*sources)

    def reset(self) -> None:
        """Resets state for each of 'sources', if possible."""
        self._sources.do_method('reset')

    def seed(self, rng_seed: Any) -> None:
        """Seed or reseed 'sources' with the given rng_seed value.

        This does nothing for any objects in 'sources' that lack a
        `seed` method.

        Args:
            rng_seed: Any seed value that the random module accepts.
        """
        self._sources.do_method('seed', rng_seed)

    def emit(self) -> T:
        """Returns emitted values, run through `self.wrapper`."""
        return self.wrapper(*(s() for s in self._sources))

    def emit_many(self, number: int) -> List[T]:
        """Returns a list of emitted, wrapped values.

        Args:
            number: See superclass.
        """
        return [self.wrapper(*args)
                for args in list(zip(*(s(number) for s in self._sources)))]

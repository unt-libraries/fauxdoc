"""Contains emitters that wrap other emitters."""
from inspect import signature
from typing import Any, Callable, List, Mapping, Optional, Sequence
from unittest.mock import call

from solrfixtures.emitter import Emitter
from solrfixtures.mixins import RandomWithChildrenMixin
from solrfixtures.typing import EmitterLikeCallable, T


class Wrap(RandomWithChildrenMixin, Emitter):
    """Abstract base class for creating wrapper emitters.

    Wrapper emitters are useful for easily converting output of an
    existing emitter without having to create a whole new class. This
    can be useful for simple operations like data conversion: the user
    initializes a new Wrap instance by supplying one or more source
    emitters and a wrapper function that takes the emitted data and
    returns the modified value.

    Optionally, the wrapper may also take an additional 'rng' kwarg, if
    it needs to generate random values. In this case the parent passes
    its 'rng' attribute, ensuring your wrapper uses the correct seed,
    etc.

    Note that there is some overhead in wrapping one emitter with
    another. If your use case requires extremely high efficiency,
    creating your own Emitter classes that do what you need will be a
    bit more performant. However, the wrapper approach is more
    flexible: you can create general-purpose wrapper functions to do
    generic data conversions instead of hard-coding it in each and
    every class that might need it.

    Attributes:
        emitters: (From RandomWithChildrenMixin.) This is a
            group.ObjectMap containing the source emitter-like
            instance(s) to wrap.
        wrapper: A callable that takes input values from the source
            emitter(s) and returns a corresponding value. Optionally,
            it may also take an 'rng' kwarg.
        rng: See superclass (RandomWithChildrenMixin).
        rng_seed: See superclass (RandomWithChildrenMixin).
    """

    def __init__(self,
                 source: Mapping[str, EmitterLikeCallable],
                 wrapper: Callable,
                 rng_seed: Optional[Any] = None):
        """Inits a Wrap emitter with a source and a wrapper callable.

        Args:
            source: A dict that maps labels to wrapped source emitters,
                used to populate the 'emitter' attribute.
            wrapper: See 'wrapper' attribute.
            rng_seed: See 'rng_seed' attribute.
        """
        self.wrapper = wrapper
        super().__init__(children=source, rng_seed=rng_seed)

    @property
    def wrapper(self) -> Callable:
        return self._wrapper

    @wrapper.setter
    def wrapper(self, wrapper: Callable) -> None:
        """Sets the `wrapper` property.

        This also looks for an 'rng' kwarg in the provided wrapper's
        call signature and sets a private '_wrapper_wants_rng'
        attribute.

        Arguments:
            wrapper: See 'wrapper' attribute.
        """
        try:
            wrapsig = signature(wrapper)
        except ValueError:
            self._wrapper_wants_rng = False
        else:
            self._wrapper_wants_rng = 'rng' in wrapsig.parameters
        self._wrapper = wrapper

    def _raise_wrapper_call_error(self, error: TypeError, args: Sequence,
                                  kwargs: Mapping) -> None:
        """Raises a TypeError based on a failed wrapper call.

        The intended use for this is to catch/raise a TypeError during
        either of the emit methods if the wrapper call fails.
        """
        call_str = str(call(*args, **kwargs))[4:]
        raise TypeError(
            f'Trying to call ``self.wrapper{call_str}`` raised a TypeError: '
            f'"{error}." (The signature for self.wrapper may not match what '
            f'the ``{type(self).__name__}`` class expects.)'
        ) from error


class WrapOne(Wrap):
    """Emitter class for wrapping one other emitter.

    Use this to create an emitter that converts values from one source
    emitter. When you call __init__, provide the source emitter and a
    wrapper function. The wrapper should take a value emitted by the
    source and return the modified value.

    E.g.:
        >>> from solrfixtures.emitters.fixed import Iterative
        >>> from solrfixtures.emitters.wrappers import Wrap
        >>> em = WrapOne(Iterative(lambda: itertools.count(), str))
        >>> em(5)
        ['0', '1', '2', '3', '4']

    See superclass (Wrap) for more details.

    Attributes:
        emitters: See superclass.
        wrapper: A callable that takes one input value from the source
            emitter and returns a corresponding value. Optionally,
            it may also take an 'rng' kwarg.
        rng: See superclass.
        rng_seed: See superclass.
    """

    def __init__(self,
                 source: EmitterLikeCallable,
                 wrapper: Callable,
                 rng_seed: Optional[Any] = None) -> None:
        """Inits a WrapOne emitter with a source and wrapper callable.

        Args:
            source: The emitter to wrap.
            wrapper: See 'wrapper' attribute.
        """
        super().__init__({'source': source}, wrapper, rng_seed)

    def emit(self) -> T:
        """Returns an emitted value, run through `self.wrapper`."""
        kwargs = {'rng': self.rng} if self._wrapper_wants_rng else {}
        args = (self._emitters['source'](),)
        try:
            return self._wrapper(*args, **kwargs)
        except TypeError as e:
            self._raise_wrapper_call_error(e, args, kwargs)

    def emit_many(self, number: int) -> List[T]:
        """Returns a list of emitted, wrapped values.

        Args:
            number: See superclass (Emitter).
        """
        emitted = self._emitters['source'](number)
        kwargs = {'rng': self.rng} if self._wrapper_wants_rng else {}
        try:
            return [self._wrapper(v, **kwargs) for v in emitted]
        except TypeError as e:
            self._raise_wrapper_call_error(e, (emitted[0],), kwargs)


class WrapMany(Wrap):
    """Emitter class for wrapping multiple other emitters.

    Use this to create an emitter that combines or converts values from
    multiple source emitters. When you call __init__, provide source
    emitters in a dict plus a wrapper function. The wrapper should take
    values emitted by the sources, using the dict keys as kwargs, and
    return the modified value.

    E.g.:
        >>> from solrfixtures.emitters.fixed import Sequential
        >>> from solrfixtures.emitters.wrappers import Wrap
        >>> em = WrapMany({
        ...     'name': Sequential(['Susan', 'Alice', 'Bob', 'Terry']),
        ...     'greet': Sequential(['Hi!', 'Yes?', 'What?', 'Yo!']),
        ... }, lambda name, greet: f'{name} says, "{greet}"')
        >>> em(4)
        ['Susan says, "Hi!"', 'Alice says, "Yes?"', 'Bob says, "What?"',
         'Terry says, "Yo!"']

    See superclass (Wrap) for more details.

    Attributes:
        emitters: See superclass.
        wrapper: A callable that takes one kwarg from each source
            emitter, using the label from the 'emitters' ObjectMap as
            the kwarg name. Optionally, it may take an addition 'rng'
            kwarg. It should return a final value based on the source
            emitter values.
        rng: See superclass.
        rng_seed: See superclass.
    """

    def emit(self) -> T:
        """Returns an emitted value, run through `self.wrapper`."""
        kwargs = {k: em() for k, em in self._emitters.items()}
        if self._wrapper_wants_rng:
            kwargs['rng'] = self.rng
        try:
            return self._wrapper(**kwargs)
        except TypeError as e:
            self._raise_wrapper_call_error(e, [], kwargs)

    def _check_emit_many_typeerror(self, error: TypeError,
                                   emitted_data: Sequence,
                                   has_rng_kwarg: bool):
        kwargs = {k: v[0] for k, v in emitted_data}
        if has_rng_kwarg:
            kwargs['rng'] = self.rng
        try:
            self._wrapper(**kwargs)
        except TypeError as e:
            self._raise_wrapper_call_error(e, [], kwargs)
        raise error

    def emit_many(self, number: int) -> List[T]:
        """Returns a list of emitted, wrapped values.

        Args:
            number: See superclass (Emitter).
        """
        emdata = [(k, em(number)) for k, em in self._emitters.items()]
        if self._wrapper_wants_rng:
            try:
                return [
                    self._wrapper(rng=self.rng, **{k: v[i] for k, v in emdata})
                    for i in range(number)
                ]
            except TypeError as e:
                self._check_emit_many_typeerror(e, emdata, True)
        try:
            return [
                self._wrapper(**{k: v[i] for k, v in emdata})
                for i in range(number)
            ]
        except TypeError as e:
            self._check_emit_many_typeerror(e, emdata, False)

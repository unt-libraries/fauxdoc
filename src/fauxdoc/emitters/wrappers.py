"""Contains emitters that wrap other emitters.

Wrapping an emitter lets you easily convert the output of an existing
emitter without having to create a whole new class. This can be useful
for simple operations like data conversion: the user initializes a new
WrapOne or WrapMany emitter instance by supplying one (WrapOne) or more
(WrapMany) source emitters plus a wrapper function that takes the
emitted data and returns the modified value.

Note that there is some overhead in wrapping one emitter with another.
If your use case requires extremely high efficiency, creating your own
Emitter classes that do what you need will be a bit more performant.
However, the wrapper approach is more flexible: you can create general-
purpose wrapper functions to do generic data conversions instead of
hard-coding them in each and every class that might need them.
"""
from inspect import signature, Signature
from typing import Any, Callable, Generic, List, Mapping, Optional
from unittest.mock import call

from fauxdoc.emitter import Emitter
from fauxdoc.mixins import RandomWithChildrenMixin
from fauxdoc.typing import EmitterLike, ImplementsRNG, OutputT, SourceT


class BoundWrapper(Generic[SourceT, OutputT]):
    """Utility class for user-provided wrapper functions.

    Use this to encapsulate any user-provided wrapper callable that's
    bound to an object that can provide RNG. Doing so adds a couple of
    handy features to the callable:

    - Automatic handling of RNG. If the user-provided callable includes
      an `rng` kwarg in its signature, then calls to the BoundWrapper
      instance automatically forward the `rng` attribute from the
      `bound_to` object to the wrapped function. If not, they don't.
      (This way, seeding and resetting RNG function as expected with
      the wrapper.)
    - Exposes the signature of the function via a `signature`
      attribute.
    - You can check that the user-provided wrapper function has the
      expected signature by using the `try_mock_call` method.

    This frees the object that the wrapper is bound to from having to
    implement these.

    Attributes:
        function: The function to wrap, called by calling this
            BoundWrapper instance.
        bound_to: The object that this wrapper is bound to. This object
            must implement RNG (see the typing.ImplementsRNG protocol).
            E.g., this will be the WrapOne or WrapMany instance that
            instantiates this wrapper.
        signature: An inspect.Signature object for the wrapped
            function's signature. If your wrapped function is a built-
            in method or type, then the signature cannot be determined,
            and it will be None.
        wants_rng: True if this wrapper has an `rng` kwarg in its call
            signature and therefore expects an RNG (random.Random obj)
            to be provided.
    """

    def __init__(self,
                 function: Callable[..., OutputT],
                 bound_to: ImplementsRNG) -> None:
        """Inits a BoundWrapper object with the given function.

        Args:
            function: See 'function' attribute.
            bound_to:
        """
        self.function = function
        self.bound_to = bound_to
        try:
            self.signature: Optional[Signature] = signature(function)
        except ValueError:
            # We get a ValueError if we try to use builtin methods or
            # types, like `str`.
            self.signature = None
            self.wants_rng = False
        else:
            self.wants_rng = 'rng' in self.signature.parameters

    def __call__(self, *args: SourceT, **kwargs: SourceT) -> OutputT:
        if self.wants_rng:
            return self.function(*args, rng=self.bound_to.rng, **kwargs)
        return self.function(*args, **kwargs)

    def try_mock_call(self, *args: Any, **kwargs: Any) -> None:
        """Tests the wrapped function signature by trying a mock call.

        Use this to check the user-provided function and raise a useful
        error if the call signature is not what's expected.

        Args:
            args: Sequence of positional args to pass to the function.
            kwargs: Mapping of kwargs to pass to the function
                (including `rng`, if applicable).

        Returns:
            None, if the call signature is fine.

        Raises:
            TypeError: If the mock call fails.
        """
        if self.wants_rng:
            kwargs['rng'] = self.bound_to.rng
        try:
            if self.signature is None:
                self.function(*args, **kwargs)
            else:
                self.signature.bind(*args, **kwargs)
        except TypeError as e:
            call_str = str(call(*args, **kwargs))[4:]
            raise TypeError(
                f'The callback provided to {type(self.bound_to).__name__} '
                f'does not appear to have the correct signature. Attempting a '
                f'mock call using {call_str} raised a TypeError: {e}.'
            ) from e


class Wrap(Generic[SourceT, OutputT], RandomWithChildrenMixin,
           Emitter[OutputT]):
    """(Deprecated) Abstract base class for creating wrapper emitters.

    I've moved the specific functionality that the Wrap ABC *used* to
    provide into the `BoundWrapper` class so that we can implement
    WrapOne and WrapMany separately without a base class. (I think,
    using `Wrap` as a base class and WrapOne and WrapMany having
    different `wrapper` signatures violated Liskov. The new solution is
    also a lot cleaner.)

    Because `Wrap` is part of the v1.0.0 API, I'm deprecating it rather
    than removing it. It will be removed in a future update.

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
                 source: Mapping[str, EmitterLike[SourceT]],
                 wrapper: Callable[..., OutputT],
                 rng_seed: Any = None):
        """Inits a Wrap emitter with a source and a wrapper callable.
        Args:
            source: A dict that maps labels to wrapped source emitters,
                used to populate the 'emitter' attribute.
            wrapper: See 'wrapper' attribute.
            rng_seed: See 'rng_seed' attribute.
        """
        super().__init__(children=source, rng_seed=rng_seed)
        self.wrapper: BoundWrapper[SourceT, OutputT] = BoundWrapper(
            wrapper, self
        )


class WrapOne(Generic[SourceT, OutputT], RandomWithChildrenMixin,
              Emitter[OutputT]):
    """Emitter class for wrapping one other emitter.

    Use this to create an emitter that converts the values produced by
    a single source emitter to some other output value. When you call
    __init__, provide the source emitter and a wrapper function.

    The wrapper should take one value emitted by the source and return
    the modified value. Optionally, the wrapper may also take an
    additional 'rng' kwarg, if it needs to generate random values. In
    that case the parent passes its 'rng' attribute, ensuring your
    wrapper uses the correct seed, etc.

    E.g.:
        >>> from fauxdoc.emitters.fixed import Iterative
        >>> from fauxdoc.emitters.wrappers import WrapOne
        >>> em = WrapOne(Iterative(lambda: itertools.count()), str)
        >>> em(5)
        ['0', '1', '2', '3', '4']

    Attributes:
        emitters: See mixins.ChildrenMixin.emitters.
        wrapper: A callable that takes one input value from the source
            emitter and returns a corresponding value. Optionally,
            it may also take an 'rng' kwarg.
        rng: See mixins.RandomMixin.rng.
        rng_seed: See mixins.RandomMixin.rng_seed.
    """

    def __init__(self,
                 source: EmitterLike[SourceT],
                 wrapper: Callable[..., OutputT],
                 rng_seed: Any = None) -> None:
        """Inits a WrapOne emitter with a source and wrapper callable.

        Args:
            source: The emitter to wrap.
            wrapper: See 'wrapper' attribute.
            rng_seed: See 'rng_seed' attribute.
        """
        super().__init__(children={'source': source}, rng_seed=rng_seed)
        self.wrapper: BoundWrapper[SourceT, OutputT] = BoundWrapper(
            wrapper, self
        )
        try:
            self.wrapper.try_mock_call(self._emitters['source']())
        except TypeError:
            raise
        finally:
            self.reset()

    def emit(self) -> OutputT:
        """Returns an emitted value, run through `self.wrapper`."""
        return self.wrapper(self._emitters['source']())

    def emit_many(self, number: int) -> List[OutputT]:
        """Returns a list of emitted, wrapped values.

        Args:
            number: See superclass (Emitter).
        """
        return [self.wrapper(v) for v in self._emitters['source'](number)]


class WrapMany(Generic[SourceT, OutputT], RandomWithChildrenMixin,
               Emitter[OutputT]):
    """Emitter class for wrapping multiple other emitters.

    Use this to create an emitter that combines or converts values from
    multiple source emitters. When you call __init__, provide your
    source emitters (as a dict) and your wrapper function.

    The wrapper should take the values emitted by the sources as kwargs
    and return the modified value. Optionally, the wrapper may also
    take an additional 'rng' kwarg, if it needs to generate random
    values. In this case the parent passes its 'rng' attribute,
    ensuring the wrapper uses the correct seed, etc.

    E.g.:
        >>> from fauxdoc.emitters.fixed import Sequential
        >>> from fauxdoc.emitters.wrappers import WrapMany
        >>> em = WrapMany({
        ...     'name': Sequential(['Susan', 'Alice', 'Bob', 'Terry']),
        ...     'greet': Sequential(['Hi!', 'Yes?', 'What?', 'Yo!']),
        ... }, lambda **kw: f'{kw['name']} says, "{kw['greet']}"')
        >>> em(4)
        ['Susan says, "Hi!"', 'Alice says, "Yes?"', 'Bob says, "What?"',
         'Terry says, "Yo!"']

    Attributes:
        emitters: See mixins.ChildrenMixin.emitters.
        wrapper: A callable that takes one kwarg from each source
            emitter, using the label from the 'emitters' ObjectMap as
            the kwarg name. Optionally, it may take an addition 'rng'
            kwarg. It should return a final value based on the source
            emitter values.
        rng: See mixins.RandomMixin.rng.
        rng_seed: See mixins.RandomMixin.rng_seed.
    """

    def __init__(self,
                 sources: Mapping[str, EmitterLike[SourceT]],
                 wrapper: Callable[..., OutputT],
                 rng_seed: Any = None) -> None:
        """Inits a WrapMany emitter with source emitters and a wrapper.

        Args:
            sources: The emitters to wrap, as a dict that maps kwarg
                names to emitters. The dict keys should correspond to
                kwarg names in your wrapper.
            wrapper: See 'wrapper' attribute.
            rng_seed: See 'rng_seed' attribute.
        """
        super().__init__(children=sources, rng_seed=rng_seed)
        self.wrapper: BoundWrapper[SourceT, OutputT] = BoundWrapper(
            wrapper, self
        )
        kwargs = {k: v() for k, v in self._emitters.items()}
        try:
            self.wrapper.try_mock_call(**kwargs)
        except TypeError:
            raise
        finally:
            self.reset()

    def emit(self) -> OutputT:
        """Returns an emitted value, run through `self.wrapper`."""
        kwargs = {k: em() for k, em in self._emitters.items()}
        return self.wrapper(**kwargs)

    def emit_many(self, number: int) -> List[OutputT]:
        """Returns a list of emitted, wrapped values.

        Args:
            number: See superclass (Emitter).
        """
        emdata = [(k, em(number)) for k, em in self._emitters.items()]
        return [
            self.wrapper(**{k: v[i] for k, v in emdata})
            for i in range(number)
        ]

"""Contains base Emitter classes, for emitting data values."""
from abc import ABC, abstractmethod
from copy import deepcopy
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

    Attributes:
        interface_name: A string representing the most specific
            interface that this class implements. It should correspond
            with the interface_description.
        interface_description: A verbose description of what's required
            for an object to use the interface named in interface_name.
            This should be operationalized via the 
            `_check_object_interface` method.
    """

    interface_name = 'Emitter'
    interface_description = (
        "To be Emitter-like, an object must 1. Be callable, returning a "
        "single value if called with no args and a list or tuple of values if "
        "called with a 'number' kwarg. And, 2. Have a `reset` method that "
        "resets state when called and takes no args."
    )

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

    @classmethod
    def _check_object_interface(cls, emitter: T) -> Any:
        """Raises a TypeError if the given object fails a type check.

        This method implements duck-typing checks to see if a given
        object conforms to the necessary interface for this class.
        Override as needed in base classes, e.g. to implement checks
        for subtypes. Note that this method is private; users should
        never call this directly but instead use `check_object`, which
        creates a deep copy of the object first.

        If you override this method, you probably need to override the
        `interface_name` and `interface_description` attributes also.
        
        Args:
            emitter: The object you want to check.

        Returns:
            The value that the emitter emitted during the type checks,
            if all checks pass.
        """
        err_msg = f"Object is not {cls.interface_name}-like"
        try:
            emitted_value = emitter()
        except TypeError:
            raise TypeError(f'{err_msg} (it is not callable).') from None
        try:
            multi_value = emitter(number=1)
        except TypeError:
            raise TypeError(
                f"{err_msg} (it does not take a 'number' kwarg when called)."
            ) from None
        if not isinstance(multi_value, (list, tuple)):
            raise TypeError (
                f"{err_msg} (it does not return a list or tuple when called "
                f"with a 'number' kwarg)."
            ) from None
        try:
            emitter.reset()
        except AttributeError:
            raise TypeError(
                f'{err_msg} (it lacks a `reset` method).'
            ) from None
        except TypeError:
            raise TypeError(
                f'{err_msg} (its `reset` method takes the incorrect number of '
                f'arguments).'
            ) from None
        return emitted_value

    @staticmethod
    def check_emitted_val_types(em_val: T, val_types: Sequence[type]) -> None:
        """Raises a TypeError if an emitted val is not a certain type.

        Args:
            em_val: A sample value from the emitter whose output value
                type you want to check.

        Returns:
            None, if all checks pass.
        """
        if not isinstance(em_val, val_types):
            type_strs = [f"`{vtype.__name__}`" for vtype in val_types]
            if len(val_types) == 1:
                type_str = type_strs[0]
            elif len(val_types) == 2:
                type_str = ' or '.join(type_strs)
            else:
                type_str = f"{', '.join(type_strs[:-1])}, or {type_strs[-1]}"
            raise TypeError(
                f"Object appears to emit values that are "
                f"`{type(em_val).__name__}`-type, not {type_str}-type."
            )

    @classmethod
    def check_object(cls,
                     emitter: T,
                     val_types: Optional[Sequence[type]] = None) -> T:
        """Raises a TypeError if the given object fails checks.

        This is a utility method to check that a given object conforms
        to the interface for this class. Optionally, it also checks
        that it emits the right type(s) of values, if the 'val_types'
        arg is provided.

        In subclasses, you should override `_check_object_interface`
        instead of this method if you need additional checks. If you do
        need to override this, be sure to make a deep copy of the
        emitter first before doing checks (assuming your checks may
        activate the object and could disturb saved state).

        Arguments:
            emitter: The object you want to check.
            val_types: (Optional.) A type, or a list/tuple of types, that
                you want to check the emitter output against. That
                check is skipped if not provided.
        """
        obj_to_check = deepcopy(emitter)
        try:
            emitted_value = cls._check_object_interface(obj_to_check)
        except TypeError as e:
            raise TypeError(
                f"{e} {cls.interface_description}"
            ) from None

        if val_types is not None:
            try:
                cls.check_emitted_val_types(emitted_value, val_types)
            except TypeError as e:
                raise TypeError(
                    f"Object is {cls.interface_name}-like but emits the wrong "
                    f"type of values. {e}"
                ) from None
        return emitter


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

    interface_name = 'RandomEmitter'
    interface_description = (
        "To be RandomEmitter-like, an object must 1. Be callable, returning "
        "one value if called with no args and a list or tuple of values if "
        "called with a 'number' kwarg. 2. Have a `reset` method that resets "
        "state and takes no args. And, 3. Have a `seed` method that takes an "
        "`rng_seed` arg, which it uses to seed all applicable RNGs on the "
        "object."
    )

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

    @classmethod
    def _check_object_interface(cls, emitter: T) -> Any:
        """Raises a TypeError if the given object fails a type check.

        This implements additional RandomEmitter-like checks.

        Args:
            emitter: The object you want to check.

        Returns:
            The value that the emitter emitted during the type checks,
            if all checks pass.
        """
        err_msg = f"Object is not {cls.interface_name}-like"
        emitted_value = super()._check_object_interface(emitter)
        try:
            emitter.seed(12345679)
        except AttributeError:
            raise TypeError(f'{err_msg} (it lacks a `seed` method).') from None
        except TypeError:
            raise TypeError(
                f'{err_msg} (its `seed` method takes the incorrect number of '
                f'arguments).'
            ) from None
        return emitted_value


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

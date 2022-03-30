"""
Contains classes for creating faux-data-generation profiles.
"""
from collections import OrderedDict
from typing import Any, Callable, Optional, Union

from solrfixtures.emitter import Emitter, StaticEmitter
from solrfixtures.emitters.choice import Choice
from solrfixtures.typing import EmitterLike, IntEmitterLike, T


class Field:
    """Class for representing a field in a schema."""

    IntOrIntEmitter = Union[int, IntEmitterLike]

    def __init__(self,
                 name: str,
                 emitter: EmitterLike,
                 repeat: Optional[IntOrIntEmitter] = None,
                 chance: Optional[IntOrIntEmitter] = None,
                 rng_seed: Any = None) -> None:
        """Inits a Field instance."""
        self.name = name
        self._init_emitter(emitter)
        self._init_repeat_emitter(repeat)
        self._init_gate_emitter(chance)
        self._cache = None
        self.rng_seed = rng_seed
        self.reset()

    def _init_emitter(self, emitter: EmitterLike) -> None:
        try:
            self.emitter = Emitter.check_object(emitter)
        except TypeError as e:
            raise TypeError(f"Incorrect type for 'emitter' attribute.") from e

    def _init_repeat_emitter(self, repeat: Optional[IntOrIntEmitter]) -> None:
        err_msg = (
            f"Incorrect type for 'repeat' argument. Expected an `int` or a "
            f"callable {Emitter.interface_name}-like that emits `int`s"
        )
        if callable(repeat):
            try:
                self.repeat_emitter = Emitter.check_object(repeat, (int,))
            except TypeError as e:
                raise TypeError(
                    f'{err_msg}; got a callable object that failed further '
                    f'type checks.'
                ) from e
        else:
            if repeat is not None and not isinstance(repeat, int):
                raise TypeError(f'{err_msg}, but got a `{type(repeat)}`.')
            self.repeat_emitter = StaticEmitter(repeat)

    def _init_gate_emitter(self, chance: Optional[IntOrIntEmitter]) -> None:
        err_msg = (
            f"Incorrect type for 'chance' argument. Expected an `int` between "
            f"0 and 100 or a callable {Emitter.interface_name}-like that "
            "emits `bool`s"
        )
        if callable(chance):
            try:
                self.gate_emitter = Emitter.check_object(chance, (bool,))
            except TypeError as e:
                raise TypeError(
                    f'{err_msg}; got a callable object that failed further '
                    f'type checks.'
                ) from e
        elif chance is None:
            self.gate_emitter = StaticEmitter(True)
        else:
            if not isinstance(chance, int):
                raise TypeError(f'{err_msg}, but got a `{type(chance)}`.')
            if not 0 <= chance <= 100:
                raise ValueError(
                    f"Incorrect 'chance' argument. `int` values must be 0 to "
                    f"100; got {chance}."
                )
            self.gate_emitter = Choice([True, False], [chance, 100 - chance])

    def reset(self) -> None:
        """Resets state on this field, including attached emitters."""
        for attr in ('emitter', 'repeat_emitter', 'gate_emitter'):
            emitter = getattr(self, attr)
            if emitter:
                try:
                    emitter.rng_seed = self.rng_seed
                except AttributeError:
                    pass
                emitter.reset()

    def seed(self, rng_seed: Any) -> None:
        """See superclass."""
        self.rng_seed = rng_seed
        for attr in ('emitter', 'repeat_emitter', 'gate_emitter'):
            emitter = getattr(self, attr)
            if emitter:
                try:
                    emitter.seed(rng_seed)
                except AttributeError:
                    pass

    def __call__(self) -> T:
        """Generates a new value via the emitter and field settings."""
        if self.gate_emitter():
            self._cache = self.emitter(self.repeat_emitter())
        else:
            self._cache = None
        return self._cache

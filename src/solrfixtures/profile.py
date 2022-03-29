"""
Contains classes for creating faux-data-generation profiles.
"""
from collections import OrderedDict
from typing import Any, Callable, Optional, Union

from solrfixtures.emitter import check_emitter, StaticEmitter
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
            self.emitter = check_emitter(emitter)
        except TypeError as e:
            raise TypeError(f"Incorrect type for 'emitter' attribute. {e}")

    def _init_repeat_emitter(self, repeat: Optional[IntOrIntEmitter]) -> None:
        if callable(repeat):
            try:
                self.repeat_emitter = check_emitter(repeat)
            except TypeError as e:
                raise TypeError(
                    f"Incorrect type for 'repeat' argument. A callable was "
                    f"provided, but it should be Emitter-like. {e}"
                )
        else:
            self.repeat_emitter = StaticEmitter(repeat)

    def _init_gate_emitter(self, chance: Optional[IntOrIntEmitter]) -> None:
        if callable(chance):
            try:
                self.gate_emitter = check_emitter(chance)
            except TypeError as e:
                raise TypeError(
                    f"Incorrect type for 'chance' argument. A callable was "
                    f"provided, but it should be Emitter-like. {e}"
                )
        elif chance is None:
            self.gate_emitter = StaticEmitter(True)
        else:
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

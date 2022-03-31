"""
Contains classes for creating faux-data-generation profiles.
"""
from collections import OrderedDict
from typing import Any, Callable, Optional, Union

from solrfixtures.emitter import Emitter, StaticEmitter
from solrfixtures.emitters.choice import Choice
from solrfixtures.typing import BoolEmitterLike, EmitterLike, IntEmitterLike, T


class Field:
    """Class for representing a field in a schema."""

    def __init__(self,
                 name: str,
                 emitter: EmitterLike,
                 repeat: Optional[IntEmitterLike] = None,
                 gate: Optional[BoolEmitterLike] = None,
                 rng_seed: Any = None) -> None:
        """Inits a Field instance."""
        self.name = name
        self.emitter = emitter
        self.repeat_emitter = StaticEmitter(None) if repeat is None else repeat
        self.gate_emitter = StaticEmitter(True) if gate is None else gate
        self._cache = None
        self.rng_seed = rng_seed
        self.reset()

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

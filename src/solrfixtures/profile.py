"""
Contains classes for creating faux-data-generation profiles.
"""
from collections import OrderedDict
from typing import Any, Callable, Optional, Union

from solrfixtures.emitters.choice import Choice
from solrfixtures.typing import EmitterLike


class Field:
    """Class for representing a field in a schema."""

    GettableInt = Union[int, Callable[[], int]]

    def __init__(self,
                 name: str,
                 emitter: EmitterLike,
                 repeat: Optional[GettableInt] = None,
                 chance: Optional[GettableInt] = None):
        """Inits a Field instance."""
        self.name = name
        self.emitter = emitter
        if callable(repeat):
            self.repeat = repeat
        else:
            self.repeat = lambda: repeat
        if callable(chance):
            self.chance = chance
        elif chance is not None:
            chooser = Choice([True, False], [chance, 100-chance])
            self.chance = lambda: chooser()
        else:
            self.chance = lambda: True

        # This is utterly horrible and needs to be re-thought, but for
        # now this is a working alternative to the above, and is
        # slightly faster.
        generator = self.emitter
        if repeat is not None:
            if callable(repeat):
                repeater = lambda thing: lambda: thing(repeat())
            else:
                repeater = lambda thing: lambda: thing(repeat)
            generator = repeater(self.emitter)

        if chance is not None:
            if not callable(chance):
                chance = Choice([True, False], [chance, 100-chance])
            chancer = lambda thing: lambda: thing() if chance() else None
            generator = chancer(generator)

        self._generate = generator
        self._cache = None

    @property
    def name(self) -> str:
        """Read-only property. Returns the 'name' attribute."""
        return self._name

    @name.setter
    def name(self, name: str) -> None:
        """Setter for the 'name' attribute. Can only be set once."""
        if hasattr(self, '_name'):
            raise AttributeError("Can't set attribute 'name'")
        if not isinstance(name, str):
            raise ValueError(
                "Attribute 'name' must be a str instance representing the "
                "name of this field."
            )
        self._name = name

    @property
    def emitter(self) -> EmitterLike:
        """Read-only property. Returns the 'emitter' attribute."""
        return self._emitter

    @emitter.setter
    def emitter(self, emitter: EmitterLike) -> None:
        """Setter for the 'emitter' attribute. Can only be set once."""
        if hasattr(self, '_emitter'):
            raise AttributeError("Can't set attribute 'emitter'")
        seems_valid = False
        try:
            check_single = emitter()
            check_multi = emitter(number=1)
            emitter.reset()
        except (TypeError, AttributeError):
            pass
        else:
            try:
                seems_valid = type(check_multi[0]) == type(check_single)
            except TypeError:
                pass
        if not seems_valid:
            raise ValueError(
                "Attribute 'emitter' must be an emitter.Emitter-like object, "
                "with the following qualities. 1. It must be callable, "
                "returning a single value if called with no arguments and a "
                "list of values if called with a `number` kwarg. 2. It must "
                "have a `reset` method that takes no args and resets emitter "
                "state when called."
            )
        self._emitter = emitter

    def reset(self) -> None:
        """Resets state on this field, including the emitter."""
        self.emitter.reset()

    def generate(self) -> Any:
        """Generates a new value via the emitter and field settings."""
        # self._cache = self._generate()
        if self.chance():
            self._cache = self.emitter(self.repeat())
        else:
            self._cache = None
        return self._cache

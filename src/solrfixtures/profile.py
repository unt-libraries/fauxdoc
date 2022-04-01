"""
Contains classes for creating faux-data-generation profiles.
"""
from collections import OrderedDict
from typing import Any, Callable, Optional, Union

from solrfixtures.emitter import Emitter, EmitterGroup, StaticEmitter
from solrfixtures.emitters.choice import Choice
from solrfixtures.typing import BoolEmitterLike, EmitterLike, IntEmitterLike, T


class Field:
    """Class for representing a field in a schema.

    Each Field instance wraps an emitter and provides some additional
    metadata and convenience features to allow it to work well within a
    schema. Like emitters, Field instances output a value each time
    they are called. Unlike emitters, they can only output one field
    value at a time (though, "one" value may be a list of emitted
    values, e.g. for a multi-valued field). Conceptually, each call to
    a field generates the data for that field for one record or doc.

    Note: Field controls include a separate `repeat` (how many values
    to output) AND `gate` (whether or not to output anything). You CAN
    gate the output just using `repeat` by allowing your repeat_emitter
    to output 0 -- e.g., a Choice(range(0, 5)) would output between 0
    and 5 values. And you can even control the chances of a 0 selection
    using weights. However, having a separate `gate` value makes it
    easier to determine what weights to assign for each behavior --
    especially if you want to use a PoissonChoice or GaussianChoice
    emitter for repeat values, where 0 may not fall along the same
    probability curve. Generally, my rule-of-thumb is never to use
    `repeat` to control gating. (If you do, also be aware that a 0
    repeat value will emit an empty list while a False gate value will
    emit None. See the tests in `tests/test_profile.py for some
    examples.)

    Attributes:
        name: A string representing the name by which this field should
            be referenced.
        emitter: The emitter-like object that emits data values for
            this field.
        repeat_emitter: An emitter-like object that is called each time
            the field generates data, used to determine how many values
            to emit that time. E.g., for a multi-valued field, it
            should return an appropriate integer for how many values to
            generate for a given call. (Some kind of Choice emitter
            would give you a randomized number for each call.) For a
            single-valued field, it should just be a StaticEmitter that
            emits None.
        gate_emitter: An emitter-like object that is called each time
            the field generates data, used to determine whether to
            generate a value at all for a given call. (True if yes,
            False if no.) E.g., for a field in your schema that is
            populated in ~10 percent of records or docs, a Chance(10)
            emitter instance would do the trick.
        emitter_group: An EmitterGroup instance that wraps/contains the
            three emitter instances associated with this field.
        rng_seed: (Optional.) Any valid seed value you'd provide to
            random.seed. This value is used to reset any RNGs on the
            three emitter instances attached to this field. Pass the
            seed value you want during __init__, and/or set a new value
            via the `seed` method.
        previous: A read-only attribute storing the previous value
            emitted by this field. (Fields may generate data based on
            values from other fields; this provides that access for
            other fields or emitters.)
    """

    def __init__(self,
                 name: str,
                 emitter: EmitterLike,
                 repeat: Optional[IntEmitterLike] = None,
                 gate: Optional[BoolEmitterLike] = None,
                 rng_seed: Any = None) -> None:
        """Inits a Field instance.

        Args:
            name: See `name` attribute.
            emitter: See `emitter` attribute.
            repeat: (Optional.) For multi-valued fields. This should be
                an emitter-like object that emits integers, used as the
                `repeat_emitter` attribute, to determine how many
                values to emit with each call. If a field is not multi-
                valued and only needs one value per record or doc, then
                use the default (None).
            gate: (Optional.) An emitter-like object that emits boolean
                values, used as the `gate_emitter` attribute. If a
                field should always have a value, then use the default
                (None).
            rng_seed: See `rng_seed` attribute.
        """
        self.name = name
        self.emitter = emitter
        self.repeat_emitter = StaticEmitter(None) if repeat is None else repeat
        self.gate_emitter = StaticEmitter(True) if gate is None else gate
        self.emitter_group = EmitterGroup(self.emitter, self.repeat_emitter,
                                          self.gate_emitter)
        self.rng_seed = rng_seed
        self.reset()

    @property
    def previous(self):
        """Read-only attribute to access the last generated value."""
        return self._cache

    def reset(self) -> None:
        """Resets state on this field, including attached emitters."""
        self._cache = None
        self.emitter_group.setattr('rng_seed', self.rng_seed)
        self.emitter_group.do_method('reset')

    def seed(self, rng_seed: Any) -> None:
        """Seeds all RNGs associated with emitters on this field.
        
        Args:
            rng_seed: The new seed you want to set. Ultimately this is
                passed to a random.Random instance, so it should be any
                value valid for seeding random.Random.
        """
        self.rng_seed = rng_seed
        self.emitter_group.do_method('seed', self.rng_seed)

    def __call__(self) -> T:
        """Generates one field value via the emitter.

        If `gate_emitter` returns False, then this returns None.
        
        For multi-valued fields (e.g. where `repeat_emitter` generates
        an integer), this generates a list of values of the appropriate
        length. For single-valued fields (e.g. where `repeat_emitter`
        generates None), this just generates the one value.
        """
        if self.gate_emitter():
            self._cache = self.emitter(self.repeat_emitter())
        else:
            self._cache = None
        return self._cache

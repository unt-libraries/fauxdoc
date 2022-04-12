"""
Contains classes for creating faux-data-generation profiles.
"""
from typing import Any, Callable, Dict, Optional, Union

from solrfixtures.group import ObjectGroup, ObjectMap
from solrfixtures.emitter import Emitter, StaticEmitter
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
    especially if you are using a poisson or gaussian weight
    distribution for repeat values, where 0 may not fall along the same
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
            populated in ~10 percent of records or docs, an emitter
            instance like emitters.choice.chance(10) would work.
        multi_valued: True if this Field can emit multiple values at
            once; False if it only emits one at a time.
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
        self._emitters = ObjectMap({})
        self.name = name
        self.emitter = emitter
        self.repeat_emitter = StaticEmitter(None) if repeat is None else repeat
        self.gate_emitter = StaticEmitter(True) if gate is None else gate
        self.rng_seed = rng_seed
        self.reset()

    @property
    def previous(self) -> Any:
        """Read-only attribute to access the last generated value."""
        return self._cache

    @property
    def emitter(self) -> EmitterLike:
        """Returns the 'emitter' attribute."""
        return self._emitters['emitter']

    @emitter.setter
    def emitter(self, emitter: EmitterLike) -> None:
        """Sets the 'emitter' attribute."""
        self._emitters['emitter'] = emitter

    @property
    def repeat_emitter(self) -> EmitterLike:
        """Returns the 'repeat_emitter' attribute."""
        return self._emitters['repeat']

    @repeat_emitter.setter
    def repeat_emitter(self, repeat_emitter: EmitterLike) -> None:
        """Sets the 'repeat_emitter' attribute.

        Also sets the 'multi_valued' attribute; False if the
        repeat_emitter only emits None, otherwise True.
        """
        self._emitters['repeat'] = repeat_emitter
        try:
            self.multi_valued = repeat_emitter.value is not None
        except AttributeError:
            self.multi_valued = True

    @property
    def gate_emitter(self) -> EmitterLike:
        """Returns the 'gate_emitter' attribute."""
        return self._emitters['gate']

    @gate_emitter.setter
    def gate_emitter(self, gate_emitter: EmitterLike) -> None:
        """Sets the 'gate_emitter' attribute."""
        self._emitters['gate'] = gate_emitter

    def reset(self) -> None:
        """Resets state on this field, including attached emitters."""
        self._cache = None
        self._emitters.setattr('rng_seed', self.rng_seed)
        self._emitters.do_method('reset')

    def seed(self, rng_seed: Any) -> None:
        """Seeds all RNGs associated with emitters on this field.
        
        Args:
            rng_seed: The new seed you want to set. Ultimately this is
                passed to a random.Random instance, so it should be any
                value valid for seeding random.Random.
        """
        self.rng_seed = rng_seed
        self._emitters.do_method('seed', self.rng_seed)

    def __call__(self) -> T:
        """Generates one field value via the emitter.

        Returns:
            None, one value, or a list of values. For multi-valued
            fields (e.g. where `repeat_emitter` generates an integer),
            this returns a list of values. For single-valued fields
            (e.g. where `repeat_emitter` generates None), this just
            generates the one value. If `gate_emitter` returns False,
            then this returns None.
        """
        if self._emitters['gate']():
            self._cache = self._emitters['emitter'](self._emitters['repeat']())
        else:
            self._cache = None
        return self._cache


class Schema:
    """Class to define schemas, for generating full records/docs.

    Pass the field objects you want in your schema to __init__, add
    them via `add_fields`, or modify `fields` directly. Call the object
    to generate the next record.

    Attributes:
        fields: An ObjectMap that maps field names (field.name) to
            field objects. Note that fields are stored in the order
            they're assigned, and output is generated in that same
            order. (If you have a field with an emitter that uses the
            cached data values from other fields, be sure it appears
            after the fields it copies data from.)
    """

    def __init__(self, *fields: Field) -> None:
        """Inits a Schema instance with the provided fields.

        Args:
            *fields: The Field instances that compose your schema. Note
                this is a star argument, so provide your fields as
                args. The `fields` attribute is generated from this.
                Your field names become keys.
        """
        self.fields = ObjectMap({})
        self.add_fields(*fields)

    def add_fields(self, *fields: Field) -> None:
        """Adds fields to your schema, in the order provided.

        Args:
            *fields: The Field instances to add. Note this is a star
                argument, so provided your fields as args.
        """
        self.fields.update({field.name: field for field in fields})

    def reset_fields(self) -> None:
        """Resets state on all schema fields."""
        self.fields.do_method('reset')

    def seed_fields(self, rng_seed: Any) -> None:
        """Seeds all RNGs on all schema fields.

        Args:
            rng_seed: The new seed you want to set. Ultimately this is
                passed to a random.Random instance, so it should be any
                value valid for seeding random.Random.
        """
        self.fields.do_method('seed', rng_seed)

    def __call__(self) -> Dict[str, Any]:
        """Generates field values for one record or doc.

        Returns:
            A dict, where field names are keys and field values are
            values.
        """
        return {fname: field() for fname, field in self.fields.items()}

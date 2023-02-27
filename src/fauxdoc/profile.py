"""Contains classes for creating faux-data-generation profiles."""
from typing import Any, Dict, Generic, List, Optional, Union

from fauxdoc.group import ObjectMap
from fauxdoc.emitters.fixed import Static
from fauxdoc.mixins import RandomWithChildrenMixin
from fauxdoc.typing import EmitterLike, FieldLike, T


class Field(RandomWithChildrenMixin, Generic[T]):
    """Class for representing a field in a schema.

    Each Field instance wraps an emitter and provides some additional
    metadata and convenience features to allow it to work well within a
    schema. Like an emitter, calling a Field instance outputs field
    data -- conceptually, each call generates the data for that field
    for one record or document. Unlike an emitter, you cannot provide
    an integer to output values for multiple records at a time. (Note:
    if your Field is multi-valued, then one call gives you the full
    list of values for that field for that record or document.)

    A Field provides configuration for gating or repeating values from
    a provided data emitter. As such, the implementation makes some
    assumptions around what the output of one Field instance should be.

    - A field is EITHER "single-valued" and emits one atomic value at a
      time, OR it is "multi-valued" and emits a *list* of atomic
      values. The same field instance should not be able to emit a
      single value with one call and multiple values with another.
    - One "atomic value" is relative to the field's data emitter. I.e.,
      for single-valued fields, `field()` is equivalent to
      `field.emitter()`, and for multi-valued fields, it is equivalent
      to `field.emitter(int)`. (An atomic value could be of any type,
      including a list, depending on the emitter. A multi-valued field
      will output a list of whatever type of atomic value the emitter
      outputs.)
    - HOW MANY values a multi-valued field outputs can vary from call
      to call.
    - Both single- and multi-valued fields may sometimes emit NOTHING.
      I.e., if, in a given collection of documents, a field is empty
      half the time, then you may want half of the corresponding Field
      instance calls to output None half the time. (Note that an empty
      multi-valued field outputs None, not [None].)
    - The `repeat_emitter` controls whether a field is single-valued or
      multi-valued. AND it controls how many values a multi-valued
      field emits on a given call. If the `repeat_emitter` is
      `fauxdoc.emitters.Static(None)` (i.e., it ONLY emits None) then
      the field is single-valued. If it emits integers, then the field
      is multi-valued, and the emitted integers control how many values
      are output.
    - The `gate_emitter` controls how often a field emits nothing. If
      calling the `gate_emitter` outputs True, then the field emits a
      value; otherwise, it emits None.
    - The edge case where `repeat_emitter` may emit integers 0 or 1 may
      be confusing, given all of the above. In these cases, the Field
      instance is still considered multi-valued and will always output
      a list (0 => [] and 1 => [value]).
    - Rules of thumb: 1) For a multi-valued field, `repeat_emitter`
      should output integers, and for single-valued fields, it should
      output None. 2) Always use `gate_emitter` to control whether or
      not a Field outputs a value. For multi-valued fields,
      `repeat_emitter` should output values >=1.

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
            single-valued field, it should just be a Static emitter
            that emits None.
        gate_emitter: An emitter-like object that is called each time
            the field generates data, used to determine whether to
            generate a value at all for a given call. (True if yes,
            False if no.) E.g., for a field in your schema that is
            populated in ~10 percent of records or docs, an emitter
            instance like emitters.choice.chance(0.1) would work.
        multi_valued: (Read-only.) True if this Field can emit multiple
            values at once; False if it only emits one at a time.
        hide: If True, the field generates and caches a value but is
            not included in schema output. This is for generating data
            to use as a basis for `BasedOnFields` emitters that *are*
            included in schema output.
        rng_seed: (Optional.) Any valid seed value you'd provide to
            random.seed. This value is used to reset any RNGs on the
            three emitter instances attached to this field. Pass the
            seed value you want during __init__, and/or set a new value
            via the `seed` method. You can set this independently, but
            it won't take effect until you reset.
        previous: (Read-only.) Stores the previous value emitted by
            this field.
    """

    def __init__(self,
                 name: str,
                 emitter: EmitterLike[T],
                 repeat: Optional[
                     Union[EmitterLike[None], EmitterLike[int]]
                 ] = None,
                 gate: Optional[EmitterLike[bool]] = None,
                 hide: bool = False,
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
            hidden: See `hidden` attribute.
            rng_seed: See `rng_seed` attribute.
        """
        self.name = name
        self.hide = hide
        super().__init__(children={
            'emitter': emitter,
            'repeat': repeat or Static(None),
            'gate': gate or Static(True)
        }, rng_seed=rng_seed)

    @property
    def multi_valued(self) -> bool:
        """See the 'multi_valued' attribute."""
        if hasattr(self.repeat_emitter, 'items'):
            return bool(self.repeat_emitter.items != [None])
        return True

    @property
    def previous(self) -> Any:
        """Read-only attribute to access the last generated value."""
        return self._cache

    @property
    def emitter(self) -> EmitterLike[T]:
        """See the 'emitter' attribute."""
        return self._emitters['emitter']

    @emitter.setter
    def emitter(self, emitter: EmitterLike[T]) -> None:
        """Sets the 'emitter' attribute."""
        self._emitters['emitter'] = emitter

    @property
    def repeat_emitter(self) -> Union[EmitterLike[None], EmitterLike[int]]:
        """See the 'repeat_emitter' attribute."""
        return self._emitters['repeat']

    @repeat_emitter.setter
    def repeat_emitter(self,
                       repeat_emitter: Union[EmitterLike[None],
                                             EmitterLike[int]]) -> None:
        """Sets the 'repeat_emitter' attribute."""
        self._emitters['repeat'] = repeat_emitter

    @property
    def gate_emitter(self) -> EmitterLike[bool]:
        """See the 'gate_emitter' attribute."""
        return self._emitters['gate']

    @gate_emitter.setter
    def gate_emitter(self, gate_emitter: EmitterLike[bool]) -> None:
        """Sets the 'gate_emitter' attribute."""
        self._emitters['gate'] = gate_emitter

    def reset(self) -> None:
        """Resets state on this field, including attached emitters."""
        super().reset()
        self._cache: Any = None

    def __call__(self) -> Optional[Union[T, List[T]]]:
        """Generates one field value via the emitter.

        Returns:
            None, one value, or a list of values. For multi-valued
            fields (e.g. where `repeat_emitter` generates an integer),
            this returns a list of values. For single-valued fields
            (e.g. where `repeat_emitter` generates None), this just
            generates the one value. If `gate_emitter` returns False,
            then this returns None.
        """
        if self.gate_emitter():
            self._cache = self.emitter(self.repeat_emitter())
        else:
            self._cache = None
        return self._cache


class Schema:
    """Class to define schemas, for generating full records/docs.

    Pass the field objects you want in your schema to __init__, add
    them via `add_fields`, or set them via `set_fields`. Call the
    Schema instance to generate the next record.

    Attributes:
        fields: An ObjectMap that maps field names (field.name) to
            field objects. Note that fields are stored in the order
            they're assigned, and output is generated in that same
            order. (If you have a field with an emitter that uses the
            cached data values from other fields, be sure it appears
            after the fields it copies data from.)
        hidden_fields: (Read-only. Immutable.) An ObjectMap that maps
            field names to field objects, where `field.hide` is True.
        public_fields: (Read-only. Immutable.) An ObjectMap that maps
            field names to field objects, where `field.hide` is False.
    """

    def __init__(self, *fields: FieldLike[Any]) -> None:
        """Inits a Schema instance with the provided fields.

        Args:
            *fields: The Field instances that compose your schema. Note
                this is a star argument, so provide your fields as
                args. The `fields` attribute is generated from this.
                Your field names become keys.
        """
        self.set_fields(*fields)

    def set_fields(self, *fields: FieldLike[Any]) -> None:
        """Sets `fields` from the given Field instances.

        This is a convenience method for setting the `fields`
        attribute, which is an ObjectMap instance, from one or more
        given Field instances. (You can still set `fields` directly by
        passing an ObjectMap.)

        Args:
            *fields: The Field instances to add. Note this is a star
                argument, so provide your fields as args.
        """
        self.fields: ObjectMap[FieldLike[Any]] = ObjectMap({})
        self.add_fields(*fields)

    def add_fields(self, *fields: FieldLike[Any]) -> None:
        """Adds schema fields, in the order provided.

        Args:
            *fields: The Field instances to add. Note this is a star
                argument, so provide your fields as args.
        """
        self.fields.update({field.name: field for field in fields})

    @property
    def hidden_fields(self) -> ObjectMap[FieldLike[Any]]:
        """See `hidden_fields` attribute.

        Note that this is a read-only calculated attribute. It gives
        an ObjectMap that is technically mutable, but because it
        doesn't actually store the ObjectMap, changes made to that obj
        aren't saved, so the attribute itself is effectively immutable.

        Use the `fields` attribute instead to change the fields in a
        schema.
        """
        return ObjectMap({
            fn: fd for fn, fd in self.fields.items() if fd.hide
        })

    @property
    def public_fields(self) -> ObjectMap[FieldLike[Any]]:
        """See `public_fields` attribute.

        Note that this is a read-only calculated attribute. It gives
        an ObjectMap that is technically mutable, but because it
        doesn't actually store the ObjectMap, changes made to that obj
        aren't saved, so the attribute itself is effectively immutable.

        Use the `fields` attribute instead to change the fields in a
        schema.
        """
        return ObjectMap({
            fn: fd for fn, fd in self.fields.items() if not fd.hide
        })

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
        doc = {}
        # We have to make sure hidden fields are evaluated even though
        # their output is not added directly to the doc. (Output from
        # hidden fields can be used in e.g. `fromfields` emitters.)
        # This is why we don't simply skip them, here.
        for fname, field in self.fields.items():
            val = field()
            if not field.hide:
                doc[fname] = val
        return doc

"""Contains emitters that use Field data to generate output."""
from inspect import signature
from typing import Any, Callable, List, Mapping, Optional, Sequence, Union
from unittest.mock import call

from fauxdoc.group import ObjectGroup
from fauxdoc.emitter import Emitter
from fauxdoc.mixins import RandomMixin
from fauxdoc.typing import FieldLike, T


class CopyFields(Emitter):
    """Emitter class for copying data from Field instances.

    Use this if you have fields in your schema that need to copy data
    from one or more existing fields. This emitter can handle these
    scenarios:
        - Creating an exact duplicate of one field, copying the value
          as-is for a single-valued field or the list of values from a
          multi-valued field.
        - Duplicating values from multiple fields into one field, as a
          value list.
        - Collapsing values from one multi-valued field OR multiple
          fields into a single string value, joined using a provided
          'separator'.

    Use a BasedOnFields emitter instead if you need to modify the
    values from existing fields or otherwise base your output on
    existing fields rather than copy it exactly.

    Note that, in your schema assignment, you should put each Field
    using this emitter AFTER all the fields it copies. E.g., the value
    being copied won't exist until the source field emits data.

    Attributes:
        source: An ObjectGroup containing the Field instance(s) to copy
            data from. Values are output in Field order.
        separator: (Optional.) A string value to use to join multiple
            values. If provided, then it's assumed you want multiple
            values collapsed into one string value.
    """

    def __init__(self,
                 source: Union[FieldLike, Sequence[FieldLike]],
                 separator: Optional[str] = None) -> None:
        """Inits a CopyFields obj with source fields and separator.

        Args:
            source: Provide either one Field instance or a sequence of
                Field instances (to copy data from).
            separator: (Optional.) See `separator` attribute.
        """
        self.source = source
        self.separator = separator

    @property
    def source(self) -> ObjectGroup:
        """Returns the 'source' attribute."""
        return self._source

    @source.setter
    def source(self, source: Union[FieldLike, Sequence[FieldLike]]) -> None:
        """Sets the 'source' attribute.

        Also sets a private '_single_valued' attribute, True if this
        emitter has one source field that emits single values.

        Args:
            source: One Field instance or a sequence of Field instances
                (to copy data from).
        """
        if isinstance(source, (list, tuple)):
            self._source = ObjectGroup(*source)
            self._single_valued = False
        else:
            self._source = ObjectGroup(source)
            self._single_valued = not source.multi_valued

    def reset_source(self) -> None:
        """Calls `reset` on all source fields.

        Note that calling `self.reset` does not automatically reset
        source fields because that behavior would generally be
        redundant. I.e., usually a CopyField instance and its source
        Field instances will belong to the same Schema instance, and
        when used in that context, calling the Schema's `reset_fields`
        method resets all source fields anyway. So with the primary use
        case, reseting sources when `self.reset` is called would reset
        them twice. This method is provided for unusual or advanced use
        cases where you're using a BasedOnField instance outside a
        schema, or your source fields aren't part of the same schema.
        """
        self._source.do_method('reset')

    def emit(self) -> T:
        """Returns one emitted value."""
        if self._single_valued:
            return self._source[0].previous
        vals = []
        for field in self._source:
            val = field.previous
            if val is not None:
                if not isinstance(val, (list, tuple)):
                    val = [val]
                vals.extend(val)
        if self.separator is None:
            return vals or None
        return self.separator.join([str(v) for v in vals])

    def emit_many(self, number: int) -> List[T]:
        """Returns a list of emitted values.

        Args:
            number: See superclass.
        """
        return [self.emit()] * number


class BasedOnFields(RandomMixin, CopyFields):
    """Emitter class for basing output on existing Field instances.

    Use this if you need to emit data that is *based on* the data from
    other fields. This is like CopyFields, but, instead of making a
    straight copy of the 'source' field, you supply an 'action' function
    that can modify the value(s) before returning anything.

    Like with CopyFields, the 'source' you supply may be a single field
    or a sequence of fields. If it's a single field, then the 'action'
    callable receives the raw data value from that field. If it's a
    sequence of fields, the 'action' callable receives a dictionary
    that maps source fields to their output values, using field names
    as keys.

    Note that this is faster than using wrapper emitters to wrap
    CopyFields output, although it's functionally equivalent.

    Also note that, in your schema assignment, you should put each
    Field using this emitter AFTER all of its source fields. E.g., the
    values being sourced won't exist until the source fields emit data.

    Attributes:
        source: An ObjectGroup containing the Field instance(s) to copy
            data from. Values are sent to the 'action' function in
            Field order.
        action: A callable that takes data from the source field(s) and
            returns some output value(s) based on the source data. The
            appropriate call signature depends on your source fields
            and whether your function requires RNG. 1) If you have one
            source field, the first positional arg provided will be the
            output value for that field. 2) Or, if you have multiple
            source fields, one kwarg for each source field will be
            provided, where the kwarg name is the field name and the
            value is the output value. 3) If you need RNG, supply an
            'rng' kwarg, and the RNG (random.Random) instance attached
            to the BasedOnFields instance will be provided.
        rng_seed: (Optional.) See parent class (RandomMixin).
    """

    def __init__(self,
                 source: Union[FieldLike, Sequence[FieldLike]],
                 action: Callable,
                 rng_seed: Any = None) -> None:
        """Inits a BasedOnFields instance.

        Args:
            source: Provide either one Field instance or a sequence of
                Field instances (to get base data values from).
            action: See `action` attribute.
            rng_seed: (Optional.) See `rng_seed` attribute.
        """
        super().__init__(source, rng_seed=rng_seed)
        self.action = action

    @property
    def action(self) -> Callable:
        return self._action

    @action.setter
    def action(self, action: Callable) -> None:
        """Sets the `action` property.

        This also looks for an 'rng' kwarg in the provided action's
        call signature and sets a private '_action_wants_rng'
        attribute.

        Arguments:
            action: See 'action' attribute.
        """
        try:
            actionsig = signature(action)
        except ValueError:
            self._action_wants_rng = False
        else:
            self._action_wants_rng = 'rng' in actionsig.parameters
        self._action = action

    def _raise_action_call_error(self, error: TypeError, args: Sequence,
                                 kwargs: Mapping) -> None:
        """Raises a TypeError based on a failed wrapper call.

        The intended use for this is to catch/raise a TypeError during
        either of the emit methods if the wrapper call fails.
        """
        call_str = str(call(*args, **kwargs))[4:]
        raise TypeError(
            f'Trying to call ``self.action{call_str}`` raised a TypeError: '
            f'"{error}." (The signature for self.action may not match what '
            f'the ``{type(self).__name__}`` class expects.)'
        ) from error

    def seed_source(self, rng_seed: Any) -> None:
        """Seeds all RNGs associated with source fields.

        Note that calling `self.seed` does not automatically reseed
        source fields because that behavior would generally be
        redundant. I.e., usually a BasedOnField instance and its source
        Field instances will belong to the same Schema instance, and
        when used in that context, calling the Schema's `seed_fields`
        method seeds all source fields anyway. So with the primary use
        case, seeding sources when `self.seed` is called would seed
        them twice. This method is provided for unusual or advanced use
        cases where you're using a BasedOnField instance outside a
        schema, or your source fields aren't part of the same schema.

        Args:
            rng_seed: The new seed you want to set. Ultimately this is
                passed to a random.Random instance, so it should be any
                value valid for seeding random.Random.
        """
        self._source.do_method('seed', rng_seed)

    def emit(self) -> T:
        """Returns one emitted value."""
        args = []
        kwargs = {}
        if len(self._source) == 1:
            args = [self._source[0].previous]
        else:
            for field in self._source:
                kwargs[field.name] = field.previous
        if self._action_wants_rng:
            kwargs['rng'] = self.rng
        try:
            return self.action(*args, **kwargs)
        except TypeError as e:
            self._raise_action_call_error(e, args, kwargs)

"""Contains emitters that use Field data to generate output."""
from typing import (
    Any, Callable, Generic, List, Optional, Sequence, Union
)

from fauxdoc.group import ObjectGroup
from fauxdoc.emitter import Emitter
from fauxdoc.emitters.wrappers import BoundWrapper
from fauxdoc.mixins import RandomMixin
from fauxdoc.typing import FieldLike, FieldReturn, OutputT, SourceT, T


# Local type alias -- not needed in other modules
SourceFields = Union[FieldLike[T], Sequence[FieldLike[T]]]


class SourceFieldGroup(ObjectGroup[FieldLike[T]]):
    """Provide utility features for groups of source fields.

    This class abstracts out (an admittedly small amount of)
    functionality around groups of Field or FieldLike objects, which
    are used as data sources for the CopyFields and BasedOnFields
    emitters.

    - Your supplied field list can be one single FieldLike instance or
      a Sequence of them.
    - Provides a property that tells you if your source field(s) output
      a single (singular) value, or a list of values.
    """

    def __init__(self, fields: SourceFields[T]):
        """Inits a SourceFieldGroup instance.

        Args:
            fields: You can provide a single FieldLike instance or a
                Sequence of them.
        """
        if isinstance(fields, Sequence):
            super().__init__(*fields)
            self._init_as_single_valued = False
        else:
            super().__init__(fields)
            self._init_as_single_valued = True

    @property
    def single_valued(self) -> bool:
        """True if there is one source field that is not multi-valued.

        If False, then you can assume the output of the group will
        always be a list of values.
        """
        # If there is one field in this group, it may have been
        # initialized singularly (as `field`) or not (as `[field]`).
        # Only the first is considered single-valued. The
        # `_init_as_single_valued` tells us this. We assume that, if
        # this is False, then it's intended to behave as multi-valued.
        # (This way, `single_valued` will return a logical value if the
        # field list is modified after it's created.)
        if len(self) == 1 and self._init_as_single_valued:
            # Note that pylint doesn't seem to like it if we don't do
            # something to tell it `self` is indexable, like wrapping
            # `self` in `list`.
            return not list(self)[0].multi_valued
        return False


class CopyFields(Generic[T], Emitter[Optional[Union[T, List[T], str]]]):
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

    Use CopyFields if you want an exact copy. Use BasedOnFields instead
    if you need to modify or otherwise base your output on values from
    existing fields.

    Note that, in your schema assignment, you should put each Field
    using this emitter AFTER all the fields it copies. E.g., the value
    being copied won't exist until the source field emits data.

    Attributes:
        source: A SourceFieldGroup instance containing the Field
            instance(s) to copy data from.
        separator: (Optional.) A string value to use to join multiple
            values. If provided, then it's assumed you want multiple
            values collapsed into one string value.
    """

    def __init__(self,
                 source: SourceFields[T],
                 separator: Optional[str] = None) -> None:
        """Inits a CopyFields obj with source fields and separator.

        Args:
            source: Provide either one Field instance or a sequence of
                Field instances (to copy data from).
            separator: (Optional.) See `separator` attribute.
        """
        self.separator = separator
        self.set_source_fields(source)

    def set_source_fields(self, fields: SourceFields[T]) -> None:
        """Sets the 'source' attr from a Field or Field sequence.

        This is a convenience method -- you can set 'source' directly,
        but in that case it must be a SourceFieldGroup instance.

        Args:
            fields: One or a sequence of Field instances to serve as
                the data source.
        """
        self.source: SourceFieldGroup[T] = SourceFieldGroup(fields)

    def reset_source(self) -> None:
        """Calls `reset` on all source fields.

        Note that the `reset` method does not automatically reset
        source fields -- you have to use `reset_source`.
        """
        self.source.do_method('reset')

    @property
    def single_valued(self) -> bool:
        """True if there is one source field that returns one value."""
        return self.source.single_valued

    def emit(self) -> Optional[Union[T, List[T], str]]:
        """Returns one emitted value."""
        if self.source.single_valued:
            return self.source[0].previous
        vals: List[T] = []
        for field in self.source:
            val = field.previous
            if val is not None:
                if not isinstance(val, (list, tuple)):
                    val = [val]
                vals.extend(val)
        if self.separator is None:
            return vals or None
        return self.separator.join([str(v) for v in vals])

    def emit_many(self, number: int) -> List[Optional[Union[T, List[T], str]]]:
        """Returns a list of emitted values.

        Args:
            number: See superclass.
        """
        return [self.emit()] * number


class BasedOnFields(Generic[SourceT, OutputT], RandomMixin, Emitter[OutputT]):
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

    Note that this performs better than using wrapper emitters to wrap
    CopyFields output, although it's functionally equivalent.

    Also note that, in your schema assignment, you should put each
    Field using this emitter AFTER all of its source fields. E.g., the
    values being sourced won't exist until the source fields emit data.

    Attributes:
        source: A SourceFieldGroup containing the Field instance(s) to
            copy data from. Values are sent to the 'action' function in
            Field order.
        action: A BoundWrapper callable that takes data from the source
            field(s) and returns some output value(s). The appropriate
            call signature depends on your source fields and whether
            your function requires RNG. 1) If you have one source
            field, the first positional arg provided will be the output
            value for that field. 2) Or, if you have multiple source
            fields, one kwarg for each source field will be provided,
            where the kwarg name is the field name and the value is the
            output value. 3) If you need RNG, supply an 'rng' kwarg,
            and the RNG (random.Random) instance attached to the
            BasedOnFields instance will be provided.
        rng_seed: (Optional.) See parent class (RandomMixin).
    """

    def __init__(self,
                 source: SourceFields[SourceT],
                 action: Callable[..., OutputT],
                 rng_seed: Any = None) -> None:
        """Inits a BasedOnFields instance.

        Args:
            source: Provide either one Field instance or a sequence of
                Field instances (to get base data values from).
            action: See `action` attribute.
            rng_seed: (Optional.) See `rng_seed` attribute.
        """
        super().__init__(rng_seed=rng_seed)
        self.set_source_fields(source)
        self.set_action_function(action)

    def set_source_fields(self, fields: SourceFields[SourceT]) -> None:
        """Sets the 'source' attr given a Field or Fields sequence.

        This is a convenience method -- you can set 'source' directly,
        but in that case it must be a SourceFieldGroup instance.

        Args:
            fields: One or a sequence of Field instances to serve as
                the data source.
        """
        self.source: SourceFieldGroup[SourceT] = SourceFieldGroup(fields)

    def set_action_function(self, function: Callable[..., OutputT]) -> None:
        """Sets the 'action' attr from a given function.

        This is a convenience method -- you can set 'action' directly,
        but in that case it must be a BoundWrapper instance.

        Args:
            function: A callable that gets passed to BoundWrapper to
                create the 'action' attribute.
        """
        self.action = BoundWrapper(function, self)

    @property
    def action(self) -> BoundWrapper[FieldReturn[SourceT], OutputT]:
        """The 'action' attribute."""
        return self._action

    @action.setter
    def action(self,
               action: BoundWrapper[FieldReturn[SourceT], OutputT]) -> None:
        """Sets the 'action' attribute.

        Args:
            action: See the 'action' attribute.
        """
        self._action = action
        if len(self.source) == 1:
            args = [self.source[0]()]
            kwargs = {}
        else:
            args = []
            kwargs = {field.name: field() for field in self.source}
        try:
            self._action.try_mock_call(*args, **kwargs)
        except TypeError:
            raise
        finally:
            self.reset()

    def reset_source(self) -> None:
        """Calls `reset` on all source fields.

        Note that the `reset` method does not automatically reset
        source fields -- you have to use `reset_source`.
        """
        self.source.do_method('reset')

    def seed_source(self, rng_seed: Any) -> None:
        """Calls `seed` on all source fields.

        Note that the `seed` method does not automatically seed source
        fields -- you have to use `seed_source`.

        Args:
            rng_seed: The new seed you want to set, to seed a
                random.Random object.
        """
        self.source.do_method('seed', rng_seed)

    def emit(self) -> OutputT:
        """Returns one emitted value."""
        if len(self.source) == 1:
            return self._action(self.source[0].previous)
        kwargs = {field.name: field.previous for field in self.source}
        return self._action(**kwargs)

    def emit_many(self, number: int) -> List[OutputT]:
        """Returns a list of emitted values.

        Args:
            number: See superclass.
        """
        return [self.emit()] * number

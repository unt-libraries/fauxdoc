"""Contains emitters that use Field data to generate output."""
from typing import Any, List, Optional, Sequence, Union

from solrfixtures.group import ObjectGroup
from solrfixtures.emitter import Emitter
from solrfixtures.typing import FieldLike


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

    If you need anything more complicated, you'll have to create a
    custom emitter.

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

    def emit(self, number: int) -> List[Any]:
        """Returns a list of emitted values.

        Each emitted value is a full copy of the source field(s). If
        'number' > 1, it emits multiple full copies.
        
        Args:
            number: How many values to return (int).
        """
        if self._single_valued:
            data = self._source[0].previous
        else:
            vals = []
            for field in self._source:
                val = field.previous
                if val is not None:
                    if not isinstance(val, (list, tuple)):
                        val = [val]
                    vals.extend(val)
            if self.separator is not None:
                data = self.separator.join([str(v) for v in vals])
            else:
                data = vals or None

        # This is a bit weird, but is done to satisfy the requirement
        # that each Emitter can emit multiple values depending on the
        # 'number' argument.
        return [data] * number

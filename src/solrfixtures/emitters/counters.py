"""Contains functions and classes for implementing counter emitters."""
import itertools
from typing import List, Optional, Union

from solrfixtures.emitter import Emitter
from solrfixtures.typing import Number


class AutoIncrementNumber(Emitter):
    """Emitter class for emitting number-based auto-incrementing IDs.

    Define the number to start with ('start'), and each value emitted
    will increment the number by 1. Optionally, if you need a number
    formatted in some special way, you can include a string template
    to use for formatting. With no template defined, this emits ints.
    With a template defined, this emits strings.

    Attributes:
        start: The number to start counting from.
        template: (Optional.) A string to use to format the number. You
            must format the string such that `template.format(n)`,
            where `n` is the number, will return your formatted number.
            E.g.: template "A{}B" yields "A0B", "A1B", etc.; "A{0}{0}"
            yields "A00", "A11", etc.
    """
    def __init__(self,
                 start: Number = 0,
                 template: Optional[str] = None) -> None:
        """Inits an AutoIncrementNumber with a start val and template.

        Args:
            start: (Optional.) See `start` attribute. Default is 0.
            template: (Optional.) See `template` attribute.
        """
        self.start = start
        self.template = template
        self.reset()

    def reset(self) -> None:
        """Resets the current count back to `self.start`."""
        self._count = self.start

    @property
    def emits_unique_values(self) -> bool:
        """Returns True; all AutoIncrement instances emit unique vals."""
        return True

    def emit(self, number: int) -> List[Union[str, int]]:
        """Returns a list of emitted values.

        Args:
            number: How many values to return (int).
        """
        if self.template is None:
            data = list(range(self._count, self._count + number))
        else:
            data = [self.template.format(n)
                    for n in range(self._count, self._count + number)]
        self._count += number
        return data

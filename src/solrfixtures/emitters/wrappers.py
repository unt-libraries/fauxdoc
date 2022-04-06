"""Contains emitters that wrap other emitters."""
from typing import Any, Callable, List, Sequence, Union

from solrfixtures.emitter import Emitter
from solrfixtures.typing import EmitterLike, T


class Wrap(Emitter):
    """General Emitter class for wrapping another emitter.

    The intention is to allow creating emitters that convert the
    values that another emitter emits, e.g.:
    Wrap(AutoIncrementNumber(), str) creates an emitter that outputs
    auto-incrementing numbers as strings.
    
    Attributes:
        source: The emitter-like object to wrap. It *could* be any
            callable that takes an int (number of values to emit) and
            returns a sequence of that length.
        wrapper: A callable to serve as the wrapper. The wrapper should
            take one input value from the source sequence and return a
            corresponding value.
    """

    def __init__(self,
                 source: Union[Callable[[int], Sequence], EmitterLike],
                 wrapper: Callable[[T], Any]) -> None:
        """Inits a Wrap emitter with a source and wrapper."""
        self.source = source
        self.wrapper = wrapper

    def reset(self) -> None:
        """Resets 'source' state, if it can be reset."""
        try:
            self.source.reset()
        except AttributeError:
            pass

    def emit(self, number: int) -> List[T]:
        """Returns wrapped values.
        
        Args:
            number: An int; how many values to emit.
        """
        return [self.wrapper(v) for v in self.source(number)]

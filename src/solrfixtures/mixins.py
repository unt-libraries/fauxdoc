"""Contains mixin classes."""
import random
from typing import Any, List


class RandomMixin:
    """Mixin class for defining components that need RNG.

    Use this to implement an object that generates randomized values.
    In your subclass, instead of calling the `random` module directly,
    use the 'rng' attribute. Override the `reset` and `seed` methods if
    you have something composed of multiple components using
    RandomMixin and need to seed multiple RNGs at once.

    Attributes:
        rng: A random.Random object. Use this for generating random
            values in subclasses.
        rng_seed: (Optional.) Any valid seed value you'd provide to
            random.seed. This value is used to reset the RNG when
            `reset` is called; it can be set to something else either
            directly or by calling `seed` and providing a new value.
            Default is None.
    """

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """Inits an object using RandomMixin.

        Args:
            *args: Args to pass through to the parent class' __init__.
            **kwargs: Kwargs to pass through to the parent class'
                __init__. Optionally, if you include 'rng_seed', then
                it is used as the 'rng_seed' attribute and is NOT
                passed to the parent.
        """
        self.rng_seed = kwargs.pop('rng_seed', None)
        super().__init__(*args, **kwargs)
        self.reset()

    def reset(self) -> None:
        """Reset the emitter's RNG instance."""
        self.rng = random.Random(self.rng_seed)
        try:
            super().reset()
        except AttributeError:
            pass

    def seed(self, rng_seed: Any) -> None:
        """Seeds all RNGs on this object with the given seed value.

        Args:
            seed: Any valid seed value you'd provide to random.seed.
        """
        self.rng_seed = rng_seed
        self.rng.seed(rng_seed)
        try:
            super().seed(rng_seed)
        except AttributeError:
            pass


class ItemsMixin:
    """Mixin class for emitters that emit based on a list of items.

    This is super simple, but it provides a reliable interface for
    emitters that emit from a finite set of values.

    Attributes:
        items: (Optional.) The sequence of values that this emitter
            outputs. Defaults to an empty list.
    """

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """Inits an object using ItemsMixin.

        Args:
            *args: Args to pass through to the parent class' __init__.
            **kwargs: Kwargs to pass through to the parent class'
                __init__. If you include 'items', then it is used as
                the 'items' attribute and is NOT passed through to
                parent classes.
        """
        self._items = kwargs.pop('items', [])
        super().__init__(*args, **kwargs)

    @property
    def items(self) -> List[Any]:
        """Returns this emitter's list of items."""
        return self._items

    @property
    def num_unique_values(self) -> int:
        """Returns an int, the number of unique values emittable."""
        return len(set(self._items))

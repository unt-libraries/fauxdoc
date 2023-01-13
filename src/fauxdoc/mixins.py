"""Contains mixin classes."""
import random
from typing import Any, Generic, Sequence

from fauxdoc.group import ObjectMap
from fauxdoc.typing import EmitterLike, T


class RandomMixin:
    """Mixin class for defining components that need RNG.

    Use this to implement an object that generates randomized values.
    In your subclass, instead of calling the `random` module directly,
    use the 'rng' attribute.

    If you also need child emitters, use RandomWithChildrenMixin,
    to get RandomMixin and ChildrenMixin to play well together.

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
        """Resets the emitter's RNG instance."""
        self.rng = random.Random(self.rng_seed)
        supr = super()
        if hasattr(supr, 'reset'):
            supr.reset()

    def seed(self, rng_seed: Any) -> None:
        """Seeds all RNGs on this object with the given seed value.

        Args:
            seed: Any valid seed value you'd provide to random.seed.
        """
        self.rng_seed = rng_seed
        self.rng.seed(rng_seed)
        supr = super()
        if hasattr(supr, 'seed'):
            supr.seed(rng_seed)


class ItemsMixin(Generic[T]):
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
        self._items: Sequence[T] = kwargs.pop('items', [])
        super().__init__(*args, **kwargs)

    @property
    def items(self) -> Sequence[T]:
        """Returns this emitter's list of items."""
        return self._items

    @property
    def num_unique_values(self) -> int:
        """Returns an int, the number of unique values emittable."""
        return len(set(self._items))


class ChildrenMixin:
    """Mixin class for anything that needs to use child emitters.

    All this does is give you a self._emitters attribute (and
    associated public `emitters` property) where you can add whatever
    child emitters you need to use in generating values for your parent
    to emit.

    If you also need RNG, then use the RandomWithChildrenMixin, to get
    ChildrenMixin and RandomMixin to play well together.

    Attributes:
        emitters: An ObjectMap mapping labels to child emitters.
    """

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """Inits an object using ChildrenMixin.

        Args:
            *args: Args to pass through to the parent class' __init__.
            **kwargs: Kwargs to pass through to the parent class'
                __init__. Optionally, if you include 'children', then
                that is used to populate the private '_emitters' attr.
        """
        self._emitters: ObjectMap[EmitterLike[Any]] = ObjectMap(
            kwargs.pop('children', {})
        )
        super().__init__(*args, **kwargs)

    @property
    def emitters(self) -> ObjectMap[EmitterLike[Any]]:
        """Returns the children emitters, as a dict-like ObjectMap."""
        return self._emitters

    def reset(self) -> None:
        """Resets this emitter and all children."""
        self._emitters.do_method('reset')
        supr = super()
        if hasattr(supr, 'reset'):
            supr.reset()


class RandomWithChildrenMixin(RandomMixin, ChildrenMixin):
    """Mixin class for RandomMixin + ChildrenMixin.

    Use this instead of RandomMixin and / or ChildrenMixin if your
    parent emitter or any of your children need RNG. This takes care of
    resetting and seeding the children correctly when `reset` and
    `seed` are called on the parent.
    """

    def reset(self) -> None:
        """Resets this emitter and all children, including RNG."""
        self._emitters.setattr('rng_seed', self.rng_seed)
        super().reset()

    def seed(self, rng_seed: Any) -> None:
        """Seeds RNG for this emitter and all children."""
        self._emitters.do_method('seed', rng_seed)
        try:
            super().seed(rng_seed)
        except AttributeError:
            pass

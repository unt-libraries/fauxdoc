"""Contains tests for deprecations."""
from typing import Callable, Sequence, Union
import warnings

from fauxdoc.typing import EmitterLike, T


def test_typing_number_warning():
    with warnings.catch_warnings(record=True) as caught:
        from fauxdoc.typing import Number
        assert len(caught) == 1
        assert caught[0].category is DeprecationWarning
        msg = str(caught[0].message)
        assert 'Number is deprecated' in msg
        assert 'use float instead' in msg
        assert Number == float


def test_typing_emitterlikecallable_warning():
    with warnings.catch_warnings(record=True) as caught:
        from fauxdoc.typing import EmitterLikeCallable
        assert len(caught) == 1
        assert caught[0].category is DeprecationWarning
        msg = str(caught[0].message)
        assert 'EmitterLikeCallable is deprecated' in msg
        assert 'use EmitterLike instead' in msg
        assert EmitterLikeCallable == Union[
            Callable[[int], Sequence[T]],
            EmitterLike[T]
        ]


def test_typing_stremitterlike_warning():
    with warnings.catch_warnings(record=True) as caught:
        from fauxdoc.typing import StrEmitterLike
        assert len(caught) == 1
        assert caught[0].category is DeprecationWarning
        msg = str(caught[0].message)
        assert 'StrEmitterLike is deprecated' in msg
        assert 'use EmitterLike[str] instead' in msg
        assert StrEmitterLike == EmitterLike[str]


def test_typing_intemitterlike_warning():
    with warnings.catch_warnings(record=True) as caught:
        from fauxdoc.typing import IntEmitterLike
        assert len(caught) == 1
        assert caught[0].category is DeprecationWarning
        msg = str(caught[0].message)
        assert 'IntEmitterLike is deprecated' in msg
        assert 'use EmitterLike[int] instead' in msg
        assert IntEmitterLike == EmitterLike[int]


def test_typing_boolemitterlike_warning():
    with warnings.catch_warnings(record=True) as caught:
        from fauxdoc.typing import BoolEmitterLike
        assert len(caught) == 1
        assert caught[0].category is DeprecationWarning
        msg = str(caught[0].message)
        assert 'BoolEmitterLike is deprecated' in msg
        assert 'use EmitterLike[bool] instead' in msg
        assert BoolEmitterLike == EmitterLike[bool]


def test_typing_dir_contains_deprecated_things():
    import fauxdoc
    dir_listing = dir(fauxdoc.typing)
    for item in fauxdoc.typing.DEPRECATED.keys():
        assert item in dir_listing


def test_wrappers_wrap_warning():
    with warnings.catch_warnings(record=True) as caught:
        from fauxdoc.emitters.wrappers import Wrap
        assert len(caught) == 1
        assert caught[0].category is DeprecationWarning
        msg = str(caught[0].message)
        assert 'Wrap is deprecated' in msg
        assert 'use WrapOne or WrapMany instead' in msg
        assert Wrap.__name__ == 'Wrap'
        assert Wrap.__qualname__ == 'Wrap'


def test_wrappers_dir_contains_deprecated_things():
    import fauxdoc
    dir_listing = dir(fauxdoc.emitters.wrappers)
    for item in fauxdoc.emitters.wrappers.DEPRECATED.keys():
        assert item in dir_listing


def test_emitters_wrap_warning():
    with warnings.catch_warnings(record=True) as caught:
        # See emitters/__init__.py for more of an explanation, but --
        # when we use "from" to import Wrap from emitters, we end up
        # with two warnings. This is expected.
        from fauxdoc.emitters import Wrap
        assert len(caught) == 2

        # If we import "emitters" and then access Wrap as an attribute,
        # we just get the one warning.
        from fauxdoc import emitters
        _ = emitters.Wrap
        assert len(caught) == 3

        for warning in caught:
            assert warning.category is DeprecationWarning
            msg = str(warning.message)
            assert 'Wrap is deprecated' in msg
            assert 'use WrapOne or WrapMany instead' in msg
        assert Wrap.__name__ == 'Wrap'
        assert Wrap.__qualname__ == 'Wrap'


def test_emitters_dir_contains_deprecated_things():
    import fauxdoc
    dir_listing = dir(fauxdoc.emitters)
    for item in fauxdoc.emitters.DEPRECATED.keys():
        assert item in dir_listing


def test_fixed_sequential_set_iteratorfactory_warning():
    with warnings.catch_warnings(record=True) as caught:
        from fauxdoc.emitters.fixed import Sequential
        assert len(caught) == 0
        seq = Sequential([1, 2, 3])
        assert len(caught) == 0
        seq.iterator_factory = lambda: iter([4, 5, 6])
        assert len(caught) == 1
        assert caught[0].category is DeprecationWarning
        msg = str(caught[0].message)
        assert 'iterator_factory is deprecated' in msg
        assert 'create a new Sequential instance instead' in msg

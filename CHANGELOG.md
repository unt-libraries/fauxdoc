# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/), and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).


## [v1.1.0](https://github.com/unt-libraries/fauxdoc/compare/v1.0.0...v1.1.0) — 2023-02-27

Overview of what's new in this version:
- `fauxdoc` is now fully typed and passes `mypy --strict` checks.
- Much refactoring. Fixing type hints revealed some underlying issues, and I've applied fixes and changes while leaving the public API as intact as possible — see details below about what exactly has changed.
- A small number of deprecations to be removed in v2. See details below.
- Previously undefined behavior, mainly around instance attributes, has been defined, documented, and tested. Attributes that are not read-only now have defined behavior when they are set after object instantiation.

### Added

- A `py.typed` file to indicate that the package now has type hints.
- New `mypy_strict` tox environment for running `mypy` tests.
- New tox environments for testing a package built using `build_package` against a target Python version: `py37-test_built_package` through `py311-test_built_package`.
- A new kwarg for initializing `fauxdoc.emitters.choice.Choice` instances: `cum_weights` can now be supplied, if needed. Note that you can only supply `weights` or `cum_weights` — not both. All previous args/kwargs still work as before.
- A `fauxdoc.emitters.fromfields.SourceFieldGroup` class. This is a subtype of `fauxdoc.groups.ObjectGroup`, used in `fauxdoc.emitters.fromfield` emitters to represent groups of source fields. It now implements the `single_valued` property that was previously only a private attribute on the `fauxdoc.emitters.fromfields.CopyFields` class.
- Additions to `fauxdoc.emitters.fromfields` emitters (`CopyFields` and `BasedOnFields`):
    - A new **public** attribute, `single_valued`, for both `CopyFields` and `BasedOnFields`. This attribute was previously private.
    - `set_source_fields` method, on `CopyFields` and `BasedOnFields` — used to set the `source` attribute from one or a list of `Field` instances. (You can set `source` directly, but that requires a `fauxdoc.emitters.fromfields.SourceFieldGroup` instance. This is just for convenience.)
    - `set_action_function` method, on `BasedOnFields` — used to set the `action` attribute from a function. (You can set `action` directly, but that requires a `fauxdoc.emitters.wrappers.BoundWrapper` instance. This is just for convenience.)
- Two new static methods on `fauxdoc.emitters.fixed.Iterative`, which move previously internal operations into utilities that can be used by external agents:
    - `check_iter_factory` — validates that an iterator factory function/method does not return an empty iterator, and raises a ValueError if it does.
    - `make_infinite_iter` — creates an iterator from an iterator factory that loops infinitely.
- A new `check_seq_iter_factory` static method on `fauxdoc.emitters.fixed.Sequential` allows validating that an iterator factory function/method probably generates an iterator that iterates over a sequence.
- A `fauxdoc.emitters.wrappers.BoundWrapper` class. Used to encapsulate a user-provided wrapper function, bind it to an object that provides RNG, and allow validating a given signature against the wrapper function's signature.
- A `set_wrapper_function` method on `fauxdoc.emitters.wrappers.WrapOne` and `fauxdoc.emitters.wrappers.WrapMany` — used to set the `wrapper` attribute from a function or other callable. (You can set `wrapper` directly, but that requires a `fauxdoc.emitters.wrappers.BoundWrapper` instance. This is just for convenience.)
- A new `set_fields` method, on `fauxdoc.profile.Schema` — used to set `fields` more naturally, without forcing the user to supply a `fauxdoc.groups.ObjectMap` instance. (You can still set `fields` directly, as an `ObjectMap`.)
- A `fauxdoc.typing.ImplementsRNG` protocol, for representing types that implement an `rng` attribute and `seed` method — such as `Field`s and various emitters.
- New `fauxdoc.typing.OrderedDict` and `fauxdoc.typing.UserList` types, to control for the fact that the `collections` versions of these types are not subscriptable in Python 3.7 and 3.8 (which is needed for type hints). For Python 3.7 and 3.8, a `__getitem__` method is monkey-patched onto `collections.OrderedDict` and `collections.UserList`, to make them subscriptable.
- New type aliases in `fauxdoc.typing`:
    - `F` — a TypeVar for float types.
    - `CT` — general-purpose covariant TypeVar.
    - `SourceT` — a contravariant TypeVar for e.g. callable arguments and other types that represent source data.
    - `OutputT` — a covariant TypeVar for e.g. callable return values that represent output data.
    - `FieldReturn` — represents the return type when calling `fauxdoc.profile.Field` instances.
- A new `fauxdoc.warn` module, which contains a function (`get_deprecated_attr`) for injecting a deprecation warning when a user gets a deprecated module or object attribute. (It's called from the `__getattr__` method of the applicable module or object.)

### Changed

- The minimum `pytest` version for Python 3.7 through 3.9 has been bumped up from 3.0.0 to 3.8.0. This is to allow testing deprecation warnings.
- Tox environment `build_package` no longer tries `pip install`ing the built package. It's assumed you'll use the new `*-test_built_package` environments to test the built package, which will of course have to install it.
- Comparing a `fauxdoc.dtrange.DateOrTimeRange` instance to another type of object is explicitly not supported and returns `NotImplemented`.
- On `fauxdoc.emitters.choice.Choice`, any sequences provided for the `weights` and `cum_weights` attributes are now cast to tuples on assignment so that they are immutable once assigned. (You can set a brand new sequence, but you cannot change individual elements.)
- `fauxdoc.emitters.fromfields.BasedOnFields` no longer inherits from `fauxdoc.emitters.fromfields.CopyFields`. The shared functionality that `CopyFields` previously provided is now implemented as `fauxdoc.emitters.fromfields.SourceFieldGroup`, which is now used for the `source` attribute on instances of both classes. If you set `source` directly, you must now give it a `SourceFieldGroup` instance.
- `fauxdoc.emitters.fromfields.BasedOnFields` now uses the `fauxdoc.emitters.wrappers.BoundWrapper` class for its `action` attribute. This moves all of the relevant functionality that was basically duplicated from the `wrappers` emitters out into the `BoundWrapper`. If you set `action` directly, you must now give it a `BoundWrapper` instance.
- `fauxdoc.emitters.fromfields.BasedOnFields` now validates the expected call signature of the provided `action` function when it's first set, not later when it's first called, so that the user gets notified immediately if their `action` function is not configured correctly.
- The `iterator` instance attribute of `fauxdoc.emitters.fixed.Iterative` and `fauxdoc.emitters.fixed.Sequential` is now a read-only property. It should never have been settable in the first place, as it's impossible to make this attribute settable in a way that makes any sense.
- `fauxdoc.emitters.fixed.Sequential` no longer inherits from `fauxdoc.emitters.fixed.Iterative`. Much of the specific functionality that `Sequential` needed to use from `Iterative` has been moved into public methods on `Iterative`, which `Sequential` now calls directly.
- `fauxdoc.emitters.wrappers.WrapOne` and `fauxdoc.emitters.wrappers.WrapMany` no longer inherit from `fauxdoc.emitters.wrappers.Wrap`. The shared functionality that the `Wrap` parent class provided is now implemented as `fauxdoc.emitters.wrappers.BoundWrapper`, which is now used for the `wrapper` attribute on instances of `Wrap`, `WrapOne`, and `WrapMany`. If you set `wrapper` directly, you must now give it a `BoundWrapper` instance.
- Each of `fauxdoc.emitters.wrappers.WrapOne` and `fauxdoc.emitters.wrappers.WrapMany` now validates the expected call signature of the provided `wrapper` function when it's set, not later when it's first called, so that the user gets notified immediately if their `wrapper` function is not configured correctly.
- `fauxdoc.profile.Field` now inherits from `fauxdoc.mixins.RandomWithChildrenMixin` instead of just `RandomMixin`. This moves the functionality related to setting, resetting, and seeding children emitters from `Field` into `RandomWithChildrenMixin`.
- On `fauxdoc.profile.Field`, the `multi_valued` attribute is now read-only. This attribute should never have been settable, as it is a fully computed attribute (based on `repeat_emitter`).
- On `fauxdoc.profile.Schema`, the `hidden_fields` and `public_fields` were already read-only, dynamic properties; now they are no longer even cached. They were of course never meant to be mutable — but now, if you try changing them as dictionaries, your changes will not be saved.
- The `fauxdoc.typing.EmitterLike` protocol is now more robust. It's now generic, so you can for instance use `EmitterLike[int]` to indicate that an Emitter-like type emits `int`s. It now includes properties `num_unique_values` and `emits_unique_values`. And `__call__` is overloaded to show that passing None returns a single atomic value, while passing an integer returns a list of values.
- The `fauxdoc.typing.RandomEmitterLike` protocol now inherits from both `ImplementsRNG` and `EmitterLike`, and it is now generic.
- The `fauxdoc.typing.FieldLike` protocol is now generic.

### Deprecated

- `fauxdoc.emitters.fixed.Sequential.iterator_factory`: This is currently settable but will become read-only in the future. Instead of setting `iterator_factory` to change the sequence that a `Sequential` instance emits, you should create a new `Sequential` instance using the new sequence.
- `fauxdoc.emitters.wrappers.Wrap`: Use `wrappers.WrapOne` or `WrapMany`.
- `fauxdoc.emitters.Wrap`: Use `emitters.WrapOne` or `WrapMany`.
- `fauxdoc.typing.BoolEmitterLike`: Use `EmitterLike[bool]`.
- `fauxdoc.typing.EmitterLikeCallable`: Use `EmitterLike`.
- `fauxdoc.typing.Number`: Use `float`.
- `fauxdoc.typing.IntEmitterLike`: Use `EmitterLike[int]`.
- `fauxdoc.typing.StrEmitterLike`: Use `EmitterLike[str]`.

### Fixed

- Many, many type hints throughout the package have been added or altered to resolve `mypy` errors. In some cases, specific function or method implementations have been tweaked to better accommodate added type hints.
- Many docstrings that were missing or incomplete have been added or updated.
- On `fauxdoc.emitters.choice.Choice` instances, setting either of the `weights` or `cum_weights` attributes now correctly updates object state. The provided list of weights or cumulative weights is validated to ensure it contains the same number of entries as there are `items`. Whichever "weights" attribute is set, the other is updated with the correct values. And, if the `replace` attribute is False, the global items shuffle is regenerated to reflect the new weights.
- On `fauxdoc.emitters.choice.Choice` instances, setting either of the `replace` or `replace_only_after_call` attributes may update the other to ensure valid object state. I.e., if the latter is True then the former must be True; if the former is False then the latter must also be False. Additionally, when `replace` changes to False, the global items shuffle is regenerated to reflect the current object state.
- On `fauxdoc.emitters.fixed.Static` instances, setting the `value` attribute now correctly updates the contents of the `items` attribute with the new value.
- On `fauxdoc.emitters.fixed.Iterative` and `fauxdoc.emitters.fixed.Sequential` instances, setting the `iterator_factory` attribute now performs appropriate validation on the iterator that the factory makes and then correctly regenerates the `iterator` attribute. On `Sequential` instances, it also repopulates the `items` attribute using the contents of the new iterator.
- During a call to `fauxdoc.emitters.text.Text`'s `emit_many` method, a private `_get_words_iterator` method is used to generate words from the `word_emitter`. When `word_emitter.replace_only_after_call` is True, then it attempts to generate a set of unique words for each text string. Previously, it based this on `word_emitter.num_unique_items`. This has been changed so that it bases this on `word_emitter.num_unique_values`. (The difference being that `num_unique_items` might include duplicate words in separate items, while `num_unique_values` only counts truly unique words.)
- On `fauxdoc.profile.Schema`, `fields` is both settable _and_ mutable — i.e., you can add or modify fields simply by editing `fields` as you would any dictionary. The `hidden_fields` and `public_fields` attributes are now calculated fully dynamically, meaning these now automatically update when `fields` changes. Previously they did not.


## [v1.0.0](https://github.com/unt-libraries/fauxdoc/releases/tag/v1.0.0) - 2022-11-02

First public release.

### Added

- `fauxdoc.emitter` — Emitter abstract base class to be used for all data emitters. Provides basic interface for creating callable emitter objects, which can have different underlying methods for emitting one versus many values, provide information about whether or not they emit unique values, and provide the number of unique values they emit. Emitters output values when called.
- `fauxdoc.group` and `fauxdoc.mixins` — Helper classes and mixins for creating emitters that use random-number generation, generate compound values using data from atomic children emitters, and emit values from a set sequence of items.
- `fauxdoc.dtrange` — Tools for producing and working with ranges of `datetime.datetime` and `datetime.time` objects, including a simple `range`-like factory (`fauxdoc.dtrange.dtrange`).
- `fauxdoc.mathtools` — Math-related utility functions. Includes functions for creating gaussian and poisson distributions, clamping a number to fit within a specific range, and randomly shuffling a list based on weights.
- `fauxdoc.profile` — Classes for building complete data profiles from emitter instances: Schema and Field. A Schema contains a set of named Field instances and outputs a data record when called. Each Field encapsulates an emitter and can be set to control the chances that any value will be output along how many values are output, per data record.
- `fauxdoc.emitters.choice` — Choice emitters, used to select random values. Provides an optimized implementation using optional weights and optional replacement. Also provides factory methods for creating choice emitters that use common weight distributions (poisson, gaussian).
- `fauxdoc.emitters.fixed` — Fixed emitters, used for emitting predefined values: a single static value, values from an iterator, or values from a sequence.
- `fauxdoc.emitters.text` — Emitters for generating randomized text-like strings, both single words and multi-word sentences.
- `fauxdoc.emitters.fromfields` — Emitters whose output should be based on values already generated via other fields (in context of a schema). They may copy values directly or copy and then modify values.
- `fauxdoc.emitters.wrappers` — Emitters that wrap other emitter instances in order to modify their output. For example, you may have an emitter that generates random datetime objects, and you might have several functions for converting your datetime objects to strings of various formats. You could easily create wrapper emitters that wrap your datetime emitter and use the conversion functions to generate formatted strings without having to create individual emitter classes to do this.
- Preliminary type-hints, not (yet) tested via a type checker. They are therefore currently quite broken.
- A modern `pyproject.toml`-based configuration plus support for Python 3.7, 3.8, 3.9, 3.10, and 3.11.

### Changed

- Just a historical note to say that this project originated from the UNT Libraries' catalog-api project, recent development of which has moved over to our private GitLab server. When we first pulled it into its own repository (also on our private GitLab), we named it `solrfixtures` and used Poetry to manage dependencies. Shortly before releasing v1.0.0, we renamed the project `fauxdoc`, moved it to GitHub, removed the reliance on Poetry (and standardized `pyproject.toml`), and implemented GitHub actions for CI. It has also been fully and completely refactored compared to its original form. It was never public until v1.0.0, so I'm not bothering documenting those changes here.

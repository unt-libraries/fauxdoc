fauxdoc
=======

* [About](#about)
* [Installation](#installation)
* [Basic Usage](#basic-usage)
* [Contributing](#contributing)

## About

*`fauxdoc`* is designed to help you efficiently generate fake (faux) record or document (doc) data conforming to bespoke requirements.

Fauxdoc is compatible (and tested) with Python versions 3.7 and above, including 3.11. It has almost no external requirements beyond the standard library: if you are using Python 3.7, it requires typing_extensions to provide some typing features that were added in 3.8. Otherwise, it requires nothing.

### Why not Faker or Mimesis?

[Faker](https://faker.readthedocs.io) and [Mimesis](https://mimesis.name) are established tools for generating fake data, and they are way more "batteries included" than Fauxdoc. Why not just implement a set of custom data providers for one of these?

#### Dynamically Generating Bespoke Data

Whereas other libraries make it dead simple to produce values that recognizably correspond to real-world items or properties (colors, names, addresses, etc.), Fauxdoc helps you dial in on patterns or features that may only pertain to your use case. This is helpful if you're trying to test something specific, like certain sets of edge cases.

Fauxdoc began as part of a utility for helping test and benchmark Solr. We wanted to test search performance by producing text that shared certain features of a live collection, such as using specific alphabets; having word, phrase, and/or sentence lengths (etc.) within certain limits; and having specific terms occur in certain specific distributions. And we wanted to be able to simulate facets by choosing data values from a finite list of random terms that would produce a term distribution similar to the real data. Other libraries did not seem to address these needs adequately.

#### Field / Schema / Document-Set Control

Other libraries mostly focus on generating values in isolation, but Fauxdoc facilitates having more control at the `Field` and `Schema` levels. For example, when generating documents to use to benchmark Solr, we found that we wanted to be able to do things like control uniqueness on a per-field basis, control uniqueness across an entire document set, generate data based on values in other fields, and have better control over multi-valued fields.

#### Performant Extensibility

We wrote Fauxdoc knowing that we'd be using it to generate hundreds of thousands or millions of fake Solr documents at one time, so performance was a critical concern. However, Fauxdoc is also meant to be highly extensible, and it's easy for extensibility to come at the expense of performance. So, Fauxdoc classes are designed to allow performant extensibility. You generally have a choice: you can implement something as (e.g.) a wrapper that's conceptually simple but a bit slower, or you can implement the same feature using a custom class, with lower-level methods that are faster but not as simple. It just depends on your use case and where you need the extra performance.

The built-in data providers (called `Emitters`) are designed to be as fast as we could make them. Their performance is roughly comparable to Mimesis', although this is an apples-to-oranges comparison. Like Mimesis, they are much faster than Faker.

[Top](#top)


## Installation

Install the latest published version of fauxdoc with:

```
python -m pip install fauxdoc
```

See [Contributing](#contributing) for the recommended installation process if you want to develop on fauxdoc. 

[Top](#top)


## Basic Usage

### Emitters

Conceptually, `Emitters` are like Faker or Mimesis `Providers`. They are the objects that output your data values: simply instantiate one and then call it. If you need multiple values at once, you can supply an integer when calling.

```python
from fauxdoc import emitters
myrandom = emitters.Choice(['a', 'b', 'c'])

myrandom()
# 'a'

myrandom(5)
# ['c', 'c', 'a', 'b', 'a']
```

Several emitter types are provided in `fauxdoc.emitters` that have general behavior and options. Above, the `Choice` emitter chooses randomly between multiple values. You can also supply weights along with parameters to control uniqueness.

For more complex behavior, you can of course create your own Emitter classes using `fauxdoc.emitter.Emitter` as your base class. Mixins are provided in `fauxdoc.mixins` for standard ways of doing things (such as randomization).

### Fields

Each `Field` wraps an emitter instance and provides options to gate the output and/or generate multiple values. These options are themselves implemented as emitters. As with Emitters, you also call a Field instance to output values.

```python
from fauxdoc import emitters, profile

user_tags = ['adventure', 'yellow', 'awesome', 'food', 'action films']
user_tags_field = profile.Field(
  'user_tags',
  emitters.Choice(user_tags, replace_only_after_call=True),
  gate=emitters.chance(0.8),
  repeat=emitters.poisson_choice(range(1, 6), mu=3)
)

user_tags_field()
# ['action films', 'food', 'yellow']

user_tags_field()
# ['adventure', 'yellow', 'awesome', 'food']

user_tags_field()
# ['yellow', 'awesome', 'food']

user_tags_field()
# ['food', 'adventure', 'awesome', 'yellow']

user_tags_field()
# 
```

### Schema

Your `Schema` is a specific collection of field instances. Calling the schema instance generates data representing one full document (a dictionary).

```python
import itertools
from fauxdoc import emitters, profile, dtrange

ENGLISH = emitters.make_alphabet([(ord('a'), ord('z'))])
GENRES = ['Science', 'Literature', 'Medicine', 'Fiction', 'Television']

myschema = profile.Schema(
  profile.Field('id', emitters.Iterative(lambda: itertools.count(1))),
  profile.Field(
    'title',
    emitters.WrapOne(
      emitters.Text(
        numwords_emitter=emitters.poisson_choice(range(1, 10), mu=2),
        word_emitter=emitters.Word(
          length_emitter=emitters.poisson_choice(range(1, 10), mu=5),
          alphabet_emitter=emitters.Choice(ENGLISH)
        )
      ),
      lambda title: title.capitalize()
    )
  ),
  profile.Field('doc_type', emitters.Choice(['report', 'article', 'book'])),
  profile.Field('date_created', emitters.Choice(dtrange.dtrange('1950-01-01', '2025-01-01'))),
  profile.Field(
    'genres',
    emitters.Choice(GENRES, replace_only_after_call=True),
    gate=emitters.chance(0.5),
    repeat=emitters.poisson_choice(range(1, 3), mu=1)
  )
)

myschema()
# {
#   'id': 1,
#   'title': 'Dvcoqh zbuaba',
#   'doc_type': 'book',
#   'date_created': datetime.date(1951, 8, 15),
#   'genres': ['Medicine', 'Fiction']
# }

myschema()
# {
#   'id': 2,
#   'title': 'Dird',
#   'doc_type': 'report',
#   'date_created': datetime.date(1998, 4, 6),
#   'genres': ['Fiction']
# }

myschema()
# {
#   'id': 3,
#   'title': 'Wvlptqk',
#   'doc_type': 'book',
#   'date_created': datetime.date(1977, 12, 10),
#   'genres': None
# }

myschema()
# {
#   'id': 4,
#   'title': 'Tnhkez',
#   'doc_type': 'article',
#   'date_created': datetime.date(1988, 1, 22),
#   'genres': None
# }

myschema()
# {
#   'id': 5,
#   'title': 'Ld gudv lnaxx',
#   'doc_type': 'article',
#   'date_created': datetime.date(1989, 9, 30),
#   'genres': ['Medicine']
# }
```

### Generating Data Based on Other Fields

For complex schemas, you may find generating values for each field in isolation to be too limiting. Fauxdoc allows you to create emitters that can access values generated via other fields. You can also create hidden fields, allowing you to generate data in a normalized or collective way and then pull it into the appropriate de-normalized fields.

```python
import itertools
from fauxdoc import emitter, emitters, profile

def item_data_generator():
  for num in itertools.count(1):
    yield {
      'item_id': num,
      'barcode': 2000000000 + num
    }

myschema = profile.Schema(
  # This field is hidden. It generates data for 1 to 10 "items" that
  # the other fields then pull from.
  profile.Field(
    '__all_items',
    emitters.Iterative(item_data_generator),
    repeat=emitters.poisson_choice(range(1, 10), mu=3),
    hide=True,
  )
)

myschema.add_fields(
  profile.Field(
    'display_items',
    emitters.BasedOnFields(
      myschema.fields['__all_items'],
      lambda items: items[:3]
    )
  ),
  profile.Field(
    'more_items',
    emitters.BasedOnFields(
      myschema.fields['__all_items'],
      lambda items: items[3:] if len(items) > 3 else None
    )
  ),
  profile.Field(
    'has_more_items',
    emitters.BasedOnFields(
      myschema.fields['__all_items'],
      lambda items: bool(len(items) > 3)
    )
  ),
  profile.Field(
    'item_ids',
    emitters.BasedOnFields(
      myschema.fields['__all_items'],
      lambda items: [i['item_id'] for i in items]
    )
  ),
  profile.Field(
    'item_barcodes',
    emitters.BasedOnFields(
      myschema.fields['__all_items'],
      lambda items: [i['barcode'] for i in items]
    )
  )
)

myschema()
# {
#   'display_items': [
#     {'item_id': 1, 'barcode': 2000000001}
#   ],
#   'more_items': None,
#   'has_more_items': False,
#   'item_ids': [1],
#   'item_barcodes': [2000000001]
# }

myschema()
# {
#   'display_items': [
#     {'item_id': 2, 'barcode': 2000000002},
#     {'item_id': 3, 'barcode': 2000000003},
#     {'item_id': 4, 'barcode': 2000000004}
#   ],
#   'more_items': [
#     {'item_id': 5, 'barcode': 2000000005}
#   ],
#   'has_more_items': True,
#   'item_ids': [2, 3, 4, 5],
#   'item_barcodes': [2000000002, 2000000003, 2000000004, 2000000005]
# }
```

[Top](#top)


## Contributing

### Installing for Development and Testing

Fork the project on GitHub and then clone it locally:

```bash
git clone https://github.com/[your-github-account]/fauxdoc.git
```

#### Poetry

This project uses [Poetry](https://python-poetry.org/) for builds and dependency management. Although the Poetry documentation recommends installing it system wide, you don't *have* to if you don't want to; I prefer instead to isolate it within each virtual environment that needs it. In part this is because I use pyenv + pyenv-virtualenv to manage my virtual environments, and I use tox for testing against multiple environments.

If you're interested, here is my setup. (Disclaimer: I make no claims this is _objectively_ good, but it's how I've made sense of Python's notoriously convoluted dependency-management ecosystem, and it works well for me. Obviously this is not the only way to do it.)

My MO is to keep components as isolated as possible so that nothing is hardwired and I can switch things out at will. Since both tox and Poetry can manage virtual environments, this is the best way I've found to ensure they play well together. And, I've been quite happy with using pyenv + pyenv-virtualenv as my version / environment manager.

1. Install and configure [pyenv](https://github.com/pyenv/pyenv). 
2. Install and configure [pyenv-virtualenv](https://github.com/pyenv/pyenv-virtualenv).
3. Use pyenv to download and install the currently supported Python versions, e.g. 3.7 to 3.11. (`pyenv install 3.7.15`, etc.)
4. Create your main development environment using a sensible Python version: `pyenv virtualenv 3.10.8 fauxdoc-3.10.8`.
5. `cd` into the local repository root for this project and activate that virtualenv: `pyenv activate fauxdoc-3.10.8`.
6. Do `python -m pip install poetry`. (This installs Poetry into that virtualenv _only_.)
7. Do `poetry lock` to resolve dependencies and generate a `poetry.lock` file.
8. Do `poetry install -E dev` to install dependencies, including those you need for development.
9. Run the tests just to make sure everything is working...

And that's it. Now, as long as `fauxdoc-3.10.8` is activated, you can use Poetry commands to manage dependencies and run builds for that project; Poetry knows to install things there.

When you want to set up an environment for a different Python version, just deactivate your environment (`pyenv deactivate`) and run through steps 4-8 again, substituting a different base Python in step 4, like `pyenv virtualenv 3.7.15 fauxdoc-3.7.15`. Setting up each environment takes only a minute or two, and once they're set up you can of course switch between them as needed.

#### Running Tests

Tests for this project use `pytest`. Run all of them from the repository root via:

```bash
pytest
```

This runs the test suite within whatever python virtual environment you have activated. If, on the other hand, you want to run all the tests against all the supported Python versions at once, then you'd use Tox.

#### Tox

Just like Poetry, I prefer to isolate [tox](https://tox.wiki/en/latest/) within a virtual environment rather than installing it system wide. (What can I say, I have commitment issues.)

The tox configuration for this project is in `pyproject.toml`. There, I have specified several test environments: flake8, pylint, and each of py37 through py311 using both the oldest possible dependencies and newest possible dependencies. That's a total of 12 environments. When you run tox, you can target a specific environment, target a specific list of environments, or run against all 12.

When tox runs, it automatically builds each virtual environment it needs, and then it runs whatever commands it needs within that environment (for linting, or testing, etc.). All you have to do is expose all the necessary Python binaries on the path, and tox will pick the correct one. And you can use pyenv to activate multiple Python versions at once in a way that tox recognizes — *any* of the base Python versions or virtualenvs you have installed via pyenv can serve as the basis for tox's environments.

The added setup for this is relatively minimal.

1. You do need to have an environment with tox installed. If you don't have one, create one — e.g., `tox-3.10.8` — then activate it and do `python -m pip install tox`. (Nothing else.)
2. Now, in your project repository root (for fauxdoc), create a file called `.python-version`. Add all of the Python versions you want to use, 3.7 to 3.11. For 3.10, use your `tox-3.10.8`. This should look something like this:
    ```
    3.7.15
    3.8.15
    3.9.15
    tox-3.10.8
    3.11.0
    ```
4. Issue a `pyenv deactivate` command so that pyenv picks up what's in the file. (A manually-activated environment overrides anything set in a `.python-version` file.)
5. At this point you should have all five environments active at once in that directory. You can issue commands that run using binaries from any of those versions, and they will run correctly. For commands that multiple environments share, like `python`, the one for the first Python version listed is what runs. In other words — if you run `python` or `python3.7` then you'll get a 3.7.15 shell. If you run `python3.9` you'll get the 3.9.15 shell. When you run `tox`, the tox in your `tox-3.10.8` environment will run.

Run tox like this to run linters and all tests against all environments:

```bash
tox
```

Or like this just to run linters:

```bash
tox -e flake8,pylint_critical
```

Or like this to run tests against other specific environments:

```bash
tox -e py39-oldest,py39-newest
```

In my workflow, I tend to develop using an environment like `fauxdoc-3.10.8`, from earlier. As I work, I generally just run individual tests against the one environment, issuing the appropriate `pytest` command. Then, when I've finished some unit of work — usually before a commit — I use tox to run linters plus the full suite of tests. 99% of the time you won't have errors in earlier Python versions that don't show up when testing against your dev environment, so there's no need to take the extra time to run the full tox suite more often than that. (Admittedly sometimes I run it even less frequently.)

```bash
$ pyenv activate fauxdoc-3.10.8        # Toggle a dev virtualenv ON.
# ...                                    Work on the project.
$ pytest tests/test_something.py -x    # Run specific tests against 3.10.8.
# ...                                    Continue developing / running tests.
$ pyenv deactivate                     # When ready for tox, Toggle dev OFF.
$ tox -e flake8                        # Run flake8. Fix errors until this passes.
$ tox -e pylint_critical               # Run critical pylint tests. Fix.
$ tox                                  # Run ALL tox tests. Fix.
$ git add .
$ git commit
# etc.
```

Further, the tox / multi-Python setup above works for ANY projects on a given machine, as long as you create that `.python-version` file in the project root. You don't even have to create different virtualenvs for tox — that is, until you want to upgrade a project to a different Python version, at which point you may need to use multiple `tox-` environments if different projects need different 3.10 versions.

[Top](#top)
